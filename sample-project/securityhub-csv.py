import boto3
import csv
from datetime import datetime

# Initialize AWS clients
securityhub = boto3.client('securityhub')

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

if __name__ == "__main__":
    print("""Fetch findings from AWS Security Hub""")
    findings = fetch_securityhub_findings()

    print("""Sanitize finding data (remove sensitive fields)""")
    sanitized = [sanitize_finding(f) for f in findings]
    
    print("""Save findings to CSV""")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_to_csv(sanitized, f'sample_security_findings_{timestamp}.csv')