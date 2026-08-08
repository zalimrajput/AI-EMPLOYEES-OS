-- Email threads may be classified by the AI classify_email_thread tool.
-- One nullable text column keeps the classification optional and non-blocking:
-- threads are usable/persisted even before (or without) any classification.
ALTER TABLE email_threads
    ADD COLUMN category TEXT;