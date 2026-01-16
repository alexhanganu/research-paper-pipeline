"""
AWS Lambda handler for processing research papers from S3.
Triggered by S3 upload events.
"""

import json
import os
import boto3
import time
from pathlib import Path
from datetime import datetime
from extract_text import extract_text_from_pdf
from langchain_pipeline import process_paper_with_langchain
from tenacity import retry, stop_after_attempt, wait_exponential

# Initialize AWS clients
s3_client = boto3.client('s3')
cloudwatch = boto3.client('cloudwatch')
sqs_client = boto3.client('sqs')

# Configuration from environment variables
RESULTS_BUCKET = os.environ.get('RESULTS_BUCKET')
PROVIDER = os.environ.get('PROVIDER', 'anthropic')
API_KEY = os.environ.get('ANTHROPIC_API_KEY') if PROVIDER == 'anthropic' else os.environ.get('OPENAI_API_KEY')
DLQ_URL = os.environ.get('DLQ_URL')  # Dead Letter Queue for failed processing
NAMESPACE = 'ResearchPaperProcessing'

def send_cloudwatch_metric(metric_name, value, unit='Count', dimensions=None):
    """Send metrics to CloudWatch"""
    try:
        metric_data = {
            'MetricName': metric_name,
            'Value': value,
            'Unit': unit,
            'Timestamp': datetime.utcnow()
        }
        
        if dimensions:
            metric_data['Dimensions'] = dimensions
        
        cloudwatch.put_metric_data(
            Namespace=NAMESPACE,
            MetricData=[metric_data]
        )
    except Exception as e:
        print(f"Error sending CloudWatch metric: {e}")

def send_to_dlq(message, error):
    """Send failed processing to Dead Letter Queue"""
    if not DLQ_URL:
        return
    
    try:
        sqs_client.send_message(
            QueueUrl=DLQ_URL,
            MessageBody=json.dumps({
                'original_message': message,
                'error': str(error),
                'timestamp': datetime.utcnow().isoformat()
            })
        )
    except Exception as e:
        print(f"Error sending to DLQ: {e}")

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def download_from_s3(bucket, key, local_path):
    """Download file from S3 with retry logic"""
    s3_client.download_file(bucket, key, local_path)
    return True

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def upload_to_s3(bucket, key, data):
    """Upload results to S3 with retry logic"""
    s3_client.put_object(
        Bucket=bucket,
        Key=key,
        Body=data,
        ContentType='application/json'
    )
    return True

def lambda_handler(event, context):
    """
    AWS Lambda handler for processing papers from S3.
    
    Args:
        event: S3 event containing bucket and key information
        context: Lambda context object
        
    Returns:
        Response with status code and processing results
    """
    start_time = time.time()
    
    try:
        # Parse S3 event
        record = event['Records'][0]
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        
        print(f"Processing file: s3://{bucket}/{key}")
        
        # Send metric for processing start
        send_cloudwatch_metric(
            'ProcessingStarted',
            1,
            dimensions=[{'Name': 'Provider', 'Value': PROVIDER}]
        )
        
        # Create local path in /tmp (Lambda's writable directory)
        filename = key.split('/')[-1]
        local_path = f'/tmp/{filename}'
        
        # Download PDF from S3
        try:
            download_from_s3(bucket, key, local_path)
        except Exception as e:
            error_msg = f"Failed to download from S3: {str(e)}"
            print(error_msg)
            send_cloudwatch_metric('DownloadFailure', 1)
            send_to_dlq({'bucket': bucket, 'key': key}, error_msg)
            raise
        
        # Extract text from PDF
        extraction_result = extract_text_from_pdf(local_path)
        
        if not extraction_result['success']:
            error_msg = f"Text extraction failed: {extraction_result['error']}"
            print(error_msg)
            send_cloudwatch_metric('ExtractionFailure', 1)
            send_to_dlq({'bucket': bucket, 'key': key}, error_msg)
            
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'error': error_msg,
                    'filename': filename
                })
            }
        
        # Save extracted text to S3
        text_key = f"extracted_texts/{filename.replace('.pdf', '.txt')}"
        try:
            upload_to_s3(
                RESULTS_BUCKET,
                text_key,
                extraction_result['text']
            )
        except Exception as e:
            print(f"Warning: Failed to upload extracted text: {e}")
        
        # Process paper with LangChain
        try:
            result = process_paper_with_langchain(
                extraction_result['text'],
                filename,
                api_key=API_KEY,
                provider=PROVIDER
            )
        except Exception as e:
            error_msg = f"LLM processing failed: {str(e)}"
            print(error_msg)
            send_cloudwatch_metric('ProcessingFailure', 1)
            send_to_dlq({'bucket': bucket, 'key': key}, error_msg)
            raise
        
        # Add extraction metadata
        result['num_pages'] = extraction_result['num_pages']
        result['text_length'] = len(extraction_result['text'])
        result['s3_source'] = f"s3://{bucket}/{key}"
        result['processing_timestamp'] = datetime.utcnow().isoformat()
        
        # Upload results to S3
        results_key = f"results/{filename.replace('.pdf', '.json')}"
        try:
            upload_to_s3(
                RESULTS_BUCKET,
                results_key,
                json.dumps(result, indent=2)
            )
        except Exception as e:
            error_msg = f"Failed to upload results: {str(e)}"
            print(error_msg)
            send_cloudwatch_metric('UploadFailure', 1)
            raise
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Send success metrics
        send_cloudwatch_metric(
            'ProcessingSuccess',
            1,
            dimensions=[{'Name': 'Provider', 'Value': PROVIDER}]
        )
        
        send_cloudwatch_metric(
            'ProcessingDuration',
            processing_time,
            unit='Seconds',
            dimensions=[{'Name': 'Provider', 'Value': PROVIDER}]
        )
        
        if result.get('quality_score'):
            send_cloudwatch_metric(
                'QualityScore',
                result['quality_score'],
                unit='None',
                dimensions=[{'Name': 'Provider', 'Value': PROVIDER}]
            )
        
        # Count biomarkers extracted
        num_biomarkers = len(result.get('biomarkers', []))
        send_cloudwatch_metric(
            'BiomarkersExtracted',
            num_biomarkers,
            dimensions=[{'Name': 'Provider', 'Value': PROVIDER}]
        )
        
        # Cleanup local file
        try:
            os.remove(local_path)
        except Exception as e:
            print(f"Warning: Failed to cleanup local file: {e}")
        
        print(f"Successfully processed {filename} in {processing_time:.2f}s")
        print(f"Results saved to: s3://{RESULTS_BUCKET}/{results_key}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Successfully processed paper',
                'filename': filename,
                'results_location': f"s3://{RESULTS_BUCKET}/{results_key}",
                'processing_time': processing_time,
                'quality_score': result.get('quality_score'),
                'biomarkers_found': num_biomarkers,
                'status': result.get('status')
            })
        }
        
    except Exception as e:
        # Send failure metric
        send_cloudwatch_metric(
            'ProcessingFailure',
            1,
            dimensions=[{'Name': 'Provider', 'Value': PROVIDER}]
        )
        
        error_msg = str(e)
        print(f"Error processing paper: {error_msg}")
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': error_msg,
                'timestamp': datetime.utcnow().isoformat()
            })
        }

def batch_handler(event, context):
    """
    Handler for processing batches of papers from SQS.
    
    Args:
        event: SQS event containing multiple messages
        context: Lambda context object
        
    Returns:
        Batch item failures for retry
    """
    batch_item_failures = []
    
    for record in event['Records']:
        try:
            # Parse SQS message
            message_body = json.loads(record['body'])
            
            # Create S3 event format
            s3_event = {
                'Records': [{
                    's3': {
                        'bucket': {'name': message_body['bucket']},
                        'object': {'key': message_body['key']}
                    }
                }]
            }
            
            # Process the paper
            result = lambda_handler(s3_event, context)
            
            if result['statusCode'] != 200:
                batch_item_failures.append({
                    'itemIdentifier': record['messageId']
                })
                
        except Exception as e:
            print(f"Error processing message {record['messageId']}: {e}")
            batch_item_failures.append({
                'itemIdentifier': record['messageId']
            })
    
    return {
        'batchItemFailures': batch_item_failures
    }