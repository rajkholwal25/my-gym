# My Gym

A gym workout web app: weekly schedule, exercises by muscle group, workout logging, and weekly analysis. Built with **Python (Flask)** and **Supabase**.

## Features

- **Navbar**: Home, Schedule, Diet, Weekly Analysis, Calories, BMI
- **Weekly Schedule**: 7 day cards (Mon–Sun). Each card shows day, muscle group, and image. Click a card to see exercises for that muscle group.
- **Exercises**: Cards with name and image. Click image to play exercise video. Log workout (duration, calories) when logged in.
- **User accounts**: Login with email (auto-register). Profile: name, age, weight, height, goal; customize weekly schedule (muscle group per day).
- **Weekly Analysis**: Total minutes, calories burned, exercises completed, bar chart by day, recent workout list.
- **Calories**: Simple BMR/TDEE calculator.
- **BMI**: Body Mass Index calculator.
- **Auth**: Register with full details + password login.
- **Forgot password**: Email reset link (Resend).

## Setup

### 1. Supabase

1. Create a project at [supabase.com](https://supabase.com).
2. In **SQL Editor**, run the contents of `supabase_schema.sql` (creates tables and seed exercises).
3. In **Settings → API**: copy **Project URL** and **anon public** key.

### 2. Python app

```bash
cd Gym
python -m venv venv
venv\Scripts\activate   # Windows
# or: source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

Create a `.env` file (see `.env.example`):

```env
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_role_key_optional_but_recommended
FLASK_SECRET_KEY=any-secret-string
APP_BASE_URL=http://127.0.0.1:5000
RESEND_API_KEY=your_resend_api_key
```

Run:

```bash
python app.py
```

Open **http://127.0.0.1:5000**.

## Database tables

| Table            | Purpose                    |
|-----------------|----------------------------|
| `users_profile` | User details (name, email, age, weight, height, goal) |
| `exercises`     | Exercise name, muscle_group, image_url, video_url, difficulty, equipment |
| `weekly_schedule` | Per-user plan: user_id, day, muscle_group |
| `workout_logs`  | user_id, exercise_id, duration_minutes, calories_burned, workout_date |

## Tech stack

- **Backend**: Flask, Supabase REST (PostgREST) via `requests`
- **Frontend**: HTML, CSS, vanilla JS; Chart.js for weekly chart
- **DB**: Supabase (PostgreSQL)

## Optional later

- Workout streak
- Progress chart over time
- Workout timer
