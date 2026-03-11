-- Run in Supabase SQL Editor (once). Enables "Show on home" + sequence order.
-- show_on_home: only one global exercise per muscle can be shown on the home page; admin picks which.
-- sequence_order: admin sets order (1, 2, 3...) so users see the ideal sequence for each muscle group.

ALTER TABLE exercises
  ADD COLUMN IF NOT EXISTS show_on_home BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE exercises
  ADD COLUMN IF NOT EXISTS sequence_order INTEGER NOT NULL DEFAULT 0;
