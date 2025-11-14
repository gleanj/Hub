# Authentication Testing Checklist

## Overview
Authentication flows are a HIGH PRIORITY for HubSpot bug bounty. Focus on account takeover and unauthorized data access.

## Test Categories

### 1. Signup Flow Testing

#### Email Signup
- [ ] Test email verification bypass
- [ ] Check for account enumeration
- [ ] Test disposable email blocking bypass
- [ ] Race condition in email verification
- [ ] Parameter pollution in signup form
- [ ] Test SQL injection in email field
- [ ] XSS in profile fields during signup

**Burp Actions:**
- Intercept POST to `/signup` or `/register`
- Test: `email=victim@example.com%00attacker@example.com`
- Param Miner on signup request
- Test removing email verification step

#### OAuth Signup (Google/Apple/Microsoft)
- [ ] OAuth state parameter validation
- [ ] Redirect URI manipulation
- [ ] Token/code reuse
- [ ] Account linking vulnerabilities
- [ ] Pre-account takeover (register before victim)
- [ ] OAuth token stealing via XSS

**Test Cases:**
```
redirect_uri=https://attacker.com
redirect_uri=https://app.hubspot.com@attacker.com
redirect_uri=https://app.hubspot.com.attacker.com
state=[manipulated_state]
```

### 2. Login Flow Testing

#### Email/Password Login
- [ ] Response manipulation (change "success":false to true)
- [ ] Username enumeration via timing/error messages
- [ ] Password reset token guessing
- [ ] Session fixation
- [ ] Cookie injection
- [ ] JWT manipulation

**Burp Actions:**
- Intercept login response, modify to bypass
- Compare timing for valid vs invalid usernames
- Test session cookie for predictability
- Decode JWT tokens, test signature bypass

#### SSO/SAML Testing
- [ ] SAML assertion replay
- [ ] XML signature wrapping
- [ ] SAML response tampering
- [ ] IDP confusion attacks
- [ ] Certificate validation bypass

**Burp Extensions:**
- SAML Raider
- JWT Editor

#### OAuth Login
- [ ] Authorization code interception
- [ ] Token endpoint authentication bypass
- [ ] Scope escalation
- [ ] OAuth token theft
- [ ] CSRF in OAuth flow

### 3. Multi-Factor Authentication (MFA)

#### MFA Bypass Techniques
- [ ] Direct navigation after entering password (skip MFA)
- [ ] Remove MFA parameter from request
- [ ] Response manipulation
- [ ] Rate limiting on MFA codes
- [ ] MFA code reuse
- [ ] Backup codes enumeration
- [ ] Time-based race conditions

**Test Cases:**
```
POST /login
- Remove "mfa_required": true from response
- Skip to /dashboard directly
- Reuse old MFA codes
- Test null/empty MFA code
```

#### MFA Implementation Flaws
- [ ] Weak TOTP secret generation
- [ ] Predictable backup codes
- [ ] MFA disabled without re-authentication
- [ ] Account takeover via MFA reset
- [ ] SMS/Email interception opportunities

### 4. Password Reset Flow

#### Critical Tests
- [ ] Password reset token predictability
- [ ] Token not invalidated after use
- [ ] Token reuse across accounts
- [ ] Token leakage in referrer
- [ ] Host header injection
- [ ] Email parameter tampering
- [ ] Race condition in reset process

**Burp Actions:**
```
POST /password-reset
{
  "email": "victim@example.com",
  "email": "attacker@example.com"  // Parameter pollution
}
```

- Test token format: Is it predictable? JWT? UUID?
- Brute force token if short/predictable
- Test token expiration
- Check for token in response/URL

#### Host Header Injection
```
POST /password-reset HTTP/1.1
Host: attacker.com
...

Could result in:
Reset link: https://attacker.com/reset?token=xxx
```

### 5. Session Management

#### Session Security
- [ ] Session fixation vulnerabilities
- [ ] Session token in URL
- [ ] Session doesn't invalidate on logout
- [ ] Session doesn't invalidate on password change
- [ ] Concurrent session limits
- [ ] Session token predictability
- [ ] Missing Secure/HttpOnly flags

**Burp Actions:**
- Decode session cookies (base64, JWT, etc.)
- Test session reuse after logout
- Check for session in GET parameters
- Sequencer analysis on session tokens

#### Cross-Portal Session Issues
- [ ] Session from Portal A works on Portal B
- [ ] Portal ID not validated in session
- [ ] JWT contains portal ID but not validated
- [ ] Session escalation across portals

### 6. API Authentication

#### API Key Testing
- [ ] API key in URL parameters
- [ ] API key leakage in logs/errors
- [ ] API key not scoped to portal
- [ ] Weak API key generation
- [ ] API key in HTTP instead of HTTPS

**Test Endpoints:**
```
GET /api/v1/contacts?apikey=xxx
GET /api/v1/contacts?hapikey=xxx
Authorization: Bearer xxx
X-API-Key: xxx
```

#### OAuth Token Testing
- [ ] Token doesn't expire
- [ ] Refresh token reuse
- [ ] Scope validation bypass
- [ ] Token works across portals
- [ ] Token in URL/logs

### 7. Account Takeover Scenarios

#### Direct Takeover Paths
- [ ] Change email without verification
- [ ] Change password without current password
- [ ] OAuth account linking abuse
- [ ] Portal transfer/ownership takeover
- [ ] User invitation abuse
- [ ] Email change race condition

**High Priority Tests:**
```
POST /account/email
{"new_email": "attacker@example.com"}
// Without email verification

POST /account/link-oauth
{"provider": "google", "token": "attacker_token"}
// Link attacker's Google to victim's HubSpot
```

#### Indirect Takeover Paths
- [ ] XSS to steal session tokens
- [ ] CSRF to change email/password
- [ ] Subdomain takeover with session cookies
- [ ] Cookie tossing attacks
- [ ] Clickjacking on sensitive actions (if high impact)

## Burp Suite Configuration

### Intruder Payloads for Auth Testing

**Portal IDs:**
- Your test portal ID
- 46962361 (CTF portal)
- Common/default portal IDs

**User Agents:**
- Mobile apps: `HubSpot/iOS`, `HubSpot/Android`
- Various browsers
- API clients

**Email Formats:**
```
victim@example.com
victim+tag@example.com
victim@example.com%00attacker@example.com
victim@example.com%0aattacker@example.com
"victim@example.com"@example.com
```

### Match & Replace Rules

Add these to automatically test variations:
```
Type: Request header
Match: Authorization: Bearer (.*)
Replace: Authorization: Bearer $1malformed
Action: Test without proper auth

Type: Request body
Match: "mfa_required": true
Replace: "mfa_required": false
Action: Test MFA bypass
```

### Useful Extensions
- **JSON Web Tokens**: Analyze and manipulate JWTs
- **AuthMatrix**: Map authentication requirements
- **Autorize**: Test authorization bypass
- **Session Timeout Test**: Check session expiration
- **SAML Raider**: SAML attack testing

## Common Authentication Vulnerabilities

### JWT Vulnerabilities
- [ ] Algorithm confusion (HS256 vs RS256)
- [ ] None algorithm
- [ ] Weak secret key
- [ ] Missing signature verification
- [ ] Expired token accepted
- [ ] Token tampering (change portal_id, user_id)

**Burp JWT Testing:**
```
1. Decode JWT header and payload
2. Test: "alg": "none"
3. Test: Change portal_id in payload
4. Test: Remove signature
5. Test: Brute force weak secrets
```

### OAuth 2.0 Vulnerabilities
- [ ] Missing state parameter
- [ ] Redirect URI validation bypass
- [ ] Token leakage via referrer
- [ ] Scope escalation
- [ ] Authorization code replay
- [ ] Open redirect in OAuth flow

### Password Reset Token Flaws
- [ ] Tokens don't expire
- [ ] Weak token entropy
- [ ] Token for one user works for another
- [ ] Token leaked in HTTP headers
- [ ] Tokens accepted over HTTP

## Testing Workflow

### 1. Map Authentication Flows
- [ ] Create accounts with different methods
- [ ] Document all auth-related endpoints
- [ ] Identify tokens, cookies, headers used
- [ ] Map user roles and permissions

### 2. Baseline Testing
- [ ] Perform normal auth flows
- [ ] Save all requests in Burp
- [ ] Document expected behavior
- [ ] Identify security controls

### 3. Vulnerability Testing
- [ ] Follow checklist items above
- [ ] Use Intruder for fuzzing
- [ ] Use Repeater for manual testing
- [ ] Use Autorize for authz testing
- [ ] Document findings as you go

### 4. Exploit Development
- [ ] Create proof-of-concept exploits
- [ ] Test end-to-end attack scenarios
- [ ] Document impact clearly
- [ ] Prepare demo for submission

## High-Value Targets

### Critical Findings (Likely P1/P2)
- Complete authentication bypass
- Account takeover without user interaction
- Cross-portal authentication bypass
- MFA bypass leading to account takeover
- Mass account compromise

### High-Value Findings (Likely P2/P3)
- Password reset token prediction
- Session fixation
- OAuth implementation flaws
- JWT signature bypass
- Email verification bypass

## Documentation Template

For each finding, document:
```markdown
## Vulnerability: [Name]

**Severity**: [Critical/High/Medium/Low]
**CWE**: [CWE-XXX]
**CVSS**: [Score]

### Description
[What is the vulnerability]

### Impact
[What can an attacker do]

### Reproduction Steps
1. [Step 1]
2. [Step 2]
3. [etc.]

### Proof of Concept
[Burp request/response or curl command]

### Affected Endpoints
- [Endpoint 1]
- [Endpoint 2]

### Recommended Fix
[How to fix it]

### References
[Related CVEs, articles, etc.]
```

## Red Flags to Investigate
- Authentication checks only on client-side
- Portal ID in JWT but not validated server-side
- Different auth requirements for different API versions
- Session tokens that don't rotate
- API endpoints with missing authentication
- OAuth redirects to non-whitelisted domains
- Password resets that don't invalidate sessions
