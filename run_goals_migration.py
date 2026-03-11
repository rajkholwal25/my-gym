"""
Run this once to create goals and diet_plans tables + seed data in Supabase.
Uses DATABASE_URL from .env (direct Postgres connection).

Set in .env:
  DATABASE_URL=postgresql://postgres.PROJECT_REF:PASSWORD@aws-1-ap-south-1.pooler.supabase.com:6543/postgres

Get PROJECT_REF from your Supabase URL (e.g. jpqjactosfnxiuxkepfn from https://jpqjactosfnxiuxkepfn.supabase.co).
Get PASSWORD from Supabase Dashboard -> Project Settings -> Database -> Database password.
"""
import os
import sys
from pathlib import Path

# Load .env from project root
env_path = Path(__file__).resolve().parent / ".env"
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(env_path)

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set in .env")
    print("Add: DATABASE_URL=postgresql://postgres.PROJECT_REF:YOUR_DB_PASSWORD@aws-1-ap-south-1.pooler.supabase.com:6543/postgres")
    sys.exit(1)

try:
    import psycopg2
except ImportError:
    print("Install psycopg2: pip install psycopg2-binary")
    sys.exit(1)

DDL = """
CREATE TABLE IF NOT EXISTS goals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL UNIQUE,
  display_order INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS diet_plans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  goal_id UUID NOT NULL REFERENCES goals(id) ON DELETE CASCADE,
  day_name TEXT NOT NULL,
  day_order INTEGER NOT NULL,
  title TEXT,
  content TEXT NOT NULL,
  UNIQUE(goal_id, day_name)
);

ALTER TABLE goals ENABLE ROW LEVEL SECURITY;
ALTER TABLE diet_plans ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow public read on goals" ON goals;
CREATE POLICY "Allow public read on goals" ON goals FOR SELECT USING (true);

DROP POLICY IF EXISTS "Allow public read on diet_plans" ON diet_plans;
CREATE POLICY "Allow public read on diet_plans" ON diet_plans FOR SELECT USING (true);
"""

INSERT_GOALS = """
INSERT INTO goals (name, display_order) VALUES
  ('Muscle gain', 1),
  ('Weight loss', 2),
  ('Endurance', 3),
  ('General fitness', 4),
  ('Strength', 5)
ON CONFLICT (name) DO NOTHING;
"""

# Weekly diet plan seed per goal (using subqueries to get goal ids)
DIET_SEED = """
INSERT INTO diet_plans (goal_id, day_name, day_order, title, content)
SELECT g.id, d.day_name, d.day_order, d.title, d.content
FROM (VALUES
  ('Muscle gain', 'Monday', 1, 'High protein + carbs', 'Breakfast: Oats, eggs, banana. Lunch: Chicken, rice, greens. Dinner: Fish, sweet potato, salad. Snacks: Greek yogurt, nuts.'),
  ('Muscle gain', 'Tuesday', 2, 'Protein focus', 'Breakfast: Eggs, whole grain toast. Lunch: Lean beef, quinoa, broccoli. Dinner: Paneer/ tofu, dal, roti. Snacks: Protein shake, fruit.'),
  ('Muscle gain', 'Wednesday', 3, 'Recovery meals', 'Breakfast: Smoothie with protein. Lunch: Turkey, brown rice. Dinner: Grilled chicken, veggies. Snacks: Cottage cheese, almonds.'),
  ('Muscle gain', 'Thursday', 4, 'Calorie surplus', 'Breakfast: Oats, peanut butter, milk. Lunch: Rice, dal, chicken curry. Dinner: Salmon, rice, beans. Snacks: Dry fruits, milk.'),
  ('Muscle gain', 'Friday', 5, 'Pre-workout carbs', 'Breakfast: Banana, eggs, toast. Lunch: Pasta, chicken, salad. Dinner: Rice, fish, greens. Snacks: Dates, nuts.'),
  ('Muscle gain', 'Saturday', 6, 'Balanced', 'Breakfast: Paratha, curd. Lunch: Biryani/ rice, raita, salad. Dinner: Grilled meat, sweet potato. Snacks: Protein bar.'),
  ('Muscle gain', 'Sunday', 7, 'Rest day nutrition', 'Breakfast: Eggs, avocado. Lunch: Rice, dal, sabzi. Dinner: Chicken soup, bread. Snacks: Fruit, nuts.'),
  ('Weight loss', 'Monday', 1, 'Low carb', 'Breakfast: Eggs, spinach. Lunch: Salad with grilled chicken. Dinner: Fish, steamed veggies. Snacks: Cucumber, green tea.'),
  ('Weight loss', 'Tuesday', 2, 'High fibre', 'Breakfast: Oats, berries. Lunch: Dal, sabzi, small roti. Dinner: Soup, salad. Snacks: Apple, nuts (small).'),
  ('Weight loss', 'Wednesday', 3, 'Protein + veg', 'Breakfast: Poha, chai. Lunch: Chicken breast, broccoli. Dinner: Grilled fish, salad. Snacks: Buttermilk.'),
  ('Weight loss', 'Thursday', 4, 'Calorie deficit', 'Breakfast: Smoothie (no sugar). Lunch: Quinoa, veggies. Dinner: Lentil soup, salad. Snacks: Carrots, hummus.'),
  ('Weight loss', 'Friday', 5, 'Light meals', 'Breakfast: Idli, sambar. Lunch: Brown rice, dal, sabzi. Dinner: Grilled chicken, greens. Snacks: Fruit.'),
  ('Weight loss', 'Saturday', 6, 'Balanced low-cal', 'Breakfast: Daliya, milk. Lunch: Chapati, veg curry. Dinner: Paneer, salad. Snacks: Green tea.'),
  ('Weight loss', 'Sunday', 7, 'Rest day', 'Breakfast: Omelette, tomato. Lunch: Rice, dal, minimal oil. Dinner: Soup, salad. Snacks: Nuts (small portion).'),
  ('Endurance', 'Monday', 1, 'Carbs + electrolytes', 'Breakfast: Oats, banana, honey. Lunch: Rice, potato, chicken. Dinner: Pasta, salad. Snacks: Banana, electrolyte drink.'),
  ('Endurance', 'Tuesday', 2, 'Energy focus', 'Breakfast: Toast, peanut butter, fruit. Lunch: Rice, dal, sabzi. Dinner: Sweet potato, fish. Snacks: Dates, nuts.'),
  ('Endurance', 'Wednesday', 3, 'Recovery', 'Breakfast: Smoothie, oats. Lunch: Quinoa, veggies. Dinner: Rice, chicken. Snacks: Yogurt, fruit.'),
  ('Endurance', 'Thursday', 4, 'Complex carbs', 'Breakfast: Daliya, milk. Lunch: Brown rice, dal. Dinner: Pasta, lean meat. Snacks: Energy bar.'),
  ('Endurance', 'Friday', 5, 'Pre-long session', 'Breakfast: Oats, banana. Lunch: Rice, potato, veggies. Dinner: Rice, fish. Snacks: Dry fruits.'),
  ('Endurance', 'Saturday', 6, 'Balanced', 'Breakfast: Paratha, curd. Lunch: Rice, curry. Dinner: Chicken, rice. Snacks: Fruit.'),
  ('Endurance', 'Sunday', 7, 'Rest', 'Breakfast: Eggs, toast. Lunch: Dal, roti, sabzi. Dinner: Soup, bread. Snacks: Nuts.'),
  ('General fitness', 'Monday', 1, 'Balanced', 'Breakfast: Oats or eggs. Lunch: Rice/roti, dal, sabzi, protein. Dinner: Grilled meat/fish, veggies. Snacks: Fruit, nuts.'),
  ('General fitness', 'Tuesday', 2, 'Variety', 'Breakfast: Idli/dosa, chutney. Lunch: Chapati, chicken/ paneer. Dinner: Rice, fish, salad. Snacks: Yogurt.'),
  ('General fitness', 'Wednesday', 3, 'Whole foods', 'Breakfast: Poha, fruit. Lunch: Rice, dal, curry. Dinner: Chicken, broccoli. Snacks: Almonds.'),
  ('General fitness', 'Thursday', 4, 'Protein + veg', 'Breakfast: Eggs, toast. Lunch: Quinoa, veggies. Dinner: Dal, roti, sabzi. Snacks: Milk.'),
  ('General fitness', 'Friday', 5, 'Flexible', 'Breakfast: Smoothie. Lunch: Rice, curry. Dinner: Grilled fish, salad. Snacks: Fruit.'),
  ('General fitness', 'Saturday', 6, 'Weekend', 'Breakfast: Paratha, curd. Lunch: Biryani/ rice, raita. Dinner: Chicken, veggies. Snacks: Protein shake.'),
  ('General fitness', 'Sunday', 7, 'Rest day', 'Breakfast: Omelette. Lunch: Dal, roti. Dinner: Soup, salad. Snacks: Nuts.'),
  ('Strength', 'Monday', 1, 'Heavy protein', 'Breakfast: Eggs, oats, milk. Lunch: Beef/chicken, rice, greens. Dinner: Fish, sweet potato. Snacks: Cottage cheese.'),
  ('Strength', 'Tuesday', 2, 'Recovery', 'Breakfast: Protein shake, banana. Lunch: Dal, roti, chicken. Dinner: Paneer, rice. Snacks: Nuts.'),
  ('Strength', 'Wednesday', 3, 'Carbs + protein', 'Breakfast: Oats, peanut butter. Lunch: Rice, curry, meat. Dinner: Chicken, potato. Snacks: Yogurt.'),
  ('Strength', 'Thursday', 4, 'Full meals', 'Breakfast: Eggs, toast, fruit. Lunch: Rice, dal, sabzi, fish. Dinner: Grilled meat, veggies. Snacks: Milk.'),
  ('Strength', 'Friday', 5, 'Pre-workout', 'Breakfast: Banana, eggs. Lunch: Pasta, chicken. Dinner: Rice, fish. Snacks: Dates.'),
  ('Strength', 'Saturday', 6, 'Training day', 'Breakfast: Oats, nuts. Lunch: Rice, curry. Dinner: Chicken, sweet potato. Snacks: Protein bar.'),
  ('Strength', 'Sunday', 7, 'Rest', 'Breakfast: Eggs, avocado. Lunch: Dal, roti. Dinner: Soup, chicken. Snacks: Fruit.')
) AS d(goal_name, day_name, day_order, title, content)
JOIN goals g ON g.name = d.goal_name
ON CONFLICT (goal_id, day_name) DO NOTHING;
"""

def main():
    print("Connecting to Supabase Postgres...")
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cur = conn.cursor()
    try:
        print("Creating goals and diet_plans tables + RLS...")
        cur.execute(DDL)
        print("Inserting goals...")
        cur.execute(INSERT_GOALS)
        print("Inserting weekly diet plans per goal...")
        cur.execute(DIET_SEED)
        print("Done. goals and diet_plans are ready.")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()
