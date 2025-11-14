#!/usr/bin/env python3
"""
Creative CTF Attack Vectors
Non-standard approaches to access portal 46962361
"""

import requests
import json
from config import get_api_key, TARGET_PORTAL_ID, HUBSPOT_COOKIES

def test_public_forms():
    """Check if portal has public forms we can access"""
    print("\n[*] Testing for public forms/websites...")

    urls = [
        f"https://{TARGET_PORTAL_ID}.hs-sites.com",
        f"https://{TARGET_PORTAL_ID}.hubspot.com",
        f"https://www.hubspot.com/portal/{TARGET_PORTAL_ID}",
    ]

    for url in urls:
        try:
            resp = requests.get(url, timeout=10, allow_redirects=True)
            print(f"  {url}")
            print(f"    Status: {resp.status_code}, Length: {len(resp.text)}")

            if resp.status_code == 200:
                print(f"    [!] Found accessible site!")
                # Check for forms or contact info
                if 'form' in resp.text.lower() or 'email' in resp.text.lower():
                    print(f"    [!] Contains forms/email fields - might be able to sign up!")

        except Exception as e:
            print(f"  {url}: {e}")

def test_company_domain_lookup():
    """Try to find the company associated with portal"""
    print("\n[*] Attempting to identify portal owner...")

    api_key = get_api_key()

    # Try to get portal info (might reveal company name)
    urls = [
        f"https://api.hubapi.com/integrations/v1/me",
        f"https://api.hubapi.com/account-info/v3/details",
        f"https://api.hubapi.com/account-info/v3/api-usage/daily",
    ]

    headers = {'Authorization': f'Bearer {api_key}'}

    for url in urls:
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                print(f"  [+] {url}")
                print(f"      {resp.text[:300]}")
        except:
            pass

def test_email_permutations():
    """Test if we can find the contact's email through pattern matching"""
    print("\n[*] Testing common email patterns for portal 46962361...")

    # Common patterns for CTF challenges
    patterns = [
        "ctf@hubspot.com",
        "challenge@hubspot.com",
        "bugbounty@hubspot.com",
        "security@hubspot.com",
        f"contact@{TARGET_PORTAL_ID}.com",
    ]

    print("  Potential email addresses to investigate:")
    for email in patterns:
        print(f"    - {email}")

    print("\n  [!] If you can find the contact's email, you might:")
    print("      1. Sign up for their portal (if they allow it)")
    print("      2. Submit a form to become a contact")
    print("      3. Access public information about them")

def test_metadata_endpoints():
    """Check for metadata leaks"""
    print("\n[*] Testing metadata/info endpoints...")

    api_key = get_api_key()
    headers = {'Authorization': f'Bearer {api_key}'}

    # Try to get properties definition (might work cross-portal)
    urls = [
        "https://api.hubapi.com/properties/v2/contacts/properties",
        "https://api.hubapi.com/crm/v3/properties/contacts",
    ]

    for url in urls:
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                # Look for super_secret property
                if isinstance(data, list):
                    for prop in data:
                        if prop.get('name') == 'super_secret':
                            print(f"  [!] Found super_secret property definition!")
                            print(f"      {json.dumps(prop, indent=2)[:500]}")
        except:
            pass

def test_timeline_events():
    """Check if timeline/activities are accessible"""
    print("\n[*] Testing timeline/activity endpoints...")

    api_key = get_api_key()
    headers = {'Authorization': f'Bearer {api_key}'}

    # Timeline might have different authorization
    urls = [
        f"https://api.hubapi.com/integrations/v1/{TARGET_PORTAL_ID}/timeline/events",
        f"https://api.hubapi.com/timeline/v3/events",
    ]

    for url in urls:
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            print(f"  {url[:60]}... : {resp.status_code}")
            if resp.status_code not in [401, 403, 404]:
                print(f"    Response: {resp.text[:200]}")
        except:
            pass

def check_ctf_hints():
    """Display CTF analysis and hints"""
    print("\n" + "="*70)
    print("CTF ANALYSIS & HINTS")
    print("="*70)

    print("""
Portal ID: 46962361
Contact ID: 1 (assumption)
Properties: firstname ($15K), super_secret ($5K), email

KEY OBSERVATIONS:

1. PORTAL INFO:
   - Portal 46962361 is a real HubSpot portal
   - It likely belongs to HubSpot's security team
   - Contact ID 1 is typically the first contact created

2. THE CHALLENGE:
   - "Access contact properties in portal 46962361"
   - No social engineering of the contact
   - No brute force
   - Email submission ID to contact's email address

3. POTENTIAL APPROACHES NOT YET TRIED:

   A) LEGITIMATE ACCESS:
      - Can you sign up / create account in portal 46962361?
      - Is there a demo/trial form?
      - Does portal have a public website with signup?
      - Check: https://46962361.hs-sites.com for forms

   B) PUBLIC INFORMATION:
      - Research the portal owner
      - Find their company website
      - Look for publicly posted contact info
      - Check if they've posted the flag publicly (meta approach)

   C) ALTERNATIVE DATA ACCESS:
      - Webhooks (if portal sends data to public endpoints)
      - Public pages/forms that display contact data
      - Marketing emails that might leak info
      - Public CRM integrations

   D) TECHNICAL EDGE CASES:
      - API rate limiting bypass (flood requests)
      - Time-based attacks (specific timestamps)
      - Encoding variations (UTF-8, UTF-16, etc.)
      - Case sensitivity issues

4. REALITY CHECK:
   - We've tested 50+ standard attack vectors - all blocked
   - HubSpot's authorization is working correctly
   - The vulnerability (if it exists) is likely:
     * A subtle edge case
     * A logic flaw, not a configuration issue
     * Or... the "attack" is actually legitimate access

5. RECOMMENDED NEXT STEPS:

   [1] Visit https://46962361.hs-sites.com
       - Look for signup forms
       - Check for public pages
       - See if you can legitimately register

   [2] Research HubSpot CTF challenges
       - Google "HubSpot CTF 46962361"
       - Check HackerOne/bug bounty forums
       - See if anyone has discussed this challenge

   [3] Test YOUR portal thoroughly first
       - Practice all techniques on portal 50708459
       - Create test contacts with the same properties
       - Verify what IS and ISN'T possible

   [4] Manual Burp Suite testing
       - Load templates from burp-requests/
       - Try subtle variations
       - Look for response timing differences

   [5] Accept that this might be unsolvable
       - The $20K exists because it's HARD
       - Your time might be better spent on other targets
       - You've already built valuable tools/knowledge
    """)

def main():
    print("="*70)
    print("CREATIVE CTF ATTACK VECTORS")
    print("="*70)

    test_public_forms()
    test_company_domain_lookup()
    test_email_permutations()
    test_metadata_endpoints()
    test_timeline_events()
    check_ctf_hints()

    print("\n" + "="*70)
    print("CREATIVE ATTACKS COMPLETED")
    print("="*70)

if __name__ == '__main__':
    main()
