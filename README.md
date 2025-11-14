# HubSpot Bug Bounty Hunting Guide

## Project Overview
This project is set up for systematic security testing of HubSpot's bug bounty program using Burp Suite Pro.

### Key Information
- **Target**: HubSpot web applications and APIs
- **CTF Challenge**: Portal ID `46962361` on `app.hubspot.com`
- **CTF Rewards**: $15,000 for `firstname` flag + $5,000 for `super_secret` flag
- **Focus**: Authentication flows, IDORs, XSS, and cross-portal data leakage

## Directory Structure
```
Hub/
├── README.md (this file)
├── BugbountyInstructions.txt (program rules)
├── burp-config/ (Burp Suite configurations)
├── testing-checklists/ (systematic testing guides)
├── findings/ (document discovered vulnerabilities)
└── scripts/ (automation scripts)
```

## Quick Start

### 1. Initial Setup
1. Create HubSpot trial portal at: https://offers.hubspot.com/free-trial
   - Use @WEAREHACKERONE.COM email address
2. Set up Burp Suite Pro with the configuration files in `burp-config/`
3. Configure API key following: https://developers.hubspot.com/docs/guides/apps/authentication/intro-to-auth

### 2. Burp Suite Configuration
- Import scope configuration from `burp-config/hubspot-scope.json`
- Load match-replace rules from `burp-config/match-replace-rules.txt`
- Enable extensions: Logger++, Autorize, Param Miner, Turbo Intruder

### 3. Testing Workflow
Follow the checklists in order of priority:
1. `CTF-challenge-checklist.md` - High reward CTF challenge
2. `authentication-testing.md` - Auth flow vulnerabilities
3. `IDOR-testing.md` - Cross-portal and privilege escalation
4. `XSS-testing.md` - Cross-site scripting
5. `API-testing.md` - API security testing

## High Priority Targets

### CTF Challenge (Portal 46962361)
- **Objective**: Access contact record with `firstname` and `super_secret` properties
- **Method**: Permission bypass without social engineering or brute force
- **Reward**: $15,000 + $5,000 bonus

### Critical In-Scope Domains
- `app*.hubspot.com` - Critical severity, main application
- `api*.hubspot.com` - Critical severity, API endpoints
- `api*.hubapi.com` - Critical severity, API endpoints
- `*.hubspotemail.net` - Medium severity
- `chatspot.ai` - Medium severity
- Mobile apps (Android & iOS) - High severity

### Out of Scope (DO NOT TEST)
- `connect.com` (sunsetting June 2025)
- `shop.hubspot.com`
- `trust.hubspot.com`
- `thespot.hubspot.com`
- `ir.hubspot.com`
- `events.hubspot.com`

## Focus Areas

### 1. Authentication Testing
- Signup flows (email, Google, Apple, Microsoft)
- Login flows (email, SSO, OAuth)
- MFA bypass attempts
- Password reset vulnerabilities
- OAuth implementation flaws

### 2. IDOR Testing
**High Priority:**
- Cross-portal data access (Portal A → Portal B)
- Sensitive properties (PHI/PII data)
- Financial/billing information
- Super Admin privilege escalation
- Account takeover via IDOR

**Lower Priority:**
- Same-portal low-privilege to high-privilege API access
- Non-sensitive CRUD operations

### 3. XSS Testing
**Rewardable XSS:**
- Executes in context of `*.hubspot.com`
- On customer connected domains (if HubSpot-introduced)
- Leads to account takeover or data theft

**Non-Rewardable XSS:**
- Preview domains: `hs-sites.com`, `hubspotpagebuilder.com`, `hubspotpreview.com`
- Customer-introduced vulnerabilities in HubL/JS

### 4. Additional Vulnerabilities
- Subdomain takeovers (with proof of ownership)
- Server-side code execution
- Sensitive data exposure
- Cross-portal data leakage

## Out of Scope (Not Rewardable)
- Rate limiting issues
- Login/password brute force
- Denial of Service (DoS)
- Email flooding
- Social engineering
- Vulnerable libraries without PoC
- Clickjacking
- Missing HTTP headers
- Missing best practices without immediate risk

## Testing Best Practices

### Before Testing
- [ ] Created trial portal with @WEAREHACKERONE.COM email
- [ ] Configured Burp Suite with in-scope domains
- [ ] Generated API key for testing
- [ ] Read complete bounty brief
- [ ] Enabled beta features in trial account

### During Testing
- [ ] Only test owned portals or CTF target (46962361)
- [ ] Do NOT send emails to addresses you don't own
- [ ] Follow API usage guidelines
- [ ] Document all requests/responses
- [ ] Take screenshots of vulnerabilities
- [ ] Keep detailed reproduction steps

### Report Submission Requirements
Include in every report:
1. **Attack Scenario**: Real-world exploitation context
2. **Clear Reproduction Steps**: Consistently reproducible
3. **Recommended Fix**: Practical mitigation solution
4. **Impact Assessment**: CVSS score and business impact

### For CTF Challenge Submissions
1. Provide flag property names and values
2. Include detailed reproduction steps
3. Email submission ID to address in contact's `email` property
4. Subject line: "HubSpot CTF Challenge"

## Useful Resources
- HubSpot API Docs: https://developers.hubspot.com/docs/api/overview
- Authentication Guide: https://developers.hubspot.com/docs/guides/apps/authentication/intro-to-auth
- API Usage Guidelines: https://developers.hubspot.com/docs/guides/apps/api-usage/usage-details
- Customer Portal Setup: https://knowledge.hubspot.com/inbox/set-up-a-customer-portal
- Beta Features: https://knowledge.hubspot.com/account-management/opt-your-hubspot-account-into-a-public-beta-feature

## Notes
- First valid CTF submission wins the reward
- HubSpot can pause/stop CTF at any time
- Standard bug bounty rules apply to CTF
- Use CVSS for initial vulnerability rating
- Priority may be adjusted based on likelihood and impact
