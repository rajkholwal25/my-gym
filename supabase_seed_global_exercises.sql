-- Seed ~7 global exercises per muscle group (created_by = NULL so all users see them).
-- Run in Supabase SQL Editor after supabase_admin_dashboard.sql (exercises.created_by exists).
-- When a user selects e.g. Chest in weekly schedule and opens that day, they see these + their own custom exercises.

INSERT INTO exercises (name, muscle_group, image_url, video_url, difficulty, equipment, created_by) VALUES
-- CHEST (7)
('Bench Press', 'chest', 'https://images.unsplash.com/photo-1534368959876-26bf04f2c947?w=400&h=240&fit=crop', NULL, 'intermediate', 'barbell', NULL),
('Incline Dumbbell Press', 'chest', 'https://images.unsplash.com/photo-1581009146145-b84ef30149ce?w=400&h=240&fit=crop', NULL, 'intermediate', 'dumbbells', NULL),
('Cable Fly', 'chest', 'https://images.unsplash.com/photo-1581009146145-b84ef30149ce?w=400&h=240&fit=crop', NULL, 'beginner', 'cable', NULL),
('Push-Up', 'chest', 'https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=400&h=240&fit=crop', NULL, 'beginner', 'bodyweight', NULL),
('Dumbbell Pullover', 'chest', 'https://images.unsplash.com/photo-1534368959876-26bf04f2c947?w=400&h=240&fit=crop', NULL, 'intermediate', 'dumbbells', NULL),
('Decline Bench Press', 'chest', 'https://images.unsplash.com/photo-1581009146145-b84ef30149ce?w=400&h=240&fit=crop', NULL, 'intermediate', 'barbell', NULL),
('Pec Deck Fly', 'chest', 'https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=400&h=240&fit=crop', NULL, 'beginner', 'machine', NULL),
-- SHOULDERS (7)
('Overhead Press', 'shoulders', 'https://images.unsplash.com/photo-1605296867424-35fc25c9212a?w=400&h=240&fit=crop', NULL, 'intermediate', 'barbell', NULL),
('Lateral Raise', 'shoulders', 'https://images.unsplash.com/photo-1605296867424-35fc25c9212a?w=400&h=240&fit=crop', NULL, 'beginner', 'dumbbells', NULL),
('Front Raise', 'shoulders', 'https://images.unsplash.com/photo-1605296867424-35fc25c9212a?w=400&h=240&fit=crop', NULL, 'beginner', 'dumbbells', NULL),
('Face Pull', 'shoulders', 'https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=400&h=240&fit=crop', NULL, 'beginner', 'cable', NULL),
('Arnold Press', 'shoulders', 'https://images.unsplash.com/photo-1605296867424-35fc25c9212a?w=400&h=240&fit=crop', NULL, 'intermediate', 'dumbbells', NULL),
('Reverse Fly', 'shoulders', 'https://images.unsplash.com/photo-1605296867424-35fc25c9212a?w=400&h=240&fit=crop', NULL, 'beginner', 'dumbbells', NULL),
('Upright Row', 'shoulders', 'https://images.unsplash.com/photo-1605296867424-35fc25c9212a?w=400&h=240&fit=crop', NULL, 'intermediate', 'barbell', NULL),
-- BACK (7)
('Deadlift', 'back', 'https://images.unsplash.com/photo-1541534741688-6078c6bfb5c5?w=400&h=240&fit=crop', NULL, 'intermediate', 'barbell', NULL),
('Barbell Row', 'back', 'https://images.unsplash.com/photo-1541534741688-6078c6bfb5c5?w=400&h=240&fit=crop', NULL, 'intermediate', 'barbell', NULL),
('Lat Pulldown', 'back', 'https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=400&h=240&fit=crop', NULL, 'beginner', 'cable', NULL),
('Pull-Up', 'back', 'https://images.unsplash.com/photo-1541534741688-6078c6bfb5c5?w=400&h=240&fit=crop', NULL, 'intermediate', 'bodyweight', NULL),
('Dumbbell Row', 'back', 'https://images.unsplash.com/photo-1541534741688-6078c6bfb5c5?w=400&h=240&fit=crop', NULL, 'beginner', 'dumbbells', NULL),
('Seated Cable Row', 'back', 'https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=400&h=240&fit=crop', NULL, 'beginner', 'cable', NULL),
('T-Bar Row', 'back', 'https://images.unsplash.com/photo-1541534741688-6078c6bfb5c5?w=400&h=240&fit=crop', NULL, 'intermediate', 'barbell', NULL),
-- BICEPS (7)
('Barbell Curl', 'biceps', 'https://images.unsplash.com/photo-1583454110551-21f2fa2afe61?w=400&h=240&fit=crop', NULL, 'beginner', 'barbell', NULL),
('Hammer Curl', 'biceps', 'https://images.unsplash.com/photo-1598971639050-f3c2a04e1b24?w=400&h=240&fit=crop', NULL, 'beginner', 'dumbbells', NULL),
('Preacher Curl', 'biceps', 'https://images.unsplash.com/photo-1583454110551-21f2fa2afe61?w=400&h=240&fit=crop', NULL, 'beginner', 'barbell', NULL),
('Cable Curl', 'biceps', 'https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=400&h=240&fit=crop', NULL, 'beginner', 'cable', NULL),
('Concentration Curl', 'biceps', 'https://images.unsplash.com/photo-1598971639050-f3c2a04e1b24?w=400&h=240&fit=crop', NULL, 'beginner', 'dumbbells', NULL),
('Incline Dumbbell Curl', 'biceps', 'https://images.unsplash.com/photo-1598971639050-f3c2a04e1b24?w=400&h=240&fit=crop', NULL, 'beginner', 'dumbbells', NULL),
('Spider Curl', 'biceps', 'https://images.unsplash.com/photo-1583454110551-21f2fa2afe61?w=400&h=240&fit=crop', NULL, 'intermediate', 'barbell', NULL),
-- TRICEPS (7)
('Tricep Pushdown', 'triceps', 'https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=400&h=240&fit=crop', NULL, 'beginner', 'cable', NULL),
('Skull Crusher', 'triceps', 'https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=400&h=240&fit=crop', NULL, 'intermediate', 'barbell', NULL),
('Overhead Tricep Extension', 'triceps', 'https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=400&h=240&fit=crop', NULL, 'beginner', 'dumbbells', NULL),
('Close-Grip Bench Press', 'triceps', 'https://images.unsplash.com/photo-1534368959876-26bf04f2c947?w=400&h=240&fit=crop', NULL, 'intermediate', 'barbell', NULL),
('Dips', 'triceps', 'https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=400&h=240&fit=crop', NULL, 'intermediate', 'bodyweight', NULL),
('Tricep Kickback', 'triceps', 'https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=400&h=240&fit=crop', NULL, 'beginner', 'dumbbells', NULL),
('Diamond Push-Up', 'triceps', 'https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=400&h=240&fit=crop', NULL, 'beginner', 'bodyweight', NULL),
-- LEGS (7)
('Squats', 'legs', 'https://images.unsplash.com/photo-1598289431512-b97b0917affc?w=400&h=240&fit=crop', NULL, 'beginner', 'barbell', NULL),
('Leg Press', 'legs', 'https://images.unsplash.com/photo-1598289431512-b97b0917affc?w=400&h=240&fit=crop', NULL, 'beginner', 'machine', NULL),
('Romanian Deadlift', 'legs', 'https://images.unsplash.com/photo-1541534741688-6078c6bfb5c5?w=400&h=240&fit=crop', NULL, 'intermediate', 'barbell', NULL),
('Lunges', 'legs', 'https://images.unsplash.com/photo-1598289431512-b97b0917affc?w=400&h=240&fit=crop', NULL, 'beginner', 'dumbbells', NULL),
('Leg Curl', 'legs', 'https://images.unsplash.com/photo-1598289431512-b97b0917affc?w=400&h=240&fit=crop', NULL, 'beginner', 'machine', NULL),
('Leg Extension', 'legs', 'https://images.unsplash.com/photo-1598289431512-b97b0917affc?w=400&h=240&fit=crop', NULL, 'beginner', 'machine', NULL),
('Calf Raise', 'legs', 'https://images.unsplash.com/photo-1598289431512-b97b0917affc?w=400&h=240&fit=crop', NULL, 'beginner', 'machine', NULL),
-- CORE (7)
('Plank', 'core', 'https://images.unsplash.com/photo-1518611012118-696072aa579a?w=400&h=240&fit=crop', NULL, 'beginner', 'bodyweight', NULL),
('Crunches', 'core', 'https://images.unsplash.com/photo-1518611012118-696072aa579a?w=400&h=240&fit=crop', NULL, 'beginner', 'bodyweight', NULL),
('Russian Twist', 'core', 'https://images.unsplash.com/photo-1518611012118-696072aa579a?w=400&h=240&fit=crop', NULL, 'beginner', 'bodyweight', NULL),
('Leg Raise', 'core', 'https://images.unsplash.com/photo-1518611012118-696072aa579a?w=400&h=240&fit=crop', NULL, 'beginner', 'bodyweight', NULL),
('Bicycle Crunch', 'core', 'https://images.unsplash.com/photo-1518611012118-696072aa579a?w=400&h=240&fit=crop', NULL, 'beginner', 'bodyweight', NULL),
('Mountain Climber', 'core', 'https://images.unsplash.com/photo-1518611012118-696072aa579a?w=400&h=240&fit=crop', NULL, 'intermediate', 'bodyweight', NULL),
('Dead Bug', 'core', 'https://images.unsplash.com/photo-1518611012118-696072aa579a?w=400&h=240&fit=crop', NULL, 'beginner', 'bodyweight', NULL);
