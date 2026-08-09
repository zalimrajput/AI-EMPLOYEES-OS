"use client";

import { useQuery } from "@tanstack/react-query";
import { supabase } from "@/lib/supabase/client";
import type { Session } from "@supabase/supabase-js";

export interface SessionUser {
  id: string;
  email: string;
  name?: string | null;
  orgId?: string | null;
  orgName?: string | null;
  roles: string[];
  /** Module keys enabled for the user's org (both flags on). Empty for super admin. */
  enabledModules?: string[];
}

/**
 * localStorage key holding the workspace the signup form could not create yet
 * because Supabase email confirmation delayed the session. It is created right
 * after the user verifies their inbox and signs in.
 */
export const PENDING_WORKSPACE_KEY = "aios:pending-workspace";

/** The organization the user currently belongs to, or null. */
export async function fetchUserOrgId(userId: string): Promise<string | null> {
  const { data } = await supabase
    .from("users")
    .select("organization_id")
    .eq("id", userId)
    .maybeSingle();
  return (data?.organization_id as string | null) ?? null;
}

/** Fetch the human roles assigned to a user (company roles + platform role). */
export async function fetchUserRoles(userId: string): Promise<string[]> {
  const roles: string[] = [];

  // Company roles via user_roles -> roles (e.g. "Company Admin", "CEO / Executive").
  const { data } = await supabase
    .from("user_roles")
    .select("roles(name)")
    .eq("user_id", userId);
  roles.push(
    ...(data ?? [])
      .map((ur) => (ur.roles as { name?: string } | null)?.name)
      .filter((name): name is string => Boolean(name))
  );

  // Platform role (e.g. "Super Admin").
  const { data: platform } = await supabase
    .from("platform_roles")
    .select("role")
    .eq("user_id", userId);
  roles.push(
    ...(platform ?? [])
      .map((pr) => (pr.role as string | null) ?? null)
      .filter((role): role is string => Boolean(role))
  );

  return roles;
}

export function useSession() {
  return useQuery({
    queryKey: ["session"],
    queryFn: async (): Promise<{ session: Session | null; user: SessionUser | null }> => {
      const {
        data: { session },
      } = await supabase.auth.getSession();
      if (!session) return { session: null, user: null };

      let name: string | null = null;
      let orgId: string | null = null;
      let orgName: string | null = null;

      const { data: profile } = await supabase
        .from("users")
        .select("full_name, organization_id")
        .eq("id", session.user.id)
        .maybeSingle();

      if (profile) {
        name = profile.full_name ?? null;
        orgId = profile.organization_id ?? null;
      }

      if (orgId) {
        const { data: org } = await supabase
          .from("organizations")
          .select("name")
          .eq("id", orgId)
          .maybeSingle();
        orgName = org?.name ?? null;
      }

      const roles = await fetchUserRoles(session.user.id);

      // Org-enabled modules (both flags on). Super admin has no org — leave
      // empty so module filters treat everything as enabled.
      let enabledModules: string[] | undefined;
      if (orgId) {
        const { data: mods, error: modsError } = await supabase
          .from("org_modules")
          .select("module_key, enabled_by_super_admin, enabled_by_org_admin")
          .eq("organization_id", orgId);
        // On error, stay undefined (treat all as enabled) rather than hiding
        // every module behind an empty array.
        if (!modsError) {
          enabledModules = (mods ?? [])
            .filter(
              (m) => m.enabled_by_super_admin !== false && m.enabled_by_org_admin !== false
            )
            .map((m) => m.module_key as string);
        }
      }

      return {
        session,
        user: {
          id: session.user.id,
          email: session.user.email ?? "",
          name,
          orgId,
          orgName,
          roles,
          enabledModules,
        },
      };
    },
  });
}

export async function signIn(email: string, password: string) {
  const { data, error } = await supabase.auth.signInWithPassword({ email, password });
  if (error) throw error;
  return data;
}

export async function signUp(email: string, password: string, fullName?: string) {
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: fullName ? { data: { full_name: fullName } } : undefined,
  });
  if (error) throw error;
  return data;
}

export async function signOut() {
  await supabase.auth.signOut();
}
