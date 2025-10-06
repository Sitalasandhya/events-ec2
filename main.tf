# Custom IAM Policy
resource "aws_iam_policy" "tf_ec2_actions" {
  name        = "tf_ec2_actions"
  description = "Custom policy for Lambda to manage ec2 instance created through terraform"

  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Sid" : "VisualEditor0",
        "Effect" : "Allow",
        "Action" : [
          "ec2:DescribeInstances",
          "ec2:TerminateInstances",
          "ec2:StartInstances",
          "ec2:RunInstances",
          "ec2:StopInstances",
          "ec2:DescribeInstanceStatus",
          "ec2:CreateKeyPair",
          "ec2:DescribeKeyPairs",
          "s3:PutObject",
          "s3:GetObject",
		  "lambda:CreateFunction"
        ],
        "Resource" : "*"
      }
    ]
  })
}

# IAM Role for Lambda
resource "aws_iam_role" "tf_lambda_ec2_actions" {
  name = "tf_lambda_ec2_actions"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Principal = {
          Service = "lambda.amazonaws.com"
        },
        Effect = "Allow",
        Sid    = ""
      }
    ]
  })
}


# Attach Custom Policy to Role
resource "aws_iam_role_policy_attachment" "custom_policy_attachment" {
  role       = aws_iam_role.tf_lambda_ec2_actions.name
  policy_arn = aws_iam_policy.tf_ec2_actions.arn
}

# Creating S3 Bucket
resource "aws_s3_bucket" "lambda_bucket" {
  bucket = "tf-ec2actions-${random_id.suffix.hex}"
}

# Random suffix to ensure bucket name uniqueness
resource "random_id" "suffix" {
  byte_length = 4
}

# Lambda Function with Environment Variables
resource "aws_lambda_function" "tf_events_ec2_actions" {
  function_name = "tf_events_ec2_actions"
  role          = aws_iam_role.tf_lambda_ec2_actions.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.13"
  filename      = "lambda_function_payload.zip"
  source_code_hash = filebase64sha256("lambda_function_payload.zip")
  timeout = 120

  environment {
    variables = {
      AMI     = "ami-0b09ffb6d8b58ca91"
      INSTANCE_TYPE = "t2.micro"
      S3_BUCKET   = aws_s3_bucket.lambda_bucket.bucket
	  REGION	= "us-east-1"
    }
  }
}

# API Gateway REST API
resource "aws_api_gateway_rest_api" "api_gateway" {
  name        = "tf_events_ec2"
  description = "API Gateway to manage ec2 actions"
}

# API Resource in REST API
resource "aws_api_gateway_resource" "actions_resource" {
  rest_api_id = aws_api_gateway_rest_api.api_gateway.id
  parent_id   = aws_api_gateway_rest_api.api_gateway.root_resource_id
  path_part   = "actions"
}

#API Resource with method with IAM Authentication
resource "aws_api_gateway_method" "actions_post" {
  rest_api_id   = aws_api_gateway_rest_api.api_gateway.id
  resource_id   = aws_api_gateway_resource.actions_resource.id
  http_method   = "POST"
  authorization = "AWS_IAM"
}

# Integration with Lambda
resource "aws_api_gateway_integration" "lambda_integration" {
  rest_api_id             = aws_api_gateway_rest_api.api_gateway.id
  resource_id             = aws_api_gateway_resource.actions_resource.id
  http_method             = aws_api_gateway_method.actions_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.tf_events_ec2_actions.invoke_arn
}

# Lambda Permission for API Gateway
resource "aws_lambda_permission" "api_gateway_permission" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.tf_events_ec2_actions.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api_gateway.execution_arn}/*/*"
}

# Deployment
resource "aws_api_gateway_deployment" "api_deployment" {
  depends_on  = [aws_api_gateway_integration.lambda_integration]
  rest_api_id = aws_api_gateway_rest_api.api_gateway.id
}

#Deployment with stage
resource "aws_api_gateway_stage" "api_stage" {
  rest_api_id    = aws_api_gateway_rest_api.api_gateway.id
  stage_name     = "test"
  deployment_id  = aws_api_gateway_deployment.api_deployment.id
}

# Output API Endpoint
output "api_endpoint" {
  value = "https://${aws_api_gateway_rest_api.api_gateway.id}.execute-api.${var.region}.amazonaws.com/${aws_api_gateway_stage.api_stage.stage_name}/actions"
}