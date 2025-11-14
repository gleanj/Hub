# HubSpot CTF Quick Reference Card
## $15,000 Bounty - Portal 46962361

---

## 🚀 FASTEST PATH TO FLAG

```bash
# 1. Get your credentials ready
# - API Key: Settings → Integrations → Private Apps
# - Cookies: Browser DevTools → Application → Cookies

# 2. Run the master hunter
cd /home/user/Hub
python3 scripts/master_hunter.py --auto

# 3. While that runs, manually test in Burp
# Open: burp-requests/02-batch-operations.txt (HIGH PRIORITY)
# Open: burp-requests/03-search-endpoints.txt (CRITICAL)
```

---

## 🎯 TARGET INFO

| Item | Value |
|------|-------|
| Portal ID | 46962361 |
| Contact ID | 1 (likely, but test 1-100) |
| Flag 1 Property | `firstname` ($15,000) |
| Flag 2 Property | `super_secret` ($5,000 bonus) |
| Email Property | `email` (submit here) |
| Target Domain | app.hubspot.com |

---

## 🔥 TOP 5 ATTACK VECTORS

### 1. Batch Read Operations ⭐⭐⭐⭐⭐
```bash
# Test this FIRST - batch endpoints often have weaker auth
POST https://api.hubapi.com/crm/v3/objects/contacts/batch/read
Body: {"properties":["firstname","super_secret","email"],"inputs":[{"id":"1"}],"portalId":"46962361"}
```

### 2. Search Endpoints ⭐⭐⭐⭐⭐
```bash
# Search often bypasses authorization
POST https://api.hubapi.com/crm/v3/objects/contacts/search?portalId=46962361
Body: {"filterGroups":[{"filters":[{"propertyName":"hs_object_id","operator":"EQ","value":"1"}]}],"properties":["firstname","super_secret","email"],"limit":10}
```

### 3. GraphQL Queries ⭐⭐⭐⭐
```bash
# Different auth context
python3 scripts/graphql_introspection.py
# Try: crmObject(objectId: "1", objectTypeId: "0-1")
```

### 4. Parameter Pollution ⭐⭐⭐⭐
```bash
# Test all 13 variations in burp-requests/05-parameter-pollution.txt
# Key ones:
?portalId=YOURS&portalId=46962361
?portalId[]=46962361
?hubId=46962361
```

### 5. Internal App APIs ⭐⭐⭐
```bash
# Session-based, different auth
GET https://app.hubspot.com/api/inbounddb-objects/v1/crm-objects/0-1/1?portalId=46962361&includeAllValues=true
# Requires session cookies
```

---

## ⚡ ONE-LINER COMMANDS

### Run All Automated Tests
```bash
python3 scripts/master_hunter.py --api-key "YOUR_KEY" --cookies "YOUR_COOKIES" --auto
```

### Just the Scanner
```bash
python3 scripts/ctf_automated_scanner.py
```

### Just GraphQL
```bash
python3 scripts/graphql_introspection.py
```

### Just Fuzzer
```bash
python3 scripts/fuzzer_advanced.py
```

---

## 🔍 WHAT TO LOOK FOR

### Success Indicators:
- ✅ HTTP 200 (SUCCESS!)
- ⚠️ HTTP 500 (error might leak data)
- ⚠️ HTTP 404 (different from 403 = interesting)
- ⚠️ Different response length
- ⚠️ Partial data in JSON
- ⚠️ Error messages with contact info

### Ignore These:
- ❌ HTTP 403 Forbidden (expected)
- ❌ HTTP 401 Unauthorized (expected)
- ❌ HTTP 429 Rate Limited (slow down)

---

## 🛠️ BURP SUITE QUICK HITS

### Setup Burp:
1. Import scope: `burp-config/hubspot-scope.json`
2. Install extensions: Turbo Intruder, Autorize, Param Miner
3. Configure Autorize with your session

### Priority Testing Order:
1. `02-batch-operations.txt` ⭐⭐⭐⭐⭐
2. `03-search-endpoints.txt` ⭐⭐⭐⭐⭐
3. `05-parameter-pollution.txt` ⭐⭐⭐⭐
4. `04-graphql-queries.txt` ⭐⭐⭐⭐
5. `09-internal-apis.txt` ⭐⭐⭐
6. `10-race-conditions.txt` ⭐⭐⭐

### Turbo Intruder (Race Conditions):
```python
# Send 100 parallel requests
def queueRequests(target, wordlists):
    engine = RequestEngine(endpoint=target.endpoint, concurrentConnections=50)
    for i in range(100):
        engine.queue(target.req)
```

---

## 📝 TESTING CHECKLIST

### Initial Setup
- [ ] Got API key
- [ ] Got session cookies
- [ ] Scripts are executable (`chmod +x scripts/*.py`)
- [ ] Burp Suite configured
- [ ] Extensions installed

### Automated Testing
- [ ] Run master_hunter.py
- [ ] Review scan_results_*.json
- [ ] Review fuzzing_results.json
- [ ] Check for any non-403 responses

### Manual Burp Testing
- [ ] Test all batch operations (file 02)
- [ ] Test all search endpoints (file 03)
- [ ] Test 13 parameter pollution variants (file 05)
- [ ] Test GraphQL queries (file 04)
- [ ] Test internal APIs with cookies (file 09)
- [ ] Run race conditions with Turbo Intruder (file 10)

### Advanced Testing
- [ ] GraphQL introspection completed
- [ ] Contact IDs 1-100 tested
- [ ] Mixed auth methods (API + cookies)
- [ ] Different times of day
- [ ] Error message analysis

---

## 🎲 CREATIVE IDEAS

### Mix & Match:
- Try API key in header + portalId in URL + cookies
- Test during YOUR portal updates
- Send requests from different IPs
- Mix HTTP/1.1 and HTTP/2

### Error Analysis:
- Invalid contact IDs
- Malformed JSON
- Special characters
- Very long property names

### Timing Attacks:
- Measure response times
- Look for processing indicators
- Test during high traffic vs low traffic

---

## 💡 IF YOU FIND IT

### Immediate Steps:
1. ⛔ STOP - Don't modify anything
2. 📸 Screenshot everything
3. 💾 Save full request/response from Burp
4. 📝 Document exact reproduction steps

### Extraction:
```json
{
  "firstname": "[COPY THIS VALUE]",
  "super_secret": "[COPY THIS VALUE]",
  "email": "[SEND SUBMISSION HERE]"
}
```

### Submission:
- **To**: Email address from `email` property
- **Subject**: "HubSpot CTF Challenge"
- **Body**: Flag values + reproduction steps + submission ID

---

## 🔧 TROUBLESHOOTING

### Scripts Won't Run:
```bash
pip3 install requests urllib3
chmod +x scripts/*.py
```

### API Rate Limiting:
- Add delays between requests
- Use different API keys
- Test at off-peak hours

### Burp Issues:
- Check scope is set correctly
- Verify cookies are fresh
- Disable JavaScript in browser for cleaner requests

### No Results:
- You're testing the right things
- The vuln is subtle and non-obvious
- Keep systematic testing
- Document everything
- Try combinations

---

## 📊 EXPECTED TIMELINE

| Phase | Duration | Activity |
|-------|----------|----------|
| Setup | 30 min | Get creds, configure tools |
| Auto Scan | 2-3 hours | Run all automated tools |
| Burp Manual | 3-5 hours | Work through all Burp requests |
| GraphQL | 2-3 hours | Deep dive into GraphQL |
| Race Conditions | 1-2 hours | Turbo Intruder testing |
| Creative | Ongoing | Mix attacks, try variations |

**Total**: 10-15 hours of focused testing minimum

This CTF requires **persistence**. The flag is there. Find it. 🎯

---

## 🎯 REMEMBER

1. **Be Systematic** - Track every test
2. **Document Everything** - Even 403s are data points
3. **Look for Patterns** - Similar endpoints behave similarly
4. **Analyze Errors** - Errors leak information
5. **Stay Persistent** - The vulnerability is subtle but real

---

## 📂 KEY FILES

- `TOOL-USAGE-GUIDE.md` - Detailed usage instructions
- `CTF-NEXT-STEPS.md` - Methodology and phases
- `BugbountyInstructions.txt` - Official rules
- `burp-requests/README.md` - Burp testing guide

---

**GO GET THAT $15,000!** 💰🚀🎯
