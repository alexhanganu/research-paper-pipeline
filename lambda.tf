# Terraform configuration for AWS Lambda deployment of research paper processing pipeline

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

variable "anthropic_api_key" {
  description = "Anthropic API key for Claude"
  type        = string
  sensitive   = true
  default     = ""
}

variable "openai_api_key" {
  description = "OpenAI API key for GPT"
  type        = string
  sensitive   = true
  default     = ""
}

variable "provider_choice" {
  description = "AI provider to use: anthropic or openai"
  type        = string
  default     = "anthropic"
  validation {
    condition     = contains(["anthropic", "openai"], var.provider_choice)
    error_message = "Provider must be either 'anthropic' or 'openai'."
  }
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
}

# S3 Bucket for input papers
resource "aws_s3_bucket" "papers" {
  bucket = "research-papers-input-${var.environment}"
  
  tags = {
    Name        = "Research Papers Input"
    Environment = var.environment
  }
}

# S3 Bucket for results
resource "aws_s3_bucket" "results" {
  bucket = "research-papers-results-${var.environment}"
  
  tags = {
    Name        = "Research Papers Results"
    Environment = var.environment
  }
}

# Enable versioning for results bucket
resource "aws_s3_bucket_versioning" "results_versioning" {
  bucket = aws_s3_bucket.results.id
  
  versioning_configuration {
    status = "Enabled"
  }
}

# SQS Queue for batch processing
resource "aws_sqs_queue" "paper_processing_queue" {
  name                       = "research-paper-processing-${var.environment}"
  visibility_timeout_seconds = 900  # 15 minutes (same as Lambda timeout)
  message_retention_seconds  = 86400  # 24 hours
  receive_wait_time_seconds  = 20
  
  tags = {
    Name        = "Paper Processing Queue"
    Environment = var.environment
  }
}

# Dead Letter Queue for failed processing
resource "aws_sqs_queue" "paper_processing_dlq" {
  name                       = "research-paper-processing-dlq-${var.environment}"
  message_retention_seconds  = 1209600  # 14 days
  
  tags = {
    Name        = "Paper Processing DLQ"
    Environment = var.environment
  }
}

# Configure DLQ for main queue
resource "aws_sqs_queue_redrive_policy" "paper_processing_queue_redrive" {
  queue_url = aws_sqs_queue.paper_processing_queue.id
  
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.paper_processing_dlq.arn
    maxReceiveCount     = 3
  })
}

# IAM Role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "research-paper-lambda-role-${var.environment}"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
  
  tags = {
    Name        = "Lambda Execution Role"
    Environment = var.environment
  }
}

# IAM Policy for Lambda
resource "aws_iam_role_policy" "lambda_policy" {
  name = "research-paper-lambda-policy-${var.environment}"
  role = aws_iam_role.lambda_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.papers.arn,
          "${aws_s3_bucket.papers.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:PutObjectAcl"
        ]
        Resource = [
          "${aws_s3_bucket.results.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = aws_sqs_queue.paper_processing_queue.arn
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage"
        ]
        Resource = aws_sqs_queue.paper_processing_dlq.arn
      },
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# Lambda Layer for dependencies
resource "aws_lambda_layer_version" "dependencies" {
  filename            = "lambda_layer.zip"  # You need to create this
  layer_name          = "research-paper-dependencies-${var.environment}"
  compatible_runtimes = ["python3.11"]
  
  description = "Dependencies for research paper processing: anthropic, openai, langchain, pypdf, etc."
}

# Lambda Function
resource "aws_lambda_function" "paper_processor" {
  filename         = "lambda_deployment.zip"  # You need to create this
  function_name    = "research-paper-processor-${var.environment}"
  role             = aws_iam_role.lambda_role.arn
  handler          = "lambda_handler.lambda_handler"
  runtime          = "python3.11"
  timeout          = 900  # 15 minutes
  memory_size      = 3008  # Maximum memory for better performance
  
  layers = [aws_lambda_layer_version.dependencies.arn]
  
  environment {
    variables = {
      RESULTS_BUCKET     = aws_s3_bucket.results.id
      PROVIDER           = var.provider_choice
      ANTHROPIC_API_KEY  = var.anthropic_api_key
      OPENAI_API_KEY     = var.openai_api_key
      DLQ_URL            = aws_sqs_queue.paper_processing_dlq.url
      ENVIRONMENT        = var.environment
    }
  }
  
  ephemeral_storage {
    size = 10240  # 10 GB for large PDFs
  }
  
  tags = {
    Name        = "Research Paper Processor"
    Environment = var.environment
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${aws_lambda_function.paper_processor.function_name}"
  retention_in_days = 30
  
  tags = {
    Name        = "Lambda Logs"
    Environment = var.environment
  }
}

# S3 Event Notification Permission
resource "aws_lambda_permission" "allow_s3" {
  statement_id  = "AllowExecutionFromS3"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.paper_processor.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.papers.arn
}

# S3 Bucket Notification
resource "aws_s3_bucket_notification" "paper_upload" {
  bucket = aws_s3_bucket.papers.id
  
  lambda_function {
    lambda_function_arn = aws_lambda_function.paper_processor.arn
    events              = ["s3:ObjectCreated:*"]
    filter_suffix       = ".pdf"
  }
  
  depends_on = [aws_lambda_permission.allow_s3]
}

# Event Source Mapping for SQS (optional batch processing)
resource "aws_lambda_event_source_mapping" "sqs_trigger" {
  event_source_arn = aws_sqs_queue.paper_processing_queue.arn
  function_name    = aws_lambda_function.paper_processor.arn
  batch_size       = 10
  enabled          = true
  
  function_response_types = ["ReportBatchItemFailures"]
}

# CloudWatch Alarms

# Alarm for processing failures
resource "aws_cloudwatch_metric_alarm" "processing_failures" {
  alarm_name          = "research-paper-processing-failures-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ProcessingFailure"
  namespace           = "ResearchPaperProcessing"
  period              = 300  # 5 minutes
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "Alert when more than 5 papers fail to process in 5 minutes"
  treat_missing_data  = "notBreaching"
  
  dimensions = {
    Provider = var.provider_choice
  }
  
  tags = {
    Name        = "Processing Failures Alarm"
    Environment = var.environment
  }
}

# Alarm for Lambda errors
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "research-paper-lambda-errors-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 3
  alarm_description   = "Alert when Lambda function has errors"
  treat_missing_data  = "notBreaching"
  
  dimensions = {
    FunctionName = aws_lambda_function.paper_processor.function_name
  }
  
  tags = {
    Name        = "Lambda Errors Alarm"
    Environment = var.environment
  }
}

# Alarm for DLQ messages
resource "aws_cloudwatch_metric_alarm" "dlq_messages" {
  alarm_name          = "research-paper-dlq-messages-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Average"
  threshold           = 0
  alarm_description   = "Alert when messages appear in DLQ"
  treat_missing_data  = "notBreaching"
  
  dimensions = {
    QueueName = aws_sqs_queue.paper_processing_dlq.name
  }
  
  tags = {
    Name        = "DLQ Messages Alarm"
    Environment = var.environment
  }
}

# EventBridge Rule for daily processing (optional scheduled trigger)
resource "aws_cloudwatch_event_rule" "daily_processing" {
  name                = "research-paper-daily-processing-${var.environment}"
  description         = "Trigger daily paper processing"
  schedule_expression = "cron(0 2 * * ? *)"  # 2 AM UTC daily
  
  tags = {
    Name        = "Daily Processing Rule"
    Environment = var.environment
  }
}

# EventBridge Target
resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.daily_processing.name
  target_id = "TriggerLambda"
  arn       = aws_lambda_function.paper_processor.arn
}

# Permission for EventBridge to invoke Lambda
resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.paper_processor.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_processing.arn
}

# Outputs
output "papers_bucket_name" {
  description = "Name of the S3 bucket for input papers"
  value       = aws_s3_bucket.papers.id
}

output "results_bucket_name" {
  description = "Name of the S3 bucket for results"
  value       = aws_s3_bucket.results.id
}

output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.paper_processor.function_name
}

output "sqs_queue_url" {
  description = "URL of the SQS queue"
  value       = aws_sqs_queue.paper_processing_queue.url
}

output "dlq_url" {
  description = "URL of the Dead Letter Queue"
  value       = aws_sqs_queue.paper_processing_dlq.url
}