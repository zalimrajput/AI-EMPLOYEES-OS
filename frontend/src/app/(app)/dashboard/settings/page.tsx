"use client";

import { useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Building2,
  Check,
  Copy,
  CreditCard,
  KeyRound,
  LayoutDashboard,
  Loader2,
  Lock,
  Plug,
  Shield,
  Trash2,
  UserPlus,
  Users,
  Network,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs } from "@/components/ui/tabs";
import { Avatar } from "@/components/ui/avatar";
import { Skeleton } from "@/components/ui/skeleton";
import { useSession } from "@/hooks/use-session";
import { addDepartment, fetchOrgDepartments, fetchOrgMembers, fetchOrgModules, fetchOrgRoles, inviteMember, removeDepartment, removeMember, updateMyOrgModule } from "@/services/admin";
import { MODULE_BY_KEY, TOGGLEABLE_MODULES } from "@/lib/modules";
import { ROLE_META } from "@/lib/roles";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";

const INTEGRATIONS = [
  { name: "Gmail", desc: "Draft, send & summarize emails", emoji: "📧", connected: true },
  { name: "Outlook", desc: "Microsoft 365 mail & calendar", emoji: "📅", connected: false },
  { name: "WhatsApp Business", desc: "Customer support on WhatsApp", emoji: "💬", connected: true },
  { name: "Google Calendar", desc: "Meetings & scheduling", emoji: "🗓️", connected: true },
  { name: "Slack", desc: "Team notifications & approvals", emoji: "⚡", connected: false },
  { name: "QuickBooks", desc: "Accounting & invoicing sync", emoji: "🧾", connected: false },
  { name: "Stripe", desc: "Payments & billing", emoji: "💳", connected: true },
  { name: "Google Drive", desc: "Document storage & OCR", emoji: "☁️", connected: false },
];

export default function SettingsPage() {
  const { data: session } = useSession();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState("users");
  const [apiKey] = useState("sk-ai-os-••••••••••••••••••••");

  const { data: members, isLoading: membersLoading } = useQuery({
    queryKey: ["org-members"],
    queryFn: fetchOrgMembers,
  });
  const { data: roles, isLoading: rolesLoading } = useQuery({ queryKey: ["org-roles"], queryFn: fetchOrgRoles });
  const { data: orgModules } = useQuery({ queryKey: ["org-modules"], queryFn: fetchOrgModules });
  const { data: departments, isLoading: departmentsLoading } = useQuery({
    queryKey: ["org-departments"],
    queryFn: fetchOrgDepartments,
  });

  const enabledBySuperAdmin = useMemo(() => {
    const map: Record<string, boolean> = {};
    for (const m of orgModules ?? []) map[m.module_key] = m.enabled_by_super_admin !== false;
    return map;
  }, [orgModules]);

  const myOrgId = session?.user?.orgId;

  function copyKey() {
    navigator.clipboard?.writeText(apiKey).catch(() => {});
    toast.success("API key copied");
  }

  async function toggleModule(key: string, enabled: boolean) {
    const { error } = await updateMyOrgModule(key, enabled);
    if (error) return toast.error(error);
    queryClient.invalidateQueries({ queryKey: ["org-modules"] });
    toast.success(`${enabled ? "Enabled" : "Disabled"} ${MODULE_BY_KEY[key]?.name ?? key}`);
  }

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-semibold text-primary-soft">Organization management</p>
        <h1 className="mt-1 text-2xl font-bold tracking-tight text-white md:text-3xl">Settings</h1>
      </div>

      <Tabs
        items={[
          { value: "users", label: "Users", icon: <Users className="h-3.5 w-3.5" /> },
          { value: "departments", label: "Departments", icon: <Network className="h-3.5 w-3.5" /> },
          { value: "modules", label: "Modules", icon: <Plug className="h-3.5 w-3.5" /> },
          { value: "workspace", label: "Workspace", icon: <Building2 className="h-3.5 w-3.5" /> },
          { value: "roles", label: "Roles", icon: <Shield className="h-3.5 w-3.5" /> },
          { value: "api", label: "API Keys", icon: <KeyRound className="h-3.5 w-3.5" /> },
          { value: "billing", label: "Billing", icon: <CreditCard className="h-3.5 w-3.5" /> },
          { value: "integrations", label: "Integrations", icon: <Plug className="h-3.5 w-3.5" /> },
        ]}
        onValueChange={setTab}
        className="flex-wrap"
      />

      <Card className="max-w-3xl">
        {tab === "users" && <UsersTab orgId={myOrgId} roles={roles ?? []} members={members ?? []} loading={membersLoading} />}

        {tab === "departments" && (
          <DepartmentsTab departments={departments ?? []} loading={departmentsLoading} />
        )}

        {tab === "modules" && (
          <>
            <CardHeader>
              <CardTitle>Modules & dashboards</CardTitle>
              <CardDescription>
                Choose which modules your workspace uses. Modules disabled by the platform admin are locked for your company.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="mb-2 flex items-center gap-3 rounded-xl border border-primary/30 bg-primary/10 p-3 opacity-80">
                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-accent text-white">
                  <LayoutDashboard className="h-4 w-4" />
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block text-sm font-bold text-white">Overview</span>
                  <span className="block truncate text-xs text-slate-500">Company-wide overview and quick stats.</span>
                </span>
                <Badge variant="secondary">Always on</Badge>
              </div>
              <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                {TOGGLEABLE_MODULES.map((m) => {
                  const superEnabled = enabledBySuperAdmin[m.key] ?? true;
                  const row = (orgModules ?? []).find((r) => r.module_key === m.key);
                  const enabled = superEnabled && (row ? row.enabled_by_org_admin !== false : true);
                  const Icon = m.icon;
                  return (
                    <button
                      key={m.key}
                      disabled={!superEnabled}
                      onClick={() => toggleModule(m.key, !enabled)}
                      className={cn(
                        "flex items-center gap-3 rounded-xl border p-3 text-left transition-all",
                        superEnabled ? "cursor-pointer hover:border-primary/40" : "cursor-not-allowed opacity-50",
                        enabled ? "border-primary/30 bg-primary/10" : "border-border-soft bg-card-soft/40"
                      )}
                    >
                      <span className={cn(
                        "flex h-9 w-9 shrink-0 items-center justify-center rounded-lg",
                        enabled ? "bg-gradient-to-br from-primary to-accent text-white" : "bg-card-soft text-slate-500"
                      )}>
                        <Icon className="h-4 w-4" />
                      </span>
                      <span className="min-w-0 flex-1">
                        <span className="flex items-center gap-1.5 text-sm font-bold text-white">
                          {m.name}
                          {!superEnabled && <Lock className="h-3 w-3 text-warning" />}
                        </span>
                        <span className="block truncate text-xs text-slate-500">{m.description}</span>
                      </span>
                      <span
                        className={cn(
                          "relative h-5 w-9 shrink-0 rounded-full transition-colors",
                          enabled ? "bg-gradient-to-r from-primary to-accent" : "bg-card-soft"
                        )}
                      >
                        <span
                          className={cn(
                            "absolute top-0.5 h-4 w-4 rounded-full bg-white shadow transition-all",
                            enabled ? "left-4.5" : "left-0.5"
                          )}
                        />
                      </span>
                    </button>
                  );
                })}
              </div>
              <p className="mt-4 flex items-center gap-2 rounded-xl border border-warning/30 bg-warning/10 px-4 py-3 text-xs text-warning">
                <Lock className="h-3.5 w-3.5 shrink-0" />
                Locked modules were disabled by the platform admin — you can&apos;t enable them from here.
              </p>
            </CardContent>
          </>
        )}

        {tab === "workspace" && (
          <>
            <CardHeader>
              <CardTitle>Workspace</CardTitle>
              <CardDescription>Company profile used across emails, quotations and reports.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label>Company name</Label>
                  <Input defaultValue={session?.user?.orgName ?? "Acme Inc."} />
                </div>
                <div className="space-y-2">
                  <Label>Industry</Label>
                  <Input defaultValue="Technology" />
                </div>
                <div className="space-y-2">
                  <Label>Country</Label>
                  <Input defaultValue="United States" />
                </div>
                <div className="space-y-2">
                  <Label>Timezone</Label>
                  <Input defaultValue="UTC-05:00 (EST)" />
                </div>
              </div>
              <Button onClick={() => toast.success("Workspace settings saved")}>
                <Check className="h-4 w-4" /> Save changes
              </Button>
            </CardContent>
          </>
        )}

        {tab === "roles" && (
          <>
            <CardHeader>
              <CardTitle>Roles & permissions</CardTitle>
              <CardDescription>Department-based access control for larger teams.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {(roles ?? []).map((r) => (
                <div key={r.id} className="flex items-center justify-between rounded-xl border border-border-soft bg-card-soft/40 p-4">
                  <div>
                    <p className="text-sm font-bold text-white">{r.name}</p>
                    <p className="text-xs text-slate-500">{r.description}</p>
                  </div>
                  <Badge variant="secondary">
                    {ROLE_META[r.name]?.label ?? r.name}
                  </Badge>
                </div>
              ))}
              {!rolesLoading && (roles ?? []).length === 0 && (
                <p className="py-6 text-center text-sm text-slate-500">No roles defined yet.</p>
              )}
            </CardContent>
          </>
        )}

        {tab === "api" && (
          <>
            <CardHeader>
              <CardTitle>API keys</CardTitle>
              <CardDescription>Programmatic access for ERP integrations and custom workflows.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-2">
                <Input value={apiKey} readOnly className="font-mono" />
                <Button variant="secondary" size="icon" onClick={copyKey} aria-label="Copy key">
                  <Copy className="h-4 w-4" />
                </Button>
              </div>
              <Button onClick={() => toast.success("New API key generated")}>
                <KeyRound className="h-4 w-4" /> Generate new key
              </Button>
            </CardContent>
          </>
        )}

        {tab === "billing" && (
          <>
            <CardHeader>
              <CardTitle>Billing</CardTitle>
              <CardDescription>Your current plan and usage.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="gradient-border rounded-2xl p-[1px]">
                <div className="rounded-2xl bg-card p-5">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-bold text-white">Pro Plan</p>
                      <p className="text-xs text-slate-500">$49/month · 5 users · 10,000 AI requests</p>
                    </div>
                    <Badge variant="accent">Current</Badge>
                  </div>
                </div>
              </div>
              <div className="flex gap-2">
                <Button onClick={() => toast.info("Opening Stripe checkout…")}>Upgrade to Business</Button>
                <Button variant="secondary" onClick={() => toast.info("Usage report coming soon")}>View usage</Button>
              </div>
            </CardContent>
          </>
        )}

        {tab === "integrations" && (
          <>
            <CardHeader>
              <CardTitle>Integrations</CardTitle>
              <CardDescription>Connect the tools your AI employees operate.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-3 sm:grid-cols-2">
                {INTEGRATIONS.map((i) => (
                  <div key={i.name} className="flex items-center gap-3 rounded-xl border border-border-soft bg-card-soft/40 p-4">
                    <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-card text-xl">{i.emoji}</span>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-bold text-white">{i.name}</p>
                      <p className="truncate text-xs text-slate-500">{i.desc}</p>
                    </div>
                    <Badge variant={i.connected ? "success" : "secondary"}>
                      {i.connected ? "Connected" : "Connect"}
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </>
        )}
      </Card>
    </div>
  );
}

// ── Departments tab (org admin: list / create / delete) ───
function DepartmentsTab({
  departments,
  loading,
}: {
  departments: { id: string; name: string; description?: string | null }[];
  loading: boolean;
}) {
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [saving, setSaving] = useState(false);
  const [removingId, setRemovingId] = useState<string | null>(null);
  const [form, setForm] = useState({ name: "", description: "" });

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!form.name.trim()) return toast.error("Department name is required");
    setSaving(true);
    const { error } = await addDepartment({
      name: form.name.trim(),
      description: form.description.trim() || null,
    });
    setSaving(false);
    if (error) return toast.error(error);
    toast.success(`${form.name.trim()} department created`);
    setForm({ name: "", description: "" });
    setShowCreate(false);
    queryClient.invalidateQueries({ queryKey: ["org-departments"] });
  }

  async function handleRemove(deptId: string) {
    setRemovingId(deptId);
    const { error } = await removeDepartment(deptId);
    setRemovingId(null);
    if (error) return toast.error(error);
    toast.success("Department removed");
    queryClient.invalidateQueries({ queryKey: ["org-departments"] });
  }

  return (
    <>
      <CardHeader className="flex-row items-center justify-between">
        <div>
          <CardTitle>Departments</CardTitle>
          <CardDescription>Structure your team into departments so roles and work are assigned by area.</CardDescription>
        </div>
        <Button size="sm" onClick={() => setShowCreate((s) => !s)}>
          <UserPlus className="h-4 w-4" /> Create department
        </Button>
      </CardHeader>
      <CardContent className="space-y-3">
        <AnimatePresence>
          {showCreate && (
            <motion.form
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              onSubmit={handleCreate}
              className="overflow-hidden rounded-xl border border-primary/30 bg-primary/5 p-4"
            >
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <Label>Department name</Label>
                  <Input
                    value={form.name}
                    onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                    placeholder="e.g. Engineering, Sales, Finance"
                  />
                </div>
                <div className="space-y-1.5">
                  <Label>Description (optional)</Label>
                  <Input
                    value={form.description}
                    onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                    placeholder="What this department does"
                  />
                </div>
              </div>
              <div className="mt-3 flex gap-2">
                <Button type="submit" size="sm" disabled={saving}>
                  {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />} Create
                </Button>
                <Button type="button" variant="ghost" size="sm" onClick={() => setShowCreate(false)}>Cancel</Button>
              </div>
            </motion.form>
          )}
        </AnimatePresence>

        {loading ? (
          <div className="space-y-2">
            {[0, 1, 2].map((i) => <Skeleton key={i} className="h-14 w-full" />)}
          </div>
        ) : departments.length === 0 ? (
          <p className="py-6 text-center text-sm text-slate-500">
            No departments yet — create your first one (e.g. Sales, Engineering, Finance).
          </p>
        ) : (
          departments.map((d) => (
            <div key={d.id} className="flex items-center gap-3 rounded-xl border border-border-soft bg-card-soft/40 p-3">
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-secondary text-white">
                <Network className="h-4 w-4" />
              </span>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-bold text-white">{d.name}</p>
                <p className="truncate text-xs text-slate-500">{d.description || "No description"}</p>
              </div>
              <Button
                variant="ghost"
                size="sm"
                className="text-danger hover:text-danger"
                disabled={removingId === d.id}
                onClick={() => handleRemove(d.id)}
                title="Remove department"
              >
                {removingId === d.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
              </Button>
            </div>
          ))
        )}
      </CardContent>
    </>
  );
}

// ── Users tab (org admin: list / invite / delete) ─────────
function UsersTab({
  orgId,
  roles,
  members,
  loading,
}: {
  orgId?: string | null;
  roles: { id: string; name: string }[];
  members: { id: string; full_name?: string | null; email?: string | null; status: string; roles: string[] }[];
  loading: boolean;
}) {
  const queryClient = useQueryClient();
  const [showInvite, setShowInvite] = useState(false);
  const [saving, setSaving] = useState(false);
  const [removingId, setRemovingId] = useState<string | null>(null);
  const [form, setForm] = useState({ full_name: "", email: "", password: "", role_name: "Employee/User" });

  async function handleInvite(e: React.FormEvent) {
    e.preventDefault();
    if (!orgId) return toast.error("No organization bound to your account yet");
    setSaving(true);
    const { error } = await inviteMember({ ...form, organization_id: orgId });
    setSaving(false);
    if (error) return toast.error(error);
    toast.success(`${form.full_name || form.email} added to the team`);
    setForm({ full_name: "", email: "", password: "", role_name: "Employee/User" });
    setShowInvite(false);
    queryClient.invalidateQueries({ queryKey: ["org-members"] });
  }

  async function handleRemove(userId: string) {
    setRemovingId(userId);
    const { error } = await removeMember(userId);
    setRemovingId(null);
    if (error) return toast.error(error);
    toast.success("Member removed");
    queryClient.invalidateQueries({ queryKey: ["org-members"] });
  }

  return (
    <>
      <CardHeader className="flex-row items-center justify-between">
        <div>
          <CardTitle>Team members</CardTitle>
          <CardDescription>People who can command your AI workforce. Roles decide what each member sees.</CardDescription>
        </div>
        <Button size="sm" onClick={() => setShowInvite((s) => !s)}>
          <UserPlus className="h-4 w-4" /> Invite member
        </Button>
      </CardHeader>
      <CardContent className="space-y-3">
        <AnimatePresence>
          {showInvite && (
            <motion.form
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              onSubmit={handleInvite}
              className="overflow-hidden rounded-xl border border-primary/30 bg-primary/5 p-4"
            >
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <Label>Full name</Label>
                  <Input value={form.full_name} onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))} placeholder="Jane Doe" />
                </div>
                <div className="space-y-1.5">
                  <Label>Email</Label>
                  <Input type="email" required value={form.email} onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))} placeholder="jane@company.com" />
                </div>
                <div className="space-y-1.5">
                  <Label>Password</Label>
                  <Input type="password" required minLength={8} value={form.password} onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))} placeholder="Min 8 characters" />
                </div>
                <div className="space-y-1.5">
                  <Label>Role</Label>
                  <select
                    value={form.role_name}
                    onChange={(e) => setForm((f) => ({ ...f, role_name: e.target.value }))}
                    className="h-11 w-full rounded-xl border border-border-soft bg-card-soft/60 px-3 text-sm text-white focus:border-primary/60 focus:outline-none"
                  >
                    {(roles.length > 0 ? roles : [{ id: "emp", name: "Employee/User" }]).map((r) => (
                      <option key={r.id} value={r.name}>{r.name}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="mt-3 flex gap-2">
                <Button type="submit" size="sm" disabled={saving}>
                  {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <UserPlus className="h-4 w-4" />} Add member
                </Button>
                <Button type="button" variant="ghost" size="sm" onClick={() => setShowInvite(false)}>Cancel</Button>
              </div>
            </motion.form>
          )}
        </AnimatePresence>

        {loading ? (
          <div className="space-y-2">
            {[0, 1, 2].map((i) => <Skeleton key={i} className="h-14 w-full" />)}
          </div>
        ) : members.length === 0 ? (
          <p className="py-6 text-center text-sm text-slate-500">No members yet — invite your first teammate.</p>
        ) : (
          members.map((m) => (
            <div key={m.id} className="flex items-center gap-3 rounded-xl border border-border-soft bg-card-soft/40 p-3">
              <Avatar name={m.full_name || m.email || "U"} size="md" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-bold text-white">{m.full_name || "Unnamed member"}</p>
                <p className="truncate text-xs text-slate-500">{m.email}</p>
              </div>
              <div className="flex flex-wrap justify-end gap-1">
                {m.roles.map((r) => (
                  <Badge key={r} variant="secondary">{r}</Badge>
                ))}
                {m.roles.length === 0 && <Badge variant="secondary">No role</Badge>}
              </div>
              <Button
                variant="ghost"
                size="sm"
                className="text-danger hover:text-danger"
                disabled={removingId === m.id}
                onClick={() => handleRemove(m.id)}
                title="Remove member"
              >
                {removingId === m.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
              </Button>
            </div>
          ))
        )}
      </CardContent>
    </>
  );
}
