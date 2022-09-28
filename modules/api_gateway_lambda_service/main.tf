data "tfe_outputs" "ecr_repositories" {
  organization = "everyones-a-critic"
  workspace    = "ecr-repositories"
}

data "tfe_outputs" "api_gateway" {
  organization = "everyones-a-critic"
  workspace    = "api-gateway"
}

resource "aws_lambda_function" "main" {
  image_uri     = "${data.tfe_outputs.ecr_repositories.values.communities_service_repository_url}:latest"
  package_type  = "Image"
  function_name = var.service_name
  role          = var.lambda_role

  image_config {
    # use this to point to different handlers within
    # the same image, or omit `image_config` entirely
    # if only serving a single Lambda function
    command = [var.command]
  }

  environment {
    variables = {
      MONGO_URI = var.mongo_cluster.connection_strings.0.standard_srv
      MONGO_CLUSTER_NAME = var.mongo_cluster.name
    }
  }
}

resource "aws_cloudwatch_log_group" "example" {
  name              = "/aws/lambda/${var.service_name}"
  retention_in_days = 1
}

resource "aws_api_gateway_method" "method" {
  rest_api_id   = data.tfe_outputs.api_gateway.values.gateway_id
  resource_id   = var.gateway_resource.id
  http_method   = var.http_method
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = data.tfe_outputs.api_gateway.values.authorizer_id
}

resource "aws_api_gateway_integration" "integration" {
  rest_api_id             = data.tfe_outputs.api_gateway.values.gateway_id
  resource_id             = var.gateway_resource.id
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
  source_arn = "arn:aws:execute-api:${var.aws_region}:${var.aws_account_id}:${data.tfe_outputs.api_gateway.values.gateway_id}/*/${aws_api_gateway_method.method.http_method}${var.gateway_resource.path}"
}