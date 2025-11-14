# Project Summary

## 📁 HubSpot Bug Bounty Testing Framework

This project contains everything you need to systematically hunt for security vulnerabilities in HubSpot's bug bounty program using Burp Suite Pro.

## 🎯 High-Value Opportunity

**CTF Challenge**: Portal 46962361
- **$15,000** for accessing `firstname` property
- **$5,000** for accessing `super_secret` property  
- **$20,000 total** potential reward
- Must bypass permissions without social engineering or brute force

## 📂 Project Structure

```
Hub/
├── README.md                    # Main project overview
├── QUICK-START.md               # Get started in minutes
├── BugbountyInstructions.txt   # Official program rules
│
├── burp-config/                 # Burp Suite configurations
│   ├── hubspot-scope.json      # Import into Burp for scope
│   └── BURP-SETUP-GUIDE.md     # Complete Burp configuration
│
├── testing-checklists/          # Systematic testing guides
│   ├── CTF-challenge-checklist.md       # $20k CTF focus
│   ├── authentication-testing.md        # Auth vulnerabilities
│   ├── IDOR-testing.md                  # Cross-portal access
│   └── XSS-testing.md                   # XSS vulnerabilities
│
├── scripts/                     # Automation tools
│   ├── portal_enumeration.py   # Test cross-portal access
│   └── analyze_burp_logs.py    # Analyze Burp traffic
│
└── findings/                    # Document your discoveries
    └── TEMPLATE-vulnerability-report.md  # Report template
```

## 🚀 Getting Started (30 Minutes)

### 1. Account Setup (10 min)
```bash
# Create trial portal
1. Go to: https://offers.hubspot.com/free-trial
2. Use @WEAREHACKERONE.COM email
3. Note your Portal ID
4. Generate API key
```

### 2. Burp Suite Setup (15 min)
```bash
1. Open Burp Suite Pro
2. Import scope: burp-config/hubspot-scope.json
3. Install extensions: Autorize, Logger++, JWT tools
4. Configure browser proxy
5. Read: burp-config/BURP-SETUP-GUIDE.md
```

### 3. Start Testing (5 min)
```bash
# First priority: CTF Challenge
1. Open: testing-checklists/CTF-challenge-checklist.md
2. Follow the testing strategy
3. Document everything in findings/
```

## 🎯 Testing Priorities

### Priority 1: CTF Challenge ($20k)
**Target**: Portal 46962361, contact with `firstname` and `super_secret` flags

**Key Approaches**:
- Direct API access with portal parameter manipulation
- Cross-portal IDOR testing
- JWT token modification
- API version exploitation (v1, v2, v3)
- Parameter pollution and bypass techniques

**Checklist**: `testing-checklists/CTF-challenge-checklist.md`

### Priority 2: Cross-Portal IDORs
**High Value**: Accessing Portal A data from Portal B

**Focus Areas**:
- Contact/Company/Deal access across portals
- Sensitive properties (PHI/PII)
- Financial/billing information
- Admin privilege escalation

**Checklist**: `testing-checklists/IDOR-testing.md`

### Priority 3: Authentication Vulnerabilities
**High Value**: Account takeover and auth bypass

**Focus Areas**:
- OAuth implementation flaws
- JWT manipulation
- MFA bypass
- Password reset vulnerabilities
- Session management issues

**Checklist**: `testing-checklists/authentication-testing.md`

### Priority 4: XSS Leading to Account Takeover
**Value**: Context-dependent (must execute in *.hubspot.com)

**Focus Areas**:
- Stored XSS in CRM fields
- Reflected XSS in search/filters
- DOM-based XSS
- XSS leading to token theft

**Checklist**: `testing-checklists/XSS-testing.md`

## 🛠️ Essential Tools

### Burp Suite Extensions (Install These First)
1. **Autorize** - Auto-test authorization (critical for IDOR)
2. **Logger++** - Advanced request logging
3. **JSON Web Tokens** - JWT analysis and manipulation
4. **Param Miner** - Discover hidden parameters
5. **Turbo Intruder** - Race conditions and fast fuzzing

### Python Scripts
```bash
# Test cross-portal access
python scripts/portal_enumeration.py

# Analyze Burp logs for patterns
python scripts/analyze_burp_logs.py
```

## 📋 In Scope

### ✅ High-Value Targets (Critical Severity)
- `app*.hubspot.com` - Main application
- `api*.hubspot.com` - API endpoints
- `api*.hubapi.com` - API endpoints
- Mobile apps (Android & iOS)

### ✅ Also In Scope
- `*.hubspotemail.net` - Medium severity
- `*.hubspotpagebuilder.com/eu` - Low severity
- `chatspot.ai` - Medium severity
- Customer portals (set up your own)
- Customer connected domains (if HubSpot-introduced vuln)

### ❌ Out of Scope (Don't Test!)
- `connect.com` (being sunset)
- `shop.hubspot.com`
- `trust.hubspot.com`
- `thespot.hubspot.com`
- `ir.hubspot.com`
- `events.hubspot.com`

## 💰 What Pays Well

### Critical Findings ($$$$$)
- Cross-portal data access (Portal A → Portal B)
- Authentication bypass leading to account takeover
- Remote code execution
- SQL injection with data access
- Mass data exfiltration

### High Findings ($$$$)
- Same-portal privilege escalation
- Access to sensitive properties (PHI/PII)
- Subdomain takeovers
- SSRF with internal access
- Stored XSS leading to account takeover

### Medium Findings ($$$)
- Reflected XSS in *.hubspot.com context
- Information disclosure (sensitive data)
- CSRF on sensitive actions
- Authorization bypass (limited impact)

### Low/Informational ($)
- Non-sensitive IDOR
- XSS on preview domains
- Missing best practices
- Low-impact information disclosure

## 🚫 What Doesn't Pay

- Rate limiting issues
- Brute force attacks
- DoS/DDoS
- Social engineering
- Clickjacking
- Missing HTTP headers
- Vulnerable libraries without PoC
- XSS on preview domains (hs-sites.com, hubspotpreview.com, etc.)

## 📊 Testing Methodology

### Week 1: Foundation
- **Day 1**: Setup accounts, Burp, initial exploration
- **Day 2-3**: CTF challenge focus (high value)
- **Day 4**: Authentication testing
- **Day 5**: IDOR testing (create second portal)

### Week 2: Deep Testing
- **Day 1**: XSS hunting
- **Day 2**: API security testing
- **Day 3**: Advanced techniques
- **Day 4**: Automation and scanning
- **Day 5**: Report preparation

### Daily Workflow
1. **Morning**: Focus on one checklist (2-3 hours)
2. **Afternoon**: Different area or follow-up (2-3 hours)
3. **Evening**: Review, document, plan (1 hour)

## 🔍 Red Flags to Investigate

If you see these, dig deeper:
- 🚩 Portal ID in URL but not validated
- 🚩 Different auth between API versions
- 🚩 Error messages with cross-portal data
- 🚩 JWT tokens with modifiable portal_id
- 🚩 Batch operations without portal checks
- 🚩 Deprecated endpoints
- 🚩 GraphQL introspection enabled
- 🚩 Session works across portals

## 📝 When You Find Something

### Immediate Actions:
1. **STOP** - Don't access more than necessary
2. **Screenshot** - Capture everything
3. **Save** - Burp request/response
4. **Document** - Detailed notes
5. **Verify** - Test multiple times

### Report Preparation:
1. Use `findings/TEMPLATE-vulnerability-report.md`
2. Include:
   - Clear reproduction steps
   - Attack scenario
   - Business impact
   - Recommended fix
   - All evidence (screenshots, Burp files)

### Before Submitting:
- ✅ Verified it's in scope
- ✅ Not a duplicate
- ✅ Tested on latest version
- ✅ Clear steps to reproduce
- ✅ Demonstrated impact
- ✅ Followed program rules

## 🎓 Learning Resources

### HubSpot Specific
- API Docs: https://developers.hubspot.com/docs/api/overview
- Auth Guide: https://developers.hubspot.com/docs/guides/apps/authentication/intro-to-auth
- Program Rules: Read `BugbountyInstructions.txt` thoroughly

### General Bug Bounty
- OWASP Testing Guide: https://owasp.org/www-project-web-security-testing-guide/
- PortSwigger Web Security Academy: https://portswigger.net/web-security
- HackerOne Resources: https://www.hackerone.com/resources

### Burp Suite
- Documentation: https://portswigger.net/burp/documentation
- YouTube Tutorials: Search "Burp Suite tutorial"
- This Project: `burp-config/BURP-SETUP-GUIDE.md`

## ⚠️ Important Rules

### DO:
- ✅ Test only your own portals (or CTF: 46962361)
- ✅ Follow responsible disclosure
- ✅ Document everything
- ✅ Respect rate limits
- ✅ Use @WEAREHACKERONE.COM email

### DON'T:
- ❌ Test out-of-scope domains
- ❌ Access portals you don't own (except CTF)
- ❌ Send emails to addresses you don't own
- ❌ Use social engineering
- ❌ Perform DoS attacks
- ❌ Share findings publicly before resolution

## 🏆 Success Tips

1. **Be Systematic** - Follow checklists, don't skip steps
2. **Focus on Impact** - High-impact = better bounties
3. **Document Everything** - You'll need it for reports
4. **Read the Rules** - Carefully, multiple times
5. **Think Like an Attacker** - How to abuse each feature?
6. **Don't Give Up** - Try multiple approaches
7. **Take Breaks** - Fresh eyes find more bugs
8. **Learn from Others** - Read disclosed reports

## 📞 Support

### Issues with This Project
- Review README.md for detailed information
- Check QUICK-START.md for step-by-step guide
- Read BURP-SETUP-GUIDE.md for Burp configuration

### HubSpot Program Questions
- Review: `BugbountyInstructions.txt`
- HackerOne platform: Use the report form
- Do NOT contact HubSpot directly

### Technical Questions
- Burp Suite: https://portswigger.net/support
- HubSpot API: https://developers.hubspot.com/docs

## 🎯 Next Steps

1. **Right Now** (5 min):
   - Read `QUICK-START.md`
   - Create HubSpot trial account
   - Generate API key

2. **Today** (2 hours):
   - Configure Burp Suite
   - Read `CTF-challenge-checklist.md`
   - Start initial testing

3. **This Week**:
   - Complete CTF challenge testing
   - Work through authentication checklist
   - Set up second portal for IDOR testing
   - Document any findings

4. **Ongoing**:
   - Work through all checklists systematically
   - Run automation scripts
   - Prepare reports for valid findings
   - Stay updated on program changes

## 🌟 Remember

The **CTF challenge** ($20k) is the highest-value target, but it's likely been attempted by many researchers. Balance your time between:
- 40% CTF challenge (high reward, low probability)
- 30% IDOR testing (good reward, medium probability)
- 20% Authentication testing (good reward, medium probability)
- 10% Other vulnerabilities (varies)

**First submission wins the CTF** - but there are many other valuable vulnerabilities to find in the program!

Good hunting! 🎯🔍💰
