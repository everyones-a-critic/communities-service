terraform {
  required_providers {
    mongodbatlas = {
      source  = "mongodb/mongodbatlas"
      version = "1.4.5"
    }
  }

  cloud {
    organization = "everyones-a-critic"
    workspaces {
      name = "communities-service"
    }
  }
}

provider "mongodbatlas" {}

provider "aws" {
  region = var.aws_region
}

data "tfe_outputs" "api_gateway" {
  organization = "everyones-a-critic"
  workspace = "api-gateway"
}

data "tfe_outputs" "ecr_repositories" {
  organization = "everyones-a-critic"
  workspace = "ecr-repositories"
}

resource "mongodbatlas_project" "main" {
  name   = "eac-ratings"
  org_id = var.mongo_org_id
}

resource "mongodbatlas_advanced_cluster" "main" {
  project_id = mongodbatlas_project.main.id
  name       = "eac-ratings-dev"
  cluster_type = "REPLICASET"

  replication_specs {
    region_configs {
      electable_specs {
        instance_size = "M0"
      }

      provider_name               = "TENANT"
      backing_provider_name       = "AWS"
      region_name        = var.mongo_region
    }
  }
}

resource "mongodbatlas_cloud_provider_access_setup" "main" {
  project_id    = mongodbatlas_project.main.id
  provider_name = "AWS"
}

resource "mongodbatlas_database_user" "admin" {
  username           = aws_iam_role.mongo-atlas-access.arn
  project_id         = mongodbatlas_project.main.id
  auth_database_name = "$external"
  aws_iam_type       = "ROLE"

  roles {
    role_name     = "readWriteAnyDatabase"
    database_name = "admin"
  }

  scopes {
    name   = mongodbatlas_advanced_cluster.main.name
    type = "CLUSTER"
  }
}

resource "aws_iam_role" "mongo-atlas-access" {
  name = "mongo-atlas-access-${mongodbatlas_advanced_cluster.main.name}"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "${mongodbatlas_cloud_provider_access_setup.main.aws.atlas_aws_account_arn}"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "${mongodbatlas_cloud_provider_access_setup.main.aws.atlas_assumed_role_external_id}"
        }
      }
    },
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

resource "mongodbatlas_cloud_provider_access_authorization" "auth_role" {
  project_id = mongodbatlas_cloud_provider_access_setup.main.project_id
  role_id    = mongodbatlas_cloud_provider_access_setup.main.role_id

  aws {
    iam_assumed_role_arn = aws_iam_role.mongo-atlas-access.arn
  }
}

resource "aws_lambda_function" "main" {
  image_uri     = "${data.tfe_outputs.ecr_repositories.values.communities_service_repository_url}:latest"
  package_type  = "Image"
  function_name = var.service_name
  role          = aws_iam_role.mongo-atlas-access.arn

  image_config {
    # use this to point to different handlers within
    # the same image, or omit `image_config` entirely
    # if only serving a single Lambda function
    command = ["services.list_communities"]
  }

  environment {
    variables = {
      MONGO_URI = mongodbatlas_advanced_cluster.main.connection_strings.0.standard_srv
    }
  }
}

resource "aws_cloudwatch_log_group" "example" {
  name              = "/aws/lambda/${var.service_name}"
  retention_in_days = 1
}

# See also the following AWS managed policy: AWSLambdaBasicExecutionRole
resource "aws_iam_policy" "lambda_logging" {
  name        = "lambda_logging"
  path        = "/"
  description = "IAM policy for logging from a lambda"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*",
      "Effect": "Allow"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.mongo-atlas-access.name
  policy_arn = aws_iam_policy.lambda_logging.arn
}

resource "aws_api_gateway_resource" "communities" {
  path_part   = "communities"
  parent_id   = data.tfe_outputs.api_gateway.values.root_resource_id
  rest_api_id = data.tfe_outputs.api_gateway.values.gateway_id
}

resource "aws_api_gateway_method" "method" {
  rest_api_id = data.tfe_outputs.api_gateway.values.gateway_id
  resource_id   = aws_api_gateway_resource.communities.id
  http_method   = "GET"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = data.tfe_outputs.api_gateway.values.authorizer_id
}

resource "aws_api_gateway_integration" "integration" {
  rest_api_id = data.tfe_outputs.api_gateway.values.gateway_id
  resource_id   = aws_api_gateway_resource.communities.id
  http_method             = aws_api_gateway_method.method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.main.invoke_arn
}

resource "aws_lambda_permission" "apigw_lambda" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.main.function_name
  principal     = "apigateway.amazonaws.com"

  # More: http://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-control-access-using-iam-policies-to-invoke-api.html
  source_arn = "arn:aws:execute-api:${var.aws_region}:${var.aws_account_id}:${data.tfe_outputs.api_gateway.values.gateway_id}/*/${aws_api_gateway_method.method.http_method}${aws_api_gateway_resource.communities.path}"
}