# RingCentral JWT Setup Guide

## Step 1: Enable JWT (DO THIS NOW)

On the current page:

1. ☑️ Check "JWT auth flow"
2. Select "Yes" for "Issue refresh tokens"
3. Click "Save" at the bottom
4. Wait for page to refresh

## Step 2: Generate JWT Credentials

After saving:

1. Go to the "Credentials" tab (top of page)
2. Look for "JWT Credentials" section
3. Click "Create JWT Credentials" button
4. You'll see a JWT token (very long string)
5. **COPY THE ENTIRE JWT TOKEN**

## Step 3: Add JWT Token to .env

Add this line to your .env file:

```
RC_JWT_TOKEN=<paste_your_jwt_token_here>
```

## Step 4: Update Authentication Code

The code will automatically use JWT if RC_JWT_TOKEN is present.

---

## Why JWT instead of Password?

- ✅ More secure
- ✅ Recommended by RingCentral
- ✅ No username/password needed
- ✅ Better for server-side apps
- ✅ Tokens can be rotated easily

---

**After you save and get the JWT token, paste it here and I'll update
your .env file!**
