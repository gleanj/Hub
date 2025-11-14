#!/usr/bin/env python3
"""
HubSpot GitHub Repository Analyzer
Analyzes HubSpot's public repos for API endpoints, auth patterns, and potential attack vectors
"""

import requests
import json
import re
from collections import defaultdict
import time

print("="*80)
print("HubSpot GitHub Repository Analyzer")
print("="*80)

# GitHub API (no auth needed for public repos)
GITHUB_API = "https://api.github.com"
ORG = "HubSpot"

findings = {
    'api_endpoints': set(),
    'auth_patterns': set(),
    'portal_id_usage': [],
    'contact_endpoints': [],
    'deprecated_apis': [],
    'interesting_files': [],
    'potential_vectors': []
}

def get_repos():
    """Get all HubSpot repositories"""
    print("\n[*] Fetching HubSpot repositories...")

    repos = []
    page = 1

    while True:
        url = f"{GITHUB_API}/orgs/{ORG}/repos?per_page=100&page={page}"
        r = requests.get(url, timeout=30)

        if r.status_code != 200:
            print(f"Error: {r.status_code}")
            break

        data = r.json()
        if not data:
            break

        repos.extend(data)
        print(f"  Fetched {len(repos)} repos so far...")
        page += 1
        time.sleep(0.5)  # Rate limit

    print(f"  Total: {len(repos)} repositories")
    return repos

def analyze_repo(repo):
    """Analyze a single repository"""
    repo_name = repo['name']

    # Focus on API/SDK related repos
    keywords = ['api', 'sdk', 'client', 'integration', 'auth', 'crm', 'contact']

    if not any(kw in repo_name.lower() for kw in keywords):
        return

    print(f"\n[*] Analyzing: {repo_name}")
    print(f"    Description: {repo['description']}")
    print(f"    Language: {repo.get('language', 'N/A')}")
    print(f"    Stars: {repo['stargazers_count']}")

    # Search for interesting files
    search_patterns = [
        'api.py', 'api.js', 'client.py', 'client.js',
        'auth', 'contact', 'crm', 'portal', 'hubspot'
    ]

    # Get repo contents
    try:
        contents_url = f"{GITHUB_API}/repos/{ORG}/{repo_name}/contents"
        r = requests.get(contents_url, timeout=10)

        if r.status_code == 200:
            contents = r.json()

            for item in contents:
                if item['type'] == 'file':
                    # Check if filename matches our patterns
                    for pattern in search_patterns:
                        if pattern in item['name'].lower():
                            findings['interesting_files'].append({
                                'repo': repo_name,
                                'file': item['name'],
                                'url': item['html_url']
                            })
                            print(f"    Found: {item['name']}")
    except Exception as e:
        print(f"    Error: {str(e)[:50]}")

def search_code_patterns():
    """Search for specific code patterns across HubSpot repos"""
    print("\n[*] Searching for API patterns in code...")

    # Search queries
    searches = [
        'org:HubSpot "api.hubapi.com" extension:py',
        'org:HubSpot "api.hubapi.com" extension:js',
        'org:HubSpot "contacts/v1" extension:py',
        'org:HubSpot "crm/v3" extension:py',
        'org:HubSpot "portalId" extension:py',
        'org:HubSpot "Authorization Bearer" extension:py',
        'org:HubSpot "/contacts/" path:/ extension:py',
    ]

    for query in searches:
        print(f"\n  Searching: {query}")

        try:
            url = f"{GITHUB_API}/search/code?q={requests.utils.quote(query)}"
            r = requests.get(url, timeout=30)

            if r.status_code == 200:
                results = r.json()
                total = results.get('total_count', 0)
                print(f"    Found {total} results")

                # Analyze top 5 results
                for item in results.get('items', [])[:5]:
                    print(f"      - {item['repository']['name']}/{item['name']}")
                    print(f"        {item['html_url']}")

                    findings['potential_vectors'].append({
                        'query': query,
                        'file': f"{item['repository']['name']}/{item['name']}",
                        'url': item['html_url']
                    })

            time.sleep(2)  # Rate limit

        except Exception as e:
            print(f"    Error: {str(e)[:100]}")

def extract_endpoints_from_file(url):
    """Extract API endpoints from a file"""
    try:
        # Get raw file content
        raw_url = url.replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
        r = requests.get(raw_url, timeout=10)

        if r.status_code == 200:
            content = r.text

            # Find API endpoints
            api_pattern = r'https://api\.hubapi\.com/[^\s"\']+'
            endpoints = re.findall(api_pattern, content)

            # Find portalId usage patterns
            portal_patterns = [
                r'portalId["\']?\s*[=:]\s*["\']?(\d+)',
                r'portal_id["\']?\s*[=:]\s*["\']?(\d+)',
                r'\?portalId=(\d+)',
            ]

            for pattern in portal_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    findings['portal_id_usage'].append({
                        'file': url,
                        'pattern': pattern,
                        'examples': matches[:3]
                    })

            return endpoints
    except:
        pass

    return []

def analyze_api_sdks():
    """Analyze official HubSpot API SDKs"""
    print("\n[*] Analyzing HubSpot official SDKs...")

    sdk_repos = [
        'hubspot-api-python',
        'hubspot-api-nodejs',
        'hubspot-api-ruby',
        'hubspot-api-php',
    ]

    for sdk in sdk_repos:
        print(f"\n  Analyzing SDK: {sdk}")

        try:
            # Get README
            readme_url = f"https://raw.githubusercontent.com/{ORG}/{sdk}/master/README.md"
            r = requests.get(readme_url, timeout=10)

            if r.status_code == 200:
                readme = r.text

                # Extract example endpoints
                api_examples = re.findall(r'https://api\.hubapi\.com/[^\s\)]+', readme)

                for endpoint in api_examples:
                    findings['api_endpoints'].add(endpoint)
                    print(f"    Endpoint: {endpoint}")

                # Look for auth patterns
                auth_patterns = re.findall(r'(Bearer|hapikey|Authorization)[^\n]+', readme)
                for auth in auth_patterns[:5]:
                    findings['auth_patterns'].add(auth)

        except Exception as e:
            print(f"    Error: {str(e)[:50]}")

        time.sleep(1)

def find_deprecated_apis():
    """Search for deprecated API mentions"""
    print("\n[*] Searching for deprecated APIs...")

    search_queries = [
        'org:HubSpot "deprecated" "api" extension:md',
        'org:HubSpot "v1/contacts" "deprecated"',
        'org:HubSpot "legacy" "api"',
    ]

    for query in search_queries:
        try:
            url = f"{GITHUB_API}/search/code?q={requests.utils.quote(query)}"
            r = requests.get(url, timeout=30)

            if r.status_code == 200:
                results = r.json()

                for item in results.get('items', [])[:3]:
                    findings['deprecated_apis'].append({
                        'file': f"{item['repository']['name']}/{item['name']}",
                        'url': item['html_url']
                    })
                    print(f"    Found: {item['repository']['name']}/{item['name']}")

            time.sleep(2)
        except:
            pass

# ============================================================================
# MAIN EXECUTION
# ============================================================================

print("\nThis will analyze HubSpot's public GitHub repositories for:")
print("  1. API endpoint patterns")
print("  2. Authentication methods")
print("  3. portalId usage patterns")
print("  4. Deprecated APIs")
print("  5. Potential attack vectors")
print("\nNote: This uses GitHub API without authentication (60 requests/hour limit)")
print("="*80)

# Get all repos
repos = get_repos()

# Filter for API/SDK related repos
api_repos = [r for r in repos if any(kw in r['name'].lower()
              for kw in ['api', 'sdk', 'client', 'integration', 'crm'])]

print(f"\n[*] Found {len(api_repos)} API/SDK related repos")
for repo in api_repos[:10]:  # Analyze top 10
    analyze_repo(repo)

# Analyze official SDKs
analyze_api_sdks()

# Search for code patterns
search_code_patterns()

# Find deprecated APIs
find_deprecated_apis()

# ============================================================================
# GENERATE REPORT
# ============================================================================

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)

print(f"\nAPI Endpoints Found: {len(findings['api_endpoints'])}")
for endpoint in list(findings['api_endpoints'])[:10]:
    print(f"  - {endpoint}")

print(f"\nAuth Patterns Found: {len(findings['auth_patterns'])}")
for pattern in list(findings['auth_patterns'])[:5]:
    print(f"  - {pattern}")

print(f"\nInteresting Files: {len(findings['interesting_files'])}")
for item in findings['interesting_files'][:10]:
    print(f"  - {item['repo']}/{item['file']}")
    print(f"    {item['url']}")

print(f"\nPortalId Usage Patterns: {len(findings['portal_id_usage'])}")
for item in findings['portal_id_usage'][:5]:
    print(f"  - Pattern: {item['pattern']}")
    print(f"    Examples: {item['examples']}")

print(f"\nDeprecated APIs: {len(findings['deprecated_apis'])}")
for item in findings['deprecated_apis'][:5]:
    print(f"  - {item['file']}")

print(f"\nPotential Attack Vectors: {len(findings['potential_vectors'])}")

# Save findings
with open('/home/user/Hub/findings/github_analysis.json', 'w') as f:
    # Convert sets to lists for JSON serialization
    findings_serializable = {
        'api_endpoints': list(findings['api_endpoints']),
        'auth_patterns': list(findings['auth_patterns']),
        'portal_id_usage': findings['portal_id_usage'],
        'contact_endpoints': findings['contact_endpoints'],
        'deprecated_apis': findings['deprecated_apis'],
        'interesting_files': findings['interesting_files'],
        'potential_vectors': findings['potential_vectors']
    }
    json.dump(findings_serializable, f, indent=2)

print("\nSaved to: findings/github_analysis.json")

print("\n" + "="*80)
print("RECOMMENDATIONS")
print("="*80)
print("""
1. MANUALLY REVIEW the interesting files found above
   - Look for non-standard API endpoints
   - Check for unusual authentication patterns
   - Find deprecated endpoints that might have weaker security

2. TEST DEPRECATED APIS
   - Older API versions might have authorization bugs
   - Deprecated endpoints often have less scrutiny

3. EXAMINE SDK IMPLEMENTATION
   - SDKs might reveal undocumented parameters
   - Look for error handling that leaks information
   - Check for commented-out code or debug endpoints

4. LOOK FOR INTERNAL APIS
   - Some repos might reference internal endpoints
   - Admin/debug endpoints accidentally exposed

5. STUDY AUTHENTICATION FLOWS
   - Different auth methods might have different security
   - OAuth flows might have CSRF or state issues

NEXT STEPS:
- Run this script to get initial data
- Manually review the most promising repos
- Test any new endpoints discovered
- Look for API version mismatches
""")
