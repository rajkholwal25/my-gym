# Deploy My Gym on Render (Web Service)

After pushing this repo to GitHub, follow these steps.

## 1. Push latest code (including gunicorn)

Make sure `requirements.txt` includes `gunicorn` and push to GitHub:

```bash
git add requirements.txt DEPLOY_RENDER.md
git commit -m "Add gunicorn and Render deploy notes"
git push origin main
```

## 2. Create Web Service on Render

1. Go to **https://dashboard.render.com** and sign in (or sign up with GitHub).
2. Click **New +** → **Web Service**.
3. Connect your **GitHub** account if not already, then select the **repository** that has My Gym (e.g. `Gym` or your repo name).
4. Use these settings:

| Field | Value |
|-------|--------|
| **Name** | `my-gym` (or any name you like) |
| **Region** | Choose closest to you (e.g. Singapore / Oregon) |
| **Branch** | `main` (or your default branch) |
| **Runtime** | **Python 3** |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn app:app --bind 0.0.0.0:$PORT` |

5. Click **Advanced** and add **Environment Variables** (same names as in your `.env`; use your real values, not the placeholders):

| Key | Value (example / where to get it) |
|-----|-----------------------------------|
| `FLASK_SECRET_KEY` | Long random string (e.g. generate one at https://randomkeygen.com) |
| `SUPABASE_URL` | `https://jpqjactosfnxiuxkepfn.supabase.co` (your project URL) |
| `SUPABASE_KEY` | Your Supabase **anon** key |
| `SUPABASE_SERVICE_KEY` | Your Supabase **service_role** key (Project Settings → API) |
| `APP_BASE_URL` | **Your Render URL** after first deploy, e.g. `https://my-gym-xxxx.onrender.com` (then Save; needed for password reset links) |
| `EXERCISE_IMAGE_BUCKET` | `exercise-images` |
| `EXERCISE_VIDEO_BUCKET` | `exercise-videos` |
| `ADMIN_EMAILS` | `rajkholwal25@gmail.com` (comma-separated if more) |
| `RESEND_API_KEY` | (optional) Your Resend API key |
| `RESEND_FROM_EMAIL` | (optional) e.g. `My Gym <onboarding@resend.dev>` |
| `GMAIL_USER` | (optional) Your Gmail for password reset |
| `GMAIL_APP_PASSWORD` | (optional) Gmail app password for reset emails |

6. Click **Create Web Service**.

Render will clone the repo, run `pip install -r requirements.txt`, then start with `gunicorn --bind 0.0.0.0:$PORT app:app`. Your app will get a URL like `https://my-gym-xxxx.onrender.com`.

## 3. After first deploy

1. Copy the **URL** Render gives you (e.g. `https://my-gym-xxxx.onrender.com`).
2. In Render dashboard → your service → **Environment** → set **`APP_BASE_URL`** to that URL (so password reset emails use the correct link).
3. Save. Render will redeploy once.

## 4. APP_BASE_URL + Forgot password link (important)

- **Role:** Forgot-password emails send a link like `APP_BASE_URL/reset-password?token=...`. If `APP_BASE_URL` is wrong, the link opens nowhere or the wrong place.
- **On Render you must:** In **Environment**, set **`APP_BASE_URL`** to your **exact Render URL**, e.g. `https://my-gym-xxxx.onrender.com` (no trailing slash, use **https**). If it’s missing or set to `http://127.0.0.1:5000`, the reset link will not work.
- **For emails to be sent on Render:** In **Environment** also set either **Gmail** (`GMAIL_USER` + `GMAIL_APP_PASSWORD`) or **Resend** (`RESEND_API_KEY` + `RESEND_FROM_EMAIL`). Without these, the reset email is never sent and “nothing happens” when you click Forgot password.
- **If you get "Internal Server Error" on Forgot password:** In **Supabase** → SQL Editor, run **`supabase_add_reset_token_columns.sql`** once (adds reset token columns to `users_profile` if missing). Then try again.
- **Locally:** Keep `APP_BASE_URL=http://127.0.0.1:5000` in `.env` for local testing.

## 5. “No open HTTP ports” on Render

- **Cause:** Render expects the app to listen on **`0.0.0.0:$PORT`**. It sets `PORT` itself (e.g. 10000). If the app listens on another port or only on 127.0.0.1, Render sees no open port and kills the service.
- **Fix:**
  1. **Start Command** must be exactly:  
     `gunicorn app:app --bind 0.0.0.0:$PORT`  
     (Do **not** run `python app.py` on Render.)
  2. **Do not** set **`PORT`** in Render’s Environment. Let Render set it.
  3. **Do not** change the port in `app.py` (the `if __name__ == "__main__"` block). That block is only for local `python app.py`; on Render only gunicorn runs and it uses `$PORT`.
- Changing `app.py` to port 5000 or 10000 has **no effect** on Render; the “No open ports” error is fixed only by the correct **Start Command** and not overriding `PORT`.

## 6. Free tier: “Crash” / service stops after ~1 hour

- On the **free tier**, Render **spins down** your service after about **15 minutes** of no traffic. The next request then does a **cold start** (30–60 seconds). That is **not** a crash — the service is sleeping to save resources.
- If the service actually **crashes** (error in logs, not just slow first load), check **Logs** in the Render dashboard. Common causes: out-of-memory, or a request that takes too long (e.g. big video upload). You can increase gunicorn timeout in the Start Command:
  ```bash
  gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120
  ```
  (120 seconds; increase if you need longer uploads.)

## 7. Keep Render awake (no sleep on free tier)

This repo has a **GitHub Action** that pings your app every **7 minutes** so Render doesn’t spin it down.

**One-time setup:**

1. After your app is live on Render, copy its URL (e.g. `https://my-gym-xxxx.onrender.com`).
2. On **GitHub** → your repo → **Settings** → **Secrets and variables** → **Actions**.
3. Click **New repository secret**:
   - **Name:** `RENDER_APP_URL`
   - **Value:** your Render URL (no trailing slash), e.g. `https://my-gym-xxxx.onrender.com`
4. Push the repo (the workflow is already in `.github/workflows/keep-render-awake.yml`). GitHub will run it every 7 minutes and call your app’s `/health` endpoint.

The app has a **`/health`** route that returns 200 OK; the workflow just hits that URL. No extra signup (UptimeRobot etc.) needed.

## 8. About `if __name__ == "__main__"` in app.py

That block runs **only** when you run `python app.py` locally. On Render, **gunicorn** imports `app` and never runs that block, so it does **not** cause Render crashes. Render always uses the Start Command you set (`gunicorn app:app --bind 0.0.0.0:$PORT`).

---

**Summary:** New → Web Service → connect GitHub repo → Build: `pip install -r requirements.txt` → Start: `gunicorn app:app --bind 0.0.0.0:$PORT` → set **APP_BASE_URL** to your Render URL → add other env vars → Create Web Service.
