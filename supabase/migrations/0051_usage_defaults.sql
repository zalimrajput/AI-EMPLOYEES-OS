-- 0051_usage_defaults.sql
-- Apply plan storage limits to storage_quotas whenever a subscription is
-- created or its plan changes (Basic=1GB, Pro=20GB, Business=200GB).

CREATE OR REPLACE FUNCTION public.apply_plan_defaults()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    storage_gb INTEGER;
BEGIN
    SELECT storage_limit_gb INTO storage_gb
    FROM public.plans
    WHERE id = NEW.plan_id;

    INSERT INTO public.storage_quotas (organization_id, max_storage_bytes, used_storage_bytes)
    VALUES (NEW.organization_id, COALESCE(storage_gb, 1) * 1073741824, 0)
    ON CONFLICT (organization_id)
    DO UPDATE SET max_storage_bytes = EXCLUDED.max_storage_bytes,
                  updated_at = NOW();

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_apply_plan_defaults ON subscriptions;
CREATE TRIGGER trg_apply_plan_defaults
    AFTER INSERT OR UPDATE OF plan_id ON subscriptions
    FOR EACH ROW
    EXECUTE FUNCTION public.apply_plan_defaults();
