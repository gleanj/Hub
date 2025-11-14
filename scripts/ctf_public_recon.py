#!/usr/bin/env python3
"""
Public Reconnaissance - No Auth Required
Look for publicly accessible information about target portal
"""

import requests
import json
import urllib3
import os
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv()

TARGET_PORTAL = os.getenv('TARGET_PORTAL_ID', '46962361')

print("="*70)
print(" Public Reconnaissance for Portal", TARGET_PORTAL)
print("="*70)

findings = []

# ============================================================================
# 1. PUBLIC PAGES - Check if portal has public pages
# ============================================================================

def check_public_pages():
    """Check for publicly accessible HubSpot pages"""
    print("\n[*] Checking for public pages...")

    public_urls = [
        f"https://app.hubspot.com/signup/{TARGET_PORTAL}",
        f"https://app.hubspot.com/meetings/{TARGET_PORTAL}",
        f"https://meetings.hubspot.com/{TARGET_PORTAL}",
        f"https://knowledge.hubspot.com/contacts/{TARGET_PORTAL}",
        f"https://share.hubspot.com/{TARGET_PORTAL}",
    ]

    for url in public_urls:
        try:
            r = requests.get(url, allow_redirects=True, timeout=10, verify=False)
            print(f"  {url.split('/')[3]}: {r.status_code} (length: {len(r.text)})")

            if r.status_code == 200 and len(r.text) > 1000:
                print(f"     Found public page!")
                if 'firstname' in r.text.lower() or 'email' in r.text.lower():
                    findings.append({'type': 'public_page', 'url': url, 'content': r.text[:1000]})
        except Exception as e:
            print(f"  {url}: Error")

# ============================================================================
# 2. FORMS - Check for public forms
# ============================================================================

def check_public_forms():
    """Check for publicly accessible forms"""
    print("\n[*] Checking for public forms...")

    # HubSpot forms are often at: https://forms.hubspot.com/...
    form_urls = [
        f"https://api.hsforms.com/submissions/v3/integration/submit/{TARGET_PORTAL}",
        f"https://forms.hubspot.com/uploads/form/v2/{TARGET_PORTAL}",
    ]

    for url in form_urls:
        try:
            # Try to get form info (will likely fail, but worth trying)
            r = requests.get(url, timeout=10, verify=False)
            print(f"  {url.split('/')[3]}: {r.status_code}")

            if r.status_code != 404:
                print(f"    Response: {r.text[:200]}")
        except:
            pass

# ============================================================================
# 3. DNS/SUBDOMAIN ENUMERATION
# ============================================================================

def check_subdomains():
    """Check common HubSpot subdomains for this portal"""
    print("\n[*] Checking common portal subdomains...")

    # HubSpot allows custom subdomains like: {custom}.hubspot.com
    # But we don't know the custom name, so try common patterns
    test_paths = [
        f"https://app.hubspot.com/contacts/{TARGET_PORTAL}/contacts/list/view/all",
        f"https://app.hubspot.com/contacts/{TARGET_PORTAL}",
        f"https://app.hubspot.com/settings/{TARGET_PORTAL}",
        f"https://app.hubspot.com/reports-dashboard/{TARGET_PORTAL}",
    ]

    for url in test_paths:
        try:
            # These will redirect to login, but we can check the response
            r = requests.get(url, allow_redirects=False, timeout=10, verify=False)
            print(f"  {url.split('/')[4] if len(url.split('/')) > 4 else 'portal'}: {r.status_code}")

            if r.status_code == 302:  # Redirect to login
                location = r.headers.get('Location', '')
                print(f"     Redirects to: {location[:100]}")
        except:
            pass

# ============================================================================
# 4. API ENDPOINTS - No Auth
# ============================================================================

def check_public_apis():
    """Check public API endpoints"""
    print("\n[*] Checking public API endpoints...")

    # Some HubSpot APIs might not require auth
    public_api_urls = [
        f"https://api.hubapi.com/integrations/v1/{TARGET_PORTAL}/settings",
        f"https://api.hubspot.com/contacts/v1/lists/all/contacts/all?count=100&portalId={TARGET_PORTAL}",
        f"https://api.hubapi.com/crm/v3/objects/contacts?portalId={TARGET_PORTAL}",
    ]

    for url in public_api_urls:
        try:
            # No auth headers
            r = requests.get(url, timeout=10, verify=False)
            print(f"  {url.split('/')[4]}: {r.status_code}")

            if r.status_code == 200:
                print(f"     SUCCESS - No auth required!")
                data = r.json()
                findings.append({'type': 'public_api', 'url': url, 'data': data})
            elif r.status_code != 401 and r.status_code != 403:
                print(f"    Response: {r.text[:150]}")
        except Exception as e:
            pass

# ============================================================================
# 5. TRACKING CODE - Check for tracking code data
# ============================================================================

def check_tracking():
    """Check HubSpot tracking endpoints"""
    print("\n[*] Checking tracking endpoints...")

    tracking_urls = [
        f"https://api.hubspot.com/analytics/v2/reports/web-analytics/total/summary?portalId={TARGET_PORTAL}",
        f"https://track.hubspot.com/__ptq.gif?a={TARGET_PORTAL}",
    ]

    for url in tracking_urls:
        try:
            r = requests.get(url, timeout=10, verify=False)
            print(f"  {url.split('/')[3]}: {r.status_code}")

            if r.status_code == 200:
                findings.append({'type': 'tracking', 'url': url})
        except:
            pass

# ============================================================================
# 6. CACHED/ARCHIVED DATA
# ============================================================================

def check_archives():
    """Check for cached/archived versions"""
    print("\n[*] Checking archive sites...")

    # Archive.org, Google cache, etc.
    archive_urls = [
        f"https://web.archive.org/web/*/app.hubspot.com/contacts/{TARGET_PORTAL}/*",
        f"http://webcache.googleusercontent.com/search?q=cache:app.hubspot.com/contacts/{TARGET_PORTAL}",
    ]

    for url in archive_urls:
        try:
            r = requests.get(url, timeout=15, verify=False)
            print(f"  {url.split('/')[2]}: {r.status_code}")

            if r.status_code == 200 and len(r.text) > 1000:
                if 'firstname' in r.text or TARGET_PORTAL in r.text:
                    findings.append({'type': 'archive', 'url': url})
        except:
            pass

# ============================================================================
# 7. SEARCH FOR PORTAL INFO ONLINE
# ============================================================================

def search_portal_info():
    """Look for information about the portal online"""
    print("\n[*] Searching for portal information...")

    # Check if portal has a public website
    print(f"  Portal ID {TARGET_PORTAL} might have:")
    print(f"    - A public website (search Google for '{TARGET_PORTAL} site:hubspot.com')")
    print(f"    - Public forms or pages")
    print(f"    - Leaked credentials or data")
    print(f"\n  Manual search recommendations:")
    print(f"    • Google: 'portal {TARGET_PORTAL} hubspot'")
    print(f"    • Google: 'site:app.hubspot.com {TARGET_PORTAL}'")
    print(f"    • Shodan: 'hubspot {TARGET_PORTAL}'")
    print(f"    • GitHub: 'hubspot {TARGET_PORTAL}'")

# ============================================================================
# 8. CORS AND OPTIONS
# ============================================================================

def check_cors():
    """Check CORS configuration"""
    print("\n[*] Checking CORS configuration...")

    test_url = f"https://api.hubapi.com/crm/v3/objects/contacts"

    try:
        # Send OPTIONS request
        r = requests.options(test_url, headers={'Origin': 'https://evil.com'}, timeout=10, verify=False)
        print(f"  OPTIONS: {r.status_code}")
        print(f"  Access-Control-Allow-Origin: {r.headers.get('Access-Control-Allow-Origin', 'Not set')}")
        print(f"  Access-Control-Allow-Credentials: {r.headers.get('Access-Control-Allow-Credentials', 'Not set')}")

        if r.headers.get('Access-Control-Allow-Origin') == '*':
            print(f"     CORS allows all origins!")
            findings.append({'type': 'cors', 'details': 'Allows all origins'})
    except:
        pass

# ============================================================================
# MAIN
# ============================================================================

check_public_pages()
check_public_forms()
check_subdomains()
check_public_apis()
check_tracking()
check_archives()
search_portal_info()
check_cors()

print("\n" + "="*70)
print(f" Reconnaissance Complete!")
print(f" Findings: {len(findings)}")
print("="*70)

if findings:
    print("\n Found public information:\n")
    for i, finding in enumerate(findings, 1):
        print(f"{i}. {finding['type']}: {json.dumps(finding, indent=2)[:200]}...")

    with open('/home/user/Hub/findings/public_recon.json', 'w') as f:
        json.dump(findings, f, indent=2)
else:
    print("\n No public information found.")
    print("\nThis is expected - HubSpot properly restricts access.")
    print("The CTF challenge requires finding an authorization bypass vulnerability.")
