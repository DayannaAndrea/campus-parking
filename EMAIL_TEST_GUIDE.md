# 📧 Email Test Guide - Confirmation & Reminder

## ✅ Testing Email Notifications (2 types)

### Prerequisites:
- ✅ Server running: http://127.0.0.1:5050
- ✅ Email configured: jhonadevalmanza@gmail.com
- ✅ User registered with valid email

---

## 🎯 IMMEDIATE TEST - Confirmation Email (NO WAITING!)

### Step 1: Login
1. Go to: http://127.0.0.1:5050/login
2. Enter your email: `jhoalmanza52@gmail.com` (or the email you registered with)
3. Click "Iniciar Sesión"

### Step 2: Create a Reservation
1. From dashboard, click **"Reservar Cupo"**
2. Fill the form:
   - **Zona:** Zona A
   - **Fecha:** Today's date (e.g., 2026-10-16)
   - **Hora inicio:** Current time + 30 minutes (e.g., if now is 11:10, put 11:40)
   - **Hora fin:** Current time + 2 hours (e.g., 13:10)
3. Click **"Reservar"**

### Step 3: Check Email IMMEDIATELY
- **⏱️ Expected time:** 2-10 seconds after clicking "Reservar"
- **📧 Check inbox:** jhoalmanza52@gmail.com (or your email)
- **📬 Subject:** "Confirmacion de Reserva - Campus Parking"
- **✅ If you don't see it in Inbox, CHECK SPAM FOLDER**

### Step 4: Verify in Server Logs
Look at the console where Flask is running. You should see:
```
[CONFIRMACION] Enviando email de confirmación a jhoalmanza52@gmail.com...
[OK] Email enviado a jhoalmanza52@gmail.com: Confirmacion de Reserva - Campus Parking
[CONFIRMACION] Email de confirmacion enviado exitosamente a jhoalmanza52@gmail.com
```

---

## ⏰ TIMED TEST - Reminder Email (Wait 15 minutes)

### If you want to test the reminder email:

1. **Create a reservation starting in ~20 minutes:**
   - Example: If now is 11:00, set start time to 11:20
   - This gives you time to wait

2. **Wait ~5 minutes** (until 15 minutes before start)
   - The scheduler runs every 1 minute
   - It sends reminders 13-17 minutes before start (15 ± 2 min window)

3. **Check your email again:**
   - **📧 Subject:** "Recordatorio: Tu reserva de parqueadero inicia en 15 minutos"
   - **⏱️ When:** Exactly 15 minutes before your reservation start time

4. **Verify in Server Logs:**
```
[HH:MM:SS] Ejecutando job de recordatorios...
[OK] Email enviado a jhoalmanza52@gmail.com: Recordatorio: Tu reserva...
[OK] Se enviaron 1 recordatorios
```

---

## 🔍 Troubleshooting

### I didn't receive the confirmation email immediately:

1. **Check Server Logs** (console output):
   - Look for `[CONFIRMACION]` messages
   - If you see `Error: No se pudo enviar` → SMTP problem

2. **Check SPAM folder** in Gmail

3. **Verify SMTP configuration:**
   ```bash
   # Go to this URL:
   http://127.0.0.1:5050/sistema
   # Click "Probar conexión SMTP"
   # Should show: "Conexión SMTP exitosa"
   ```

4. **Verify your user has an email:**
   ```bash
   py -c "from app.db import get_conn; conn = get_conn(); print(conn.execute('SELECT placa, nombre, email FROM usuarios').fetchall()); conn.close()"
   ```

### The server logs don't show [CONFIRMACION] messages:

This means the email code is not being executed. Possible causes:
- Server needs restart
- Environment variables not set
- Check if you're actually logged in before creating reservation

---

## 📊 Expected Results

### Successful Test Shows:

1. **✅ Confirmation Email (immediate):**
   - Arrives in 2-10 seconds
   - Green theme
   - Subject: "Confirmacion de Reserva - Campus Parking"
   - Contains: Zone, Date, Start/End time, License plate

2. **✅ Reminder Email (15 min before):**
   - Arrives exactly 15 minutes before start
   - Purple theme
   - Subject: "Recordatorio: Tu reserva de parqueadero inicia en 15 minutos"
   - Contains: Same reservation details + warning about 15-min grace period

3. **✅ Server Logs Show:**
   ```
   [CONFIRMACION] Email de confirmacion enviado exitosamente
   [OK] Email enviado a ...
   ```

---

## 🎉 Success Criteria

- ✅ Confirmation email received within 10 seconds
- ✅ Email appears in inbox or spam
- ✅ Email has correct reservation details
- ✅ Server logs show successful sending
- ✅ Reminder email received 15 minutes before (if you wait)

---

**Your email is configured and ready! Test it now!**

Server: http://127.0.0.1:5050
Email: jhonadevalmanza@gmail.com (sender)
Test recipient: jhoalmanza52@gmail.com
