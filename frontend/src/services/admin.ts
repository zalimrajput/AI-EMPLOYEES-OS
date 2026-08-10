import { supabase } from "@/lib/supabase/client";
import type {
  DepartmentCreate,
  OrgDepartment,
  OrgMember,
  OrgModuleRow,
  OrgRole,
  OrgWithStats,
  PlatformOverview,
} from "@/lib/api/types";
import { api } from "@/lib/api/client";

async function getCurrentOrgId(): Promise<string | null> {
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) return null;
  const { data } = await supabase
    .from("users")
    .select("organization_id")
    .eq("id", user.id)
    .maybeSingle();
  return (data?.organization_id as string) ?? null;
}

// ── Platform (super admin) ─────────────────────────────────

/** All organizations with member counts and module settings (super admin only). */
export async function fetchPlatformOrgs(): Promise<OrgWithStats[]> {
  const [orgs, users, modules] = await Promise.all([
    supabase.from("organizations").select("*").order("created_at", { ascending: false }),
    supabase.from("users").select("id, organization_id"),
    supabase.from("org_modules").select("*"),
  ]);

  if (orgs.error || users.error || modules.error) {
    throw new Error(
      orgs.error?.message ?? users.error?.message ?? modules.error?.message ?? "Failed to load organizations"
    );
  }

  const userCounts: Record<string, number> = {};
  for (const u of users.data ?? []) {
    const oid = u.organization_id as string | null;
    if (oid) userCounts[oid] = (userCounts[oid] ?? 0) + 1;
  }

  const modulesByOrg: Record<string, OrgModuleRow[]> = {};
  for (const m of (modules.data ?? []) as OrgModuleRow[]) {
    (modulesByOrg[m.organization_id] ??= []).push(m);
  }

  return (orgs.data ?? []).map((o) => ({
    id: o.id as string,
    name: o.name as string,
    slug: o.slug as string,
    industry: (o.industry as string | null) ?? null,
    country: (o.country as string | null) ?? null,
    plan: (o.plan as string) ?? "Trial",
    status: (o.status as string) ?? "active",
    max_users: (o.max_users as number | null) ?? null,
    storage_limit_gb: (o.storage_limit_gb as number | null) ?? null,
    created_at: o.created_at as string,
    users: userCounts[o.id as string] ?? 0,
    modules: modulesByOrg[o.id as string] ?? [],
  }));
}

/**
 * Platform-level numbers for the Super Admin dashboard:
 * subscription plans, AI employees (models), integrations, dashboards.
 * Super admin RLS grants cross-tenant reads, so counts are global.
 */
export async function fetchPlatformOverview(): Promise<PlatformOverview> {
  const [plans, aiModels, integrations, dashboards] = await Promise.all([
    supabase.from("plans").select("*").order("price_monthly", { ascending: true }),
    supabase.from("ai_employees").select("id", { count: "exact", head: true }),
    supabase.from("integrations").select("id", { count: "exact", head: true }),
    supabase.from("dashboards").select("id", { count: "exact", head: true }),
  ]);

  if (plans.error || aiModels.error || integrations.error || dashboards.error) {
    throw new Error(
      plans.error?.message ??
        aiModels.error?.message ??
        integrations.error?.message ??
        dashboards.error?.message ??
        "Failed to load platform overview"
    );
  }

  return {
    plans: (plans.data ?? []) as PlatformOverview["plans"],
    aiModels: aiModels.count ?? 0,
    integrations: integrations.count ?? 0,
    dashboards: dashboards.count ?? 0,
  };
}

/** Toggle a module flag for an organization (super admin: enabled_by_super_admin). */
export async function updateOrgModule(
  orgId: string,
  moduleKey: string,
  patch: Partial<Pick<OrgModuleRow, "enabled_by_super_admin" | "enabled_by_org_admin">>
): Promise<{ error: string | null }> {
  if (patch.enabled_by_super_admin !== undefined) {
    try {
      await api.updateOrgModuleAdmin(orgId, moduleKey, patch.enabled_by_super_admin);
      return { error: null };
    } catch (err) {
      return { error: (err as Error).message };
    }
  }
  // Fallback path (org-admin flag via direct DB) kept for safety.
  const { error } = await supabase
    .from("org_modules")
    .update({ ...patch, updated_at: new Date().toISOString() })
    .eq("organization_id", orgId)
    .eq("module_key", moduleKey);
  return { error: error?.message ?? null };
}

/** Update an organization's plan/status (super admin). */
export async function updateOrgMeta(
  orgId: string,
  patch: Partial<Pick<OrgWithStats, "plan" | "status">>
): Promise<{ error: string | null }> {
  const { error } = await supabase
    .from("organizations")
    .update(patch)
    .eq("id", orgId);
  return { error: error?.message ?? null };
}

// ── Organization (org admin) ───────────────────────────────

/** The current org's module settings (org admin toggles enabled_by_org_admin). */
export async function fetchOrgModules(): Promise<OrgModuleRow[]> {
  const orgId = await getCurrentOrgId();
  if (!orgId) return [];
  const { data, error } = await supabase
    .from("org_modules")
    .select("*")
    .eq("organization_id", orgId);
  if (error) throw new Error(error.message);
  return (data ?? []) as OrgModuleRow[];
}

/** Toggle a module the org admin controls (enabled_by_org_admin) via the backend. */
export async function updateMyOrgModule(
  moduleKey: string,
  enabled: boolean
): Promise<{ error: string | null }> {
  try {
    await api.updateMyModule(moduleKey, enabled);
    return { error: null };
  } catch (err) {
    const message = (err as Error).message ?? "";
    // Only fall back to a direct DB update when the backend is unreachable.
    // A 400 (e.g. "disabled by platform admin") must NOT be bypassed.
    if (!message.includes("Could not reach the backend")) {
      return { error: message };
    }
    const orgId = await getCurrentOrgId();
    if (!orgId) return { error: message };
    const { error } = await supabase
      .from("org_modules")
      .update({ enabled_by_org_admin: enabled, updated_at: new Date().toISOString() })
      .eq("organization_id", orgId)
      .eq("module_key", moduleKey);
    return { error: error?.message ?? null };
  }
}

/** All roles defined for the current org. */
export async function fetchOrgRoles(): Promise<OrgRole[]> {
  const orgId = await getCurrentOrgId();
  if (!orgId) return [];
  const { data, error } = await supabase
    .from("roles")
    .select("id, name, description, permissions")
    .eq("organization_id", orgId)
    .order("name", { ascending: true });
  if (error) throw new Error(error.message);
  return (data ?? []) as OrgRole[];
}

/** All members of the current org with their role names. */
export async function fetchOrgMembers(): Promise<OrgMember[]> {
  const orgId = await getCurrentOrgId();
  if (!orgId) return [];

  const [users, userRoles] = await Promise.all([
    supabase
      .from("users")
      .select("id, full_name, email, avatar_url, status, created_at")
      .eq("organization_id", orgId)
      .order("created_at", { ascending: true }),
    supabase
      .from("user_roles")
      .select("user_id, roles(name)")
      .eq("organization_id", orgId),
  ]);

  if (users.error || userRoles.error) {
    throw new Error(users.error?.message ?? userRoles.error?.message ?? "Failed to load members");
  }

  const rolesByUser: Record<string, string[]> = {};
  for (const ur of userRoles.data ?? []) {
    const name = (ur.roles as { name?: string } | null)?.name;
    const uid = ur.user_id as string;
    if (name) (rolesByUser[uid] ??= []).push(name);
  }

  return (users.data ?? []).map((u) => ({
    id: u.id as string,
    full_name: (u.full_name as string | null) ?? null,
    email: (u.email as string | null) ?? null,
    avatar_url: (u.avatar_url as string | null) ?? null,
    status: (u.status as string) ?? "active",
    created_at: u.created_at as string,
    roles: rolesByUser[u.id as string] ?? [],
  }));
}

/** Invite a member (org admin) — creates the Auth user + assigns a role. */
export async function inviteMember(input: {
  organization_id: string;
  full_name: string;
  email: string;
  password: string;
  role_name: string;
}): Promise<{ error: string | null }> {
  try {
    await api.createUser(input);
    return { error: null };
  } catch (err) {
    return { error: (err as Error).message };
  }
}

/** Delete a member (org admin). */
export async function removeMember(userId: string): Promise<{ error: string | null }> {
  try {
    await api.deleteUser(userId);
    return { error: null };
  } catch (err) {
    return { error: (err as Error).message };
  }
}

// ── Departments (org admin) ────────────────────────────────

/** All departments of the current org. */
export async function fetchOrgDepartments(): Promise<OrgDepartment[]> {
  try {
    return await api.fetchDepartments();
  } catch (err) {
    const message = (err as Error).message ?? "";
    // Only fall back to a direct Supabase read on a network failure — real
    // server errors (403/500) must surface, not be masked.
    if (!message.includes("Could not reach the backend")) {
      throw err;
    }
    const orgId = await getCurrentOrgId();
    if (!orgId) return [];
    const { data, error } = await supabase
      .from("departments")
      .select("*")
      .eq("organization_id", orgId)
      .order("name", { ascending: true });
    if (error) throw new Error(error.message);
    return (data ?? []) as OrgDepartment[];
  }
}

/** Create a department (org admin). */
export async function addDepartment(
  input: DepartmentCreate
): Promise<{ error: string | null }> {
  try {
    await api.createDepartment(input);
    return { error: null };
  } catch (err) {
    return { error: (err as Error).message };
  }
}

/** Delete a department (org admin). */
export async function removeDepartment(
  departmentId: string
): Promise<{ error: string | null }> {
  try {
    await api.deleteDepartment(departmentId);
    return { error: null };
  } catch (err) {
    return { error: (err as Error).message };
  }
}

/** Connect an integration by submitting the token manually. */
export async function connectIntegrationToken(input: {
  provider: string;
  access_token: string;
  refresh_token?: string;
}): Promise<{ error: string | null }> {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    const token = session?.access_token;
    if (!token) throw new Error("Not authenticated");
    const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";
    const res = await fetch(`${BACKEND_URL}/api/v1/integrations/connect-token`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
      },
      body: JSON.stringify(input)
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail ?? "Failed to connect integration");
    }
    return { error: null };
  } catch (err) {
    return { error: (err as Error).message };
  }
}

/** Disconnect an integration by deleting the row. */
export async function disconnectIntegration(integrationId: string): Promise<{ error: string | null }> {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    const token = session?.access_token;
    if (!token) throw new Error("Not authenticated");
    const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";
    const res = await fetch(`${BACKEND_URL}/api/v1/integrations/${integrationId}`, {
      method: "DELETE",
      headers: {
        "Authorization": `Bearer ${token}`
      }
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail ?? "Failed to disconnect integration");
    }
    return { error: null };
  } catch (err) {
    return { error: (err as Error).message };
  }
}

