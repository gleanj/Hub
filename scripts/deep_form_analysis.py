#!/usr/bin/env python3
"""
Deep analysis of public forms - extract ALL data
Forms found: 1, 3, 4, 5, 6, 8, 13, 18, 1000
"""

import requests
import json
import re
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings()

TARGET_PORTAL = '46962361'

print("="*80)
print("DEEP PUBLIC FORM ANALYSIS")
print("="*80)

form_ids = [1, 3, 4, 5, 6, 8, 13, 18, 1000]

all_findings = []

for form_id in form_ids:
    print(f"\n{'='*80}")
    print(f"ANALYZING FORM {form_id}")
    print("="*80)

    # Try multiple form URLs
    form_urls = [
        f'https://share.hsforms.com/{TARGET_PORTAL}/{form_id}',
        f'https://forms.hubspot.com/{TARGET_PORTAL}/{form_id}',
        f'https://forms.hsforms.com/{TARGET_PORTAL}/{form_id}',
    ]

    for url in form_urls:
        try:
            r = requests.get(url, verify=False, timeout=10)

            if r.status_code != 200:
                continue

            print(f"\n[*] Accessible URL: {url}")
            print(f"    Size: {len(r.text)} bytes")

            html = r.text
            soup = BeautifulSoup(html, 'html.parser')

            # ================================================================
            # 1. EXTRACT ALL INPUT FIELDS AND THEIR DEFAULT VALUES
            # ================================================================

            print("\n[1] Extracting form fields...")

            inputs = soup.find_all('input')
            selects = soup.find_all('select')
            textareas = soup.find_all('textarea')

            all_fields = []

            for inp in inputs:
                field_info = {
                    'type': inp.get('type', 'text'),
                    'name': inp.get('name', ''),
                    'id': inp.get('id', ''),
                    'value': inp.get('value', ''),
                    'placeholder': inp.get('placeholder', ''),
                    'class': inp.get('class', ''),
                }

                if field_info['name'] or field_info['id']:
                    all_fields.append(field_info)

                    # Check if it's a contact-related field
                    if any(term in str(field_info).lower() for term in ['firstname', 'email', 'contact', 'super_secret', 'name']):
                        print(f"    Found: {field_info}")

                    # Check for pre-filled values
                    if field_info['value']:
                        print(f"    PRE-FILLED VALUE: {field_info['name']} = {field_info['value']}")
                        all_findings.append({
                            'form_id': form_id,
                            'type': 'prefilled_value',
                            'field': field_info['name'],
                            'value': field_info['value']
                        })

            # ================================================================
            # 2. EXTRACT JAVASCRIPT CONFIGURATION
            # ================================================================

            print("\n[2] Searching for JavaScript config...")

            # Look for form configuration in scripts
            scripts = soup.find_all('script')

            for script in scripts:
                script_text = script.string if script.string else ''

                # Look for form config patterns
                config_patterns = [
                    r'hbspt\.forms\.create\((.*?)\)',
                    r'formData\s*=\s*({.*?})',
                    r'portalId["\']?\s*[:=]\s*["\']?(\d+)',
                    r'formId["\']?\s*[:=]\s*["\']?([^"\']+)',
                    r'contactProperties\s*[:=]\s*(\[.*?\])',
                ]

                for pattern in config_patterns:
                    matches = re.findall(pattern, script_text, re.DOTALL | re.IGNORECASE)
                    if matches:
                        print(f"    Config found: {pattern[:40]}...")
                        for match in matches[:3]:
                            print(f"      {str(match)[:200]}")

                # Look for contact data
                if 'super_secret' in script_text.lower():
                    print(f"\n    *** FOUND super_secret in script! ***")

                    # Extract surrounding context
                    idx = script_text.lower().find('super_secret')
                    context = script_text[max(0, idx-200):min(len(script_text), idx+200)]
                    print(f"    Context: {context}")

                    all_findings.append({
                        'form_id': form_id,
                        'type': 'super_secret_in_js',
                        'context': context
                    })

                if 'firstname' in script_text.lower():
                    # Try to extract firstname value
                    firstname_patterns = [
                        r'firstname["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                        r'"firstname":\s*"([^"]+)"',
                    ]

                    for fp in firstname_patterns:
                        fmatches = re.findall(fp, script_text, re.IGNORECASE)
                        if fmatches:
                            print(f"    *** FOUND firstname value: {fmatches[0]} ***")
                            all_findings.append({
                                'form_id': form_id,
                                'type': 'firstname_value',
                                'value': fmatches[0]
                            })

            # ================================================================
            # 3. EXTRACT META TAGS
            # ================================================================

            print("\n[3] Checking meta tags...")

            meta_tags = soup.find_all('meta')
            for meta in meta_tags:
                if meta.get('content'):
                    content = meta.get('content', '')
                    if any(term in content.lower() for term in ['firstname', 'email', 'contact', 'super_secret']):
                        print(f"    Meta: {meta.get('name', meta.get('property', ''))} = {content}")

            # ================================================================
            # 4. CHECK FOR FORM EMBED URL / API ENDPOINT
            # ================================================================

            print("\n[4] Looking for form API endpoints...")

            # Extract any URLs in the HTML
            urls_in_html = re.findall(r'https?://[^\s<>"\']+', html)

            for extracted_url in urls_in_html:
                if 'api' in extracted_url.lower() and TARGET_PORTAL in extracted_url:
                    print(f"    API URL: {extracted_url}")

                    # Try accessing it
                    try:
                        api_r = requests.get(extracted_url, verify=False, timeout=5)
                        if api_r.status_code == 200:
                            print(f"      Status: 200 - Accessible!")
                            try:
                                api_data = api_r.json()
                                print(f"      Data: {json.dumps(api_data, indent=2)[:500]}")

                                if 'super_secret' in json.dumps(api_data).lower():
                                    print(f"\n      *** API CONTAINS super_secret! ***")
                                    all_findings.append({
                                        'form_id': form_id,
                                        'type': 'api_endpoint',
                                        'url': extracted_url,
                                        'data': api_data
                                    })
                            except:
                                pass
                    except:
                        pass

            # ================================================================
            # 5. TRY TO GET FORM DEFINITION VIA API
            # ================================================================

            print("\n[5] Attempting to fetch form definition...")

            form_def_urls = [
                f'https://api.hsforms.com/forms/v2/forms/{TARGET_PORTAL}?formId={form_id}',
                f'https://api.hubapi.com/forms/v2/forms/{TARGET_PORTAL}/{form_id}',
                f'https://forms.hubspot.com/api/v2/forms/{TARGET_PORTAL}/{form_id}',
            ]

            for def_url in form_def_urls:
                try:
                    def_r = requests.get(def_url, verify=False, timeout=5)
                    if def_r.status_code == 200:
                        print(f"    *** Form definition accessible! ***")
                        print(f"    URL: {def_url}")

                        try:
                            form_def = def_r.json()
                            print(f"    Definition: {json.dumps(form_def, indent=2)[:800]}")

                            # Check for contact properties
                            if 'fields' in form_def:
                                for field in form_def['fields']:
                                    field_name = field.get('name', '')
                                    if field_name in ['firstname', 'super_secret', 'email']:
                                        print(f"    Field found: {field}")

                            if 'super_secret' in json.dumps(form_def).lower():
                                print(f"\n    *** Form definition contains super_secret! ***")
                                all_findings.append({
                                    'form_id': form_id,
                                    'type': 'form_definition',
                                    'data': form_def
                                })
                        except:
                            print(f"    Response: {def_r.text[:300]}")
                except:
                    pass

            # ================================================================
            # 6. CHECK FOR THANK YOU PAGE / REDIRECT
            # ================================================================

            print("\n[6] Checking for redirect/thank you pages...")

            # Look for redirect URLs in the form
            redirect_patterns = [
                r'redirectUrl["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                r'thankYouUrl["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                r'action\s*=\s*["\']([^"\']+)["\']',
            ]

            for pattern in redirect_patterns:
                matches = re.findall(pattern, html)
                for match in matches:
                    print(f"    Redirect: {match}")

                    # Try accessing the thank you page
                    if match.startswith('http'):
                        try:
                            thank_r = requests.get(match, verify=False, timeout=5)
                            if thank_r.status_code == 200 and 'super_secret' in thank_r.text.lower():
                                print(f"      *** Thank you page contains super_secret! ***")
                        except:
                            pass

            # Save form HTML for manual review
            with open(f'/home/user/Hub/findings/form_{form_id}.html', 'w') as f:
                f.write(html)

            print(f"\n    Saved: findings/form_{form_id}.html")

        except Exception as e:
            print(f"    Error: {str(e)[:100]}")

print("\n" + "="*80)
print("FORM ANALYSIS COMPLETE")
print("="*80)

if all_findings:
    print(f"\n*** FOUND {len(all_findings)} POTENTIAL DATA POINTS! ***\n")

    for finding in all_findings:
        print(f"\nForm {finding['form_id']} - {finding['type']}:")
        print(f"  {json.dumps(finding, indent=2)[:500]}")

        # Check if we found the flag
        if finding.get('type') == 'firstname_value' and finding.get('form_id') == 1:
            print("\n" + "="*80)
            print("*** POTENTIAL CTF FLAG - FIRSTNAME FROM FORM 1! ***")
            print("="*80)
            print(f"Value: {finding.get('value')}")

    with open('/home/user/Hub/findings/form_analysis.json', 'w') as f:
        json.dump(all_findings, f, indent=2)

    print("\nSaved: findings/form_analysis.json")
else:
    print("\nNo sensitive data found in forms.")
    print("Forms appear to be properly configured.")
