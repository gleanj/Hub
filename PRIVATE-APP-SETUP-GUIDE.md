# HubSpot Private App Setup Guide

This guide will walk you through creating a Private App in HubSpot to get a valid access token for the CTF security testing tools.

---

## Why Private Apps?

HubSpot has deprecated standard API keys in favor of **Private Apps** for better security:
- More granular permissions (scopes)
- Easier to revoke/manage
- Better security practices
- Per-app access tokens

---

## Step-by-Step: Create a Private App

### Step 1: Access Private Apps Settings

1. **Log into your HubSpot account**
2. Click the **Settings icon** (gear) in the top navigation bar
3. In the left sidebar, navigate to:
   ```
   Integrations → Private Apps
   ```

### Step 2: Create a New Private App

1. Click **"Create a private app"** button
2. Fill in the Basic Info tab:
   - **Name**: `HubSpot CTF Security Testing`
   - **Description**: `Security testing tool for HubSpot CTF challenge and bug bounty program`

### Step 3: Set Required Scopes (Permissions)

Click on the **"Scopes"** tab and enable the following permissions:

#### ✅ Required CRM Scopes:
- ✅ `crm.objects.contacts.read` - Read contacts
- ✅ `crm.objects.contacts.write` - Write contacts (for testing)
- ✅ `crm.objects.companies.read` - Read companies
- ✅ `crm.objects.deals.read` - Read deals
- ✅ `crm.schemas.contacts.read` - Read contact schemas
- ✅ `crm.schemas.companies.read` - Read company schemas
- ✅ `crm.schemas.deals.read` - Read deal schemas

#### ✅ Optional but Recommended:
- ✅ `crm.objects.owners.read` - Read owners
- ✅ `crm.lists.read` - Read lists
- ✅ `crm.objects.custom.read` - Read custom objects (if any)

#### ⚠️ For Advanced Testing (optional):
- `crm.objects.contacts.write` - Modify contacts
- `crm.objects.companies.write` - Modify companies
- `timeline` - Timeline events
- `files` - File access

### Step 4: Create the App

1. Review your scopes
2. Click **"Create app"** button at the top right
3. **IMPORTANT**: A dialog will appear showing your access token
   - This is **the only time** you'll see the full token!
   - Copy it immediately!

### Step 5: Copy Your Access Token

The token will look something like this:
```
pat-na1-12345678-abcd-1234-efgh-123456789012
```

**Copy this token now!**

---

## Step 6: Update Your Configuration

Once you have your new Private App access token, update the `.env` file:

1. Open the file: `C:\Users\glean\OneDrive\Desktop\Hub\.env`

2. Update the `HUBSPOT_API_KEY` line with your new token:
   ```bash
   HUBSPOT_API_KEY=pat-na1-12345678-abcd-1234-efgh-123456789012
   ```

3. You can also find your Portal ID in HubSpot:
   - Go to Settings → Account Setup → Account Defaults
   - Look for "Hub ID" or "Portal ID"
   - Update `MY_PORTAL_ID` in `.env` with this value

4. Save the file

---

## Step 7: Test Your New Token

Run the credential test script:

```bash
cd C:\Users\glean\OneDrive\Desktop\Hub
python scripts/test_credentials.py
```

You should see:
```
[SUCCESS] API Key (hapikey) works!
[*] Found X contacts
```

---

## Step 8: Start Testing!

Once credentials are verified, you can run the CTF scanners:

### Run Full Automated Suite:
```bash
python scripts/master_hunter.py
```

### Or Run Individual Scanners:
```bash
# Main CTF scanner (40+ tests)
python scripts/ctf_automated_scanner.py

# GraphQL testing
python scripts/graphql_introspection.py

# Advanced fuzzing
python scripts/fuzzer_advanced.py
```

---

## Important Security Notes

🔒 **Protect Your Access Token:**
- Never commit the `.env` file to git (it's already in `.gitignore`)
- Never share your access token publicly
- Treat it like a password

🔄 **Token Management:**
- You can view your Private Apps anytime in Settings → Integrations → Private Apps
- You can deactivate/delete apps to revoke tokens
- You can't view the token again after creation, but you can create a new one

⚠️ **If Token is Compromised:**
1. Go to Settings → Integrations → Private Apps
2. Find the app
3. Click "Delete" to immediately revoke the token
4. Create a new private app with a fresh token

---

## Troubleshooting

### "This app hasn't been granted all required scopes"
- Go back to Settings → Integrations → Private Apps
- Click on your app
- Click "Scopes" tab
- Enable the missing scopes mentioned in the error
- Click "Save"

### "Authentication credentials not found"
- Make sure you're using the token from the Private App, not an old API key
- Verify the token is correctly copied in the `.env` file (no extra spaces)
- Check that the token starts with `pat-` (Private App Token)

### Can't Find Private Apps Setting
- Make sure you have the right permissions in your HubSpot account
- You need **Super Admin** or **App Marketplace Access** permissions
- Contact your HubSpot account admin if you don't see this option

---

## What's Your Portal ID?

To find your Portal ID (needed for `MY_PORTAL_ID` in `.env`):

1. Log into HubSpot
2. Go to **Settings** (gear icon)
3. Navigate to **Account Setup → Account Defaults**
4. Look for **"Hub ID"** or **"Portal ID"**
5. It's usually a number like `12345678`

---

## Next Steps After Setup

Once you have valid credentials:

1. ✅ **Create Test Data** - Add some test contacts in your portal
2. ✅ **Run Automated Scans** - Let the tools test for vulnerabilities
3. ✅ **Manual Testing** - Use Burp Suite with the request templates
4. ✅ **Review Findings** - Check the `findings/` directory for results

---

## Need Help?

If you run into issues:
1. Run `python scripts/config.py` to check configuration status
2. Run `python scripts/test_credentials.py` to verify credentials
3. Check the error messages for specific scope requirements
4. Refer to the main [README.md](README.md) for more information

Good luck with the $20,000 CTF challenge! 🎯
