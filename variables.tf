variable "aws_region" {
  description = "Region used for AWS services"
  default     = "us-west-1"
}

variable "aws_account_id" {
 default = "081924037451"
}

variable "service_name" {
  description = "Name of the service provided by the endpoint"
  default     = "get-communities"
}

variable "mongo_region" {
  description = "Region used for mongo's AWS services"
  default     = "US_WEST_2"
}

variable "mongo_org_id" {
  description = "Organization id from mongo"
  default     = "61527ca063086f463022f613"
}
