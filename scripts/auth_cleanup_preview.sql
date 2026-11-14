-- Read-only. Use a private psql variables file; never put credentials here.
\set ON_ERROR_STOP on
\if :{?allow_disposable}
\else
  \set allow_disposable false
\endif
BEGIN READ ONLY;
SET LOCAL statement_timeout = '10s';
SELECT current_database() = 'phishlens_dev'
  AND (:'HOST' = 'ep-soft-fog-b3orfa8a.c-4.ap-southeast-1.aws.neon.tech'
       OR (:'allow_disposable' = 'true' AND :'HOST' IN ('127.0.0.1', 'localhost')))
  AS correct_database \gset
\if :correct_database
\else
  ROLLBACK;
  DO $$BEGIN RAISE EXCEPTION 'Expected confirmed direct staging host and phishlens_dev'; END$$;
\endif
WITH expected(alias, subject, user_id) AS (
  VALUES ('a', :'account_a_subject', :'account_a_user_id'::uuid),
         ('b', :'account_b_subject', :'account_b_user_id'::uuid)
)
SELECT e.alias, e.user_id AS recorded_user_id,
       u.id IS NOT NULL AS exact_mapping_found,
       COALESCE(u.email = 'demo@phishlens.test', false) AS is_demo_identity,
       count(a.id) AS remaining_reports,
       COALESCE(json_agg(a.id) FILTER (WHERE a.id IS NOT NULL), '[]') AS remaining_report_ids
FROM expected e
LEFT JOIN users u ON u.id = e.user_id AND u.neon_auth_subject = e.subject
LEFT JOIN analyzed_emails a ON a.user_id = u.id
GROUP BY e.alias, e.user_id, u.id, u.email ORDER BY e.alias;
ROLLBACK;
