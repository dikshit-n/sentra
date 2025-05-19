import boto3
import csv
from datetime import datetime
import os
import io  # For in-memory CSV handling

# Initialize AWS clients
securityhub = boto3.client('securityhub')
s3 = boto3.client('s3')

def fetch_securityhub_findings():
    findings = []
    paginator = securityhub.get_paginator('get_findings')
    
    for page in paginator.paginate():
        findings.extend(page['Findings'])
    
    return findings

def sanitize_finding(finding):
    return {
        'Id': finding.get('Id', ''),
        'Title': finding.get('Title', '').replace(',', '-'),  # Remove commas for CSV
        'Severity': finding.get('Severity', {}).get('Label', ''),
        'Status': finding.get('Workflow', {}).get('Status', ''),
        'LastObserved': finding.get('LastObservedAt', '')
    }

def save_to_csv(findings, filename):
    if not findings:
        print("No findings to save!")
        return
    
    keys = findings[0].keys()
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(findings)
    print(f"Saved {len(findings)} findings to {filename}")

def save_to_s3(findings, bucket, key):
    if not findings:
        print("No findings to save!")
        return False

    try:
        # Ensure all findings have same keys
        fieldnames = list(findings[0].keys())
        csv_buffer = io.StringIO()
        
        writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
        writer.writeheader()
        
        for finding in findings:
            if finding:  # Skip None values
                writer.writerow(finding)
        
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=csv_buffer.getvalue().encode('utf-8'),
            ContentType='text/csv'
        )
        print(f"Successfully uploaded {len(findings)} findings to s3://{bucket}/{key}")
        return True
    except Exception as e:
        print(f"Upload failed: {e}")
        return False

if __name__ == "__main__":
    print("""Fetch findings from AWS Security Hub""")
    findings = fetch_securityhub_findings()

    print("""Sanitize finding data (remove sensitive fields)""")
    sanitized = [sanitize_finding(f) for f in findings]

    print("""Saving to S3 Bucket""")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    s3_bucket = os.getenv('AWS_S3_BUCKET_NAME')
    s3_key = f"security-findings/{timestamp}.csv"
    save_to_s3(sanitized, s3_bucket, s3_key)

    # print("""Save findings to CSV""")
    # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # save_to_csv(sanitized, f'sample_security_findings_{timestamp}.csv')
