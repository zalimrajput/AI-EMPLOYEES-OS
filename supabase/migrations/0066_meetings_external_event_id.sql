-- Meetings may reference the Google Calendar event they were synced to.
-- Nullable: the internal meeting always exists even when Calendar sync is
-- not connected or fails (scheduling must never hard-fail).
ALTER TABLE meetings
    ADD COLUMN external_event_id TEXT;
