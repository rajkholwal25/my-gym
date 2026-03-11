-- Run this in Supabase SQL Editor (one time) to enable admin + global exercises.

-- 1) Add admin flag to users
ALTER TABLE IF EXISTS users_profile
  ADD COLUMN IF NOT EXISTS is_admin BOOLEAN NOT NULL DEFAULT FALSE;

-- 2) Add created_by to exercises so we can separate:
--    - admin/global exercises: created_by IS NULL
--    - user exercises: created_by = user_id
ALTER TABLE IF EXISTS exercises
  ADD COLUMN IF NOT EXISTS created_by UUID REFERENCES users_profile(id) ON DELETE SET NULL;

-- Optional: make a specific email admin (recommended once you have that user row created)
-- UPDATE users_profile SET is_admin = TRUE WHERE email = 'rajkholwal25@gmail.com';

