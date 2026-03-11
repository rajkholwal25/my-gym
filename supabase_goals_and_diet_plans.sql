-- Run this in Supabase SQL Editor — adds goals + diet_plans tables and seed data

-- 1. goals table
CREATE TABLE IF NOT EXISTS goals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL UNIQUE,
  display_order INTEGER DEFAULT 0
);

-- 2. diet_plans table
CREATE TABLE IF NOT EXISTS diet_plans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  goal_id UUID NOT NULL REFERENCES goals(id) ON DELETE CASCADE,
  day_name TEXT NOT NULL,
  day_order INTEGER NOT NULL,
  title TEXT,
  content TEXT NOT NULL,
  UNIQUE(goal_id, day_name)
);

-- 3. RLS
ALTER TABLE goals ENABLE ROW LEVEL SECURITY;
ALTER TABLE diet_plans ENABLE ROW LEVEL SECURITY;

-- 4. Policies (drop first if re-running)
DROP POLICY IF EXISTS "Allow public read on goals" ON goals;
CREATE POLICY "Allow public read on goals" ON goals FOR SELECT USING (true);

DROP POLICY IF EXISTS "Allow public read on diet_plans" ON diet_plans;
CREATE POLICY "Allow public read on diet_plans" ON diet_plans FOR SELECT USING (true);

-- 5. Seed goals
INSERT INTO goals (name, display_order) VALUES
  ('Muscle gain', 1),
  ('Weight loss', 2),
  ('Endurance', 3),
  ('General fitness', 4),
  ('Strength', 5)
ON CONFLICT (name) DO NOTHING;

-- 6. Seed weekly diet plans per goal
DO $$
DECLARE
  g_muscle UUID; g_weight UUID; g_endurance UUID; g_general UUID; g_strength UUID;
BEGIN
  SELECT id INTO g_muscle FROM goals WHERE name = 'Muscle gain' LIMIT 1;
  SELECT id INTO g_weight FROM goals WHERE name = 'Weight loss' LIMIT 1;
  SELECT id INTO g_endurance FROM goals WHERE name = 'Endurance' LIMIT 1;
  SELECT id INTO g_general FROM goals WHERE name = 'General fitness' LIMIT 1;
  SELECT id INTO g_strength FROM goals WHERE name = 'Strength' LIMIT 1;

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
