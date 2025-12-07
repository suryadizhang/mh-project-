-- Create feedback.review_status enum (needed for feedback.customer_reviews table)
CREATE TYPE feedback.review_status AS ENUM ('pending', 'approved', 'rejected', 'flagged');
