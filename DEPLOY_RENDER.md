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
| **Start Command** | `gunicorn app:app` |

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

Render will clone the repo, run `pip install -r requirements.txt`, then start with `gunicorn app:app`. Your app will get a URL like `https://my-gym-xxxx.onrender.com`.

## 3. After first deploy

1. Copy the **URL** Render gives you (e.g. `https://my-gym-xxxx.onrender.com`).
2. In Render dashboard → your service → **Environment** → set **`APP_BASE_URL`** to that URL (so password reset emails use the correct link).
3. Save. Render will redeploy once.

## 4. Free tier note

On the free tier the service may **spin down** after ~15 minutes of no traffic. The first request after that can take 30–60 seconds (cold start). This is normal.

---

**Summary:** New → Web Service → connect GitHub repo → Build: `pip install -r requirements.txt` → Start: `gunicorn app:app` → add env vars → Create Web Service.
