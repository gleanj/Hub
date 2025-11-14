#!/usr/bin/env python3
"""
Extract API endpoint patterns from JavaScript in HTML pages
"""

import re
import json
from collections import Counter

print("="*80)
print("Extracting API Patterns from JavaScript")
print("="*80)

# Read one of the saved HTML pages
html_file = '/home/user/Hub/findings/contact_1_page.html'

try:
    with open(html_file, 'rb') as f:
        content = f.read()

    # Try to decode
    html = content.decode('utf-8', errors='ignore')

    print(f"\nAnalyzing: {html_file}")
    print(f"Size: {len(html)} bytes")

    # Extract all URLs that look like API endpoints
    api_patterns = [
        r'https?://[^"\'<> ]+/api/[^"\'<> ]+',
        r'/api/[^"\'<> ]+',
        r'"(/[a-z-]+/v\d+/[^"]+)"',
        r'endpoint["\']?\s*[:=]\s*["\']([^"\']+)["\']',
        r'url["\']?\s*[:=]\s*["\']([^"\']+api[^"\']+)["\']',
    ]

    all_endpoints = []

    for pattern in api_patterns:
        matches = re.findall(pattern, html)
        all_endpoints.extend(matches)

    # Deduplicate
    unique_endpoints = list(set(all_endpoints))

    print(f"\nFound {len(unique_endpoints)} unique API endpoint patterns:")
    for i, endpoint in enumerate(sorted(unique_endpoints)[:50], 1):
        print(f"  {i}. {endpoint[:100]}")

    # Look for fetch/axios calls
    print("\n[*] Looking for fetch() calls...")
    fetch_patterns = [
        r'fetch\(["\']([^"\']+)["\']',
        r'\.get\(["\']([^"\']+)["\']',
        r'\.post\(["\']([^"\']+)["\']',
        r'axios\.[a-z]+\(["\']([^"\']+)["\']',
    ]

    fetch_calls = []
    for pattern in fetch_patterns:
        matches = re.findall(pattern, html)
        fetch_calls.extend(matches)

    if fetch_calls:
        print(f"Found {len(set(fetch_calls))} unique fetch/axios calls:")
        for call in sorted(set(fetch_calls))[:20]:
            print(f"  - {call}")

    # Look for GraphQL queries
    print("\n[*] Looking for GraphQL...")
    if 'graphql' in html.lower():
        print("  Found 'graphql' in page!")
        gql_contexts = re.findall(r'.{50}graphql.{50}', html, re.I)
        for ctx in gql_contexts[:5]:
            print(f"  Context: {' '.join(ctx.split())[:100]}")

    # Look for contact-specific patterns
    print("\n[*] Looking for contact-specific patterns...")
    contact_patterns = [
        r'contacts?/\d+',
        r'vid[=/]\d+',
        r'contactId["\']?\s*[:=]\s*\d+',
        r'object["\']?\s*[:=]\s*["\']0-1["\']',  # HubSpot object type for contacts
    ]

    for pattern in contact_patterns:
        matches = re.findall(pattern, html, re.I)
        if matches:
            print(f"  Pattern '{pattern}': {len(set(matches))} matches")
            for m in sorted(set(matches))[:5]:
                print(f"    - {m}")

    # Look for property names
    print("\n[*] Looking for property patterns...")
    if 'super_secret' in html.lower():
        print("  *** 'super_secret' found in HTML! ***")
        contexts = re.findall(r'.{100}super_secret.{100}', html, re.I)
        for ctx in contexts[:3]:
            print(f"  Context: {' '.join(ctx.split())[:150]}")
    else:
        print("  'super_secret' NOT in HTML")

    if 'firstname' in html.lower():
        print("  'firstname' found in HTML")
        # Try to find what API loads it
        fn_contexts = re.findall(r'.{50}firstname.{50}', html, re.I)
        for ctx in fn_contexts[:3]:
            cleaned = ' '.join(ctx.split())
            if 'api' in cleaned.lower() or 'fetch' in cleaned.lower():
                print(f"  API context: {cleaned[:100]}")

    # Save all extracted endpoints
    with open('/home/user/Hub/findings/extracted_api_endpoints.txt', 'w') as f:
        for endpoint in sorted(unique_endpoints):
            f.write(endpoint + '\n')

    print(f"\nSaved extracted endpoints to: findings/extracted_api_endpoints.txt")

except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*80)
print("Next: Try using the extracted endpoints with fresh session cookies")
print("="*80)
