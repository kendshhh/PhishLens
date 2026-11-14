-- Destructive only after separate authorization and successful private preview.
-- This never removes Auth provider accounts; a named Auth administrator does that.
\set ON_ERROR_STOP on
\if :{?allow_disposable}
\else
  \set allow_disposable false
\endif
\if :{?authorize_cleanup}
\else
  \echo 'Missing explicit cleanup authorization flag; stopped.'
  DO $$BEGIN RAISE EXCEPTION 'Cleanup authorization flag required'; END$$;
\endif
SELECT :'authorize_cleanup' = 'true' AS authorized \gset
\if :authorized
\else
  DO $$BEGIN RAISE EXCEPTION 'Cleanup authorization flag must be true'; END$$;
\endif
BEGIN;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '10s';
SELECT current_database() = 'phishlens_dev'
  AND (:'HOST' = 'ep-soft-fog-b3orfa8a.c-4.ap-southeast-1.aws.neon.tech'
       OR (:'allow_disposable' = 'true' AND :'HOST' IN ('127.0.0.1', 'localhost')))
  AND :'account_a_subject' <> '' AND :'account_b_subject' <> ''
  AND :'account_a_subject' <> :'account_b_subject'
  AND :'account_a_user_id'::uuid <> :'account_b_user_id'::uuid AS inputs_valid \gset
\if :inputs_valid
\else
  ROLLBACK;
  DO $$BEGIN RAISE EXCEPTION 'Cleanup target or recorded identities invalid'; END$$;
\endif
-- Lock the exact users before checking for dependent reports. Concurrent inserts
-- must not slip between the dependent-row check and the user DELETE cascade.
SELECT u.id FROM users u
JOIN (VALUES (:'account_a_subject', :'account_a_user_id'::uuid),
             (:'account_b_subject', :'account_b_user_id'::uuid)) e(subject, user_id)
  ON u.id = e.user_id AND u.neon_auth_subject = e.subject
ORDER BY u.id FOR UPDATE OF u;
WITH expected(subject, user_id) AS (
  VALUES (:'account_a_subject', :'account_a_user_id'::uuid),
         (:'account_b_subject', :'account_b_user_id'::uuid)
)
SELECT count(*) = 2
  AND bool_and(u.email <> 'demo@phishlens.test')
  AND bool_and(NOT EXISTS (SELECT 1 FROM analyzed_emails a WHERE a.user_id = u.id))
  AS safe_to_remove
FROM users u JOIN expected e ON u.id = e.user_id AND u.neon_auth_subject = e.subject \gset
\if :safe_to_remove
\else
  ROLLBACK;
  \echo 'Identity mismatch, missing mapping, demo identity, or remaining reports; stopped.'
  DO $$BEGIN RAISE EXCEPTION 'Exact zero-report non-demo mappings required'; END$$;
\endif
WITH removed AS (
  DELETE FROM users u
  USING (VALUES (:'account_a_subject', :'account_a_user_id'::uuid),
                (:'account_b_subject', :'account_b_user_id'::uuid)) e(subject, user_id)
  WHERE u.id = e.user_id AND u.neon_auth_subject = e.subject
    AND u.email <> 'demo@phishlens.test'
  RETURNING u.id
)
SELECT count(*) = 2 AS both_removed FROM removed \gset
\if :both_removed
  COMMIT;
\else
  ROLLBACK;
  DO $$BEGIN RAISE EXCEPTION 'Expected exactly two removed mappings'; END$$;
\endif
