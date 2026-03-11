-- Run this in Supabase SQL Editor — adds user_diet_plan so users can edit and save their daily meals

CREATE TABLE IF NOT EXISTS user_diet_plan (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users_profile(id) ON DELETE CASCADE,
  day_name TEXT NOT NULL,
  breakfast TEXT,
  lunch TEXT,
  dinner TEXT,
  snacks TEXT,
  UNIQUE(user_id, day_name)
);

ALTER TABLE user_diet_plan ENABLE ROW LEVEL SECURITY;

-- Users can read/insert/update/delete only their own rows
DROP POLICY IF EXISTS "Users own user_diet_plan" ON user_diet_plan;
CREATE POLICY "Users own user_diet_plan" ON user_diet_plan FOR ALL USING (true);
