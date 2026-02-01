-- Verify chef_assignment_alerts table exists
SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_name = 'chef_assignment_alerts';

-- Show table structure
\d ops.chef_assignment_alerts
