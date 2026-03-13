"""
My Gym - Workout web application
Python Flask backend + Supabase
"""
import os
import re
import hashlib
import secrets
import smtplib
import mimetypes
import threading
import traceback
import uuid
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from functools import wraps

import requests
from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    session,
    flash,
)
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

# Always load .env from this project folder (fixes missing vars when running from a different cwd)
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env", override=True)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-in-production")
CORS(app)

# Supabase (REST)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")  # anon key works for public RLS; service role bypasses RLS
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")  # optional, recommended for secure profile/password ops
SUPABASE_REST = f"{SUPABASE_URL.rstrip('/')}/rest/v1" if SUPABASE_URL else None

if SUPABASE_KEY and SUPABASE_KEY.startswith("sb_publishable_"):
    # Supabase "publishable" keys are not accepted by PostgREST as Bearer tokens.
    # This app expects the anon key (JWT) or service_role key.
    SUPABASE_KEY = None

RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
RESEND_FROM_EMAIL = os.environ.get("RESEND_FROM_EMAIL", "My Gym <onboarding@resend.dev>")
ALLOWED_RESET_EMAIL = (os.environ.get("ALLOWED_RESET_EMAIL") or "").strip().lower()
# Gmail SMTP: any user can get reset link (no domain). Set GMAIL_USER + GMAIL_APP_PASSWORD in .env.
GMAIL_USER = (os.environ.get("GMAIL_USER") or "").strip().lower()
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "").strip()
# Used only for password-reset links in emails. On Render set to your live URL (e.g. https://my-gym-xxx.onrender.com).
APP_BASE_URL = os.environ.get("APP_BASE_URL", "http://127.0.0.1:5000").rstrip("/")
if os.environ.get("PORT") and "127.0.0.1" in APP_BASE_URL:
    print("WARNING: APP_BASE_URL is still localhost. Set APP_BASE_URL to your Render URL in Environment so forgot-password links work.")
EXERCISE_IMAGE_BUCKET = os.environ.get("EXERCISE_IMAGE_BUCKET", "exercise-images").strip()
EXERCISE_VIDEO_BUCKET = os.environ.get("EXERCISE_VIDEO_BUCKET", "exercise-videos").strip()
ADMIN_EMAILS = {e.strip().lower() for e in (os.environ.get("ADMIN_EMAILS") or "").split(",") if e.strip()}

DAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

MUSCLE_GROUPS = [
    "chest",
    "back",
    "biceps",
    "triceps",
    "shoulders",
    "legs",
    "core",
    "rest",
]


def parse_diet_content(content: str | None) -> dict:
    """Parse 'Breakfast: ... Lunch: ... Dinner: ... Snacks: ...' into separate fields."""
    out = {"breakfast": "", "lunch": "", "dinner": "", "snacks": ""}
    if not (content and content.strip()):
        return out
    parts = re.split(r"\s+(?=Lunch:|Dinner:|Snacks:)", content.strip(), flags=re.IGNORECASE)
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if p.lower().startswith("breakfast:"):
            out["breakfast"] = p[10:].strip()
        elif p.lower().startswith("lunch:"):
            out["lunch"] = p[6:].strip()
        elif p.lower().startswith("dinner:"):
            out["dinner"] = p[7:].strip()
        elif p.lower().startswith("snacks:"):
            out["snacks"] = p[7:].strip()
    return out


def _sb_headers(prefer: str | None = None, *, key_override: str | None = None):
    key = key_override or SUPABASE_KEY
    if not key:
        raise ValueError("SUPABASE_KEY must be set in .env")
    h = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    if prefer:
        h["Prefer"] = prefer
    return h


def sb_select(table: str, *, params: dict | None = None, key_override: str | None = None):
    if not SUPABASE_REST:
        raise ValueError("SUPABASE_URL must be set in .env")
    r = requests.get(f"{SUPABASE_REST}/{table}", headers=_sb_headers(key_override=key_override), params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def sb_insert(table: str, row: dict, *, return_representation: bool = True, key_override: str | None = None):
    prefer = "return=representation" if return_representation else "return=minimal"
    r = requests.post(
        f"{SUPABASE_REST}/{table}",
        headers=_sb_headers(prefer, key_override=key_override),
        json=row,
        timeout=30,
    )
    r.raise_for_status()
    return r.json() if return_representation else None


def sb_update(table: str, updates: dict, *, match: dict, key_override: str | None = None):
    params = {k: f"eq.{v}" for k, v in match.items()}
    r = requests.patch(
        f"{SUPABASE_REST}/{table}",
        headers=_sb_headers("return=representation", key_override=key_override),
        params=params,
        json=updates,
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def sb_delete(table: str, *, match: dict, key_override: str | None = None):
    params = {k: f"eq.{v}" for k, v in match.items()}
    r = requests.delete(
        f"{SUPABASE_REST}/{table}",
        headers=_sb_headers("return=minimal", key_override=key_override),
        params=params,
        timeout=30,
    )
    r.raise_for_status()
    return True


def sb_upsert(table: str, row: dict, *, on_conflict: str):
    params = {"on_conflict": on_conflict}
    r = requests.post(
        f"{SUPABASE_REST}/{table}",
        headers=_sb_headers("resolution=merge-duplicates,return=representation"),
        params=params,
        json=row,
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def _service_key_or_anon():
    return SUPABASE_SERVICE_KEY or SUPABASE_KEY


def upload_exercise_image_to_storage(*, user_id: str, file_storage):
    """Upload an image file to Supabase Storage and return its public URL."""
    if not SUPABASE_URL:
        raise ValueError("SUPABASE_URL must be set in .env")
    if not SUPABASE_SERVICE_KEY:
        raise ValueError("SUPABASE_SERVICE_KEY must be set in .env to upload to storage")
    if not file_storage or not getattr(file_storage, "filename", ""):
        raise ValueError("No file provided")

    filename = file_storage.filename or "image"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".png", ".jpg", ".jpeg", ".webp"]:
        raise ValueError("Only png/jpg/jpeg/webp images are allowed")

    content_type = file_storage.mimetype or mimetypes.types_map.get(ext) or "application/octet-stream"
    obj_name = f"user_{user_id}/{uuid.uuid4().hex}{ext}"
    url = f"{SUPABASE_URL.rstrip('/')}/storage/v1/object/{EXERCISE_IMAGE_BUCKET}/{obj_name}"
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": content_type,
        "x-upsert": "true",
    }
    r = requests.put(url, headers=headers, data=file_storage.stream.read(), timeout=60)
    try:
        r.raise_for_status()
    except requests.HTTPError:
        raise ValueError(f"Storage image upload failed ({r.status_code}): {r.text}") from None
    public_url = f"{SUPABASE_URL.rstrip('/')}/storage/v1/object/public/{EXERCISE_IMAGE_BUCKET}/{obj_name}"
    return public_url


def upload_exercise_video_to_storage(*, user_id: str, file_storage):
    """Upload a video file to Supabase Storage and return its public URL."""
    if not SUPABASE_URL:
        raise ValueError("SUPABASE_URL must be set in .env")
    if not SUPABASE_SERVICE_KEY:
        raise ValueError("SUPABASE_SERVICE_KEY must be set in .env to upload to storage")
    if not file_storage or not getattr(file_storage, "filename", ""):
        raise ValueError("No file provided")

    filename = file_storage.filename or "video"
    ext = os.path.splitext(filename)[1].lower()
    # Keep this permissive: browsers commonly record mp4/webm/mov
    if ext not in [".mp4", ".webm", ".mov", ".m4v", ".ogg", ".ogv"]:
        raise ValueError("Only mp4/webm/mov/m4v/ogg videos are allowed")

    content_type = file_storage.mimetype or mimetypes.types_map.get(ext) or "application/octet-stream"
    obj_name = f"user_{user_id}/{uuid.uuid4().hex}{ext}"
    url = f"{SUPABASE_URL.rstrip('/')}/storage/v1/object/{EXERCISE_VIDEO_BUCKET}/{obj_name}"
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": content_type,
        "x-upsert": "true",
    }
    r = requests.put(url, headers=headers, data=file_storage.stream.read(), timeout=300)
    try:
        r.raise_for_status()
    except requests.HTTPError:
        raise ValueError(f"Storage video upload failed ({r.status_code}): {r.text}") from None
    public_url = f"{SUPABASE_URL.rstrip('/')}/storage/v1/object/public/{EXERCISE_VIDEO_BUCKET}/{obj_name}"
    return public_url


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _send_reset_via_resend(*, to_email: str, reset_url: str):
    if not RESEND_API_KEY:
        raise ValueError("RESEND_API_KEY must be set in .env to send emails")
    payload = {
        "from": RESEND_FROM_EMAIL,
        "to": [to_email],
        "subject": "Reset your My Gym password",
        "html": f"<p>Click to reset your password:</p><p><a href=\"{reset_url}\">{reset_url}</a></p><p>If you didn't request this, ignore this email.</p>",
    }
    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json",
        "User-Agent": "MyGym-App/1.0",
    }
    r = requests.post("https://api.resend.com/emails", headers=headers, json=payload, timeout=30)
    try:
        r.raise_for_status()
    except requests.HTTPError:
        # Resend often returns useful JSON text explaining why it blocked the sender/domain.
        raise ValueError(f"Resend send failed ({r.status_code}): {r.text}") from None
    return r.json()


def _send_reset_via_gmail(*, to_email: str, reset_url: str):
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        raise ValueError("GMAIL_USER and GMAIL_APP_PASSWORD must be set in .env")
    html = f"<p>Click to reset your My Gym password:</p><p><a href=\"{reset_url}\">{reset_url}</a></p><p>If you didn't request this, ignore this email.</p>"
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Reset your My Gym password"
    msg["From"] = f"My Gym <{GMAIL_USER}>"
    msg["To"] = to_email
    msg.attach(MIMEText(html, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_USER, [to_email], msg.as_string())


def send_reset_email(*, to_email: str, reset_url: str):
    """Send reset link. On production (non-localhost) prefer Resend (HTTP) over Gmail (SMTP) so it works from Render."""
    is_production = APP_BASE_URL and "127.0.0.1" not in APP_BASE_URL and "localhost" not in (APP_BASE_URL or "")
    if is_production and RESEND_API_KEY and RESEND_FROM_EMAIL:
        print(f"[forgot-password] send_reset_email: using resend from={RESEND_FROM_EMAIL!r} to={to_email!r}")
        _send_reset_via_resend(to_email=to_email, reset_url=reset_url)
        return
    if GMAIL_USER and GMAIL_APP_PASSWORD:
        print(f"[forgot-password] send_reset_email: using gmail to={to_email!r}")
        _send_reset_via_gmail(to_email=to_email, reset_url=reset_url)
        return
    print(f"[forgot-password] send_reset_email: fallback resend from={RESEND_FROM_EMAIL!r} to={to_email!r}")
    _send_reset_via_resend(to_email=to_email, reset_url=reset_url)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"error": "Login required"}), 401
            flash("Please log in to continue.", "info")
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)

    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "info")
            return redirect(url_for("login"))
        user = session.get("user") or {}
        if not _is_admin_for_user(user):
            flash("Admin access required.", "error")
            return redirect(url_for("index"))
        return f(*args, **kwargs)

    return decorated


def _is_admin_for_user(user: dict | None) -> bool:
    if not user:
        return False
    email = (user.get("email") or "").strip().lower()
    return bool(user.get("is_admin")) or (email in ADMIN_EMAILS)


@app.before_request
def ensure_admin_flag_on_session_user():
    """Make sure session['user'] always has correct is_admin flag based on email/DB."""
    user = session.get("user")
    if not user:
        return
    if _is_admin_for_user(user):
        if not user.get("is_admin"):
            user["is_admin"] = True
            session["user"] = user


# ---------- Pages ----------


@app.route("/health")
def health():
    """Lightweight endpoint for uptime pings (e.g. GitHub Actions) so Render free tier doesn't spin down."""
    return "", 200


@app.route("/")
def index():
    user = session.get("user")
    schedule_data = {}
    if user and SUPABASE_REST and SUPABASE_KEY:
        try:
            rows = sb_select("weekly_schedule", params={"select": "*", "user_id": f"eq.{user['id']}"})
            schedule_data = {row["day"]: row for row in (rows or [])}
        except Exception:
            schedule_data = {}
    return render_template("index.html", user=user, schedule=schedule_data)


@app.route("/login-required")
def login_required_page():
    """Shown when a guest clicks schedule/exercise card — ask them to login and make their schedule."""
    return render_template("login_required.html", user=session.get("user"))


@app.route("/schedule")
def schedule():
    user = session.get("user")
    schedule_data = []
    if user and SUPABASE_REST and SUPABASE_KEY:
        try:
            rows = sb_select("weekly_schedule", params={"select": "*", "user_id": f"eq.{user['id']}"})
            schedule_data = {row["day"]: row for row in (rows or [])}
        except Exception:
            schedule_data = {}
    return render_template("schedule.html", days=DAYS, schedule=schedule_data, user=user, muscle_groups=MUSCLE_GROUPS)


@app.route("/schedule/day/<day_name>")
@login_required
def schedule_day(day_name):
    if day_name not in DAYS:
        flash("Invalid day.", "error")
        return redirect(url_for("schedule"))
    user = session.get("user")
    user_id = session.get("user_id")
    muscle_group = ""
    if user_id and SUPABASE_REST and SUPABASE_KEY:
        try:
            rows = sb_select("weekly_schedule", params={"select": "muscle_group", "user_id": f"eq.{user_id}", "day": f"eq.{day_name}", "limit": 1})
            if rows:
                mg = (rows[0].get("muscle_group") or "").strip().lower()
                if mg and mg != "rest":
                    muscle_group = mg
        except Exception:
            muscle_group = ""

    exercises = []
    if muscle_group and SUPABASE_REST and SUPABASE_KEY:
        try:
            # Show admin exercises + THIS user's exercises (never other users)
            exercises = sb_select(
                "exercises",
                params={
                    "select": "*",
                    "muscle_group": f"eq.{muscle_group}",
                    "or": f"(created_by.is.null,created_by.eq.{user_id})",
                    "order": "name.asc",
                },
            ) or []
        except Exception:
            exercises = []
    return render_template("schedule_day.html", user=user, day_name=day_name, muscle_group=muscle_group, exercises=exercises)


@app.route("/my-exercises")
@login_required
def my_exercises():
    user = session.get("user")
    exercises = []
    if user and user.get("id") and SUPABASE_REST and SUPABASE_KEY:
        try:
            exercises = sb_select(
                "exercises",
                params={"select": "*", "created_by": f"eq.{user['id']}", "order": "name.asc"},
                key_override=_service_key_or_anon(),
            ) or []
        except Exception:
            exercises = []
    return render_template("my_exercises.html", user=user, muscle_groups=[m for m in MUSCLE_GROUPS if m != "rest"], exercises=exercises)


@app.route("/diet")
def diet():
    user = session.get("user")
    diet_plan_week = []
    user_plans = {}  # day_name -> { breakfast, lunch, dinner, snacks }
    if user and user.get("goal") and SUPABASE_REST and SUPABASE_KEY:
        try:
            goals = sb_select("goals", params={"select": "id,name", "name": f"eq.{user['goal']}", "limit": 1})
            if goals:
                gid = goals[0]["id"]
                rows = sb_select(
                    "diet_plans",
                    params={"select": "day_name,day_order,title,content", "goal_id": f"eq.{gid}", "order": "day_order.asc"},
                )
                diet_plan_week = rows or []
            if user.get("id") and SUPABASE_REST and SUPABASE_KEY:
                try:
                    up_rows = sb_select(
                        "user_diet_plan",
                        params={"select": "day_name,breakfast,lunch,dinner,snacks", "user_id": f"eq.{user['id']}"},
                        key_override=_service_key_or_anon(),
                    )
                    user_plans = {r["day_name"]: r for r in (up_rows or [])}
                except Exception:
                    user_plans = {}
        except Exception:
            diet_plan_week = []
    # Build per-day data with breakfast/lunch/dinner/snacks (user override or parsed from content)
    week_with_meals = []
    for day in diet_plan_week:
        ud = user_plans.get(day["day_name"]) or {}
        if ud:
            week_with_meals.append({
                "day_name": day["day_name"],
                "day_order": day.get("day_order", 0),
                "title": day.get("title"),
                "breakfast": ud.get("breakfast") or "",
                "lunch": ud.get("lunch") or "",
                "dinner": ud.get("dinner") or "",
                "snacks": ud.get("snacks") or "",
            })
        else:
            parsed = parse_diet_content(day.get("content"))
            week_with_meals.append({
                "day_name": day["day_name"],
                "day_order": day.get("day_order", 0),
                "title": day.get("title"),
                "breakfast": parsed["breakfast"],
                "lunch": parsed["lunch"],
                "dinner": parsed["dinner"],
                "snacks": parsed["snacks"],
            })
    return render_template("diet.html", user=user, diet_plan_week=week_with_meals)


def _get_diet_day_data(user, day_name):
    """Get breakfast/lunch/dinner/snacks for one day (from user_diet_plan or diet_plans by goal)."""
    if day_name not in DAYS:
        return None
    out = {"day_name": day_name, "title": "", "breakfast": "", "lunch": "", "dinner": "", "snacks": ""}
    if not user or not user.get("goal") or not SUPABASE_REST or not SUPABASE_KEY:
        return out
    try:
        goals = sb_select("goals", params={"select": "id,name", "name": f"eq.{user['goal']}", "limit": 1})
        if goals:
            gid = goals[0]["id"]
            rows = sb_select(
                "diet_plans",
                params={"select": "day_name,day_order,title,content", "goal_id": f"eq.{gid}", "day_name": f"eq.{day_name}", "limit": 1},
            )
            default_day = (rows or [{}])[0] if rows else {}
        else:
            default_day = {}
        user_plan = {}
        if user.get("id"):
            try:
                up = sb_select(
                    "user_diet_plan",
                    params={"select": "breakfast,lunch,dinner,snacks", "user_id": f"eq.{user['id']}", "day_name": f"eq.{day_name}", "limit": 1},
                    key_override=_service_key_or_anon(),
                )
                user_plan = (up or [{}])[0] if up else {}
            except Exception:
                pass
        if user_plan and (user_plan.get("breakfast") or user_plan.get("lunch") or user_plan.get("dinner") or user_plan.get("snacks")):
            out["title"] = (default_day.get("title") or "")
            out["breakfast"] = user_plan.get("breakfast") or ""
            out["lunch"] = user_plan.get("lunch") or ""
            out["dinner"] = user_plan.get("dinner") or ""
            out["snacks"] = user_plan.get("snacks") or ""
        else:
            parsed = parse_diet_content(default_day.get("content"))
            out["title"] = default_day.get("title") or ""
            out["breakfast"] = parsed["breakfast"]
            out["lunch"] = parsed["lunch"]
            out["dinner"] = parsed["dinner"]
            out["snacks"] = parsed["snacks"]
    except Exception:
        pass
    return out


@app.route("/diet/day/<day_name>")
def diet_day(day_name):
    user = session.get("user")
    if day_name not in DAYS:
        flash("Invalid day.", "error")
        return redirect(url_for("diet"))
    day_data = _get_diet_day_data(user, day_name)
    return render_template("diet_day.html", user=user, day=day_data)


@app.route("/weekly-analysis")
@login_required
def weekly_analysis():
    return render_template("weekly_analysis.html", user=session.get("user"))


@app.route("/calories")
def calories():
    return render_template("calories.html", user=session.get("user"))


@app.route("/bmi")
def bmi():
    return render_template("bmi.html", user=session.get("user"))


@app.route("/admin")
@admin_required
def admin_dashboard():
    user = session.get("user") or {}
    if not SUPABASE_REST or not SUPABASE_KEY:
        flash("Database not configured. Set SUPABASE_URL and SUPABASE_KEY.", "error")
        return redirect(url_for("index"))
    if not SUPABASE_SERVICE_KEY:
        flash("SUPABASE_SERVICE_KEY is required for the admin dashboard.", "error")
        return redirect(url_for("index"))

    users = []
    admin_exercises = []
    try:
        users = sb_select(
            "users_profile",
            params={"select": "id,name,email,goal,created_at,is_admin", "order": "created_at.desc", "limit": 500},
            key_override=SUPABASE_SERVICE_KEY,
        ) or []
    except Exception:
        users = []
    try:
        admin_exercises = sb_select(
            "exercises",
            params={"select": "*", "created_by": "is.null", "order": "name.asc", "limit": 500},
            key_override=SUPABASE_SERVICE_KEY,
        ) or []
    except Exception:
        admin_exercises = []

    # Group global exercises by muscle_group for admin UI; sort each group by sequence_order then name
    muscle_order = [m for m in MUSCLE_GROUPS if m != "rest"]
    exercises_by_group = {}
    for mg in muscle_order:
        group_list = [ex for ex in admin_exercises if (ex.get("muscle_group") or "").lower() == mg]
        exercises_by_group[mg] = sorted(group_list, key=lambda e: (e.get("sequence_order") or 0, (e.get("name") or "")))
    for ex in admin_exercises:
        mg = (ex.get("muscle_group") or "").strip().lower()
        if mg and mg not in exercises_by_group:
            exercises_by_group[mg] = sorted(
                [e for e in admin_exercises if (e.get("muscle_group") or "").strip().lower() == mg],
                key=lambda e: (e.get("sequence_order") or 0, (e.get("name") or "")),
            )

    return render_template(
        "admin.html",
        user=user,
        users=users,
        muscle_groups=[m for m in MUSCLE_GROUPS if m != "rest"],
        exercises=admin_exercises,
        exercises_by_group=exercises_by_group,
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""
    if not email or not password:
        flash("Email and password are required.", "error")
        return redirect(url_for("login"))
    if not SUPABASE_REST or not SUPABASE_KEY:
        flash("Database not configured. Set SUPABASE_URL and SUPABASE_KEY.", "error")
        return redirect(url_for("login"))
    try:
        r = sb_select(
            "users_profile",
            params={"select": "id,name,email,age,weight,height,goal,password_hash,is_admin", "email": f"eq.{email}", "limit": 1},
            key_override=_service_key_or_anon(),
        )
        if not r:
            flash("You're not registered. Please register first.", "error")
            return redirect(url_for("register"))
        user = r[0]
        if not user.get("password_hash") or not check_password_hash(user["password_hash"], password):
            flash("Invalid email or password.", "error")
            return redirect(url_for("login"))
        # Promote to admin if their email is whitelisted (env) or DB flag is set.
        is_admin = _is_admin_for_user(user)
        if is_admin and not user.get("is_admin") and SUPABASE_SERVICE_KEY:
            try:
                sb_update("users_profile", {"is_admin": True}, match={"id": user["id"]}, key_override=SUPABASE_SERVICE_KEY)
                user["is_admin"] = True
            except Exception:
                user["is_admin"] = True
        session["user_id"] = str(user["id"])
        session["user"] = {k: v for k, v in user.items() if k != "password_hash"}
        flash(f"Welcome back, {user.get('name') or email}!", "success")
        next_url = request.args.get("next") or url_for("index")
        return redirect(next_url)
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        goals = []
        if SUPABASE_REST and SUPABASE_KEY:
            try:
                goals = sb_select("goals", params={"select": "id,name", "order": "display_order.asc"})
                goals = goals or []
            except Exception:
                goals = []
        return render_template("register.html", goals=goals)
    if not SUPABASE_REST or not SUPABASE_KEY:
        flash("Database not configured. Set SUPABASE_URL and SUPABASE_KEY.", "error")
        return redirect(url_for("register"))
    name = (request.form.get("name") or "").strip()
    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""
    age = request.form.get("age") or None
    weight = request.form.get("weight") or None
    height = request.form.get("height") or None
    goal = (request.form.get("goal") or "").strip()
    if not name or not email or not password:
        flash("Name, email, and password are required.", "error")
        return redirect(url_for("register"))
    try:
        existing = sb_select("users_profile", params={"select": "id", "email": f"eq.{email}", "limit": 1}, key_override=_service_key_or_anon())
        if existing:
            flash("Email already registered. Please log in.", "error")
            return redirect(url_for("login"))
        row = {
            "name": name,
            "email": email,
            "age": int(age) if age else None,
            "weight": int(float(weight)) if weight else None,
            "height": int(float(height)) if height else None,
            "goal": goal or None,
            "password_hash": generate_password_hash(password),
            "is_admin": True if email in ADMIN_EMAILS else False,
        }
        ins = sb_insert("users_profile", row, key_override=_service_key_or_anon())
        if not ins:
            flash("Could not create account.", "error")
            return redirect(url_for("register"))
        user = ins[0]
        user["is_admin"] = _is_admin_for_user(user)
        session["user_id"] = str(user["id"])
        session["user"] = {k: v for k, v in user.items() if k != "password_hash"}
        flash("Account created. Welcome!", "success")
        return redirect(url_for("index"))
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for("register"))


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "GET":
        return render_template("forgot_password.html")
    email = (request.form.get("email") or "").strip().lower()
    if not email:
        flash("Email is required.", "error")
        return redirect(url_for("forgot_password"))
    try:
        users = sb_select(
            "users_profile",
            params={"select": "id,email", "email": f"eq.{email}", "limit": 1},
            key_override=_service_key_or_anon(),
        )
        if not users:
            flash("This email is not registered. Please register first.", "error")
            return redirect(url_for("register"))
        user = users[0]
        # When Gmail is configured, we send reset link to this user's email (any user). No restriction.
        gmail_configured = bool(GMAIL_USER and GMAIL_APP_PASSWORD)
        if not gmail_configured:
            # Resend without domain: only one allowed email can receive reset.
            if "resend.dev" in (RESEND_FROM_EMAIL or ""):
                if not ALLOWED_RESET_EMAIL or email != ALLOWED_RESET_EMAIL:
                    flash(
                        "Right now only the site owner email can get a reset link. "
                        "To let every user reset their password: in .env set GMAIL_USER and GMAIL_APP_PASSWORD (Gmail App Password from myaccount.google.com/apppasswords).",
                        "error",
                    )
                    return redirect(url_for("forgot_password"))
        token = secrets.token_urlsafe(32)
        token_hash = _hash_token(token)
        expires = (datetime.utcnow() + timedelta(minutes=30)).isoformat()
        sb_update(
            "users_profile",
            {"reset_token_hash": token_hash, "reset_token_expires": expires},
            match={"id": user["id"]},
            key_override=_service_key_or_anon(),
        )
        reset_url = f"{APP_BASE_URL}/reset-password?token={token}&email={email}"

        def _send_in_background():
            try:
                send_reset_email(to_email=email, reset_url=reset_url)
            except Exception as e:
                print(f"[forgot-password] Background send failed: {type(e).__name__}: {e}\n{traceback.format_exc()}")

        threading.Thread(target=_send_in_background, daemon=True).start()
        flash("If that email exists, a reset link has been sent.", "success")
        return redirect(url_for("login"))
    except requests.HTTPError as e:
        err_body = ""
        err_url = ""
        if e.response is not None:
            try:
                err_body = e.response.text[:500] if e.response.text else ""
            except Exception:
                pass
            try:
                err_url = str(getattr(e.response, "url", "") or "")
            except Exception:
                pass
        print(
            f"[forgot-password] HTTPError: status={e.response.status_code if e.response else '?'} url={err_url!r} body={err_body}"
        )

        # Distinguish DB failures vs email provider failures (both raise HTTPError).
        if err_url and "api.resend.com" in err_url:
            flash(
                "Reset email could not be sent. Your Resend sender is blocked. "
                "Open Render logs and search [forgot-password] to see the exact Resend reason.",
                "error",
            )
        elif err_url and "supabase.co/rest" in err_url:
            if e.response is not None and e.response.status_code in (401, 403):
                flash(
                    "Server config error: Supabase permission denied for password reset. "
                    "On Render, set SUPABASE_SERVICE_KEY (service_role) so the server can update reset tokens.",
                    "error",
                )
            elif e.response is not None and e.response.status_code == 400:
                flash(
                    "Server config error: password reset columns may be missing. Run supabase_add_reset_token_columns.sql in Supabase SQL Editor.",
                    "error",
                )
            else:
                flash("Database error while creating reset link. Please try again later.", "error")
        else:
            flash("Could not send reset link. Please try again later.", "error")
        return redirect(url_for("forgot_password"))
    except requests.RequestException as e:
        print(f"[forgot-password] RequestException: {type(e).__name__}: {e}\n{traceback.format_exc()}")
        flash("Network or database error. Please try again in a moment.", "error")
        return redirect(url_for("forgot_password"))
    except Exception as e:
        print(f"[forgot-password] Error: {type(e).__name__}: {e}\n{traceback.format_exc()}")
        flash("Could not send reset link. Please try again or contact support.", "error")
        return redirect(url_for("forgot_password"))


@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if request.method == "GET":
        token = request.args.get("token") or ""
        email = (request.args.get("email") or "").strip().lower()
        return render_template("reset_password.html", token=token, email=email)
    email = (request.form.get("email") or "").strip().lower()
    token = request.form.get("token") or ""
    new_password = request.form.get("password") or ""
    if not email or not token or not new_password:
        flash("All fields are required.", "error")
        return redirect(url_for("reset_password", token=token, email=email))
    try:
        users = sb_select(
            "users_profile",
            params={"select": "id,reset_token_hash,reset_token_expires", "email": f"eq.{email}", "limit": 1},
            key_override=_service_key_or_anon(),
        )
        if not users:
            flash("Invalid reset link.", "error")
            return redirect(url_for("login"))
        user = users[0]
        expected = user.get("reset_token_hash")
        expires = user.get("reset_token_expires")
        if not expected or not expires:
            flash("Reset link expired. Please request a new one.", "error")
            return redirect(url_for("forgot_password"))
        if _hash_token(token) != expected:
            flash("Invalid reset link.", "error")
            return redirect(url_for("forgot_password"))
        if datetime.utcnow() > datetime.fromisoformat(expires[:19]):
            flash("Reset link expired. Please request a new one.", "error")
            return redirect(url_for("forgot_password"))
        sb_update(
            "users_profile",
            {
                "password_hash": generate_password_hash(new_password),
                "reset_token_hash": None,
                "reset_token_expires": None,
            },
            match={"id": user["id"]},
            key_override=_service_key_or_anon(),
        )
        flash("Password updated. Please log in.", "success")
        return redirect(url_for("login"))
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for("forgot_password"))


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = session.get("user")
    schedule_data = {}
    if SUPABASE_REST and SUPABASE_KEY:
        try:
            rows = sb_select("weekly_schedule", params={"select": "*", "user_id": f"eq.{user['id']}"})
            schedule_data = {row["day"]: row for row in (rows or [])}
        except Exception:
            pass
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        age = request.form.get("age")
        weight = request.form.get("weight")
        height = request.form.get("height")
        goal = request.form.get("goal", "").strip()
        try:
            sb_update(
                "users_profile",
                {
                    "name": name or None,
                    "age": int(age) if age else None,
                    "weight": int(weight) if weight else None,
                    "height": int(height) if height else None,
                    "goal": goal or None,
                },
                match={"id": user["id"]},
            )
            session["user"] = {**user, "name": name, "age": age, "weight": weight, "height": height, "goal": goal}
            flash("Profile updated.", "success")
        except Exception as e:
            flash(str(e), "error")
        return redirect(url_for("profile"))
    return render_template("profile.html", user=user, schedule=schedule_data, muscle_groups=MUSCLE_GROUPS)


# ---------- API ----------


@app.route("/api/exercises")
def api_exercises():
    muscle_group = request.args.get("muscle_group")
    if not SUPABASE_REST or not SUPABASE_KEY:
        return jsonify([])
    try:
        params = {"select": "*", "order": "name.asc"}
        if muscle_group:
            params["muscle_group"] = f"eq.{muscle_group}"
        # IMPORTANT: don't show other users' exercises.
        # - anonymous: admin exercises only (created_by is null)
        # - logged in: admin exercises + this user's exercises
        user_id = session.get("user_id")
        if user_id:
            params["or"] = f"(created_by.is.null,created_by.eq.{user_id})"
        else:
            params["created_by"] = "is.null"
        rows = sb_select("exercises", params=params)
        return jsonify(rows or [])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/exercises/home")
def api_exercises_home():
    """One exercise per muscle group for the home page. Uses admin's 'show on home' choice; else first by name."""
    if not SUPABASE_REST or not SUPABASE_KEY:
        return jsonify([])
    try:
        key = _service_key_or_anon()
        rows = sb_select(
            "exercises",
            params={"select": "*", "created_by": "is.null", "order": "name.asc", "limit": 500},
            key_override=key,
        ) or []
        # Build one per muscle: prefer show_on_home=True; else first by sequence then name
        muscle_order = [m for m in MUSCLE_GROUPS if m != "rest"]
        by_muscle = {}
        for ex in rows:
            mg = (ex.get("muscle_group") or "").strip().lower()
            if not mg:
                continue
            if mg not in by_muscle:
                by_muscle[mg] = []
            by_muscle[mg].append(ex)
        result = []
        for mg in muscle_order:
            list_for_mg = sorted(by_muscle.get(mg) or [], key=lambda e: (e.get("sequence_order") or 0, (e.get("name") or "")))
            chosen = next((e for e in list_for_mg if e.get("show_on_home")), list_for_mg[0] if list_for_mg else None)
            if chosen:
                result.append(chosen)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/schedule", methods=["GET", "POST", "PUT", "DELETE"])
@login_required
def api_schedule():
    user_id = session.get("user_id")
    if not SUPABASE_REST or not SUPABASE_KEY:
        return jsonify({"error": "Database not configured"}), 500
    if request.method == "GET":
        try:
            rows = sb_select("weekly_schedule", params={"select": "*", "user_id": f"eq.{user_id}"})
            return jsonify(rows or [])
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    if request.method == "POST":
        data = request.get_json() or {}
        day = data.get("day")
        muscle_group = data.get("muscle_group")
        if not day or not muscle_group:
            return jsonify({"error": "day and muscle_group required"}), 400
        try:
            rows = sb_upsert(
                "weekly_schedule",
                {"user_id": user_id, "day": day, "muscle_group": muscle_group},
                on_conflict="user_id,day",
            )
            return jsonify(rows[0] if rows else {})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    if request.method == "DELETE":
        day = request.args.get("day")
        if not day:
            return jsonify({"error": "day required"}), 400
        try:
            sb_delete("weekly_schedule", match={"user_id": user_id, "day": day})
            return jsonify({"ok": True})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return jsonify({"error": "Method not allowed"}), 405


@app.route("/api/diet-plan", methods=["POST"])
@login_required
def api_diet_plan():
    """Save or update user's diet plan for one day (breakfast, lunch, dinner, snacks)."""
    user_id = session.get("user_id")
    if not SUPABASE_REST or not SUPABASE_KEY:
        return jsonify({"error": "Database not configured"}), 500
    data = request.get_json() or request.form
    day_name = (data.get("day_name") or "").strip()
    if not day_name or day_name not in DAYS:
        return jsonify({"error": "day_name required (e.g. Monday)"}), 400
    breakfast = (data.get("breakfast") or "").strip()
    lunch = (data.get("lunch") or "").strip()
    dinner = (data.get("dinner") or "").strip()
    snacks = (data.get("snacks") or "").strip()
    try:
        sb_upsert(
            "user_diet_plan",
            {
                "user_id": user_id,
                "day_name": day_name,
                "breakfast": breakfast or None,
                "lunch": lunch or None,
                "dinner": dinner or None,
                "snacks": snacks or None,
            },
            on_conflict="user_id,day_name",
        )
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/my-exercises", methods=["GET", "POST"])
@login_required
def api_my_exercises():
    user_id = session.get("user_id")
    if not SUPABASE_REST or not SUPABASE_KEY:
        return jsonify({"error": "Database not configured"}), 500
    if request.method == "GET":
        try:
            rows = sb_select(
                "exercises",
                params={"select": "*", "created_by": f"eq.{user_id}", "order": "name.asc"},
                key_override=_service_key_or_anon(),
            )
            return jsonify(rows or [])
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # POST: create exercise (image upload OR image_url)
    try:
        # We need service role for inserts (RLS) and for Storage uploads.
        if not SUPABASE_SERVICE_KEY:
            return jsonify({
                "error": "SUPABASE_SERVICE_KEY is missing. In Supabase Dashboard → Project Settings → API → copy the service_role key, add it to .env as SUPABASE_SERVICE_KEY, then restart the app."
            }), 400

        name = (request.form.get("name") or "").strip()
        muscle_group = (request.form.get("muscle_group") or "").strip().lower()
        image_url = (request.form.get("image_url") or "").strip()
        video_url = (request.form.get("video_url") or "").strip()
        image_file = request.files.get("image_file")
        video_file = request.files.get("video_file")

        if not name or not muscle_group:
            return jsonify({"error": "name and muscle_group required"}), 400
        if muscle_group not in [m for m in MUSCLE_GROUPS if m != "rest"]:
            return jsonify({"error": "Invalid muscle_group"}), 400

        final_image_url = ""
        if image_file and getattr(image_file, "filename", ""):
            final_image_url = upload_exercise_image_to_storage(user_id=user_id, file_storage=image_file)
        else:
            final_image_url = image_url

        if not final_image_url:
            return jsonify({"error": "Provide an image upload or image_url"}), 400

        final_video_url = ""
        if video_file and getattr(video_file, "filename", ""):
            final_video_url = upload_exercise_video_to_storage(user_id=user_id, file_storage=video_file)
        else:
            final_video_url = video_url

        row = {
            "name": name,
            "muscle_group": muscle_group,
            "image_url": final_image_url,
            "video_url": final_video_url or None,
            "difficulty": None,
            "equipment": None,
            "created_by": user_id,
        }
        ins = sb_insert("exercises", row, key_override=SUPABASE_SERVICE_KEY)
        return jsonify(ins[0] if ins else {}), 200
    except requests.HTTPError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/my-exercises/<ex_id>", methods=["PUT", "DELETE"])
@login_required
def api_my_exercise_detail(ex_id):
    user_id = session.get("user_id")
    if not SUPABASE_REST or not SUPABASE_KEY:
        return jsonify({"error": "Database not configured"}), 500
    if not SUPABASE_SERVICE_KEY:
        return jsonify({"error": "SUPABASE_SERVICE_KEY is missing. Add it to .env and restart the app."}), 400
    try:
        # Ownership check: only allow edit/delete of user's own exercise
        rows = sb_select(
            "exercises",
            params={"select": "id,created_by", "id": f"eq.{ex_id}", "limit": 1},
            key_override=SUPABASE_SERVICE_KEY,
        ) or []
        if not rows:
            return jsonify({"error": "Not found"}), 404
        ex = rows[0]
        if str(ex.get("created_by") or "") != str(user_id):
            return jsonify({"error": "Not allowed"}), 403

        if request.method == "DELETE":
            sb_delete("exercises", match={"id": ex_id}, key_override=SUPABASE_SERVICE_KEY)
            return jsonify({"ok": True})

        # PUT: update fields (image upload OR url)
        name = (request.form.get("name") or "").strip()
        muscle_group = (request.form.get("muscle_group") or "").strip().lower()
        image_url = (request.form.get("image_url") or "").strip()
        video_url = (request.form.get("video_url") or "").strip()
        image_file = request.files.get("image_file")
        video_file = request.files.get("video_file")

        updates = {}
        if name:
            updates["name"] = name
        if muscle_group:
            if muscle_group not in [m for m in MUSCLE_GROUPS if m != "rest"]:
                return jsonify({"error": "Invalid muscle_group"}), 400
            updates["muscle_group"] = muscle_group
        if image_file and getattr(image_file, "filename", ""):
            updates["image_url"] = upload_exercise_image_to_storage(user_id=user_id, file_storage=image_file)
        elif image_url:
            updates["image_url"] = image_url
        if video_file and getattr(video_file, "filename", ""):
            updates["video_url"] = upload_exercise_video_to_storage(user_id=user_id, file_storage=video_file)
        else:
            # video_url can be cleared by sending empty string
            updates["video_url"] = video_url or None

        if not updates:
            return jsonify({"error": "Nothing to update"}), 400
        out = sb_update("exercises", updates, match={"id": ex_id}, key_override=SUPABASE_SERVICE_KEY)
        return jsonify(out[0] if out else {"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/workout-logs", methods=["GET", "POST"])
@login_required
def api_workout_logs():
    user_id = session.get("user_id")
    if not SUPABASE_REST or not SUPABASE_KEY:
        return jsonify({"error": "Database not configured"}), 500
    if request.method == "GET":
        week_start = request.args.get("week_start")
        try:
            params = {"select": "*,exercises(name)", "user_id": f"eq.{user_id}", "order": "workout_date.desc", "limit": 100}
            logs = sb_select("workout_logs", params=params) or []
            if week_start:
                start = datetime.fromisoformat(week_start.replace("Z", ""))
                end = start + timedelta(days=7)
                logs = [l for l in logs if start <= datetime.fromisoformat((l.get("workout_date") or "")[:19].replace("Z", "")) < end]
            return jsonify(logs)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    if request.method == "POST":
        data = request.get_json() or {}
        exercise_id = data.get("exercise_id")
        duration_minutes = data.get("duration_minutes", 0)
        calories_burned = data.get("calories_burned", 0)
        if not exercise_id:
            return jsonify({"error": "exercise_id required"}), 400
        try:
            rows = sb_insert(
                "workout_logs",
                {
                    "user_id": user_id,
                    "exercise_id": exercise_id,
                    "duration_minutes": int(duration_minutes),
                    "calories_burned": int(calories_burned),
                },
            )
            return jsonify(rows[0] if rows else {})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return jsonify({"error": "Method not allowed"}), 405


@app.route("/api/admin/users")
@admin_required
def api_admin_users():
    if not SUPABASE_REST or not SUPABASE_KEY:
        return jsonify({"error": "Database not configured"}), 500
    if not SUPABASE_SERVICE_KEY:
        return jsonify({"error": "SUPABASE_SERVICE_KEY is required"}), 400
    try:
        users = sb_select(
            "users_profile",
            params={"select": "id,name,email,goal,created_at,is_admin", "order": "created_at.desc", "limit": 1000},
            key_override=SUPABASE_SERVICE_KEY,
        )
        return jsonify(users or [])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/users/<user_id>", methods=["DELETE"])
@admin_required
def api_admin_user_delete(user_id):
    if not SUPABASE_REST or not SUPABASE_KEY:
        return jsonify({"error": "Database not configured"}), 500
    if not SUPABASE_SERVICE_KEY:
        return jsonify({"error": "SUPABASE_SERVICE_KEY is required"}), 400
    try:
        # Prevent deleting yourself
        if str(session.get("user_id")) == str(user_id):
            return jsonify({"error": "You cannot delete your own admin account from here."}), 400
        sb_delete("users_profile", match={"id": user_id}, key_override=SUPABASE_SERVICE_KEY)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/exercises", methods=["GET", "POST"])
@admin_required
def api_admin_exercises():
    if not SUPABASE_REST or not SUPABASE_KEY:
        return jsonify({"error": "Database not configured"}), 500
    if not SUPABASE_SERVICE_KEY:
        return jsonify({"error": "SUPABASE_SERVICE_KEY is required"}), 400

    if request.method == "GET":
        try:
            rows = sb_select(
                "exercises",
                params={"select": "*", "created_by": "is.null", "order": "name.asc", "limit": 1000},
                key_override=SUPABASE_SERVICE_KEY,
            )
            return jsonify(rows or [])
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # POST: create GLOBAL exercise (created_by = null)
    try:
        name = (request.form.get("name") or "").strip()
        muscle_group = (request.form.get("muscle_group") or "").strip().lower()
        image_url = (request.form.get("image_url") or "").strip()
        video_url = (request.form.get("video_url") or "").strip()
        image_file = request.files.get("image_file")
        video_file = request.files.get("video_file")
        try:
            sequence_order = int(request.form.get("sequence_order") or 0)
        except ValueError:
            sequence_order = 0

        if not name or not muscle_group:
            return jsonify({"error": "name and muscle_group required"}), 400
        if muscle_group not in [m for m in MUSCLE_GROUPS if m != "rest"]:
            return jsonify({"error": "Invalid muscle_group"}), 400

        final_image_url = ""
        if image_file and getattr(image_file, "filename", ""):
            # Store under the admin user's folder for uniqueness
            admin_id = session.get("user_id") or "admin"
            final_image_url = upload_exercise_image_to_storage(user_id=str(admin_id), file_storage=image_file)
        else:
            final_image_url = image_url
        if not final_image_url:
            return jsonify({"error": "Provide an image upload or image_url"}), 400

        final_video_url = ""
        if video_file and getattr(video_file, "filename", ""):
            admin_id = session.get("user_id") or "admin"
            final_video_url = upload_exercise_video_to_storage(user_id=str(admin_id), file_storage=video_file)
        else:
            final_video_url = video_url

        row = {
            "name": name,
            "muscle_group": muscle_group,
            "image_url": final_image_url,
            "video_url": final_video_url or None,
            "difficulty": None,
            "equipment": None,
            "created_by": None,  # GLOBAL
        }
        ins = sb_insert("exercises", row, key_override=SUPABASE_SERVICE_KEY)
        return jsonify(ins[0] if ins else {}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/exercises/<ex_id>", methods=["PUT", "DELETE"])
@admin_required
def api_admin_exercise_detail(ex_id):
    if not SUPABASE_REST or not SUPABASE_KEY:
        return jsonify({"error": "Database not configured"}), 500
    if not SUPABASE_SERVICE_KEY:
        return jsonify({"error": "SUPABASE_SERVICE_KEY is required"}), 400
    try:
        rows = sb_select(
            "exercises",
            params={"select": "id,created_by", "id": f"eq.{ex_id}", "limit": 1},
            key_override=SUPABASE_SERVICE_KEY,
        ) or []
        if not rows:
            return jsonify({"error": "Not found"}), 404
        ex = rows[0]
        if ex.get("created_by") is not None:
            return jsonify({"error": "Not a global (admin) exercise"}), 400

        if request.method == "DELETE":
            sb_delete("exercises", match={"id": ex_id}, key_override=SUPABASE_SERVICE_KEY)
            return jsonify({"ok": True})

        # PUT: update fields
        name = (request.form.get("name") or "").strip()
        muscle_group = (request.form.get("muscle_group") or "").strip().lower()
        image_url = (request.form.get("image_url") or "").strip()
        video_url = (request.form.get("video_url") or "").strip()
        image_file = request.files.get("image_file")
        video_file = request.files.get("video_file")
        try:
            sequence_order = int(request.form.get("sequence_order") or 0)
        except ValueError:
            sequence_order = 0

        updates = {}
        if name:
            updates["name"] = name
        if muscle_group:
            if muscle_group not in [m for m in MUSCLE_GROUPS if m != "rest"]:
                return jsonify({"error": "Invalid muscle_group"}), 400
            updates["muscle_group"] = muscle_group
        if image_file and getattr(image_file, "filename", ""):
            admin_id = session.get("user_id") or "admin"
            updates["image_url"] = upload_exercise_image_to_storage(user_id=str(admin_id), file_storage=image_file)
        elif image_url:
            updates["image_url"] = image_url
        if video_file and getattr(video_file, "filename", ""):
            admin_id = session.get("user_id") or "admin"
            updates["video_url"] = upload_exercise_video_to_storage(user_id=str(admin_id), file_storage=video_file)
        else:
            updates["video_url"] = video_url or None
        # sequence_order: only send if DB has the column (run supabase_show_on_home.sql); else 400
        updates_with_seq = {**updates, "sequence_order": sequence_order}

        if not updates:
            return jsonify({"error": "Nothing to update"}), 400
        try:
            out = sb_update("exercises", updates_with_seq, match={"id": ex_id}, key_override=SUPABASE_SERVICE_KEY)
            return jsonify(out[0] if out else {"ok": True})
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code in (400, 422):
                # DB may not have sequence_order column yet; retry without it
                out = sb_update("exercises", updates, match={"id": ex_id}, key_override=SUPABASE_SERVICE_KEY)
                return jsonify(out[0] if out else {"ok": True})
            raise
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/exercises/<ex_id>/show-on-home", methods=["POST"])
@admin_required
def api_admin_exercise_show_on_home(ex_id):
    """Set this global exercise as the one shown on the home page for its muscle group."""
    if not SUPABASE_REST or not SUPABASE_KEY or not SUPABASE_SERVICE_KEY:
        return jsonify({"error": "Database not configured"}), 500
    try:
        rows = sb_select(
            "exercises",
            params={"select": "id,muscle_group,created_by", "id": f"eq.{ex_id}", "limit": 1},
            key_override=SUPABASE_SERVICE_KEY,
        ) or []
        if not rows:
            return jsonify({"error": "Not found"}), 404
        ex = rows[0]
        if ex.get("created_by") is not None:
            return jsonify({"error": "Only global exercises can be shown on home"}), 400
        mg = (ex.get("muscle_group") or "").strip().lower()
        if not mg:
            return jsonify({"error": "Exercise has no muscle group"}), 400
        # Clear show_on_home for all other global exercises in this muscle group
        url = f"{SUPABASE_REST}/exercises"
        headers = _sb_headers("return=minimal", key_override=SUPABASE_SERVICE_KEY)
        params_clear = {"muscle_group": f"eq.{mg}", "created_by": "is.null"}
        r_clear = requests.patch(url, headers=headers, params=params_clear, json={"show_on_home": False}, timeout=30)
        r_clear.raise_for_status()
        # Set this exercise as show on home
        sb_update("exercises", {"show_on_home": True}, match={"id": ex_id}, key_override=SUPABASE_SERVICE_KEY)
        return jsonify({"ok": True})
    except requests.HTTPError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/weekly-stats")
@login_required
def api_weekly_stats():
    user_id = session.get("user_id")
    if not SUPABASE_REST or not SUPABASE_KEY:
        return jsonify({"error": "Database not configured"}), 500
    try:
        today = datetime.utcnow()
        week_start = (today - timedelta(days=today.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        week_end = week_start + timedelta(days=7)
        all_logs = sb_select("workout_logs", params={"select": "*", "user_id": f"eq.{user_id}"}) or []
        logs = [
            l for l in all_logs
            if week_start.isoformat() <= (l.get("workout_date") or "")[:19] < week_end.isoformat()
        ]
        total_minutes = sum(l.get("duration_minutes", 0) for l in logs)
        total_calories = sum(l.get("calories_burned", 0) for l in logs)
        by_day = {}
        for l in logs:
            d = (l.get("workout_date") or "")[:10]
            if d not in by_day:
                by_day[d] = {"minutes": 0, "calories": 0, "count": 0}
            by_day[d]["minutes"] += l.get("duration_minutes", 0)
            by_day[d]["calories"] += l.get("calories_burned", 0)
            by_day[d]["count"] += 1
        return jsonify(
            {
                "total_minutes": total_minutes,
                "total_calories": total_calories,
                "exercises_completed": len(logs),
                "by_day": by_day,
                "week_start": week_start.isoformat(),
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


import os

if __name__ == "__main__":
    if GMAIL_USER and GMAIL_APP_PASSWORD:
        print("Password reset: Gmail configured — any user can receive reset link.")
    else:
        print("Password reset: Gmail not set — only one email can receive.")

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
