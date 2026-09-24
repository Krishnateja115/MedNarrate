/* eslint-disable */
'use client';

import { useQuery } from '@tanstack/react-query';
import { fetchApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Shield, ShieldAlert, Lock, AlertTriangle, Key, Users, Activity } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';

interface SecurityOverview {
  active_admins_count: number;
  active_roles_count: number;
  active_sensitive_grants_count: number;
  recent_security_events_count: number;
  system_security_status: string;
}

interface SecurityEvent {
  id: string;
  timestamp: string;
  actor_admin_id: string | null;
  actor_email?: string;
  event: string;
  result: string;
  ip_address: string | null;
  reason: string | null;
  request_id: string | null;
  sensitive_access_flag: boolean;
}

export default function SecurityOverviewPage() {
  const { data: overview, isLoading: isLoadingOverview } = useQuery<SecurityOverview>({
    queryKey: ['security-overview'],
    queryFn: () => fetchApi('/api/v1/admin/security/overview'),
  });

  const { data: eventsData, isLoading: isLoadingEvents } = useQuery<{ events: SecurityEvent[] }>({
    queryKey: ['security-events'],
    queryFn: () => fetchApi('/api/v1/admin/security/events?limit=20'),
  });

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 flex items-center gap-2">
          <Shield className="w-7 h-7 text-blue-600" /> Security Center Overview
        </h1>
        <p className="text-slate-500 dark:text-slate-400 text-sm">
          Real-time security governance, RBAC status, active temporary sensitive access grants, and audit events.
        </p>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600 dark:text-slate-400">Active Admins</CardTitle>
            <Users className="w-4 h-4 text-slate-500" />
          </CardHeader>
          <CardContent>
            {isLoadingOverview ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <div className="text-2xl font-bold">{overview?.active_admins_count ?? 0}</div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600 dark:text-slate-400">Active RBAC Roles</CardTitle>
            <Lock className="w-4 h-4 text-slate-500" />
          </CardHeader>
          <CardContent>
            {isLoadingOverview ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <div className="text-2xl font-bold">{overview?.active_roles_count ?? 0}</div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600 dark:text-slate-400">Active Break-Glass Grants</CardTitle>
            <Key className="w-4 h-4 text-amber-500" />
          </CardHeader>
          <CardContent>
            {isLoadingOverview ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <div className="text-2xl font-bold text-amber-600 dark:text-amber-400">
                {overview?.active_sensitive_grants_count ?? 0}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600 dark:text-slate-400">Security Status</CardTitle>
            <Activity className="w-4 h-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            {isLoadingOverview ? (
              <Skeleton className="h-8 w-24" />
            ) : (
              <Badge className="bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300 font-semibold px-2.5 py-1">
                {overview?.system_security_status ?? 'SECURE'}
              </Badge>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Security Events Timeline */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg font-semibold flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-blue-600" /> Real-time Security Events Timeline
          </CardTitle>
          <CardDescription>
            Audit log events including admin logins, role changes, privilege escalations, and sensitive access requests.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoadingEvents ? (
            <div className="space-y-3">
              {[1, 2, 3, 4].map((i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : !eventsData?.events || eventsData.events.length === 0 ? (
            <div className="text-center py-8 text-slate-500 text-sm">No security events recorded yet.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="text-xs uppercase bg-slate-50 dark:bg-slate-900 text-slate-500">
                  <tr>
                    <th className="px-4 py-3">Timestamp</th>
                    <th className="px-4 py-3">Actor</th>
                    <th className="px-4 py-3">Event / Action</th>
                    <th className="px-4 py-3">Result</th>
                    <th className="px-4 py-3">IP Address</th>
                    <th className="px-4 py-3">Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                  {eventsData.events.map((evt) => (
                    <tr key={evt.id} className="hover:bg-slate-50 dark:hover:bg-slate-900/50">
                      <td className="px-4 py-3 text-slate-500 whitespace-nowrap">
                        {evt.timestamp ? new Date(evt.timestamp).toLocaleString() : 'N/A'}
                      </td>
                      <td className="px-4 py-3 font-medium text-slate-900 dark:text-slate-100">
                        {evt.actor_email || evt.actor_admin_id || 'System'}
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-blue-600 dark:text-blue-400">
                        {evt.event}
                      </td>
                      <td className="px-4 py-3">
                        <Badge
                          variant={evt.result === 'success' ? 'default' : 'destructive'}
                          className={evt.result === 'success' ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300' : ''}
                        >
                          {evt.result}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-slate-500 font-mono text-xs">
                        {evt.ip_address || 'Internal'}
                      </td>
                      <td className="px-4 py-3 text-slate-600 dark:text-slate-400 truncate max-w-xs">
                        {evt.reason || '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
