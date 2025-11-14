# CTF Challenge Testing Checklist

## Challenge Details
- **Target Portal**: `46962361`
- **Target Domain**: `app.hubspot.com`
- **Reward**: $15,000 (firstname) + $5,000 (super_secret) = $20,000 total
- **Objective**: Read contact record properties without social engineering/brute force

## Target Properties
- `firstname` - First name of contact ($15,000)
- `super_secret` - Custom sensitive property ($5,000)
- `email` - Email address (needed for submission)

## Testing Strategy

### Phase 1: Reconnaissance
- [ ] Enumerate API endpoints related to contacts
- [ ] Identify authentication mechanisms for portal 46962361
- [ ] Map all portal-related parameters in requests
- [ ] Document API patterns for contact retrieval
- [ ] Check for GraphQL endpoints
- [ ] Look for batch/bulk API endpoints

**Burp Actions:**
- Target → Site map → Filter for `46962361`
- Proxy → HTTP History → Search for "contact", "crm", "properties"
- Use Logger++ to track all portal ID references

### Phase 2: IDOR Testing
- [ ] Test direct contact ID enumeration
- [ ] Try accessing contacts via different portal contexts
- [ ] Test missing/modified portal ID in API calls
- [ ] Check for portal ID in JWT tokens
- [ ] Attempt cross-portal contact access
- [ ] Test wildcard or null portal ID values

**Test Cases:**
```
GET /contacts/v1/contact/vid/{vid}/profile
GET /contacts/v2/contacts/{contactId}
GET /crm/v3/objects/contacts/{contactId}
POST /contacts/v1/lists/all/contacts/all (with portal filters)
```

**Burp Actions:**
- Intruder → Test portal ID parameter manipulation
- Repeater → Manual portal ID substitution
- Use Autorize extension for authorization testing

### Phase 3: API Parameter Tampering
- [ ] Remove authorization headers
- [ ] Modify `portalId` parameter
- [ ] Test `hubId` vs `portalId` confusion
- [ ] Add/modify scope parameters
- [ ] Test deprecated API versions
- [ ] Check for parameter pollution

**Parameters to Test:**
- `portalId=46962361`
- `hubId=46962361`
- `accountId=46962361`
- `vid={contact_vid}`
- `email={contact_email}`

### Phase 4: Authentication Bypass
- [ ] Test API calls without authentication
- [ ] Try using your trial portal's API key for target portal
- [ ] Test OAuth token reuse across portals
- [ ] Check for JWT algorithm confusion
- [ ] Test session fixation
- [ ] Look for API keys in responses

**Burp Actions:**
- Remove `Authorization` header
- Replace API key with yours
- Modify JWT payload (alg: none, portal_id)
- Use JSON Web Tokens extension

### Phase 5: GraphQL Exploration
- [ ] Enumerate GraphQL schema
- [ ] Test introspection queries
- [ ] Check for exposed contact queries
- [ ] Test batch queries
- [ ] Look for aliases bypassing rate limits

**GraphQL Test Queries:**
```graphql
query {
  contacts(portalId: "46962361") {
    firstname
    super_secret
    email
  }
}
```

### Phase 6: API Version Testing
- [ ] Test older API versions (v1, v2, v3)
- [ ] Check for deprecated endpoints with weaker auth
- [ ] Look for legacy /contacts/ paths
- [ ] Test internal API endpoints

**Endpoints to Try:**
```
/contacts/v1/contact/...
/contacts/v2/contact/...
/crm/v3/objects/contacts/...
/crm-objects/v1/...
/engagements/v1/...
```

### Phase 7: Indirect Access Methods
- [ ] Search/filter APIs with portal ID
- [ ] Export functionality
- [ ] Reporting endpoints
- [ ] Webhook payload inspection
- [ ] Email tracking pixels with contact data
- [ ] Integration endpoints (Zapier, etc.)

**Test Cases:**
- Search APIs: `/search/v2/contacts`
- Exports: `/crm/v3/objects/contacts/export`
- Lists: `/contacts/v1/lists/{listId}/contacts/all`

### Phase 8: Mass Assignment & Property Injection
- [ ] Add `properties[]` parameter with target properties
- [ ] Test property wildcards: `properties=*`
- [ ] Request all properties explicitly
- [ ] Check for property filtering bypass

**Property Request Examples:**
```
?properties=firstname&properties=super_secret&properties=email
?properties[]=firstname&properties[]=super_secret
?includeAllProperties=true
```

### Phase 9: Timing & Race Conditions
- [ ] Test concurrent requests for authorization bypass
- [ ] Race condition in portal access checks
- [ ] Session confusion attacks
- [ ] Token reuse timing windows

### Phase 10: Error-Based Information Disclosure
- [ ] Trigger errors with invalid parameters
- [ ] Check error messages for contact data
- [ ] Test malformed requests
- [ ] Look for stack traces with sensitive data

## Burp Suite Setup for CTF

### Scope Configuration
1. Add target to scope: `app.hubspot.com`
2. Intruder payloads:
   - Portal IDs: Your portal, 46962361
   - Contact property names: firstname, super_secret, email
   - API versions: v1, v2, v3

### Extensions to Use
- **Autorize**: Test authorization across different user contexts
- **Logger++**: Track all requests mentioning portal 46962361
- **Param Miner**: Discover hidden parameters
- **Turbo Intruder**: Race condition testing
- **JSON Web Tokens**: Analyze and manipulate JWTs

### Match & Replace Rules
Add rules to automatically test variations:
- Replace your portal ID → 46962361
- Test without authentication headers
- Modify portalId in request bodies

## Documentation Requirements

### If You Find Access
Document the following:
1. **Exact reproduction steps** (with curl commands or Burp requests)
2. **Property values obtained**:
   - `firstname = [VALUE]`
   - `super_secret = [VALUE]`
   - `email = [VALUE]`
3. **HTTP request/response pairs** (full details)
4. **Screenshots** of Burp requests and responses
5. **Root cause analysis** of the vulnerability
6. **Recommended fix**

### Submission Process
1. Document everything in `findings/CTF-finding.md`
2. Save all Burp requests/responses
3. Email submission ID to the email address found in contact's email property
4. Subject line: "HubSpot CTF Challenge"

## Important Reminders
- ⚠️ **DO NOT** attempt to access other portals you don't own
- ⚠️ **DO NOT** use social engineering
- ⚠️ **DO NOT** brute force
- ⚠️ Test only technical vulnerabilities
- ⚠️ Document EVERYTHING as you test
- ⚠️ First valid submission wins

## Red Flags to Investigate
If you see any of these, dig deeper:
- Portal ID in URL but not validated
- API endpoints accessible without proper auth
- Different auth requirements for v1/v2/v3 APIs
- Contact data in error messages
- Portal confusion in multi-tenant context
- Weak session/token validation
- Missing authorization checks on property access
