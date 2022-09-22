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
    "API Gateway resource id housing the endpoint through which the lambda function will be exposed"
}