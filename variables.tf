variable "aws_region" {
  description = "Region used for AWS services"
  default     = "us-west-1"
}

variable "aws_account_id" {
  default = "081924037451"
}

variable "environment" {
  description = "Whether terraform is creating the dev, test, or prod environment"
}

variable "mongo_region" {
  description = "Region used for mongo's AWS services"
  default     = "US_WEST_2"
}
