'use client';

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import {
  Activity, AlertTriangle, Bot, Database, Flag, Gavel, HeartPulse,
  Radio, ShieldAlert, Wrench,
} from 'lucide-react';
import { fetchApi } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

type Service = { status: string; error_summary?: string | null; latency_ms?: number | null };
type GovernanceOverview = {
  status: string;
  generated_at: string;
  services: Record<string, Service>;
  active_incidents: Array<{ id: string; title: string; severity: string; status: string; affected_service?: string | null }>;
  pending_actions: {
    critical_tickets: number;
    failed_jobs_24h: Array<{ id: string; name: string; failure_category?: string | null }>;
    pending_sensitive_access: Array<{ id: string; resource_type: string }>;
    degraded_services: Array<{ name: string; status: string; error_summary?: string | null }>;
  };
  maintenance: { is_enabled: boolean; scope?: string | null; enabled_at?: string | null };
  recent_activity: Array<{ id: string; timestamp?: string | null; action: string; result: string; actor_email: string; reason?: string | null }>;
};

const SERVICE_LABELS: Record<string, { label: string; icon: typeof Activity }> = {
  api: { label: 'API', icon: Activity },
  database: { label: 'Database', icon: Database },
  llm_provider: { label: 'AI', icon: Bot },
  rag: { label: 'RAG', icon: Database },
  notifications: { label: 'Notifications', icon: Radio },
  scheduler: { label: 'Scheduler', icon: HeartPulse },
};

function statusClass(status: string) {
  if (status === 'healthy') return 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300';
  if (status === 'not_monitored') return 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300';
  return 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300';
}

export default function GovernancePage() {
  const { can } = useAuth();
  const { data, isLoading, error } = useQuery<GovernanceOverview>({
    queryKey: ['governance-overview'],
    queryFn: () => fetchApi('/api/v1/admin/governance/overview'),
    staleTime: 15_000,
    refetchInterval: 60_000,
    retry: false,
  });

  const controls = [
    { label: 'Maintenance mode', href: '/settings', icon: Wrench, allowed: can('maintenance:manage') || can('settings.manage') },
    { label: 'Feature flags', href: '/feature-flags', icon: Flag, allowed: can('feature_flags.manage') },
    { label: 'AI configuration', href: '/ai-config', icon: Bot, allowed: can('ai_config.manage') || can('ai.manage') },
    { label: 'Announcements', href: '/announcements', icon: Radio, allowed: can('announcements.manage') || can('support.manage') },
  ].filter((control) => control.allowed);

  if (error) {
    return <div className="p-6 text-sm text-destructive">Governance data could not be loaded. No operational counts are shown until the API responds.</div>;
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-bold tracking-tight"><Gavel className="h-7 w-7 text-blue-600" /> Governance Center</h1>
        <p className="text-sm text-muted-foreground">Live operational attention, privileged changes, and controls backed by MedNarrate services.</p>
      </div>

      <section>
        <h2 className="mb-3 text-base font-semibold">Operational status</h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {isLoading ? Array.from({ length: 6 }).map((_, index) => <Skeleton key={index} className="h-28" />) : Object.entries(SERVICE_LABELS).map(([key, meta]) => {
            const service = data?.services[key];
            const Icon = meta.icon;
            return <Card key={key}><CardHeader className="flex flex-row items-center justify-between pb-2"><CardTitle className="text-sm">{meta.label}</CardTitle><Icon className="h-4 w-4 text-muted-foreground" /></CardHeader><CardContent>{service ? <><Badge className={statusClass(service.status)}>{service.status.replace('_', ' ')}</Badge>{service.latency_ms !== undefined && service.latency_ms !== null && <p className="mt-2 text-xs text-muted-foreground">{service.latency_ms} ms</p>}{service.error_summary && <p className="mt-2 text-xs text-muted-foreground">{service.error_summary}</p>}</> : <span className="text-sm text-muted-foreground">Unavailable</span>}</CardContent></Card>;
          })}
        </div>
      </section>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2 text-lg"><ShieldAlert className="h-5 w-5 text-rose-600" /> Active incidents</CardTitle><CardDescription>Unresolved incidents, ordered by severity and creation time.</CardDescription></CardHeader>
          <CardContent className="space-y-3">{isLoading ? <Skeleton className="h-24" /> : data?.active_incidents.length ? data.active_incidents.map((incident) => <Link key={incident.id} href="/incidents" className="block rounded-md border p-3 hover:bg-muted/50"><div className="flex justify-between gap-3"><span className="font-medium">{incident.title}</span><Badge variant="destructive">{incident.severity}</Badge></div><p className="mt-1 text-xs text-muted-foreground">{incident.status}{incident.affected_service ? ` · ${incident.affected_service}` : ''}</p></Link>) : <p className="py-6 text-center text-sm text-muted-foreground">No active incidents.</p>}</CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2 text-lg"><AlertTriangle className="h-5 w-5 text-amber-600" /> Pending operational actions</CardTitle><CardDescription>Only current, query-backed work that may require attention.</CardDescription></CardHeader>
          <CardContent className="space-y-3">{isLoading ? <Skeleton className="h-24" /> : <>
            <Link href="/support" className="flex items-center justify-between rounded-md border p-3 hover:bg-muted/50"><span>Unresolved P1/P2 tickets</span><Badge variant={data?.pending_actions.critical_tickets ? 'destructive' : 'secondary'}>{data?.pending_actions.critical_tickets}</Badge></Link>
            <Link href="/automation-ops" className="flex items-center justify-between rounded-md border p-3 hover:bg-muted/50"><span>Failed jobs in last 24 hours</span><Badge variant={data?.pending_actions.failed_jobs_24h.length ? 'destructive' : 'secondary'}>{data?.pending_actions.failed_jobs_24h.length}</Badge></Link>
            <Link href="/breakglass" className="flex items-center justify-between rounded-md border p-3 hover:bg-muted/50"><span>Pending sensitive-access requests</span><Badge variant={data?.pending_actions.pending_sensitive_access.length ? 'destructive' : 'secondary'}>{data?.pending_actions.pending_sensitive_access.length}</Badge></Link>
            <Link href="/health" className="flex items-center justify-between rounded-md border p-3 hover:bg-muted/50"><span>Degraded or unknown monitored services</span><Badge variant={data?.pending_actions.degraded_services.length ? 'destructive' : 'secondary'}>{data?.pending_actions.degraded_services.length}</Badge></Link>
          </>}</CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader><CardTitle className="text-lg">Change controls</CardTitle><CardDescription>{data?.maintenance.is_enabled ? `Maintenance mode is enabled${data.maintenance.scope ? ` for ${data.maintenance.scope}` : ''}.` : 'Maintenance mode is currently disabled.'}</CardDescription></CardHeader>
        <CardContent className="flex flex-wrap gap-2">{controls.length ? controls.map((control) => { const Icon = control.icon; return <Link key={control.href} href={control.href}><Button variant="outline"><Icon className="mr-2 h-4 w-4" />{control.label}</Button></Link>; }) : <p className="text-sm text-muted-foreground">You do not have permission to change operational controls.</p>}</CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle className="text-lg">Recent governance activity</CardTitle><CardDescription>Privileged configuration, access, and account changes from the audit log.</CardDescription></CardHeader>
        <CardContent>{isLoading ? <Skeleton className="h-40" /> : data?.recent_activity.length ? <div className="divide-y rounded-md border">{data.recent_activity.map((activity) => <div key={activity.id} className="grid gap-1 p-3 sm:grid-cols-[1fr_auto]"><div><p className="font-mono text-xs text-blue-700 dark:text-blue-300">{activity.action}</p><p className="text-sm">{activity.actor_email}{activity.reason ? ` · ${activity.reason}` : ''}</p></div><div className="text-xs text-muted-foreground">{activity.timestamp ? new Date(activity.timestamp).toLocaleString() : '—'}</div></div>)}</div> : <p className="py-6 text-center text-sm text-muted-foreground">No privileged governance activity recorded yet.</p>}</CardContent>
      </Card>
    </div>
  );
}
