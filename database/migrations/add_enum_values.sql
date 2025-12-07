-- Add missing enum values
ALTER TYPE newsletter.template_source ADD VALUE IF NOT EXISTS 'admin';
ALTER TYPE newsletter.template_source ADD VALUE IF NOT EXISTS 'ai';
ALTER TYPE communications.template_source ADD VALUE IF NOT EXISTS 'admin';
ALTER TYPE communications.template_source ADD VALUE IF NOT EXISTS 'ai';
