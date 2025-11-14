# Burp Suite Pro Configuration Guide for HubSpot

## Initial Setup

### 1. Import Scope Configuration
1. Open Burp Suite Pro
2. Go to **Target** → **Scope**
3. Click **Load options** or manually configure:
   - Add to scope: All domains from `hubspot-scope.json`
   - Exclude from scope: Out-of-scope domains listed

### 2. Proxy Settings
1. Go to **Proxy** → **Options**
2. Ensure proxy listener is running (default: 127.0.0.1:8080)
3. Configure your browser to use Burp proxy
4. Install Burp's CA certificate in browser

### 3. Install Extensions (BApp Store)

#### Essential Extensions for HubSpot Testing:

**Authorization Testing:**
- **Autorize** - Automatic authorization testing
  - Tests same requests with different privilege levels
  - Essential for IDOR testing

**Logging:**
- **Logger++** - Advanced logging
  - Filter for portal IDs: `46962361`
  - Track all API calls
  - Export logs for analysis

**Parameter Discovery:**
- **Param Miner** - Find hidden parameters
  - Discover API parameters
  - Cache poisoning detection
  - Great for finding undocumented features

**JWT Testing:**
- **JSON Web Tokens** - JWT analysis and manipulation
  - Decode JWTs
  - Test algorithm confusion
  - Modify claims (portal_id, user_id)

**Advanced Scanning:**
- **Turbo Intruder** - Fast custom attacks
  - Race conditions
  - High-speed fuzzing
  - Custom attack patterns

**DOM XSS:**
- **DOM Invader** (Built-in) - DOM-based XSS detection
  - Automatic DOM sink detection
  - Client-side prototype pollution

**Other Useful:**
- **Collaborator Everywhere** - Out-of-band testing
- **Hackvertor** - Encoding/decoding
- **Active Scan++** - Additional scan checks
- **HTTP Request Smuggler** - Request smuggling tests

### 4. Scanner Configuration (Pro only)

Go to **Scanner** → **Scan configuration**:

**Live scanning:**
- Enable for in-scope items only
- Focus on: XSS, SQLi, IDOR, Authentication

**Crawl settings:**
- Maximum link depth: 5-10
- Handle application errors: true
- Submit forms: true

**Audit settings:**
- Enable: JavaScript analysis
- Enable: Stored attacks
- Frequently used locations: Headers, parameters, cookies

## Workflow Configuration

### Project Setup

1. Create new project: `HubSpot Bug Bounty`
2. Set working directory: `C:\Users\glean\OneDrive\Desktop\Hub`
3. Configure auto-backup

### Autorize Extension Setup (CRITICAL for IDOR Testing)

1. Install Autorize from BApp Store
2. Configure:
   ```
   High-Privilege User:
   - Portal A Admin token
   - All permissions
   
   Low-Privilege User:
   - Portal A limited user token
   - Restricted permissions
   
   Unauthenticated:
   - Remove Authorization header
   ```
3. Enable "Intercept is on"
4. Browse app as high-privilege user
5. Autorize automatically replays requests with lower privileges
6. Review results for authorization bypasses

### Logger++ Configuration

1. Install Logger++ from BApp Store
2. Configure filters:
   ```
   Filter 1: Contains "46962361" (CTF portal)
   Filter 2: Contains "contact" or "crm"
   Filter 3: Response contains "firstname" or "super_secret"
   ```
3. Enable auto-save logs
4. Export path: `Hub/findings/logs/`

### Match and Replace Rules

Go to **Proxy** → **Options** → **Match and Replace**

Add these rules for automated testing:

**Rule 1: Test Cross-Portal Access**
```
Type: Request body
Match: "portalId":"(\d+)"
Replace: "portalId":"46962361"
Comment: Auto-test CTF portal access
Enabled: [Toggle as needed]
```

**Rule 2: Test Without Auth**
```
Type: Request header
Match: ^Authorization:.*$
Replace: 
Comment: Test without authentication
Enabled: [Toggle as needed]
```

**Rule 3: Add Debug Parameters**
```
Type: Request first line
Match: ^(GET [^?]*)\??(.*) HTTP
Replace: $1?debug=1&verbose=1&$2 HTTP
Comment: Enable debug mode
Enabled: [Toggle as needed]
```

**Rule 4: Test Portal ID in URL**
```
Type: Request first line
Match: portalId=\d+
Replace: portalId=46962361
Comment: Change portal ID in URL
Enabled: [Toggle as needed]
```

## Intruder Configuration

### Preset Payload Lists

Create these payload lists for quick access:

**Portal IDs (`portal-ids.txt`):**
```
[Your Portal A ID]
[Your Portal B ID]
46962361
null
-1
0
*
```

**XSS Payloads (`xss-payloads.txt`):**
```
<script>alert(1)</script>
<img src=x onerror=alert(1)>
<svg onload=alert(1)>
"><script>alert(1)</script>
'-alert(1)-'
javascript:alert(1)
<iframe src="javascript:alert(1)">
```

**SQL Injection (`sqli-payloads.txt`):**
```
' OR '1'='1
' OR '1'='1'--
' OR 1=1--
" OR "1"="1
') OR ('1'='1
admin' OR '1'='1
```

**API Versions (`api-versions.txt`):**
```
v1
v2
v3
v4
beta
internal
legacy
```

### Common Attack Patterns

**Pattern 1: IDOR Testing**
1. Capture request with object ID
2. Send to Intruder
3. Position: Object ID parameter
4. Payload: Sniper attack
5. Payloads: Sequential numbers or known IDs
6. Options: Follow redirects
7. Grep - Match: Success indicators

**Pattern 2: Parameter Fuzzing**
1. Send request to Intruder
2. Position: All parameters
3. Attack type: Cluster bomb
4. Payload 1: Parameter names
5. Payload 2: Test values
6. Look for: Different responses, errors with data

**Pattern 3: Authentication Bypass**
1. Capture authenticated request
2. Send to Intruder
3. Position: Auth header or token
4. Payload: Token variations (modified, null, other users)
5. Compare response lengths

## Repeater Workflow

### Standard Testing Flow:

1. **Capture Request**: Proxy → Right-click → Send to Repeater
2. **Baseline Test**: Send original request, note response
3. **Modify and Test**: Change parameters systematically
4. **Document Results**: Right-click → Save item

### Repeater Tabs Organization:

Create separate tabs for:
- **Auth Testing**: Login, OAuth, MFA requests
- **IDOR Tests**: Cross-portal access attempts
- **XSS Tests**: Input reflection tests
- **CTF Challenge**: Portal 46962361 access attempts
- **API Testing**: Various API endpoint tests

### Repeater Shortcuts:
- `Ctrl+R`: Send request
- `Ctrl+Space`: Send to Repeater
- `Ctrl+I`: Send to Intruder
- `Ctrl+U`: URL-encode selection
- `Ctrl+Shift+U`: URL-decode selection

## Scanner Settings (Pro)

### Scan Configuration

**Live Passive Crawl:**
- Enable for in-scope only
- Maximum depth: 10

**Live Audit:**
- Selected issues only:
  - XSS (all types)
  - SQL injection
  - Path traversal
  - Code injection
  - OS command injection
  - XXE
  - SSRF
  
**Audit Optimization:**
- Skip duplicate insertions: Yes
- Skip common parameter names: No (we want thorough testing)

### Custom Scan Insertions

Add insertion points for HubSpot-specific parameters:
- `portalId`
- `hubId`
- `vid` (contact ID)
- `objectId`
- `ownerId`
- Custom property names

## Collaboration with Team

### Sharing Configurations

Export and share:
1. **Project File**: `HubSpot.burp` (entire session)
2. **State File**: Current scanner state
3. **Logs**: Logger++ exports
4. **Issue Reports**: Scanner findings

### Best Practices

- **Comment everything**: Add notes to interesting requests
- **Highlight findings**: Use Burp's highlight feature (right-click)
- **Regular exports**: Save project frequently
- **Document as you go**: Don't rely on memory

## Performance Optimization

### Resource Settings:

**Proxy → Options → Performance:**
- Streaming responses: Enable for large responses
- Disable response compression: Check if debugging
- Thread count: 10-20 (adjust based on system)

**Intruder → Options → Resource Pool:**
- Maximum concurrent requests: 10 (respect rate limits)
- Delay between requests: 100-500ms (avoid DoS)
- Throttle: Yes (don't overload HubSpot)

## Hotkeys Cheat Sheet

```
Ctrl+R        - Send request (Repeater)
Ctrl+I        - Send to Intruder
Ctrl+R        - Send to Repeater
Ctrl+C        - Send to Comparer
Ctrl+T        - Send to Target
Ctrl+Space    - Active scan
Ctrl+H        - Toggle Intercept
Ctrl+F        - Find in response
Ctrl+U        - URL encode
Ctrl+Shift+U  - URL decode
```

## Debugging Tips

### When things don't work:

1. **Check Proxy History**: Is request being sent?
2. **Check Alerts**: Look for SSL errors
3. **Check Scope**: Is target in scope?
4. **Check Browser**: Proxy settings correct?
5. **Check Certificate**: CA cert installed?
6. **Check Extensions**: Any conflicts?

### Common Issues:

**Issue**: Can't see HTTPS traffic
**Fix**: Install Burp CA certificate in browser

**Issue**: Extension not working
**Fix**: Restart Burp, check Java version

**Issue**: Slow performance
**Fix**: Reduce thread count, clear project

**Issue**: Scanner not finding issues
**Fix**: Enable JavaScript analysis, expand crawl depth

## Regular Maintenance

Daily:
- [ ] Export project backup
- [ ] Review Logger++ logs
- [ ] Check Autorize findings
- [ ] Review scanner issues

Weekly:
- [ ] Update extensions
- [ ] Clean old projects
- [ ] Update payload lists
- [ ] Review methodology

## Security Notes

⚠️ **Important Reminders:**
- Never test outside scope
- Respect rate limits
- Don't DoS the application
- Follow responsible disclosure
- Keep findings confidential until resolved
