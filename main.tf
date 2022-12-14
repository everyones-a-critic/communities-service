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
  workspace    = "api-gateway"
}

data "tfe_outputs" "mongo_db" {
  organization = "everyones-a-critic"
  workspace    = "mongo-db"
}

# Creating a cluster specifically for communities-service
resource "mongodbatlas_serverless_instance" "main" {
  project_id = data.tfe_outputs.mongo_db.values.project_id
  name       = "communities-service-${var.environment}"

  provider_settings_backing_provider_name = "AWS"
  provider_settings_provider_name         = "SERVERLESS"
  provider_settings_region_name           = var.mongo_region
}

# Creating mongo resources to grant AWS lambdas access to mongo clusters
resource "mongodbatlas_cloud_provider_access_setup" "main" {
  project_id    = data.tfe_outputs.mongo_db.values.project_id
  provider_name = "AWS"
}

resource "aws_iam_role" "mongo-atlas-access" {
  name = "mongo-atlas-access-${mongodbatlas_serverless_instance.main.name}"

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

resource "mongodbatlas_database_user" "admin" {
  username           = aws_iam_role.mongo-atlas-access.arn
  project_id         = data.tfe_outputs.mongo_db.values.project_id
  auth_database_name = "$external"
  aws_iam_type       = "ROLE"

  roles {
    role_name     = "readWriteAnyDatabase"
    database_name = "admin"
  }

  scopes {
    name = mongodbatlas_serverless_instance.main.name
    type = "CLUSTER"
  }
}

# Creating AWS Resources

resource "aws_api_gateway_resource" "communities" {
  path_part   = "communities"
  parent_id   = data.tfe_outputs.api_gateway.values.root_resource_id
  rest_api_id = data.tfe_outputs.api_gateway.values.gateway_id
}

module "get_communities_service" {
  source             = "./modules/api_gateway_lambda_service"
  service_name       = "get-communities"
  command            = "services.list_communities"
  http_method        = "GET"
  gateway_resource   = aws_api_gateway_resource.communities
  lambda_role        = aws_iam_role.mongo-atlas-access.arn
  mongo_cluster_uri  = mongodbatlas_serverless_instance.main.connection_strings_standard_srv
  mongo_cluster_name = mongodbatlas_serverless_instance.main.name
}

resource "aws_api_gateway_resource" "community_id" {
  path_part   = "{community_id}"
  parent_id   = aws_api_gateway_resource.communities.id
  rest_api_id = data.tfe_outputs.api_gateway.values.gateway_id
}

module "get_community_service" {
  source             = "./modules/api_gateway_lambda_service"
  service_name       = "get-community"
  command            = "services.get_community"
  http_method        = "GET"
  gateway_resource   = aws_api_gateway_resource.community_id
  lambda_role        = aws_iam_role.mongo-atlas-access.arn
  mongo_cluster_uri  = mongodbatlas_serverless_instance.main.connection_strings_standard_srv
  mongo_cluster_name = mongodbatlas_serverless_instance.main.name
}

resource "aws_api_gateway_resource" "members" {
  path_part   = "members"
  parent_id   = aws_api_gateway_resource.community_id.id
  rest_api_id = data.tfe_outputs.api_gateway.values.gateway_id
}

module "join_community" {
  source             = "./modules/api_gateway_lambda_service"
  service_name       = "join-community"
  command            = "services.join_community"
  http_method        = "POST"
  gateway_resource   = aws_api_gateway_resource.members
  lambda_role        = aws_iam_role.mongo-atlas-access.arn
  mongo_cluster_uri  = mongodbatlas_serverless_instance.main.connection_strings_standard_srv
  mongo_cluster_name = mongodbatlas_serverless_instance.main.name
}

module "leave_community" {
  source             = "./modules/api_gateway_lambda_service"
  service_name       = "leave-community"
  command            = "services.leave_community"
  http_method        = "DELETE"
  gateway_resource   = aws_api_gateway_resource.members
  lambda_role        = aws_iam_role.mongo-atlas-access.arn
  mongo_cluster_uri  = mongodbatlas_serverless_instance.main.connection_strings_standard_srv
  mongo_cluster_name = mongodbatlas_serverless_instance.main.name
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

resource "mongodbatlas_cloud_provider_access_authorization" "auth_role" {
  project_id = data.tfe_outputs.mongo_db.values.project_id
  role_id    = mongodbatlas_cloud_provider_access_setup.main.role_id

  aws {
    iam_assumed_role_arn = aws_iam_role.mongo-atlas-access.arn
  }

  depends_on = [aws_iam_role.mongo-atlas-access]
}