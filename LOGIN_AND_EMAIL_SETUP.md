# 🔐 Login System & Email Notifications Setup Guide

## Overview

The Campus Parking system now includes:
- ✅ **Email-based login** - Users log in with their email address
- ✅ **Reservation confirmation emails** - Instant confirmation when creating a reservation
- ✅ **Reminder emails** - Automatic reminders 15 minutes before reservation starts
- ✅ **User dashboard** - Personalized dashboard after login

---

## 📧 Email Configuration

### Step 1: Set up Gmail App Password

1. **Enable 2-Step Verification** on your Gmail account:
   - Go to: https://myaccount.google.com/signinoptions/two-step-verification
   - Follow the prompts to enable 2-Step Verification

2. **Generate App Password**:
   - Go to: https://myaccount.google.com/apppasswords
   - Select "Mail" or "Other (Custom name)"
   - Copy the 16-character password (e.g., `abcd efgh ijkl mnop`)

### Step 2: Configure Environment Variables

Create a `.env` file in the project root (or copy from `.env.example`):

```bash
# Email Configuration (for Gmail)
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=abcdefghijklmnop   # 16-char App Password from Step 1

# Alternative SMTP variables (optional, EMAIL_ADDRESS takes priority)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com
FROM_NAME=Campus Parking

# Secret key for sessions
SECRET_KEY=generate-a-random-secret-key-here
```

**Generate a secure SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Step 3: Install Dependencies (if needed)

```bash
pip install python-dotenv
```

---

## 🚀 How to Use the System

### 1. Register a Vehicle (First Time Users)

1. Go to: http://127.0.0.1:5050/registro
2. Fill in the form:
   - **Nombre**: Your full name
   - **Placa**: License plate (e.g., ABC123)
   - **Rol**: Student, Professor, or Administrative
   - **Email**: ⚠️ **IMPORTANT** - Use a valid email address!
3. Click "Registrar"
4. Download your QR code

### 2. Login to the System

1. Go to: http://127.0.0.1:5050/login
2. Enter your **email address** (the one you used during registration)
3. Click "Iniciar Sesión"
4. You'll be redirected to your dashboard

### 3. Make a Reservation

1. After logging in, click **"Reservar Cupo"** from the dashboard
2. Select:
   - **Zone** (Zona A, B, or C)
   - **Date**
   - **Start time** and **End time**
3. Click "Reservar"
4. ✅ **You will receive TWO emails:**
   - **Confirmation email** - Sent immediately
   - **Reminder email** - Sent 15 minutes before your reservation starts

---

## 📨 Email Templates

### Confirmation Email (Sent immediately)
- ✅ Subject: "Confirmación de Reserva - Campus Parking"
- Contains: Reservation details, zone, date, time
- Design: Professional HTML template with green theme

### Reminder Email (Sent 15 min before)
- ⏰ Subject: "Recordatorio: Tu reserva de parqueadero inicia en 15 minutos"
- Contains: Reminder to arrive on time
- Design: Professional HTML template with purple theme
- Warning: Auto-release if you don't arrive within 15 minutes

---

## 🔧 Testing Email Functionality

### Quick Test

1. **Start the application with email configuration:**
   ```bash
   py flask_app.py
   ```

2. **Register a test user:**
   - Go to http://127.0.0.1:5050/registro
   - Use a real email address you can access
   - Complete registration

3. **Login:**
   - Go to http://127.0.0.1:5050/login
   - Enter your email

4. **Create a reservation:**
   - Select a zone
   - Choose today's date
   - Set start time to: **Current time + 20 minutes**
   - Set end time to: **Current time + 2 hours**
   - Submit

5. **Check your email:**
   - You should immediately receive a **confirmation email**
   - In ~5 minutes (when it's 15 min before start), you'll receive a **reminder email**

---

## 📋 Features

### User Dashboard
After login, users see:
- ✅ Personal information (name, plate, email)
- ✅ Quick actions (Reserve, My Reservations, Availability)
- ✅ Real-time parking availability by zone
- ✅ Recent reservations with status

### Protected Routes
These routes now require login:
- `/reservar` - Create a reservation
- `/dashboard` - User dashboard

### Email Notifications
1. **Confirmation Email**: Sent when a reservation is created
2. **Reminder Email**: Sent 15 minutes before reservation starts (via scheduler)

---

## 🛠️ Troubleshooting

### "Email no configurado" warning
- **Solution**: Make sure `EMAIL_ADDRESS` and `EMAIL_PASSWORD` are set in your `.env` file
- Check: http://127.0.0.1:5050/sistema to test SMTP connection

### Not receiving emails
1. **Check spam folder** - Gmail may filter automated emails
2. **Verify App Password** - Must be 16 characters, no spaces
3. **Check email in database**:
   ```bash
   py -c "from app.db import get_conn; conn = get_conn(); print(conn.execute('SELECT placa, email FROM usuarios').fetchall()); conn.close()"
   ```

### Can't login
- **Error**: "No existe un usuario registrado con ese correo"
- **Solution**: Register your vehicle first with a valid email address

### Gmail blocking connection
- Make sure:
  - 2-Step Verification is **enabled**
  - You're using an **App Password** (not your regular password)
  - The App Password has no spaces when you paste it in .env

---

## 📁 File Structure

```
campus-parking/
├── .env                          # Your configuration (create this)
├── .env.example                  # Template with EMAIL_ADDRESS/EMAIL_PASSWORD
├── flask_app.py                  # Main app (now with login routes)
├── app/
│   ├── email_service.py         # Email sending (uses EMAIL_ADDRESS/EMAIL_PASSWORD)
│   ├── email_templates.py       # HTML templates for emails (NEW: confirmation)
│   ├── reservations.py          # Reservation logic (NEW: sends confirmation)
│   └── scheduler.py             # Background job for reminders
├── templates/
│   ├── login.html               # Login page (NEW)
│   ├── dashboard.html           # User dashboard (NEW)
│   ├── reservar.html            # Updated to use logged-in user
│   └── base.html                # Updated navbar with user menu
└── LOGIN_AND_EMAIL_SETUP.md     # This file
```

---

## ✅ Summary

**What's New:**
1. ✅ Email-based login system
2. ✅ User dashboard after login
3. ✅ Confirmation emails for reservations
4. ✅ Reminder emails 15 minutes before reservation
5. ✅ Protected routes requiring authentication
6. ✅ Beautiful HTML email templates

**Configuration:**
- Set `EMAIL_ADDRESS` and `EMAIL_PASSWORD` in `.env` file
- Use Gmail App Password (16 characters)
- Generate secure `SECRET_KEY`

**User Flow:**
1. Register → 2. Login → 3. Reserve → 4. Receive emails

**Email Types:**
1. ✅ Confirmation (immediate, green theme)
2. ⏰ Reminder (15 min before, purple theme)

---

**Need help?** Check the logs in `app.log` or console output for email sending status.
