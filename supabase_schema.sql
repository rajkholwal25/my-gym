-- Run this in Supabase SQL Editor to create tables for "My Gym"

-- 1. users_profile
CREATE TABLE IF NOT EXISTS users_profile (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT,
  is_admin BOOLEAN NOT NULL DEFAULT FALSE,
  age INTEGER,
  weight INTEGER,
  height INTEGER,
  goal TEXT,
  reset_token_hash TEXT,
  reset_token_expires TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. exercises
CREATE TABLE IF NOT EXISTS exercises (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  muscle_group TEXT NOT NULL,
  image_url TEXT,
  video_url TEXT,
  difficulty TEXT,
  equipment TEXT,
  created_by UUID REFERENCES users_profile(id) ON DELETE SET NULL
);

-- 3. weekly_schedule
CREATE TABLE IF NOT EXISTS weekly_schedule (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users_profile(id) ON DELETE CASCADE,
  day TEXT NOT NULL,
  muscle_group TEXT NOT NULL,
  UNIQUE(user_id, day)
);

-- 4. workout_logs
CREATE TABLE IF NOT EXISTS workout_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users_profile(id) ON DELETE CASCADE,
  exercise_id UUID NOT NULL REFERENCES exercises(id) ON DELETE CASCADE,
  duration_minutes INTEGER NOT NULL,
  calories_burned INTEGER DEFAULT 0,
  workout_date TIMESTAMPTZ DEFAULT NOW()
);

-- 5. goals (options for user goal at signup: muscle gain, weight loss, etc.)
CREATE TABLE IF NOT EXISTS goals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL UNIQUE,
  display_order INTEGER DEFAULT 0
);

-- 6. diet_plans (weekly diet plan per goal: one row per day per goal)
CREATE TABLE IF NOT EXISTS diet_plans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  goal_id UUID NOT NULL REFERENCES goals(id) ON DELETE CASCADE,
  day_name TEXT NOT NULL,
  day_order INTEGER NOT NULL,
  title TEXT,
  content TEXT NOT NULL,
  UNIQUE(goal_id, day_name)
);

-- Enable RLS (optional; configure policies in Supabase dashboard as needed)
ALTER TABLE users_profile ENABLE ROW LEVEL SECURITY;
ALTER TABLE exercises ENABLE ROW LEVEL SECURITY;
ALTER TABLE weekly_schedule ENABLE ROW LEVEL SECURITY;
ALTER TABLE workout_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE goals ENABLE ROW LEVEL SECURITY;
ALTER TABLE diet_plans ENABLE ROW LEVEL SECURITY;

-- Allow public read for exercises
CREATE POLICY "Allow public read on exercises" ON exercises FOR SELECT USING (true);

-- Allow all for demo (tighten in production)
CREATE POLICY "Allow all users_profile" ON users_profile FOR ALL USING (true);
CREATE POLICY "Allow all weekly_schedule" ON weekly_schedule FOR ALL USING (true);
CREATE POLICY "Allow all workout_logs" ON workout_logs FOR ALL USING (true);
CREATE POLICY "Allow public read on goals" ON goals FOR SELECT USING (true);
CREATE POLICY "Allow public read on diet_plans" ON diet_plans FOR SELECT USING (true);

-- Seed goals (run after goals table exists)
INSERT INTO goals (name, display_order) VALUES
  ('Muscle gain', 1),
  ('Weight loss', 2),
  ('Endurance', 3),
  ('General fitness', 4),
  ('Strength', 5)
ON CONFLICT (name) DO NOTHING;

-- Seed diet_plans: weekly plan per goal (run after goals exist; get goal ids from goals table or use by name)
-- For simplicity we insert by goal name via a subquery. If your Supabase doesn't support that, run INSERTs with explicit UUIDs after selecting from goals.
DO $$
DECLARE
  g_muscle UUID; g_weight UUID; g_endurance UUID; g_general UUID; g_strength UUID;
BEGIN
  SELECT id INTO g_muscle FROM goals WHERE name = 'Muscle gain' LIMIT 1;
  SELECT id INTO g_weight FROM goals WHERE name = 'Weight loss' LIMIT 1;
  SELECT id INTO g_endurance FROM goals WHERE name = 'Endurance' LIMIT 1;
  SELECT id INTO g_general FROM goals WHERE name = 'General fitness' LIMIT 1;
  SELECT id INTO g_strength FROM goals WHERE name = 'Strength' LIMIT 1;

  -- Muscle gain weekly plan
  IF g_muscle IS NOT NULL THEN
    INSERT INTO diet_plans (goal_id, day_name, day_order, title, content) VALUES
      (g_muscle, 'Monday', 1, 'High protein + carbs', 'Breakfast: Oats, eggs, banana. Lunch: Chicken, rice, greens. Dinner: Fish, sweet potato, salad. Snacks: Greek yogurt, nuts.'),
      (g_muscle, 'Tuesday', 2, 'Protein focus', 'Breakfast: Eggs, whole grain toast. Lunch: Lean beef, quinoa, broccoli. Dinner: Paneer/ tofu, dal, roti. Snacks: Protein shake, fruit.'),
      (g_muscle, 'Wednesday', 3, 'Recovery meals', 'Breakfast: Smoothie with protein. Lunch: Turkey, brown rice. Dinner: Grilled chicken, veggies. Snacks: Cottage cheese, almonds.'),
      (g_muscle, 'Thursday', 4, 'Calorie surplus', 'Breakfast: Oats, peanut butter, milk. Lunch: Rice, dal, chicken curry. Dinner: Salmon, rice, beans. Snacks: Dry fruits, milk.'),
      (g_muscle, 'Friday', 5, 'Pre-workout carbs', 'Breakfast: Banana, eggs, toast. Lunch: Pasta, chicken, salad. Dinner: Rice, fish, greens. Snacks: Dates, nuts.'),
      (g_muscle, 'Saturday', 6, 'Balanced', 'Breakfast: Paratha, curd. Lunch: Biryani/ rice, raita, salad. Dinner: Grilled meat, sweet potato. Snacks: Protein bar.'),
      (g_muscle, 'Sunday', 7, 'Rest day nutrition', 'Breakfast: Eggs, avocado. Lunch: Rice, dal, sabzi. Dinner: Chicken soup, bread. Snacks: Fruit, nuts.')
    ON CONFLICT (goal_id, day_name) DO NOTHING;
  END IF;

  -- Weight loss weekly plan
  IF g_weight IS NOT NULL THEN
    INSERT INTO diet_plans (goal_id, day_name, day_order, title, content) VALUES
      (g_weight, 'Monday', 1, 'Low carb', 'Breakfast: Eggs, spinach. Lunch: Salad with grilled chicken. Dinner: Fish, steamed veggies. Snacks: Cucumber, green tea.'),
      (g_weight, 'Tuesday', 2, 'High fibre', 'Breakfast: Oats, berries. Lunch: Dal, sabzi, small roti. Dinner: Soup, salad. Snacks: Apple, nuts (small).'),
      (g_weight, 'Wednesday', 3, 'Protein + veg', 'Breakfast: Poha, chai. Lunch: Chicken breast, broccoli. Dinner: Grilled fish, salad. Snacks: Buttermilk.'),
      (g_weight, 'Thursday', 4, 'Calorie deficit', 'Breakfast: Smoothie (no sugar). Lunch: Quinoa, veggies. Dinner: Lentil soup, salad. Snacks: Carrots, hummus.'),
      (g_weight, 'Friday', 5, 'Light meals', 'Breakfast: Idli, sambar. Lunch: Brown rice, dal, sabzi. Dinner: Grilled chicken, greens. Snacks: Fruit.'),
      (g_weight, 'Saturday', 6, 'Balanced low-cal', 'Breakfast: Daliya, milk. Lunch: Chapati, veg curry. Dinner: Paneer, salad. Snacks: Green tea.'),
      (g_weight, 'Sunday', 7, 'Rest day', 'Breakfast: Omelette, tomato. Lunch: Rice, dal, minimal oil. Dinner: Soup, salad. Snacks: Nuts (small portion).')
    ON CONFLICT (goal_id, day_name) DO NOTHING;
  END IF;

  -- Endurance weekly plan
  IF g_endurance IS NOT NULL THEN
    INSERT INTO diet_plans (goal_id, day_name, day_order, title, content) VALUES
      (g_endurance, 'Monday', 1, 'Carbs + electrolytes', 'Breakfast: Oats, banana, honey. Lunch: Rice, potato, chicken. Dinner: Pasta, salad. Snacks: Banana, electrolyte drink.'),
      (g_endurance, 'Tuesday', 2, 'Energy focus', 'Breakfast: Toast, peanut butter, fruit. Lunch: Rice, dal, sabzi. Dinner: Sweet potato, fish. Snacks: Dates, nuts.'),
      (g_endurance, 'Wednesday', 3, 'Recovery', 'Breakfast: Smoothie, oats. Lunch: Quinoa, veggies. Dinner: Rice, chicken. Snacks: Yogurt, fruit.'),
      (g_endurance, 'Thursday', 4, 'Complex carbs', 'Breakfast: Daliya, milk. Lunch: Brown rice, dal. Dinner: Pasta, lean meat. Snacks: Energy bar.'),
      (g_endurance, 'Friday', 5, 'Pre-long session', 'Breakfast: Oats, banana. Lunch: Rice, potato, veggies. Dinner: Rice, fish. Snacks: Dry fruits.'),
      (g_endurance, 'Saturday', 6, 'Balanced', 'Breakfast: Paratha, curd. Lunch: Rice, curry. Dinner: Chicken, rice. Snacks: Fruit.'),
      (g_endurance, 'Sunday', 7, 'Rest', 'Breakfast: Eggs, toast. Lunch: Dal, roti, sabzi. Dinner: Soup, bread. Snacks: Nuts.')
    ON CONFLICT (goal_id, day_name) DO NOTHING;
  END IF;

  -- General fitness weekly plan
  IF g_general IS NOT NULL THEN
    INSERT INTO diet_plans (goal_id, day_name, day_order, title, content) VALUES
      (g_general, 'Monday', 1, 'Balanced', 'Breakfast: Oats or eggs. Lunch: Rice/roti, dal, sabzi, protein. Dinner: Grilled meat/fish, veggies. Snacks: Fruit, nuts.'),
      (g_general, 'Tuesday', 2, 'Variety', 'Breakfast: Idli/dosa, chutney. Lunch: Chapati, chicken/ paneer. Dinner: Rice, fish, salad. Snacks: Yogurt.'),
      (g_general, 'Wednesday', 3, 'Whole foods', 'Breakfast: Poha, fruit. Lunch: Rice, dal, curry. Dinner: Chicken, broccoli. Snacks: Almonds.'),
      (g_general, 'Thursday', 4, 'Protein + veg', 'Breakfast: Eggs, toast. Lunch: Quinoa, veggies. Dinner: Dal, roti, sabzi. Snacks: Milk.'),
      (g_general, 'Friday', 5, 'Flexible', 'Breakfast: Smoothie. Lunch: Rice, curry. Dinner: Grilled fish, salad. Snacks: Fruit.'),
      (g_general, 'Saturday', 6, 'Weekend', 'Breakfast: Paratha, curd. Lunch: Biryani/ rice, raita. Dinner: Chicken, veggies. Snacks: Protein shake.'),
      (g_general, 'Sunday', 7, 'Rest day', 'Breakfast: Omelette. Lunch: Dal, roti. Dinner: Soup, salad. Snacks: Nuts.')
    ON CONFLICT (goal_id, day_name) DO NOTHING;
  END IF;

  -- Strength weekly plan
  IF g_strength IS NOT NULL THEN
    INSERT INTO diet_plans (goal_id, day_name, day_order, title, content) VALUES
      (g_strength, 'Monday', 1, 'Heavy protein', 'Breakfast: Eggs, oats, milk. Lunch: Beef/chicken, rice, greens. Dinner: Fish, sweet potato. Snacks: Cottage cheese.'),
      (g_strength, 'Tuesday', 2, 'Recovery', 'Breakfast: Protein shake, banana. Lunch: Dal, roti, chicken. Dinner: Paneer, rice. Snacks: Nuts.'),
      (g_strength, 'Wednesday', 3, 'Carbs + protein', 'Breakfast: Oats, peanut butter. Lunch: Rice, curry, meat. Dinner: Chicken, potato. Snacks: Yogurt.'),
      (g_strength, 'Thursday', 4, 'Full meals', 'Breakfast: Eggs, toast, fruit. Lunch: Rice, dal, sabzi, fish. Dinner: Grilled meat, veggies. Snacks: Milk.'),
      (g_strength, 'Friday', 5, 'Pre-workout', 'Breakfast: Banana, eggs. Lunch: Pasta, chicken. Dinner: Rice, fish. Snacks: Dates.'),
      (g_strength, 'Saturday', 6, 'Training day', 'Breakfast: Oats, nuts. Lunch: Rice, curry. Dinner: Chicken, sweet potato. Snacks: Protein bar.'),
      (g_strength, 'Sunday', 7, 'Rest', 'Breakfast: Eggs, avocado. Lunch: Dal, roti. Dinner: Soup, chicken. Snacks: Fruit.')
    ON CONFLICT (goal_id, day_name) DO NOTHING;
  END IF;
END $$;

-- Seed exercises (run after tables exist)
INSERT INTO exercises (name, muscle_group, image_url, video_url, difficulty, equipment) VALUES
  ('Bench Press', 'chest', 'https://images.unsplash.com/photo-1534368959876-26bf04f2c947?w=400&h=240&fit=crop', 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4', 'intermediate', 'barbell'),
  ('Incline Dumbbell Press', 'chest', 'https://images.unsplash.com/photo-1581009146145-b84ef30149ce?w=400&h=240&fit=crop', 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4', 'intermediate', 'dumbbells'),
  ('Barbell Curl', 'biceps', 'https://images.unsplash.com/photo-1583454110551-21f2fa2afe61?w=400&h=240&fit=crop', 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4', 'beginner', 'barbell'),
  ('Hammer Curl', 'biceps', 'https://images.unsplash.com/photo-1598971639050-f3c2a04e1b24?w=400&h=240&fit=crop', NULL, 'beginner', 'dumbbells'),
  ('Squats', 'legs', 'https://images.unsplash.com/photo-1598289431512-b97b0917affc?w=400&h=240&fit=crop', NULL, 'beginner', 'barbell'),
  ('Deadlift', 'back', 'https://images.unsplash.com/photo-1541534741688-6078c6bfb5c5?w=400&h=240&fit=crop', NULL, 'intermediate', 'barbell'),
  ('Overhead Press', 'shoulders', 'https://images.unsplash.com/photo-1605296867424-35fc25c9212a?w=400&h=240&fit=crop', NULL, 'intermediate', 'barbell'),
  ('Tricep Pushdown', 'triceps', 'https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=400&h=240&fit=crop', NULL, 'beginner', 'cable'),
  ('Plank', 'core', 'https://images.unsplash.com/photo-1518611012118-696072aa579a?w=400&h=240&fit=crop', NULL, 'beginner', 'bodyweight');
