# HubSpot CTF Tool Usage Guide
## Complete Arsenal for the $15,000 Bounty

---

## 🎯 Quick Start

### Option 1: Run Everything Automatically
```bash
cd /home/user/Hub
python3 scripts/master_hunter.py --auto
```

### Option 2: Interactive Menu
```bash
python3 scripts/master_hunter.py
```

### Option 3: Manual Tool Selection
Run individual tools as needed (see below).

---

## 📚 Tool Inventory

### 1. Master Hunter (Orchestrator)
**File**: `scripts/master_hunter.py`
**Purpose**: Runs all tools in sequence and aggregates results

**Usage**:
```bash
# Interactive mode
python3 scripts/master_hunter.py

# Fully automated
python3 scripts/master_hunter.py --auto

# With credentials pre-loaded
python3 scripts/master_hunter.py --api-key YOUR_KEY --cookies "cookie1=val1; cookie2=val2" --auto
```

**What it tests**: Everything (orchestrates all other tools)

---

### 2. Automated CTF Scanner
**File**: `scripts/ctf_automated_scanner.py`
**Purpose**: Comprehensive automated testing of all API endpoints

**Usage**:
```bash
python3 scripts/ctf_automated_scanner.py
```

**What it tests**:
- ✅ Direct contact access (all API versions)
- ✅ Batch operations (HIGH PRIORITY)
- ✅ Search/filter endpoints (CRITICAL)
- ✅ Parameter pollution
- ✅ Property access
- ✅ Edge cases (archived, deleted, etc.)

**Requirements**:
- HubSpot API key (required)
- Session cookies (optional, but recommended)

**Output**:
- Console output with color-coded results
- `findings/scan_results_TIMESTAMP.json`

---

### 3. GraphQL Introspection Tool
**File**: `scripts/graphql_introspection.py`
**Purpose**: Discovers GraphQL schema and tests for authorization bypasses

**Usage**:
```bash
python3 scripts/graphql_introspection.py
```

**What it tests**:
- ✅ Full schema introspection
- ✅ Contact queries
- ✅ Batch queries
- ✅ Portal-specific queries
- ✅ Mutation attempts (errors might leak data)

**Requirements**:
- Session cookies from app.hubspot.com (REQUIRED)

**Output**:
- Console output with schema analysis
- JSON responses with potential flags

---

### 4. Advanced Fuzzer
**File**: `scripts/fuzzer_advanced.py`
**Purpose**: Parameter pollution, encoding attacks, header injection

**Usage**:
```bash
python3 scripts/fuzzer_advanced.py
```

**What it tests**:
- ✅ 15+ parameter name variations (portalId, portal_id, hubId, etc.)
- ✅ 12+ encoding methods (URL, hex, unicode, etc.)
- ✅ 10+ custom header injections
- ✅ Path traversal variations
- ✅ HTTP method fuzzing
- ✅ Array injection in POST bodies
- ✅ Contact ID range scanning (1-100)

**Requirements**:
- HubSpot API key (required)

**Output**:
- Console output with interesting findings
- `findings/fuzzing_results.json`

---

### 5. Portal Enumeration (Original)
**File**: `scripts/portal_enumeration.py`
**Purpose**: Interactive portal access testing

**Usage**:
```bash
python3 scripts/portal_enumeration.py
```

**Features**:
- Interactive menu
- Test cross-portal access
- Custom contact testing
- Endpoint enumeration

---

## 📂 Burp Suite Request Library

**Location**: `burp-requests/`

### Files:
1. `01-direct-contact-access.txt` - Direct API calls
2. `02-batch-operations.txt` - Batch read (HIGH PRIORITY)
3. `03-search-endpoints.txt` - Search/filter (CRITICAL)
4. `04-graphql-queries.txt` - GraphQL testing
5. `05-parameter-pollution.txt` - 13 pollution variants
6. `06-associations-bypass.txt` - Association-based access
7. `07-property-access.txt` - Property-specific endpoints
8. `08-edge-cases.txt` - Unusual patterns
9. `09-internal-apis.txt` - App domain APIs
10. `10-race-conditions.txt` - Turbo Intruder configs

### How to Use Burp Requests:

#### Setup:
1. Open each `.txt` file
2. Replace placeholders:
   - `YOUR_API_KEY_HERE` → Your API key
   - `YOUR_SESSION_COOKIES_HERE` → Your cookies
   - `YOUR_PORTAL_ID` → Your portal (50708459)
   - `YOUR_COMPANY_ID`, etc. → IDs from YOUR portal

#### Testing in Burp:
1. **Repeater**: Copy/paste requests into Burp Repeater
2. **Intruder**: Use `§` markers for fuzzing
3. **Turbo Intruder**: Use race condition configs (file 10)

---

## 🔑 Getting Your Credentials

### API Key:
1. Go to your HubSpot portal
2. Settings → Integrations → Private Apps
3. Create new app or use existing
4. Grant ALL CRM scopes
5. Copy API key

### Session Cookies:
1. Log into app.hubspot.com in browser
2. Open Developer Tools (F12)
3. Go to Application → Cookies → app.hubspot.com
4. Copy ALL cookies
5. Format as: `cookie1=value1; cookie2=value2; cookie3=value3`

**Important cookies to include**:
- `hubspotutk`
- `__hstc`
- `__hssc`
- Any with `session` in the name

---

## 🎯 Testing Strategy

### Phase 1: Automated Discovery (2-3 hours)
```bash
# Run all automated tools
python3 scripts/master_hunter.py --auto
```

Review all output files:
- `findings/scan_results_*.json`
- `findings/fuzzing_results.json`
- `findings/master_hunter_summary.json`

### Phase 2: Burp Suite Manual Testing (3-5 hours)
1. Configure Burp with your credentials
2. Work through `burp-requests/` files 1-10
3. Pay special attention to:
   - `02-batch-operations.txt` (HIGH PRIORITY)
   - `03-search-endpoints.txt` (CRITICAL)
   - `05-parameter-pollution.txt` (13 variations)

### Phase 3: Race Conditions (1-2 hours)
1. Install Burp Turbo Intruder extension
2. Use configs from `burp-requests/10-race-conditions.txt`
3. Send 100+ parallel requests
4. Look for ANY success

### Phase 4: GraphQL Deep Dive (2-3 hours)
```bash
python3 scripts/graphql_introspection.py
```
1. Analyze schema thoroughly
2. Test every discovered query
3. Try variations with different variables

### Phase 5: Creative Testing (Ongoing)
- Test during different times of day
- Mix authentication methods (API key + cookies)
- Combine multiple vulnerabilities
- Analyze error messages carefully

---

## 🚨 If You Find the Flag

### Immediate Actions:
1. **STOP** - Don't modify anything
2. **Screenshot** everything
3. **Save** full Burp request/response
4. **Document** exact steps

### Extract Values:
- `firstname` = [VALUE]
- `super_secret` = [VALUE]
- `email` = [VALUE]

### Submit:
1. Email to: **Address in the `email` property**
2. Subject: "HubSpot CTF Challenge"
3. Include:
   - Both flag values
   - Detailed reproduction steps
   - Your submission ID

### Example Submission Email:
```
Subject: HubSpot CTF Challenge

Hello,

I found the CTF flags for portal 46962361:

firstname = [REDACTED]
super_secret = [REDACTED]

Reproduction Steps:
1. [Exact endpoint used]
2. [Authentication method]
3. [Full request details]
4. [Response showing flags]

My HackerOne submission ID: [ID]

[Attach screenshots and Burp request/response]
```

---

## 🛠️ Tool Requirements

### Python Packages:
```bash
pip3 install requests urllib3
```

### Burp Suite Extensions:
1. **Turbo Intruder** - Race conditions
2. **Autorize** - Auto authorization testing
3. **Param Miner** - Hidden parameter discovery
4. **Logger++** - Enhanced logging

Install via: Burp → Extender → BApp Store

---

## 📊 Success Indicators

Watch for these signs (even ONE is interesting):

✅ Status code != 403 (200, 500, 404, etc.)
✅ Different response length
✅ Partial data in response
✅ Error messages with contact info
✅ Timing differences
✅ Different headers
✅ CORS errors

---

## 🎓 Pro Tips

1. **Be Systematic**: Track everything you test
2. **Document Everything**: Even failures are valuable
3. **Look for Patterns**: Authorization bugs follow patterns
4. **Test Combinations**: Mix different attack vectors
5. **Analyze Errors**: Error messages leak information
6. **Timing Matters**: Try during high/low traffic
7. **Think Different**: The vulnerability is subtle and non-obvious

---

## 📝 Test Tracking

Create: `findings/test-log.md`

Format:
```markdown
## Test #1: Batch Read with Portal in Body
- Time: 2024-01-15 14:30
- Tool: Automated Scanner
- Endpoint: /crm/v3/objects/contacts/batch/read
- Method: POST
- Portal: 46962361
- Expected: 403
- Actual: 403
- Notes: Standard behavior

## Test #2: GraphQL Contact Query
- Time: 2024-01-15 14:35
- Tool: GraphQL Tester
- Query: crmObject(objectId: "1")
- Portal: 46962361
- Expected: Error
- Actual: [DOCUMENT FINDINGS]
- Notes: [OBSERVATIONS]
```

---

## 🔄 Continuous Testing

This CTF requires **persistence**:

- Test daily
- Try different variations
- Analyze responses carefully
- Stay systematic
- Document everything

The vulnerability exists. You just need to find it. 🎯

---

## 📞 Questions?

Refer to:
- `CTF-NEXT-STEPS.md` - Detailed methodology
- `BugbountyInstructions.txt` - Official rules
- `README.md` - Project overview

---

**Good luck hunting! The $15,000 is waiting for you.** 💰🎯
