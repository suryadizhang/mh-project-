-- Grant permissions on agreement tables to staging user
GRANT SELECT, INSERT, UPDATE, DELETE ON core.agreement_templates TO myhibachi_staging_user;
GRANT SELECT, INSERT ON core.signed_agreements TO myhibachi_staging_user;
GRANT SELECT, INSERT ON core.agreement_variable_values TO myhibachi_staging_user;
GRANT SELECT, INSERT ON core.agreement_audit_log TO myhibachi_staging_user;
GRANT USAGE ON SCHEMA core TO myhibachi_staging_user;
