# IDOR (Insecure Direct Object Reference) Testing Checklist

## Overview
IDORs are HIGH PRIORITY for HubSpot, especially cross-portal data access. Focus on accessing data from portal A while authenticated to portal B.

## Priority Levels

### CRITICAL: Cross-Portal IDORs
- Accessing contacts/data from portal B while authenticated to portal A
- Reading sensitive properties (PHI/PII) across portals
- Financial/billing information from other portals
- Super Admin privilege escalation

### HIGH: Same-Portal Privilege Escalation
- Low-privileged user accessing admin APIs
- User role bypass
- Accessing restricted portal features
- Reading/modifying sensitive objects without permission

### MEDIUM/LOW: Same-Portal Non-Sensitive IDORs
- Basic CRUD on non-sensitive objects
- Sharing/permission modifications on public content

## Testing Strategy

### Phase 1: Multi-Account Setup

#### Account Creation
- [ ] Create 2+ HubSpot trial portals
- [ ] Create users with different permission levels in each portal
  - Super Admin
  - Admin
  - Standard User
  - Limited User (if available)
- [ ] Document portal IDs and user credentials
- [ ] Create test data (contacts, companies, deals, etc.)

**Document:**
```
Portal A:
- Portal ID: [ID_A]
- Admin Token: [TOKEN_A]
- User Token: [USER_TOKEN_A]

Portal B:
- Portal ID: [ID_B]
- Admin Token: [TOKEN_B]
- User Token: [USER_TOKEN_B]
```

### Phase 2: Endpoint Discovery

#### API Enumeration
- [ ] Browse HubSpot app normally with Burp running
- [ ] Access all major features (Contacts, Companies, Deals, etc.)
- [ ] Document all API endpoints that handle object access
- [ ] Identify parameters used for authorization (portal_id, object_id, etc.)
- [ ] Check API documentation: https://developers.hubspot.com/docs/api/overview

**Burp Actions:**
- Target → Site map → Look for API patterns
- Logger++ → Filter for object IDs and portal IDs
- Document endpoint patterns:
  - `/crm/v3/objects/{objectType}/{objectId}`
  - `/contacts/v1/contact/vid/{vid}`
  - `/companies/v2/companies/{companyId}`

### Phase 3: Object ID Pattern Analysis

#### Identify Object ID Formats
- [ ] Contact IDs (VID)
- [ ] Company IDs
- [ ] Deal IDs
- [ ] Ticket IDs
- [ ] Custom object IDs
- [ ] User IDs
- [ ] Portal IDs

**Questions to Answer:**
- Are IDs sequential or random?
- Are IDs globally unique or portal-scoped?
- Can you enumerate IDs?
- Are there ID format differences between portals?

### Phase 4: Cross-Portal IDOR Testing

#### Test Case 1: Direct Object Access
**Setup:**
1. In Portal A, create a contact and note the VID/ID
2. In Portal B, authenticate as admin
3. Try to access Portal A's contact from Portal B

**Burp Testing:**
```
GET /contacts/v1/contact/vid/{PORTAL_A_CONTACT_VID}/profile
Host: api.hubspot.com
Authorization: Bearer {PORTAL_B_TOKEN}

Expected: 403 Forbidden or 404 Not Found
If successful: CRITICAL VULNERABILITY
```

- [ ] Test with Portal B admin token
- [ ] Test with Portal B user token
- [ ] Test without changing portal context
- [ ] Test by adding Portal A's ID to request

#### Test Case 2: Portal ID Parameter Manipulation
**Test variations:**
```
GET /contacts/v1/contact/vid/{VID}/profile?portalId={PORTAL_A_ID}
Authorization: Bearer {PORTAL_B_TOKEN}

GET /crm/v3/objects/contacts/{ID}?hubId={PORTAL_A_ID}
Authorization: Bearer {PORTAL_B_TOKEN}

POST /contacts/v1/lists/all/contacts/all
{
  "portalId": {PORTAL_A_ID},
  "count": 100
}
Authorization: Bearer {PORTAL_B_TOKEN}
```

- [ ] Add portal ID parameter to requests that don't have it
- [ ] Change portal ID in requests that do have it
- [ ] Test `portalId`, `hubId`, `accountId` variations
- [ ] Test null, empty, or wildcard portal IDs

#### Test Case 3: Batch/Bulk Operations
```
POST /crm/v3/objects/contacts/batch/read
{
  "inputs": [
    {"id": "{PORTAL_A_CONTACT_1}"},
    {"id": "{PORTAL_A_CONTACT_2}"},
    {"id": "{PORTAL_A_CONTACT_3}"}
  ],
  "properties": ["firstname", "lastname", "email"]
}
Authorization: Bearer {PORTAL_B_TOKEN}
```

- [ ] Test batch read operations
- [ ] Test batch update operations
- [ ] Test export functionality
- [ ] Test search with cross-portal filters

#### Test Case 4: Association IDORs
**Test accessing related objects:**
```
GET /crm/v3/objects/contacts/{PORTAL_A_CONTACT}/associations/companies
Authorization: Bearer {PORTAL_B_TOKEN}

GET /crm/v3/objects/deals/{PORTAL_A_DEAL}/associations/contacts
Authorization: Bearer {PORTAL_B_TOKEN}
```

- [ ] Test contact → company associations
- [ ] Test deal → contact associations
- [ ] Test ticket → contact associations
- [ ] Test custom object associations

### Phase 5: Same-Portal Privilege Escalation

#### Test Case 5: User Role Bypass
**Setup:**
1. Create limited user in Portal A
2. Create admin user in Portal A
3. Document which APIs admin can access
4. Test if limited user can access admin APIs

**Test Examples:**
```
# Limited user tries to access admin endpoints
GET /settings/v3/users
Authorization: Bearer {LIMITED_USER_TOKEN}

GET /integrations/v1/me/settings
Authorization: Bearer {LIMITED_USER_TOKEN}

DELETE /contacts/v1/contact/vid/{VID}
Authorization: Bearer {LIMITED_USER_TOKEN}
```

- [ ] Test user management APIs
- [ ] Test settings/configuration APIs
- [ ] Test delete operations
- [ ] Test sensitive property access
- [ ] Test billing/subscription APIs

#### Test Case 6: Property-Level Authorization
**Test accessing sensitive properties:**
```
GET /contacts/v1/contact/vid/{VID}/profile?properties=super_secret
Authorization: Bearer {LOW_PRIVILEGE_TOKEN}

GET /crm/v3/objects/contacts/{ID}?properties=ssn&properties=credit_card
Authorization: Bearer {LOW_PRIVILEGE_TOKEN}
```

- [ ] Test PHI/PII properties
- [ ] Test custom sensitive properties
- [ ] Test with property wildcards: `properties=*`
- [ ] Test property enumeration

#### Test Case 7: Function-Level Authorization
- [ ] Test CRUD operations (Create, Read, Update, Delete)
- [ ] Test export functionality
- [ ] Test import functionality
- [ ] Test workflow triggers
- [ ] Test email send functionality
- [ ] Test integration management

### Phase 6: Parameter Manipulation

#### Common Parameters to Test
```
portalId={ID}
hubId={ID}
accountId={ID}
userId={ID}
objectId={ID}
vid={ID}
companyId={ID}
dealId={ID}
ownerId={ID}
```

#### Manipulation Techniques
- [ ] Remove parameter entirely
- [ ] Set to null: `portalId=null`
- [ ] Set to empty: `portalId=`
- [ ] Set to wildcard: `portalId=*`
- [ ] Set to negative: `portalId=-1`
- [ ] Set to array: `portalId[]=1&portalId[]=2`
- [ ] Parameter pollution: duplicate parameters
- [ ] Use wrong parameter name: `portal_id` vs `portalId`

**Burp Intruder Setup:**
- Position: Parameter values
- Payload: Portal IDs, object IDs from other portals
- Attack type: Sniper or Pitchfork

### Phase 7: JWT/Token Manipulation

#### JWT Analysis
**If using JWT tokens:**
- [ ] Decode JWT (Header, Payload, Signature)
- [ ] Identify portal_id, user_id, permissions in payload
- [ ] Test algorithm confusion (HS256 → None)
- [ ] Test signature bypass
- [ ] Modify portal_id in payload
- [ ] Modify user_id or role in payload

**Burp Extensions:**
- JSON Web Tokens extension
- JWT Editor

**Test Cases:**
```
Original JWT payload:
{
  "user_id": "123",
  "portal_id": "PORTAL_B_ID",
  "role": "user"
}

Modified JWT payload:
{
  "user_id": "123",
  "portal_id": "PORTAL_A_ID",  // Changed
  "role": "admin"               // Escalated
}
```

### Phase 8: API Version Comparison

#### Test Different API Versions
- [ ] Compare v1, v2, v3 APIs
- [ ] Look for deprecated endpoints with weaker auth
- [ ] Test if newer versions fixed older IDOR issues
- [ ] Test mixing versions in requests

**Example:**
```
# Modern API (might have better authz)
GET /crm/v3/objects/contacts/{ID}

# Legacy API (might have weaker authz)
GET /contacts/v1/contact/vid/{VID}/profile

# Very old API (might be forgotten)
GET /crm-objects/v1/objects/contacts/{ID}
```

### Phase 9: GraphQL IDOR Testing

#### If GraphQL is available
- [ ] Enumerate schema via introspection
- [ ] Test queries for cross-portal data
- [ ] Test mutations for unauthorized modifications
- [ ] Test aliases to bypass rate limits
- [ ] Test batching for bulk IDORs

**Test Query:**
```graphql
query {
  contact(vid: "{PORTAL_A_VID}", portalId: "{PORTAL_A_ID}") {
    firstname
    lastname
    email
    super_secret
  }
}
```

### Phase 10: Indirect IDORs

#### Test Secondary Access Paths
- [ ] Search APIs: Can you search for Portal A data from Portal B?
- [ ] Reports/Analytics: Do they leak cross-portal data?
- [ ] Webhooks: Do webhook payloads contain cross-portal info?
- [ ] Email tracking: Can you access tracking from other portals?
- [ ] File uploads: Can you access files from other portals?
- [ ] Integrations: Do third-party integrations expose IDORs?

**Example:**
```
POST /search/v2/contacts
{
  "query": "*",
  "portalId": "{PORTAL_A_ID}",
  "count": 100
}
Authorization: Bearer {PORTAL_B_TOKEN}
```

## Burp Suite Configuration

### Autorize Extension Setup
1. Install Autorize extension
2. Configure:
   - High-privilege user: Portal A Admin
   - Low-privilege user: Portal A User
   - Unauthenticated user: No token
3. Browse normally as admin
4. Autorize will automatically replay with lower privileges
5. Review results for authorization bypasses

### Intruder Payloads

**Portal ID List:**
```
Your test portal IDs
46962361 (CTF challenge)
Common/sequential IDs
null
*
-1
```

**Object ID List:**
```
Contact VIDs from Portal A
Contact VIDs from Portal B
Sequential IDs (enumerate)
```

### Match & Replace Rules

Test authorization bypass automatically:
```
Type: Request header
Match: Authorization: Bearer (.*)_PORTAL_A
Replace: Authorization: Bearer $1_PORTAL_B
Action: Test cross-portal access
```

## Red Flags to Investigate

High likelihood of IDOR if you see:
- Portal ID in URL but access granted from different portal
- Sequential or predictable object IDs
- No portal validation in API responses
- Same API key works across multiple portals
- Object IDs in error messages from other portals
- Batch operations that don't validate portal context
- Legacy API versions with weaker checks
- Portal ID only validated client-side

## Documentation Template

```markdown
## IDOR Vulnerability: [Description]

**Severity**: [Critical/High/Medium/Low]
**Type**: [Cross-Portal / Privilege Escalation / Property Access]
**CVSS**: [Score]

### Vulnerable Endpoint
`[METHOD] [URL]`

### Description
[Explain the IDOR]

### Impact
- [ ] Cross-portal data access
- [ ] Access to PHI/PII data
- [ ] Financial information disclosure
- [ ] Account takeover potential
- [ ] Privilege escalation

### Reproduction Steps

**Setup:**
1. Create Portal A with contact containing sensitive data
2. Create Portal B with standard user
3. [Additional setup]

**Exploitation:**
1. Authenticate to Portal B as standard user
2. Send request: [Burp request]
3. Observe: [What happens]

### Proof of Concept

**Request:**
```http
GET /contacts/v1/contact/vid/{PORTAL_A_VID}/profile HTTP/2
Host: api.hubspot.com
Authorization: Bearer {PORTAL_B_TOKEN}
```

**Response:**
```json
{
  "vid": "xxx",
  "firstname": "Sensitive",
  "email": "victim@portalA.com",
  "super_secret": "FLAG{...}"
}
```

### Root Cause
[Why does this happen]

### Recommended Fix
1. [Fix recommendation 1]
2. [Fix recommendation 2]

### References
- [CWE-639: Authorization Bypass Through User-Controlled Key]
```

## Testing Tips

1. **Start Simple**: Test obvious cases first (swap IDs in URL)
2. **Be Systematic**: Document every test and result
3. **Use Autorize**: Automate privilege escalation testing
4. **Think Like an Attacker**: How would you access Portal A data from Portal B?
5. **Check All Layers**: URL params, body params, headers, tokens
6. **Test Edge Cases**: null, empty, negative, wildcard values
7. **Don't Give Up**: Try different API versions and endpoints
8. **Document Everything**: Even failed attempts help understand the system

## High-Value Targets for CTF

For the CTF challenge (Portal 46962361):
- [ ] Try accessing contact directly with your portal's auth
- [ ] Test search APIs with target portal ID
- [ ] Test export with target portal filter
- [ ] Check association endpoints
- [ ] Try GraphQL with target portal ID
- [ ] Test batch operations
- [ ] Check legacy API versions
- [ ] Look for portal ID validation bypass
