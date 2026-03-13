-- Run in Supabase SQL Editor once. Adds columns needed for forgot-password reset links.
-- If you get "Internal Server Error" or 400 on forgot-password, run this.

ALTER TABLE users_profile
  ADD COLUMN IF NOT EXISTS reset_token_hash TEXT;

ALTER TABLE users_profile
  ADD COLUMN IF NOT EXISTS reset_token_expires TIMESTAMPTZ;
