# Burp Suite Request Library for HubSpot CTF

## Target Information
- **Portal ID**: 46962361
- **Objective**: Access contact with properties `firstname` (flag) and `super_secret` (bonus flag)
- **Reward**: $15,000 for firstname, $5,000 for super_secret

## How to Use This Library

### Setup
1. Replace `YOUR_API_KEY_HERE` with your HubSpot API key
2. Replace `YOUR_SESSION_COOKIES_HERE` with your authenticated session cookies from browser
3. Replace `YOUR_PORTAL_ID` with your test portal ID (50708459)
4. Replace `YOUR_COMPANY_ID`, `YOUR_DEAL_ID`, etc. with IDs from YOUR portal

### Getting Your Session Cookies
1. Log into app.hubspot.com in your browser
2. Open Developer Tools > Application > Cookies
3. Copy all cookies for app.hubspot.com
4. Format as: `cookie_name1=value1; cookie_name2=value2; ...`

### Getting Your API Key
1. Go to your HubSpot portal > Settings > Integrations > Private Apps
2. Create a new private app or use existing
3. Grant it all CRM scopes
4. Copy the API key

## Testing Strategy

### Phase 1: Automated Testing (Use Burp Intruder)
1. **Direct Access Tests** (01-direct-contact-access.txt)
   - Test all API versions
   - Use Intruder to test contact IDs 1-1000

2. **Batch Operations** (02-batch-operations.txt)
   - HIGH PRIORITY - batch endpoints often have weaker auth
   - Test each request manually first
   - Then try variations with Intruder

3. **Search Endpoints** (03-search-endpoints.txt)
   - CRITICAL - search often bypasses authorization
   - Test both API key and session cookie authentication

### Phase 2: Advanced Attacks
4. **GraphQL** (04-graphql-queries.txt)
   - Run introspection query first
   - Analyze schema for hidden queries
   - Test different variable combinations

5. **Parameter Pollution** (05-parameter-pollution.txt)
   - Test all 13 variations
   - Look for ANY different response
   - Parser differentials are key

6. **Associations** (06-associations-bypass.txt)
   - Create objects in YOUR portal first
   - Try to associate with CTF portal objects
   - Errors might leak data

### Phase 3: Edge Cases
7. **Property Access** (07-property-access.txt)
   - Try to access property definitions
   - Property history might be accessible

8. **Edge Cases** (08-edge-cases.txt)
   - Test archived/deleted contacts
   - Export endpoints might have different auth
   - GDPR endpoints worth testing

9. **Internal APIs** (09-internal-apis.txt)
   - Requires session cookies
   - Different authentication context
   - Often less hardened

10. **Race Conditions** (10-race-conditions.txt)
    - Requires Burp Turbo Intruder extension
    - Send 100 requests simultaneously
    - Look for even ONE success

## Burp Suite Extensions Needed
1. **Turbo Intruder** - For race condition testing
2. **Autorize** - Automated authorization testing
3. **Param Miner** - Find hidden parameters
4. **Logger++** - Better logging and filtering

## Success Indicators
Watch for these signs:
- ✅ Status code NOT 403 (200, 404, 500 are interesting)
- ✅ Different response length than expected
- ✅ Partial data in response
- ✅ Error messages with contact info
- ✅ Timing differences
- ✅ Headers revealing portal context

## If You Find the Flag
1. **DO NOT MODIFY ANYTHING**
2. Screenshot everything
3. Save full request/response from Burp
4. Document exact reproduction steps
5. Extract the values:
   - `firstname` = [VALUE]
   - `super_secret` = [VALUE]
   - `email` = [VALUE]
6. Email your submission to the address in the `email` property
7. Subject: "HubSpot CTF Challenge"

## Testing Checklist
- [ ] All 01-direct-access requests tested
- [ ] All 02-batch-operations requests tested
- [ ] All 03-search-endpoints requests tested
- [ ] GraphQL introspection completed
- [ ] All 13 parameter pollution variants tested
- [ ] Association bypass attempts made
- [ ] Property access tests completed
- [ ] Edge cases explored
- [ ] Internal APIs tested with session cookies
- [ ] Race condition testing with 100+ parallel requests
- [ ] Param Miner run on key endpoints
- [ ] Autorize extension configured and run

## Advanced Tips
1. **Mix Authentication Methods**: Try same request with both API key AND session cookies
2. **Test During Updates**: Make changes to YOUR portal and test CTF portal simultaneously
3. **Error Analysis**: Invalid inputs often reveal information
4. **Response Timing**: Time differences might indicate processing
5. **Case Sensitivity**: Try all parameter name variations
6. **HTTP/1.1 vs HTTP/2**: Switch protocols in Burp
7. **Different User Agents**: Mobile apps might use different APIs

## Automation
See `/scripts/` directory for automated testing scripts that can run these requests programmatically.
