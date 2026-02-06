# SSH Key Management Guide

**Last Updated:** 2026-01-13 **Purpose:** Managing SSH access to VPS
servers using key-based authentication

---

## 🔐 Current Setup

| Item                     | Value                                                   |
| ------------------------ | ------------------------------------------------------- |
| **VPS IP**               | 108.175.12.154                                          |
| **SSH User**             | root                                                    |
| **Auth Method**          | SSH Key Only (Password disabled)                        |
| **Key Type**             | RSA 2048-bit                                            |
| **Key Location (Local)** | `~/.ssh/id_rsa` (private), `~/.ssh/id_rsa.pub` (public) |
| **Cloudflare Tunnel**    | `ssh.mhapi.mysticdatanode.net` → port 22                |

---

## 📁 Your SSH Keys (Already Set Up)

Your SSH keys are **files on your computer**, not something you need
to memorize.

### Key Locations:

| File                             | Purpose                                | NEVER Share?     |
| -------------------------------- | -------------------------------------- | ---------------- |
| `C:\Users\surya\.ssh\id_rsa`     | **Private Key** - Your secret identity | ⛔ NEVER share   |
| `C:\Users\surya\.ssh\id_rsa.pub` | **Public Key** - Can be shared freely  | ✅ Safe to share |

### View Your Public Key:

```powershell
# PowerShell
cat ~/.ssh/id_rsa.pub

# Or full path
Get-Content "C:\Users\surya\.ssh\id_rsa.pub"
```

The output looks like:

```
ssh-rsa AAAAB3Nza...long string...== surya@ROG
```

---

## 🔑 How SSH Key Authentication Works

```
┌─────────────────────────────────────────────────────────────────┐
│                    SSH KEY AUTHENTICATION                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   YOUR LAPTOP                          VPS SERVER               │
│   ───────────                          ──────────               │
│                                                                  │
│   ~/.ssh/id_rsa (private)              ~/.ssh/authorized_keys   │
│   ↓                                    (contains your pub key)  │
│   Only YOU have this                   ↓                        │
│                                        Server checks if your    │
│   When you run:                        private key matches      │
│   ssh root@108.175.12.154              any authorized public    │
│   ↓                                    key                      │
│   Your private key proves              ↓                        │
│   you own the matching                 ✅ Match = Access        │
│   public key                           ❌ No match = Denied     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Key Point:** You never "remember" the key. Your computer uses the
key file automatically.

---

## 🔒 Backup Your Keys (CRITICAL)

### Option 1: Password Manager (Recommended)

Store your private key in a password manager like:

- **1Password** (supports SSH key storage)
- **Bitwarden** (as secure note)
- **KeePassXC** (as file attachment)

```powershell
# Copy private key content to clipboard
Get-Content ~/.ssh/id_rsa | Set-Clipboard
# Paste into password manager as secure note
```

### Option 2: Encrypted USB Drive

1. Get a USB drive you only use for backups
2. Create an encrypted folder (VeraCrypt or BitLocker)
3. Copy `~/.ssh/id_rsa` and `~/.ssh/id_rsa.pub` to it
4. Store USB in safe place (not with laptop)

### Option 3: Cloud Storage (Encrypted)

1. ZIP the key files with strong password:

```powershell
# Requires 7-Zip
& "C:\Program Files\7-Zip\7z.exe" a -p"YourStrongPassword123!" ssh-backup.7z ~/.ssh/id_rsa ~/.ssh/id_rsa.pub
```

2. Upload `ssh-backup.7z` to Google Drive/Dropbox
3. Store the password in a different password manager entry

---

## 🖥️ Adding Keys to New Laptop/Device

### Step 1: Get Your Private Key

Restore from your backup (password manager, USB, or encrypted cloud
file).

### Step 2: Place Key on New Device

**Windows (new laptop):**

```powershell
# Create .ssh folder
mkdir ~/.ssh -Force

# Create private key file (paste content from backup)
notepad ~/.ssh/id_rsa
# Paste your private key content, save

# Create public key file
notepad ~/.ssh/id_rsa.pub
# Paste your public key content, save

# Fix permissions (important!)
icacls "$env:USERPROFILE\.ssh\id_rsa" /inheritance:r /grant:r "$env:USERNAME:R"
```

**Mac/Linux (new device):**

```bash
# Create .ssh folder
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Create files (paste content from backup)
nano ~/.ssh/id_rsa
# Paste private key, Ctrl+X to save

nano ~/.ssh/id_rsa.pub
# Paste public key, Ctrl+X to save

# Fix permissions (CRITICAL on Mac/Linux)
chmod 600 ~/.ssh/id_rsa
chmod 644 ~/.ssh/id_rsa.pub
```

### Step 3: Test Connection

```bash
ssh root@108.175.12.154
# Should connect without password prompt
```

---

## 🔑 Adding a NEW Key (New Device with Different Key)

If you want a SEPARATE key for a new device (better security):

### Step 1: Generate New Key on New Device

```powershell
# On new device
ssh-keygen -t ed25519 -C "surya@NewLaptop"
# Press Enter for default location
# Set passphrase (optional but recommended)
```

### Step 2: Add Public Key to VPS

**From current laptop (that already has access):**

```powershell
# Get new device's public key content
# (copy from new device or email to yourself)

# Add to VPS authorized_keys
ssh root@108.175.12.154 "echo 'NEW_PUBLIC_KEY_CONTENT_HERE' >> ~/.ssh/authorized_keys"
```

**Alternative: Copy file directly from new device (if both on same
network):**

```bash
# From new device (after generating key)
ssh-copy-id root@108.175.12.154
# Will ask for password - but password auth is disabled!
```

**Since password auth is disabled, you must:**

1. Copy new public key content manually
2. SSH from old laptop and add it to `/root/.ssh/authorized_keys`

---

## 🗑️ Removing Old/Compromised Keys

If a laptop is lost/stolen, remove its key from VPS:

```powershell
# SSH to VPS from another authorized device
ssh root@108.175.12.154

# View current authorized keys
cat ~/.ssh/authorized_keys

# Edit and remove the compromised key
nano ~/.ssh/authorized_keys
# Delete the line with the old key, save
```

---

## ⚠️ Security Best Practices

| Practice                | Why                                    |
| ----------------------- | -------------------------------------- |
| Never share private key | Anyone with it can access your servers |
| Use passphrase on key   | Extra protection if laptop stolen      |
| One key per device      | Can revoke single device if lost       |
| Regular audit           | Check `authorized_keys` quarterly      |
| Backup securely         | Lost key = locked out forever          |

---

## 🆘 Emergency: Lost All Access

If you lose access to ALL authorized keys:

1. **Contact hosting provider** (Ionos.com for this VPS)
2. Request **console access** or **rescue mode**
3. From console, edit `/root/.ssh/authorized_keys`
4. Add your new public key
5. Reboot server

**Prevention:** Always have backup of keys AND hosting account
credentials.

---

## 🔧 Troubleshooting

### "Permission denied (publickey)"

```powershell
# Check key permissions on Windows
icacls "$env:USERPROFILE\.ssh\id_rsa"
# Should show only your user with Read access

# Fix permissions
icacls "$env:USERPROFILE\.ssh\id_rsa" /inheritance:r /grant:r "$env:USERNAME:R"
```

### "Could not open connection"

```powershell
# Test with verbose mode
ssh -vvv root@108.175.12.154
# Look for "Offering public key" and "Server accepts key"
```

### "Key not found"

```powershell
# Verify key exists
Test-Path ~/.ssh/id_rsa  # Should return True

# Verify key format is correct
Get-Content ~/.ssh/id_rsa | Select-Object -First 1
# Should show: -----BEGIN RSA PRIVATE KEY----- (or OPENSSH)
```

---

## 📋 Quick Reference

| Task                     | Command                                                          |
| ------------------------ | ---------------------------------------------------------------- |
| View public key          | `cat ~/.ssh/id_rsa.pub`                                          |
| Test SSH connection      | `ssh root@108.175.12.154`                                        |
| View VPS authorized keys | `ssh root@108.175.12.154 "cat ~/.ssh/authorized_keys"`           |
| Add new key to VPS       | `ssh root@108.175.12.154 "echo 'KEY' >> ~/.ssh/authorized_keys"` |
| Generate new key         | `ssh-keygen -t ed25519 -C "description"`                         |
| Backup keys              | Copy `~/.ssh/id_rsa` and `~/.ssh/id_rsa.pub` to secure location  |

---

## 🔗 Related Documentation

- [16-INFRASTRUCTURE_DEPLOYMENT.instructions.md](../../.github/instructions/16-INFRASTRUCTURE_DEPLOYMENT.instructions.md) -
  VPS setup
- [VPS_DEPLOYMENT_GUIDE.md](../../VPS_DEPLOYMENT_GUIDE.md) -
  Deployment procedures
