-- One-job-per-minute WTMM ZIP scanner schedule.
-- Prerequisites: deploy wtmm-mod-scan, apply mod_scan_sequential_queue.sql,
-- and create a random 64-hex-character Vault secret wtmm_scan_cron_token.
-- The actual key never belongs in GitHub or in the browser.
create extension if not exists pg_net with schema extensions;
create extension if not exists pg_cron;

select cron.schedule(
  'wtmm-mod-scan-serial',
  '* * * * *',
  $job$
    select net.http_post(
      url := 'https://ovvubbwzxikqcnuvvtjb.supabase.co/functions/v1/wtmm-mod-scan',
      headers := jsonb_build_object(
        'Content-Type','application/json',
        'x-wtmm-internal-token',(
          select decrypted_secret from vault.decrypted_secrets
          where name='wtmm_scan_cron_token' limit 1
        )
      ),
      body := '{}'::jsonb,
      timeout_milliseconds := 90000
    );
  $job$
);
-- To pause: select cron.unschedule('wtmm-mod-scan-serial');
