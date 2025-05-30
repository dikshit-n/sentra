import boto3
import csv
from datetime import datetime
import json
import io

# Initialize AWS clients
securityhub = boto3.client('securityhub')
s3 = boto3.client('s3')
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')  # Adjust region as needed

def fetch_securityhub_findings():
    findings = []
    paginator = securityhub.get_paginator('get_findings')
    
    for page in paginator.paginate():
        findings.extend(page['Findings'])
    
    return findings

def sanitize_finding(finding):
    return {
        'Id': finding.get('Id', ''),
        'Title': finding.get('Title', '').replace(',', '-'),
        'Severity': finding.get('Severity', {}).get('Label', ''),
        'Status': finding.get('Workflow', {}).get('Status', ''),
        'LastObserved': finding.get('LastObservedAt', '')
    }

def generate_summary(findings):
    if not findings:
        return "No findings to summarize."

    # Prepare a prompt for Claude Instant
    prompt = f"""
    You are a cybersecurity analyst. Below is a list of AWS Security Hub findings:
    
    {json.dumps(findings[:10], indent=2)}  # Limit to first 10 findings for context
    
    **Task:** Generate a concise summary report (2-3 paragraphs) covering:
    1. Overall risk level (CRITICAL/HIGH/MEDIUM/LOW)
    2. Most common vulnerabilities
    3. Recommended actions
    """

    try:
        response = bedrock.invoke_model(
            modelId="anthropic.claude-instant-v1",
            body=json.dumps({
                "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
                "max_tokens_to_sample": 500,
                "temperature": 0.5,
            })
        )
        result = json.loads(response['body'].read())
        return result.get('completion', "Failed to generate summary.")
    except Exception as e:
        print(f"Bedrock error: {e}")
        return "Summary generation failed."

def trigger_lambda_notification(bucket, key, recipient_email):
    eventbridge = boto3.client('events')
    
    event_detail = {
        "bucket": bucket,
        "key": key,
        "recipient": recipient_email,
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        response = eventbridge.put_events(
            Entries=[
                {
                    'Source': 'security.hub.reporter',
                    'DetailType': 'SecurityFindingsReportGenerated',
                    'Detail': json.dumps(event_detail),
                    'EventBusName': 'default'
                }
            ]
        )
        print(f"EventBridge trigger sent. Event ID: {response['Entries'][0]['EventId']}")
        return True
    except Exception as e:
        print(f"Failed to trigger EventBridge: {e}")
        return False

def save_to_s3(data, bucket, key, content_type='text/csv'):
    try:
        if isinstance(data, dict):
            body = json.dumps(data).encode('utf-8')
        else:
            body = data.encode('utf-8') if isinstance(data, str) else data

        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=body,
            ContentType=content_type
        )
        print(f"Uploaded to s3://{bucket}/{key}")
        return True
    except Exception as e:
        print(f"S3 upload failed: {e}")
        return False

if __name__ == "__main__":
    print("Fetching Security Hub findings...")
    findings = fetch_securityhub_findings()
    sanitized = [sanitize_finding(f) for f in findings if f]

    if not sanitized:
        print("No findings to process.")
        exit()

    # Generate CSV in memory
    csv_buffer = io.StringIO()
    writer = csv.DictWriter(csv_buffer, fieldnames=sanitized[0].keys())
    writer.writeheader()
    writer.writerows(sanitized)
    csv_data = csv_buffer.getvalue()

    # Generate summary using Bedrock
    # print("Generating summary with Claude Instant...")
    # summary = generate_summary(sanitized)
    # summary_json = {
    #     "timestamp": datetime.now().isoformat(),
    #     "summary": summary,
    #     "total_findings": len(sanitized),
    #     "severity_distribution": {
    #         "CRITICAL": len([f for f in sanitized if f['Severity'] == 'CRITICAL']),
    #         "HIGH": len([f for f in sanitized if f['Severity'] == 'HIGH']),
    #         "MEDIUM": len([f for f in sanitized if f['Severity'] == 'MEDIUM']),
    #         "LOW": len([f for f in sanitized if f['Severity'] == 'LOW']),
    #     }
    # }

    # S3 requirements
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    s3_bucket = "demo-bucket-122814843942"

    # Upload CSV
    csv_key = f"security-findings/{timestamp}/findings.csv"
    
    if save_to_s3(csv_data, s3_bucket, csv_key):
        # Trigger Lambda
        print("Trigger Lambda via EventBridge to send email notification")
        trigger_lambda_notification(
            bucket=s3_bucket,
            key=csv_key,
            recipient_email="dikshitkumarn@gmail.com"
        )


    # Upload JSON summary
    # json_key = f"security-findings/{timestamp}/summary.json"
    # save_to_s3(summary_json, s3_bucket, json_key, 'application/json')

    print("Done!")
