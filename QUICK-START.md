# Quick Start Guide - HubSpot Bug Bounty with Burp Suite

## Day 1: Initial Setup (1-2 hours)

### ✅ Account Setup
1. **Create HubSpot Trial Portal**
   - Go to: https://offers.hubspot.com/free-trial
   - Use @WEAREHACKERONE.COM email
   - Document your Portal ID
   - Enable beta features: https://knowledge.hubspot.com/account-management/opt-your-hubspot-account-into-a-public-beta-feature

2. **Generate API Key**
   - Follow: https://developers.hubspot.com/docs/guides/apps/authentication/intro-to-auth
   - Save API key securely in password manager
   - Test API key with simple request:
     ```bash
     curl -H "Authorization: Bearer YOUR_API_KEY" \
          https://api.hubapi.com/contacts/v1/lists/all/contacts/all
     ```

3. **Create Test Data**
   - Add 5-10 contacts with various properties
   - Create a few companies and deals
   - Add custom properties
   - Note the VIDs/IDs of test records

### ✅ Burp Suite Configuration

1. **Basic Setup**
   - Launch Burp Suite Pro
   - Create new project: "HubSpot Bug Bounty"
   - Configure browser proxy (127.0.0.1:8080)
   - Install Burp CA certificate

2. **Import Scope**
   - Go to Target → Scope
   - Load `burp-config/hubspot-scope.json`
   - Or manually add:
     - Include: `app*.hubspot.com`, `api*.hubspot.com`, `api*.hubapi.com`
     - Exclude: `connect.com`, `shop.hubspot.com`, etc.

3. **Install Extensions** (BApp Store)
   - Autorize (authorization testing)
   - Logger++ (advanced logging)
   - JSON Web Tokens (JWT analysis)
   - Param Miner (parameter discovery)

4. **Basic Configuration**
   - Proxy → Options → Enable "Intercept is on"
   - Target → Site map → Right-click → "Add to scope"
   - Configure auto-backup of project

### ✅ Initial Exploration

1. **Browse HubSpot App**
   - With Burp running, log into app.hubspot.com
   - Click through major features:
     - Contacts
     - Companies
     - Deals
     - Settings
     - API section
   - Let Burp build site map

2. **Review Traffic**
   - Proxy → HTTP History
   - Look for patterns:
     - Portal ID in URLs/parameters
     - API endpoints structure
     - Authentication tokens
     - Contact/company IDs

3. **Initial Documentation**
   - Note your portal ID locations in requests
   - Document main API endpoints
   - Save interesting requests to Repeater

---

## Day 2-3: CTF Challenge Focus (High Priority)

### 🎯 CTF Target: Portal 46962361
**Reward**: $15,000 for `firstname` + $5,000 for `super_secret`

### Testing Strategy

1. **Direct Access Attempts**
   ```
   GET /contacts/v1/contact/vid/{VID}/profile?portalId=46962361
   GET /crm/v3/objects/contacts/{ID}?portalId=46962361
   POST /contacts/v1/lists/all/contacts/all
   {
     "portalId": "46962361",
     "count": 100
   }
   ```

2. **Use Autorize Extension**
   - Configure with your portal credentials
   - Browse your own portal normally
   - Autorize auto-tests with modified portal IDs
   - Check results for cross-portal access

3. **Parameter Manipulation**
   - Use Intruder on portal ID parameters
   - Payloads: null, -1, 0, *, 46962361
   - Look for responses with different lengths/data

4. **API Version Testing**
   ```
   /contacts/v1/... (test this)
   /contacts/v2/... (test this)
   /crm/v3/...     (test this)
   /crm-objects/v1/... (legacy, test this)
   ```

5. **Search & Filter Bypass**
   ```
   POST /search/v2/contacts
   {
     "query": "*",
     "portalId": "46962361"
   }
   ```

### If You Find Access:
1. **STOP** - Don't access more data than needed
2. **Document everything**:
   - Exact request/response
   - Property values (firstname, super_secret, email)
   - Full reproduction steps
3. **Fill out report** using `findings/TEMPLATE-vulnerability-report.md`
4. **Email** submission ID to address in contact's email field
5. **Subject**: "HubSpot CTF Challenge"

---

## Day 4-7: Comprehensive Testing

### Monday: Authentication Testing
**Focus**: `testing-checklists/authentication-testing.md`

Priority tests:
1. OAuth flow vulnerabilities
2. JWT token manipulation
3. MFA bypass attempts
4. Password reset token issues
5. Session management flaws

### Tuesday: IDOR Deep Dive
**Focus**: `testing-checklists/IDOR-testing.md`

Create second portal for cross-portal testing:
1. Portal A (your first portal)
2. Portal B (new trial portal)
3. Test accessing Portal A data from Portal B
4. Test privilege escalation within same portal

### Wednesday: XSS Hunting
**Focus**: `testing-checklists/XSS-testing.md`

Priority areas:
1. Contact/company form fields
2. Custom properties
3. Search functionality
4. Email templates (if reflected in app)
5. ChatSpot.ai interface

### Thursday: API Security
**Focus**: General API testing

1. Enumerate all API endpoints
2. Test each for authorization issues
3. Look for sensitive data exposure
4. Test deprecated endpoints
5. GraphQL testing (if available)

### Friday: Automation & Cleanup
1. Run automated scans on interesting endpoints
2. Review all findings
3. Prepare reports for valid issues
4. Clean up test data
5. Plan next week's testing

---

## Testing Workflow (Daily)

### Morning (2-3 hours)
1. Review previous day's notes
2. Focus on one checklist section
3. Document findings in real-time
4. Take breaks every hour

### Afternoon (2-3 hours)
1. Continue testing different area
2. Review Burp Scanner results
3. Analyze Logger++ logs
4. Update documentation

### Evening (1 hour)
1. Review day's findings
2. Prioritize for tomorrow
3. Back up Burp project
4. Update progress notes

---

## Tools & Commands Cheatsheet

### Burp Suite Shortcuts
```
Ctrl+R     - Send to Repeater
Ctrl+I     - Send to Intruder  
Ctrl+T     - Send to Target
Ctrl+H     - Toggle intercept
Ctrl+F     - Find in response
```

### Useful curl Commands
```bash
# Test API endpoint
curl -H "Authorization: Bearer YOUR_KEY" \
     https://api.hubapi.com/contacts/v1/lists/all/contacts/all

# Test with different portal
curl -H "Authorization: Bearer YOUR_KEY" \
     "https://api.hubapi.com/contacts/v1/lists/all/contacts/all?portalId=46962361"

# Test GraphQL (if available)
curl -X POST https://api.hubspot.com/graphql \
     -H "Authorization: Bearer YOUR_KEY" \
     -H "Content-Type: application/json" \
     -d '{"query":"{ contacts { firstname } }"}'
```

### Python Scripts
```bash
# Portal enumeration
python scripts/portal_enumeration.py

# Log analysis
python scripts/analyze_burp_logs.py
```

---

## Red Flags (Investigate These!)

During testing, if you see any of these, investigate deeper:

🚩 **Portal ID in URL but response contains data from different portal**
🚩 **API endpoint accessible without proper authentication**
🚩 **Different behavior between API v1, v2, v3**
🚩 **Portal ID only validated client-side**
🚩 **Error messages containing data from other portals**
🚩 **Batch operations that don't validate portal context**
🚩 **JWT token with portal_id that can be modified**
🚩 **Session works across multiple portals**
🚩 **Deprecated endpoints with weaker security**
🚩 **GraphQL introspection enabled**

---

## Progress Tracking

### Week 1 Checklist
- [ ] Created 2 test portals
- [ ] Burp Suite fully configured
- [ ] Completed initial exploration
- [ ] CTF challenge: tested all approaches
- [ ] Authentication flows: tested
- [ ] IDOR: basic testing complete
- [ ] XSS: input points mapped
- [ ] Documented 3+ potential findings

### Week 2 Goals
- [ ] Deep dive into most promising areas
- [ ] Complete all testing checklists
- [ ] Submit first report
- [ ] Automated scanning complete
- [ ] Advanced testing techniques applied

---

## When You Find Something

### Immediate Actions:
1. **Document** - Screenshot, save request/response
2. **Verify** - Test multiple times, different accounts
3. **Assess** - Is it actually a vulnerability?
4. **Impact** - What's the worst-case scenario?
5. **Scope** - Is it in scope per program rules?

### Report Preparation:
1. Use `findings/TEMPLATE-vulnerability-report.md`
2. Include clear reproduction steps
3. Demonstrate impact with attack scenario
4. Provide recommended fix
5. Attach all evidence (screenshots, Burp files)

### Before Submitting:
- [ ] Verified it's not a duplicate
- [ ] Confirmed it's in scope
- [ ] Tested on latest version
- [ ] Clear reproduction steps
- [ ] Demonstrated security impact
- [ ] Removed any personal/sensitive data from report

---

## Resources Quick Links

**Documentation:**
- API Docs: https://developers.hubspot.com/docs/api/overview
- Auth Guide: https://developers.hubspot.com/docs/guides/apps/authentication/intro-to-auth
- Bug Bounty Rules: See `BugbountyInstructions.txt`

**Project Files:**
- Checklists: `testing-checklists/`
- Scripts: `scripts/`
- Findings: `findings/`
- Burp Config: `burp-config/`

**Help:**
- Burp Suite Docs: https://portswigger.net/burp/documentation
- OWASP Testing Guide: https://owasp.org/www-project-web-security-testing-guide/

---

## Daily Log Template

Copy this to track daily progress:

```markdown
## Date: [YYYY-MM-DD]

### Focus Area: [CTF / Auth / IDOR / XSS / API]

### Tests Performed:
- [ ] Test 1
- [ ] Test 2
- [ ] Test 3

### Findings:
- Finding 1: [Brief description]
- Finding 2: [Brief description]

### Interesting Observations:
- [Note anything unusual, even if not a vuln]

### Tomorrow's Priority:
- [ ] Follow up on [X]
- [ ] Test [Y] more thoroughly
- [ ] Complete [Z] checklist

### Time Spent: [X hours]
```

---

## Tips for Success

1. **Be Systematic** - Follow checklists, don't skip steps
2. **Document Everything** - You'll forget details later
3. **Focus on Impact** - High-impact findings get better bounties
4. **Think Like an Attacker** - How would you abuse this?
5. **Read the Rules** - Make sure you're testing in-scope items
6. **Don't Give Up** - Keep trying different approaches
7. **Take Breaks** - Fresh eyes find more bugs
8. **Learn Continuously** - Each test teaches you something

**Remember**: The CTF challenge is HIGH VALUE but also likely difficult. Don't spend 100% of your time on it - balance with other testing too!

Good luck! 🎯
