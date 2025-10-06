terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0" # or any version you need
    }
  }
}

provider "aws" {
  region = "us-east-1" # or your preferred region
}
