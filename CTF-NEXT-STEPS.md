# HubSpot CTF Challenge - Next Steps Guide

## Current Status
✅ Burp Suite configured with HubSpot scope
✅ Created test contacts in your portal (50708459)
✅ Identified key API endpoints (inbounddb-objects, GraphQL)
✅ Confirmed authorization is working (403s expected)

❌ Haven't found the vulnerability yet

## The Challenge Reality
This CTF has been running for a while, so:
- **Simple portal ID swaps won't work** (we confirmed this)
- **Direct IDOR attempts are blocked** (tested)
- **GraphQL direct access is blocked** (tested)
- The vulnerability is likely **subtle and non-obvious**

---

## Methodical Testing Plan

### 🎯 PHASE 1: Search & Filter Endpoints (HIGH PRIORITY)

Search endpoints often have weaker authorization checks.

#### Actions:
1. In HTTP History, search for:
   - `/search`
   - `/query`
   - `/filter`
   
2. Look for POST requests with JSON bodies containing filters

3. Test Example:
```
POST /crm/v3/objects/contacts/search HTTP/2
Host: app.hubspot.com
[Your cookies]

{
  "filterGroups": [{
    "filters": [{
      "propertyName": "createdate",
      "operator": "GT",
      "value": "0"
    }]
  }],
  "properties": ["firstname", "super_secret", "email"],
  "limit": 100
}
```

4. Try adding `portalId` to the filter or query body

---

### 🎯 PHASE 2: Batch/Export Operations (HIGH PRIORITY)

Batch operations sometimes validate differently.

#### Actions:
1. Look for `/batch` endpoints in sitemap
2. Look for `/export` endpoints
3. Test batch reads with mixed portal contexts

Example:
```
POST /crm/v3/objects/contacts/batch/read HTTP/2

{
  "inputs": [
    {"id": "1"},
    {"id": "100"},
    {"id": "1000"}
  ],
  "properties": ["firstname", "super_secret"],
  "portalId": "46962361"
}
```

---

### 🎯 PHASE 3: Property Access Patterns

Maybe you can't access the contact, but you can access specific properties?

#### Actions:
1. Test property-specific endpoints
2. Try accessing custom properties directly

Look for:
- `/properties/v1/contacts/properties`
- `/properties/v2/...`
- Property value endpoints

---

### 🎯 PHASE 4: Association/Relationship Bypass

Access contacts through other objects (companies, deals, etc.)

#### Actions:
1. Create a company in your portal
2. Associate it with a contact
3. Try to access associations from CTF portal

Example:
```
GET /crm/v3/objects/companies/{YOUR_COMPANY_ID}/associations/contacts?portalId=46962361
```

---

### 🎯 PHASE 5: API Version Fuzzing

Test EVERY version of contact access:

#### Actions:
```
/contacts/v1/contact/vid/1/profile?portalId=46962361
/contacts/v2/contacts/1?portalId=46962361
/crm/v1/objects/contacts/1?portalId=46962361
/crm/v2/objects/contacts/1?portalId=46962361
/crm/v3/objects/contacts/1?portalId=46962361
/crm-objects/v1/contacts/1?portalId=46962361
```

---

### 🎯 PHASE 6: Parameter Pollution & Edge Cases

#### Test These:
```
# Two portal IDs (maybe uses second?)
?portalId=50708459&portalId=46962361

# Array notation
?portalId[]=46962361

# JSON in URL parameter
?portalId={"value":"46962361"}

# Portal ID in body instead of URL
POST /api/inbounddb-objects/v1/crm-objects/0-1/1
{"portalId": "46962361"}

# Mixed case
?PortalId=46962361
?PORTALID=46962361

# Different parameter names
?hubId=46962361
?accountId=46962361
?portal_id=46962361
```

---

### 🎯 PHASE 7: Rate Limiting & Race Conditions

Sometimes rapid requests bypass authorization.

#### Actions:
1. Use Burp Intruder with Turbo Intruder extension
2. Send 100 requests simultaneously to CTF portal
3. Check if any slip through

---

### 🎯 PHASE 8: Error Message Analysis

Error messages sometimes leak data.

#### Actions:
1. Try invalid contact IDs with CTF portal
2. Try malformed requests
3. Look for stack traces or debug info
4. Check if errors reveal data structure

Examples:
```
GET /api/inbounddb-objects/v1/crm-objects/0-1/INVALID?portalId=46962361
GET /api/inbounddb-objects/v1/crm-objects/0-1/999999999999?portalId=46962361
```

---

### 🎯 PHASE 9: Developer/Debug Endpoints

Look for debug or internal endpoints.

#### Actions:
Search HTTP History for:
- `/debug`
- `/internal`
- `/admin`
- `/test`
- `/dev`

---

### 🎯 PHASE 10: Webhook/Event System

Sometimes webhooks expose data.

#### Actions:
1. Look for webhook endpoints in sitemap
2. Check if you can subscribe to CTF portal events
3. Test event replay attacks

---

## Systematic Testing Workflow

### Daily Testing Session (2-3 hours):

**Hour 1: Endpoint Discovery**
1. Browse HubSpot normally
2. Create contacts, companies, deals
3. Export HTTP History to new file
4. Analyze for new endpoints

**Hour 2: Methodical Testing**
1. Pick ONE phase from above
2. Test EVERY variation in that phase
3. Document ALL results (even failures)
4. Move to next phase

**Hour 3: Analysis & Documentation**
1. Review all responses
2. Look for anomalies
3. Update notes
4. Plan tomorrow's testing

---

## Tools to Use

### Burp Extensions:
- **Autorize**: Auto-test authorization
- **Param Miner**: Find hidden parameters
- **Turbo Intruder**: Race conditions
- **Logger++**: Better logging

### Install These:
1. Go to Extender → BApp Store
2. Install all four above
3. Configure Autorize with your session

---

## Red Flags to Watch For

If you see ANY of these, investigate deeper:
- Different response length for CTF portal
- Partial data in responses
- Error messages with contact info
- Timing differences
- Different status codes (even 404 vs 403 matters)
- Headers revealing info (X-Portal-Id, etc.)
- CORS errors (might indicate accessible endpoint)

---

## Documentation is Key

For EVERY test:
```markdown
## Test #X: [Description]

**Endpoint**: [URL]
**Method**: [GET/POST]
**Portal ID**: 46962361
**Expected**: 403 Forbidden
**Actual**: [What happened]
**Notes**: [Any observations]
```

Create: `findings/test-log.md` and log EVERYTHING.

---

## When You Find Something

**IMMEDIATELY**:
1. Screenshot everything
2. Save Burp request/response
3. Try to reproduce 3 times
4. Document exact steps
5. Extract the flag values
6. Find the email property
7. Submit to that email with subject "HubSpot CTF Challenge"

---

## Realistic Expectations

- This will take **multiple sessions** (days/weeks)
- You'll test **hundreds of variations**
- Most tests will fail (that's normal)
- The vulnerability is **subtle**
- Success = finding ONE working bypass

## Next Immediate Actions

1. ☐ Install Autorize, Param Miner, Logger++ extensions
2. ☐ Create findings/test-log.md file
3. ☐ Start with Phase 1 (Search endpoints)
4. ☐ Test 20+ variations today
5. ☐ Document everything
6. ☐ Come back tomorrow and continue

---

Good luck! The key is **systematic, methodical testing** and **documenting everything**. 🎯
