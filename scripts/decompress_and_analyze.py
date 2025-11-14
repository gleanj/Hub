#!/usr/bin/env python3
"""
Decompress and analyze HTML pages for contact data
"""

import os
import gzip
import json
import re

print("="*80)
print("Decompressing and Analyzing Contact Pages")
print("="*80)

findings = []

# Get all saved HTML files
html_files = []
for f in os.listdir('/home/user/Hub/findings'):
    if f.startswith('contact_') and f.endswith('_page.html'):
        html_files.append(f)

print(f"\nFound {len(html_files)} HTML files to analyze")

for filename in sorted(html_files):
    filepath = f'/home/user/Hub/findings/{filename}'
    contact_id = filename.replace('contact_', '').replace('_page.html', '')

    print(f"\n{'='*80}")
    print(f"Analyzing: {filename} (Contact ID: {contact_id})")
    print(f"{'='*80}")

    try:
        # Read file
        with open(filepath, 'rb') as f:
            content = f.read()

        # Try to decompress if gzipped
        try:
            # Check if it's gzipped (starts with 1f 8b)
            if content[:2] == b'\x1f\x8b':
                print("  File is gzip compressed, decompressing...")
                content = gzip.decompress(content)
                print(f"  Decompressed size: {len(content)} bytes")

                # Save decompressed version
                decompressed_path = filepath.replace('.html', '_decompressed.html')
                with open(decompressed_path, 'wb') as f:
                    f.write(content)
                print(f"  Saved decompressed to: {decompressed_path}")

        except:
            print("  Not gzipped or decompression failed, using as-is")

        # Convert to string
        html = content.decode('utf-8', errors='ignore')

        print(f"  HTML length: {len(html)} bytes")

        # Search for super_secret
        if 'super_secret' in html.lower():
            print(f"\n  *** FOUND 'super_secret' in HTML ***")

            # Find all occurrences
            matches = list(re.finditer(r'.{0,200}super_secret.{0,200}', html, re.I | re.DOTALL))
            print(f"  Found {len(matches)} occurrences")

            for i, match in enumerate(matches[:5], 1):
                context = match.group(0)
                # Clean up context (remove newlines, extra spaces)
                context = ' '.join(context.split())
                print(f"\n  Match {i}:")
                print(f"    Context: {context[:300]}")

                # Try to extract value
                value_patterns = [
                    r'super_secret["\']?\s*[:=]\s*["\']([^"\'<>]+)["\']',
                    r'super_secret["\']?\s*[:=]\s*([^,}\s<>]+)',
                    r'"super_secret":\s*"([^"]+)"',
                ]

                for vp in value_patterns:
                    vm = re.search(vp, context, re.I)
                    if vm:
                        value = vm.group(1)
                        print(f"    *** VALUE FOUND: {value} ***")

                        findings.append({
                            'contact_id': contact_id,
                            'file': filename,
                            'value': value,
                            'context': context[:200],
                            'pattern': vp
                        })
                        break

        # Also search for firstname to see if contact data is present
        if 'firstname' in html.lower():
            print(f"\n  'firstname' found in HTML - contact data present")

            # Try to find the value
            fn_match = re.search(r'firstname["\']?\s*[:=]\s*["\']([^"\'<>]+)["\']', html, re.I)
            if fn_match:
                print(f"    Firstname value: {fn_match.group(1)}")

        # Look for JSON data structures
        # Search for window.__INITIAL_DATA__ or similar patterns
        json_patterns = [
            r'window\.__[A-Z_]+__\s*=\s*({[^;]+});',
            r'var\s+\w+\s*=\s*({.*?})\s*;',
            r'const\s+\w+\s*=\s*({.*?})\s*;',
        ]

        for pattern in json_patterns:
            matches = re.findall(pattern, html, re.DOTALL)
            if matches:
                print(f"\n  Found potential JSON data ({pattern[:30]}...)")
                for j, match in enumerate(matches[:3], 1):
                    # Try to parse as JSON
                    try:
                        data = json.loads(match)
                        # Search for super_secret in the JSON
                        data_str = json.dumps(data)
                        if 'super_secret' in data_str.lower():
                            print(f"    *** super_secret found in JSON data block {j} ***")
                            print(f"    Data: {data_str[:500]}")

                            findings.append({
                                'contact_id': contact_id,
                                'file': filename,
                                'location': 'JSON embedded data',
                                'data': data
                            })
                    except:
                        pass

    except Exception as e:
        print(f"  Error processing {filename}: {str(e)[:100]}")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "="*80)
print(f"Analysis Complete")
print(f"Total Findings: {len(findings)}")
print("="*80)

if findings:
    print("\n*** EXTRACTED DATA ***\n")

    for i, finding in enumerate(findings, 1):
        print(f"{i}. Contact {finding['contact_id']}")
        print(f"   File: {finding['file']}")

        if 'value' in finding:
            print(f"   *** super_secret VALUE: {finding['value']} ***")
            print(f"   Context: {finding.get('context', '')[:150]}")

        if 'data' in finding:
            print(f"   Data: {json.dumps(finding['data'], indent=2)[:300]}")

        print()

    # Save findings
    with open('/home/user/Hub/findings/decompressed_analysis.json', 'w') as f:
        json.dump(findings, f, indent=2)

    print("Saved to: findings/decompressed_analysis.json")

    # Check for FLAG
    for finding in findings:
        if 'value' in finding:
            value = finding['value']
            if 'flag' in value.lower() or 'ctf' in value.lower() or len(value) > 10:
                print("\n" + "="*80)
                print("*** POTENTIAL CTF FLAG ***")
                print("="*80)
                print(f"Contact: {finding['contact_id']}")
                print(f"Value: {value}")
                print("="*80)

else:
    print("\nNo super_secret data found in any HTML pages.")
    print("\nThis suggests:")
    print("  1. Data is loaded via AJAX after page renders")
    print("  2. Need to monitor network requests in browser")
    print("  3. API endpoints are called dynamically by JavaScript")
