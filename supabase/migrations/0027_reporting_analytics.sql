-- 0027_reporting_analytics.sql
-- AI CEO Dashboard + Reporting + Business Analytics


CREATE TABLE IF NOT EXISTS dashboards (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID NOT NULL
    REFERENCES organizations(id)
    ON DELETE CASCADE,

    name TEXT NOT NULL,

    description TEXT,

    layout JSONB DEFAULT '{}'::jsonb,

    created_by UUID
    REFERENCES users(id)
    ON DELETE SET NULL,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    updated_at TIMESTAMPTZ DEFAULT NOW()

);



CREATE TABLE IF NOT EXISTS reports (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID NOT NULL
    REFERENCES organizations(id)
    ON DELETE CASCADE,

    name TEXT NOT NULL,

    report_type TEXT NOT NULL,

    parameters JSONB DEFAULT '{}'::jsonb,

    result JSONB DEFAULT '{}'::jsonb,

    ai_summary TEXT,

    generated_by UUID
    REFERENCES ai_employees(id)
    ON DELETE SET NULL,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    updated_at TIMESTAMPTZ DEFAULT NOW()

);



CREATE TABLE IF NOT EXISTS analytics_events (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID NOT NULL
    REFERENCES organizations(id)
    ON DELETE CASCADE,

    event_type TEXT NOT NULL,

    entity_type TEXT,

    entity_id UUID,

    metadata JSONB DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ DEFAULT NOW()

);



CREATE TABLE IF NOT EXISTS business_metrics (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID NOT NULL
    REFERENCES organizations(id)
    ON DELETE CASCADE,

    metric_name TEXT NOT NULL,

    metric_value NUMERIC DEFAULT 0,

    metric_unit TEXT,

    period DATE,

    metadata JSONB DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ DEFAULT NOW()

);



-- Indexes

CREATE INDEX IF NOT EXISTS analytics_dashboards_org_idx
ON dashboards(organization_id);



CREATE INDEX IF NOT EXISTS analytics_reports_org_idx
ON reports(organization_id);



CREATE INDEX IF NOT EXISTS analytics_events_org_idx
ON analytics_events(organization_id);



CREATE INDEX IF NOT EXISTS business_metrics_org_idx
ON business_metrics(organization_id);



CREATE INDEX IF NOT EXISTS analytics_events_type_idx
ON analytics_events(event_type);



CREATE INDEX IF NOT EXISTS business_metrics_name_idx
ON business_metrics(metric_name);