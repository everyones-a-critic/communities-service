variable "aws_region" {
  description = "Region used for AWS services"
  default     = "us-west-1"
}

variable "aws_account_id" {
  default = "081924037451"
}

variable "service_name" {
    description = "Name of the service provided by the endpoint. Uses method-resource nomenclature"
}

variable "command" {
    description = "python module and function name to be executed by the lambda function"
}

variable "gateway_resource" {
    description = "API Gateway resource id housing the endpoint through which the lambda function will be exposed"
}

variable "mongo_cluster_uri" {
    description = "Terraform resource representing the mongo variables which will be used by the lambda"
}

variable "mongo_cluster_name" {
    description = "Terraform resource representing the mongo variables which will be used by the lambda"
}

variable "lambda_role" {
    description = "ARN of the IAM role used when executing the lambda. Should have access to the MongoDB account."
}

variable "http_method" {
    description = "What type of http method should be used to execute the lambda"
}