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
          "s3:GetObject"
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