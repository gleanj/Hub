# Master Progress Checklist

Track your progress through the HubSpot bug bounty testing. Check off items as you complete them.

---

## 📋 Initial Setup (Day 1)

### Account Creation
- [ ] Created HubSpot trial portal at https://offers.hubspot.com/free-trial
- [ ] Used @WEAREHACKERONE.COM email address
- [ ] Documented Portal ID: ________________
- [ ] Generated API key
- [ ] Saved API key securely
- [ ] Tested API key with basic curl command
- [ ] Enabled beta features in account
- [ ] Created 5-10 test contacts
- [ ] Created test companies and deals
- [ ] Documented test data IDs

### Burp Suite Configuration
- [ ] Launched Burp Suite Pro
- [ ] Created new project: "HubSpot Bug Bounty"
- [ ] Imported scope from `burp-config/hubspot-scope.json`
- [ ] Configured browser proxy (127.0.0.1:8080)
- [ ] Installed Burp CA certificate in browser
- [ ] Verified HTTPS traffic is captured

### Burp Extensions
- [ ] Installed Autorize (authorization testing)
- [ ] Installed Logger++ (advanced logging)
- [ ] Installed JSON Web Tokens (JWT analysis)
- [ ] Installed Param Miner (parameter discovery)
- [ ] Installed Turbo Intruder (race conditions)
- [ ] Configured Logger++ filters for portal 46962361
- [ ] Set up auto-backup for Burp project

### Documentation Review
- [ ] Read `README.md` completely
- [ ] Read `QUICK-START.md`
- [ ] Read `BugbountyInstructions.txt` carefully
- [ ] Read `burp-config/BURP-SETUP-GUIDE.md`
- [ ] Bookmarked `COMMAND-REFERENCE.md` for quick access

### Initial Exploration
- [ ] Browsed HubSpot app with Burp running
- [ ] Explored all major features (Contacts, Companies, Deals)
- [ ] Reviewed Burp site map
- [ ] Identified API endpoint patterns
- [ ] Documented authentication token format
- [ ] Saved 10+ interesting requests to Repeater

---

## 🎯 CTF Challenge Testing (Priority 1)

Target: Portal 46962361 | Reward: $20,000

### Reconnaissance
- [ ] Read `testing-checklists/CTF-challenge-checklist.md` completely
- [ ] Documented API patterns for contact retrieval
- [ ] Identified all portal ID parameters in requests
- [ ] Checked for GraphQL endpoints
- [ ] Looked for batch/bulk API operations
- [ ] Reviewed API documentation for contact endpoints

### Direct Access Attempts
- [ ] Tested `/contacts/v1/contact/vid/{VID}/profile?portalId=46962361`
- [ ] Tested `/crm/v3/objects/contacts/{ID}?portalId=46962361`
- [ ] Tested `/contacts/v2/contacts` with portal parameter
- [ ] Tested batch contact retrieval
- [ ] Tested search API with portal filter
- [ ] Tested export functionality

### Parameter Manipulation
- [ ] Tested portal ID with null value
- [ ] Tested portal ID with -1
- [ ] Tested portal ID with 0
- [ ] Tested portal ID with wildcard (*)
- [ ] Tested removing portal ID parameter
- [ ] Tested portal ID as array
- [ ] Tested parameter pollution (duplicate portalId)
- [ ] Tested hubId vs portalId confusion

### Authorization Testing
- [ ] Configured Autorize with your portal credentials
- [ ] Browsed your portal while Autorize running
- [ ] Reviewed Autorize results for bypasses
- [ ] Tested API calls without authentication
- [ ] Tested with modified JWT tokens
- [ ] Tested session from your portal on CTF portal

### API Version Testing
- [ ] Tested contacts v1 API
- [ ] Tested contacts v2 API  
- [ ] Tested CRM v3 API
- [ ] Tested legacy crm-objects v1 API
- [ ] Compared authorization between versions
- [ ] Looked for deprecated endpoints

### Advanced Techniques
- [ ] Tested GraphQL queries (if available)
- [ ] Tested search/filter bypass techniques
- [ ] Tested indirect access methods (reports, analytics)
- [ ] Tested webhook payload inspection
- [ ] Tested email tracking for data leakage
- [ ] Tested integration endpoints
- [ ] Attempted race conditions
- [ ] Checked error messages for data disclosure

### If Access Gained
- [ ] Documented exact request/response
- [ ] Captured firstname property value: ________________
- [ ] Captured super_secret property value: ________________
- [ ] Captured email property value: ________________
- [ ] Created detailed reproduction steps
- [ ] Took screenshots of all evidence
- [ ] Filled out vulnerability report
- [ ] Emailed submission to address in contact email
- [ ] Subject line: "HubSpot CTF Challenge"

---

## 🔐 Authentication Testing (Priority 2)

Checklist: `testing-checklists/authentication-testing.md`

### Signup Flow
- [ ] Tested email verification bypass
- [ ] Checked for account enumeration
- [ ] Tested race condition in verification
- [ ] Tested parameter pollution
- [ ] Tested XSS in profile fields during signup

### OAuth Testing
- [ ] Tested OAuth state parameter validation
- [ ] Tested redirect URI manipulation
- [ ] Tested authorization code reuse
- [ ] Checked for account linking vulnerabilities
- [ ] Tested pre-account takeover scenarios
- [ ] Tested token stealing via XSS

### Login Flow
- [ ] Tested response manipulation (change "success":false)
- [ ] Checked for username enumeration
- [ ] Tested session fixation
- [ ] Tested cookie injection
- [ ] Analyzed JWT tokens for weaknesses

### MFA Testing
- [ ] Tested bypassing MFA with direct navigation
- [ ] Tested removing MFA parameter from request
- [ ] Tested response manipulation
- [ ] Tested MFA code reuse
- [ ] Checked backup codes for predictability
- [ ] Tested race conditions in MFA

### Password Reset
- [ ] Tested token predictability
- [ ] Tested token reuse
- [ ] Checked token invalidation after use
- [ ] Tested token leakage in referrer
- [ ] Tested host header injection
- [ ] Tested email parameter tampering

### Session Management
- [ ] Tested session fixation
- [ ] Checked session invalidation on logout
- [ ] Tested session invalidation on password change
- [ ] Analyzed session token predictability
- [ ] Checked for concurrent session limits
- [ ] Tested cross-portal session use

### JWT Testing (if applicable)
- [ ] Decoded JWT tokens
- [ ] Tested algorithm confusion (HS256 → None)
- [ ] Tested signature bypass
- [ ] Modified portal_id in payload
- [ ] Modified user_id in payload
- [ ] Modified role/permissions in payload
- [ ] Tested expired token acceptance

---

## 🔓 IDOR Testing (Priority 3)

Checklist: `testing-checklists/IDOR-testing.md`

### Setup
- [ ] Created second HubSpot trial portal
- [ ] Portal B ID: ________________
- [ ] Created test data in both portals
- [ ] Created users with different permission levels
- [ ] Documented all object IDs for testing

### Cross-Portal Testing
- [ ] Tested accessing Portal A contacts from Portal B
- [ ] Tested accessing Portal A companies from Portal B
- [ ] Tested accessing Portal A deals from Portal B
- [ ] Tested batch operations across portals
- [ ] Tested search functionality for cross-portal data
- [ ] Tested export functionality
- [ ] Tested associations across portals

### Parameter Manipulation
- [ ] Tested removing portalId parameter
- [ ] Tested null portalId
- [ ] Tested wildcard portalId
- [ ] Tested negative portalId
- [ ] Tested portalId as array
- [ ] Tested parameter pollution

### Same-Portal Privilege Escalation
- [ ] Created limited user in Portal A
- [ ] Tested limited user accessing admin APIs
- [ ] Tested user management API access
- [ ] Tested settings/configuration API access
- [ ] Tested delete operations with limited user
- [ ] Tested sensitive property access

### Property-Level Authorization
- [ ] Tested accessing sensitive properties
- [ ] Tested with property wildcards (properties=*)
- [ ] Tested accessing custom sensitive fields
- [ ] Tested PHI/PII property access

### Indirect Access
- [ ] Tested search APIs for cross-portal data
- [ ] Tested reports/analytics endpoints
- [ ] Tested webhook payloads
- [ ] Tested email tracking
- [ ] Tested file access across portals

---

## 🎨 XSS Testing (Priority 4)

Checklist: `testing-checklists/XSS-testing.md`

### Context Identification
- [ ] Mapped all input fields
- [ ] Identified where input is reflected
- [ ] Analyzed encoding/filtering per context
- [ ] Checked for Content Security Policy (CSP)

### Basic XSS Testing
- [ ] Tested basic payload: `<script>alert(1)</script>`
- [ ] Tested image payload: `<img src=x onerror=alert(1)>`
- [ ] Tested SVG payload: `<svg onload=alert(1)>`
- [ ] Tested iframe payload
- [ ] Tested attribute injection

### Filter Bypass
- [ ] Tested case variation (ScRiPt)
- [ ] Tested encoding (HTML entities, URL encoding)
- [ ] Tested Unicode/UTF-7
- [ ] Tested double encoding
- [ ] Tested tag breaking techniques

### Stored XSS
- [ ] Tested contact firstname/lastname fields
- [ ] Tested company name field
- [ ] Tested deal description
- [ ] Tested custom properties
- [ ] Tested notes and comments
- [ ] Tested blog posts (if accessible)
- [ ] Tested email templates
- [ ] Tested workflow configurations

### Reflected XSS
- [ ] Tested search parameters
- [ ] Tested URL parameters
- [ ] Tested HTTP headers (User-Agent, Referer)
- [ ] Tested API error messages
- [ ] Tested in different views (list, detail, export)

### DOM-Based XSS
- [ ] Used DOM Invader extension
- [ ] Identified dangerous DOM sinks
- [ ] Tested URL fragment manipulation
- [ ] Tested postMessage handlers

### XSS to Account Takeover
- [ ] Created payload to steal session tokens
- [ ] Created payload to steal API keys
- [ ] Created payload to change email
- [ ] Created payload to create admin user
- [ ] Tested exfiltration to external server

### Customer Connected Domains
- [ ] Set up customer portal with connected domain
- [ ] Tested XSS on connected domain
- [ ] Verified it also executes on hubspot.com
- [ ] Proved vulnerability is HubSpot-introduced

---

## 🚀 Advanced Testing

### API Security
- [ ] Enumerated all API endpoints
- [ ] Tested rate limiting
- [ ] Tested for mass assignment vulnerabilities
- [ ] Tested CORS misconfiguration
- [ ] Tested API versioning issues
- [ ] Looked for internal/debug endpoints

### GraphQL (if available)
- [ ] Tested introspection queries
- [ ] Enumerated schema
- [ ] Tested for sensitive data exposure
- [ ] Tested batch queries
- [ ] Tested mutations without authorization

### File Upload
- [ ] Tested file upload functionality
- [ ] Tested for malicious file upload
- [ ] Tested filename XSS
- [ ] Tested path traversal
- [ ] Tested accessing uploaded files cross-portal

### Subdomain Enumeration
- [ ] Enumerated HubSpot subdomains
- [ ] Tested for subdomain takeovers
- [ ] Checked DNS records
- [ ] Verified HubSpot ownership
- [ ] Created PoC for any takeovers found

---

## 📝 Findings & Reporting

### During Testing
- [ ] Documented all interesting requests
- [ ] Took screenshots of potential vulnerabilities
- [ ] Saved Burp project regularly
- [ ] Kept daily testing log
- [ ] Backed up all evidence

### For Each Finding
- [ ] Verified it's actually a vulnerability
- [ ] Confirmed it's in scope
- [ ] Checked it's not a duplicate
- [ ] Created detailed reproduction steps
- [ ] Assessed business impact
- [ ] Calculated CVSS score
- [ ] Took comprehensive screenshots
- [ ] Saved Burp request/response
- [ ] Filled out report template
- [ ] Provided recommended fix

### Before Submission
- [ ] Reviewed entire report for clarity
- [ ] Verified reproduction steps work
- [ ] Removed any sensitive personal data
- [ ] Attached all evidence
- [ ] Double-checked scope compliance
- [ ] Spell-checked and grammar-checked
- [ ] Had someone else review (if possible)

---

## 🎓 Learning & Improvement

### Knowledge Building
- [ ] Read disclosed HubSpot reports (if available)
- [ ] Studied similar IDOR vulnerabilities
- [ ] Read about authentication bypass techniques
- [ ] Learned about XSS filter bypass methods
- [ ] Reviewed OWASP Top 10

### Skill Development
- [ ] Practiced manual testing techniques
- [ ] Improved Burp Suite proficiency
- [ ] Learned scripting for automation
- [ ] Studied API security
- [ ] Improved report writing skills

### Community Engagement
- [ ] Joined bug bounty communities
- [ ] Read bug bounty write-ups
- [ ] Participated in CTF challenges
- [ ] Shared knowledge (after disclosure)

---

## 📊 Statistics

Track your progress:

### Time Investment
- Setup: _____ hours
- CTF testing: _____ hours
- Auth testing: _____ hours
- IDOR testing: _____ hours
- XSS testing: _____ hours
- Other testing: _____ hours
- **Total: _____ hours**

### Findings
- Critical vulnerabilities: _____
- High vulnerabilities: _____
- Medium vulnerabilities: _____
- Low vulnerabilities: _____
- Informational: _____
- **Total findings: _____**

### Submissions
- Reports submitted: _____
- Reports accepted: _____
- Reports duplicate: _____
- Reports N/A: _____
- **Success rate: _____%**

### Rewards
- CTF Challenge: $ _____
- Other findings: $ _____
- **Total earned: $ _____**

---

## 🎯 Weekly Goals

### Week 1
- [ ] Complete setup
- [ ] CTF challenge testing
- [ ] Authentication testing
- [ ] Submit first report (if finding)

### Week 2
- [ ] IDOR comprehensive testing
- [ ] XSS testing
- [ ] Advanced techniques
- [ ] Submit additional reports

### Week 3+
- [ ] Continue systematic testing
- [ ] Focus on high-value areas
- [ ] Improve methodologies
- [ ] Build automation

---

## ✅ Final Checklist

Before considering testing "complete":

- [ ] Worked through all testing checklists
- [ ] Tested all in-scope domains
- [ ] Attempted CTF challenge thoroughly
- [ ] Created second portal for IDOR testing
- [ ] Tested with multiple user permission levels
- [ ] Ran automated scans
- [ ] Analyzed all Burp logs
- [ ] Documented all findings
- [ ] Submitted valid reports
- [ ] Cleaned up test data
- [ ] Backed up all work

---

**Remember**: Quality over quantity. One high-impact, well-documented vulnerability is worth more than many low-quality reports!

Last Updated: _______________
