# 🚨 Email Problem Diagnosis

## Problem Identified: SMTP Connection Timeout

### What's Happening:
- Email sending command **times out** after 120 seconds
- This means Gmail SMTP server is **not accepting the connection**
- **Root cause:** Invalid or incorrect Gmail App Password

---

## ⚠️ THE ISSUE: Wrong Gmail App Password

The password you're using: `ntgd zypa afbf rygn`

**This is NOT a valid Gmail App Password because:**
1. It might be incorrectly copied
2. It might be expired or revoked
3. Gmail might not be allowing the connection

---

## ✅ SOLUTION: Generate a NEW Gmail App Password

### Step-by-Step Instructions:

### 1. **Enable 2-Step Verification** (if not already enabled)
   - Go to: https://myaccount.google.com/security
   - Find "2-Step Verification"
   - Click and follow the setup process
   - **You MUST have this enabled to create App Passwords!**

### 2. **Generate App Password**
   - Go to: https://myaccount.google.com/apppasswords
   - You might need to sign in again
   - Select: **"Mail"** or **"Other (Custom name)"**
   - Type a name: `Campus Parking` or `Test`
   - Click **"Generate"**

### 3. **Copy the Password EXACTLY**
   - Gmail will show you a **16-character password**
   - Example format: `abcd efgh ijkl mnop`
   - Copy it EXACTLY as shown (spaces are OK, they're removed automatically)
   - **Don't modify it or add anything**

### 4. **Update the Configuration**

You have two options:

#### Option A: Temporary (Current Session)
```bash
# Stop the current server (Ctrl+C if running)

# Start with new password (replace XXXX with your real password):
EMAIL_ADDRESS="jhonadevalmanza@gmail.com" EMAIL_PASSWORD="abcd efgh ijkl mnop" SECRET_KEY="campus-secret" py flask_app.py
```

#### Option B: Permanent (Create .env file)
```bash
# Create .env file:
cat > .env << 'EOF'
EMAIL_ADDRESS=jhonadevalmanza@gmail.com
EMAIL_PASSWORD=abcd efgh ijkl mnop
SECRET_KEY=campus-parking-secret-key
EOF

# Then just run:
py flask_app.py
```

---

## 🧪 Quick Test After Fixing

Once you have the CORRECT App Password:

```bash
# Test SMTP connection:
EMAIL_ADDRESS="jhonadevalmanza@gmail.com" EMAIL_PASSWORD="YOUR-NEW-PASSWORD" py -c "from app.email_service import test_email_connection; print('SUCCESS!' if test_email_connection() else 'FAILED')"
```

Expected output:
```
[OK] Conexion SMTP exitosa
SUCCESS!
```

---

## 🎯 What To Do NOW:

1. ✅ Go to https://myaccount.google.com/apppasswords
2. ✅ Generate a NEW App Password
3. ✅ Copy it EXACTLY (all 16 characters)
4. ✅ Stop the current Flask server
5. ✅ Start Flask with the NEW password:
   ```bash
   EMAIL_ADDRESS="jhonadevalmanza@gmail.com" EMAIL_PASSWORD="YOUR-NEW-16-CHAR-PASSWORD" SECRET_KEY="test" py flask_app.py
   ```
6. ✅ Test by creating a reservation
7. ✅ Email should arrive in 2-10 seconds

---

## ⚠️ Common Mistakes to Avoid:

1. ❌ Using your regular Gmail password (WON'T WORK!)
2. ❌ Not enabling 2-Step Verification first
3. ❌ Copying the password incorrectly
4. ❌ Adding extra characters or spaces manually
5. ❌ Using an old/expired App Password

---

## 📧 Expected Behavior (Once Fixed):

When you create a reservation:
1. Click "Reservar"
2. See flash message: "¡Reserva creada exitosamente!"
3. **Within 2-10 seconds:** Email arrives in jhoalmanza52@gmail.com
4. **Check SPAM folder** if not in inbox
5. Server logs show: `[CONFIRMACION] Email de confirmacion enviado exitosamente`

---

## 🔧 Alternative: Use a Different Email Service

If Gmail App Passwords don't work, you can use:
- **Mailgun** (free tier)
- **SendGrid** (free tier)
- **Outlook/Hotmail** (easier setup)

For Outlook:
```bash
EMAIL_ADDRESS="your-email@outlook.com"
SMTP_HOST="smtp-mail.outlook.com"
SMTP_PORT="587"
```

---

**Bottom Line:** The current password `ntgd zypa afbf rygn` is NOT working. Generate a NEW one from Google.

**Action Required:** Get new App Password from https://myaccount.google.com/apppasswords
