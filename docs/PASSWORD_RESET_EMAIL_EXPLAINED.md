# How We Send Password Reset Link to Users

## Overview

When a user clicks **Forgot Password** and enters their email, the app:

1. Checks if that email is registered in `users_profile`.
2. Creates a **secure token** (random, 32-byte), saves its **hash** and **expiry** (30 min) in the database.
3. Builds a **reset URL**: `APP_BASE_URL/reset-password?token=...&email=...`
4. **Sends an email** to that user with the link using one of two methods (see below).
5. When the user clicks the link, they set a new password; we verify the token and update `password_hash` in Supabase.

---

## Method 1: Resend API (Yes, We Use Resend’s API)

**When it’s used:** When **Gmail is not configured** in `.env` (no `GMAIL_USER` + `GMAIL_APP_PASSWORD`).

**How it works:**

- We call **Resend’s HTTP API** with a single `POST` request.
- No Resend SDK — we use Python `requests` and their public API.

**Request we send:**

- **URL:** `https://api.resend.com/emails`
- **Method:** `POST`
- **Headers:**
  - `Authorization: Bearer <RESEND_API_KEY>`
  - `Content-Type: application/json`
  - `User-Agent: MyGym-App/1.0`
- **Body (JSON):**
  - `from`: Sender (e.g. `My Gym <onboarding@resend.dev>` or your domain email)
  - `to`: `[user's email]` — the person who requested the reset
  - `subject`: "Reset your My Gym password"
  - `html`: Body with the reset link

**Code (simplified):**

```python
payload = {
    "from": RESEND_FROM_EMAIL,
    "to": [to_email],
    "subject": "Reset your My Gym password",
    "html": f"<p>Click to reset...</p><p><a href=\"{reset_url}\">{reset_url}</a></p>",
}
requests.post("https://api.resend.com/emails", headers=headers, json=payload)
```

So **yes — we use Resend’s API** (REST, no SDK).

---

## Why Resend Is “Limited” in Our App

Resend itself can send to **any** email; the limit in our app is **by choice** when we don’t have a custom domain:

1. **With `onboarding@resend.dev` (no domain):**
   - Resend only allows sending **to the Resend account owner’s email** (for testing).
   - So we **restrict** in code: we only send the reset email if the user’s email equals `ALLOWED_RESET_EMAIL` (that one allowed address).
   - Result: **only one email** (e.g. site owner) can receive the reset link.

2. **With your own domain (e.g. `noreply@yourdomain.com`):**
   - After you verify the domain at resend.com, you can send to **any user**.
   - We don’t add any extra limit; we’d send to whatever `to_email` is (the user who requested reset).

So the “limited” behaviour is:
- **Resend’s rule** when using `onboarding@resend.dev` (one recipient only).
- **Our code** only sends in that case when `email == ALLOWED_RESET_EMAIL` so we don’t get 403 from Resend.

---

## Method 2: Gmail SMTP (No Resend, No Domain Needed)

**When it’s used:** When **Gmail is configured** in `.env`: `GMAIL_USER` and `GMAIL_APP_PASSWORD`.

**How it works:**

- We **do not** call Resend at all.
- We use Python’s built-in `smtplib` and connect to **Gmail’s SMTP**:
  - Server: `smtp.gmail.com`, port **465** (SSL).
  - Login with `GMAIL_USER` and `GMAIL_APP_PASSWORD` (App Password from Google).
- We build the email (subject, from, to, HTML body) and send with `server.sendmail(...)`.
- **Recipient:** `to_email` = the user who requested the reset (any address).

**Code (simplified):**

```python
with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
    server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
    server.sendmail(GMAIL_USER, [to_email], msg.as_string())
```

So with Gmail we **don’t use Resend API**; we send directly via Gmail. **No “one email” limit** — every user gets the link at their own email.

---

## Which Method Is Used?

| .env config | Method used        | Who can receive reset link      |
|------------|--------------------|----------------------------------|
| Gmail set  | Gmail SMTP         | **Any** registered user         |
| Gmail not set, Resend with `onboarding@resend.dev` | Resend API | **Only** `ALLOWED_RESET_EMAIL` (one email) |
| Gmail not set, Resend with your domain | Resend API | **Any** registered user (if domain verified) |

---

## Summary

- **Yes, we use Resend’s API** when Gmail is not configured: one `POST` to `https://api.resend.com/emails` with Bearer token and JSON body.
- The “limited” behaviour is when using Resend **without your own domain** (`onboarding@resend.dev`): Resend only allows one recipient, so we only send to `ALLOWED_RESET_EMAIL`.
- To **avoid that limit** and let **every user** get the reset link without a domain, we use **Gmail SMTP** (set `GMAIL_USER` and `GMAIL_APP_PASSWORD` in `.env`).
