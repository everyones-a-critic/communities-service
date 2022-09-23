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

resource "aws_api_gateway_resource" "communities" {
  path_part   = "communities"
  parent_id   = data.tfe_outputs.api_gateway.values.root_resource_id
  rest_api_id = data.tfe_outputs.api_gateway.values.gateway_id
}

module "get_communities_service" {
  source = "./modules/api_gateway_lambda_service"
  service_name     = "get-communities"
  command          = "services.list_communities"
  http_method = "GET"
  gateway_resource = aws_api_gateway_resource.communities
  lambda_role = aws_iam_role.mongo-atlas-access.arn
  mongo_cluster = mongodbatlas_advanced_cluster.main
}

resource "aws_api_gateway_resource" "community_id" {
  path_part   = "{community_id}"
  parent_id   = aws_api_gateway_resource.communities.id
  rest_api_id = data.tfe_outputs.api_gateway.values.gateway_id
}

resource "aws_api_gateway_resource" "members" {
  path_part   = "members"
  parent_id   = aws_api_gateway_resource.community_id.id
  rest_api_id = data.tfe_outputs.api_gateway.values.gateway_id
}

module "join_community" {
  source = "./modules/api_gateway_lambda_service"
  service_name     = "join-community"
  command          = "services.join_community"
  http_method = "POST"
  gateway_resource = aws_api_gateway_resource.members
  lambda_role = aws_iam_role.mongo-atlas-access.arn
  mongo_cluster = mongodbatlas_advanced_cluster.main
}

module "leave_community" {
  source = "./modules/api_gateway_lambda_service"
  service_name     = "leave-community"
  command          = "services.leave_community"
  http_method = "DELETE"
  gateway_resource = aws_api_gateway_resource.members
  lambda_role = aws_iam_role.mongo-atlas-access.arn
  mongo_cluster = mongodbatlas_advanced_cluster.main
}


resource "mongodbatlas_project" "main" {
  name   = "everyones-a-critic"
  org_id = var.mongo_org_id
}

resource "mongodbatlas_advanced_cluster" "main" {
  project_id   = mongodbatlas_project.main.id
  name         = "prod"
  cluster_type = "REPLICASET"

  replication_specs {
    region_configs {
      electable_specs {
        instance_size = "M0"
      }

      provider_name         = "TENANT"
      backing_provider_name = "AWS"
      region_name           = var.mongo_region
      priority              = 7
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
    name = mongodbatlas_advanced_cluster.main.name
    type = "CLUSTER"
  }
}

resource "mongodbatlas_search_index" "community_name" {
  name   = "default"
  project_id = mongodbatlas_project.main.id
  cluster_name = mongodbatlas_advanced_cluster.main.name

  analyzer = "lucene.standard"
  collection_name = "community"
  database = "prod"
  mappings_dynamic = true

  search_analyzer = "lucene.standard"
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
  project_id = mongodbatlas_cloud_provider_access_setup.main.project_id
  role_id    = mongodbatlas_cloud_provider_access_setup.main.role_id

  aws {
    iam_assumed_role_arn = aws_iam_role.mongo-atlas-access.arn
  }

  depends_on = [aws_iam_role.mongo-atlas-access]
}

resource "mongodbatlas_project_ip_access_list" "main" {
  project_id = mongodbatlas_cloud_provider_access_setup.main.project_id
  cidr_block = "0.0.0.0/0"
  comment    = "Access from anywhere, as private networks aren't supported on the free tier"
}

resource "mongodbatlas_database_user" "test" {
  username           = "cli_user"
  password           = var.cli_user_password
  project_id         = mongodbatlas_project.main.id
  auth_database_name = "admin"

  roles {
    role_name     = "readWriteAnyDatabase"
    database_name = "admin"
  }
}