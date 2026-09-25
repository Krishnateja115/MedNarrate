/* eslint-disable */
'use client';

import { useQuery } from '@tanstack/react-query';
import { fetchApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { BarChart3, Users, FileText, Activity, AlertTriangle, Bot, CheckCircle, XCircle, LifeBuoy, Server, Database, BrainCircuit, HardDrive, Clock, Mail, ShieldAlert } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';

interface DashboardSummary {
  status: string;
  timestamp: string;
  users: {
    total_users: number;
    active_users: number;
    new_users_today: number;
    new_users_this_week: number;
    new_users_this_month: number;
    suspended_users: number;
  };
  reports: {
    reports_today: number;
    reports_this_week: number;
    reports_processing: number;
    reports_failed: number;
    average_processing_time_ms: number;
  };
  analysis: {
    analysis_success_rate: number;
    analysis_failure_count: number;
    failure_categories: Record<string, number>;
  };
  support: {
    open_support_tickets: number;
    p1_tickets: number;
    p2_tickets: number;
    unassigned_tickets: number;
    waiting_for_user: number;
    escalated: number;
  };
  incidents: {
    critical_incidents: number;
    open_incidents: number;
  };
}

interface SystemHealth {
  status: string;
  timestamp: string;
  services: Record<string, {
    status: string;
    last_checked: string;
    latency_ms?: number;
    error_summary?: string;
    details?: any;
  }>;
}

interface Alert {
  id: string;
  type: string;
  title: string;
  description: string;
  severity: 'high' | 'medium';
  timestamp: string;
}

export default function OverviewPage() {
  const { data: summary, isLoading: isLoadingSummary } = useQuery<DashboardSummary>({
    queryKey: ['dashboard-summary'],
    queryFn: () => fetchApi('/api/v1/admin/dashboard/summary'),
    refetchInterval: 60000,
  });

  const { data: health, isLoading: isLoadingHealth } = useQuery<SystemHealth>({
    queryKey: ['system-health'],
    queryFn: () => fetchApi('/api/v1/admin/system/health'),
    refetchInterval: 60000,
  });

  const { data: alertsData, isLoading: isLoadingAlerts } = useQuery<{ alerts: Alert[] }>({
    queryKey: ['dashboard-alerts'],
    queryFn: () => fetchApi('/api/v1/admin/dashboard/alerts'),
    refetchInterval: 60000,
  });

  if (isLoadingSummary || isLoadingHealth || isLoadingAlerts) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Command Center</h1>
          <Skeleton className="h-4 w-48 mt-2" />
        </div>
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <Card key={i}>
              <CardHeader><Skeleton className="h-4 w-1/2" /></CardHeader>
              <CardContent><Skeleton className="h-24 w-full" /></CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (!summary || !health) return null;

  const isHealthy = health.status === 'healthy';

  const formatNumber = (num: number | undefined) => {
    return num !== undefined ? num.toLocaleString() : 'N/A';
  };

  const formatPercent = (num: number | undefined) => {
    return num !== undefined ? `${num.toFixed(1)}%` : 'N/A';
  };

  const ServiceStatus = ({ name, icon: Icon, serviceKey }: { name: string, icon: any, serviceKey: string }) => {
    const service = health.services?.[serviceKey] || { status: 'unknown' };
    const healthy = service.status === 'healthy';
    const down = service.status === 'down';
    
    return (
      <div className="flex items-center justify-between p-3 border rounded-lg bg-card">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-md ${healthy ? 'bg-emerald-100 text-emerald-600 dark:bg-emerald-900/30' : down ? 'bg-destructive/10 text-destructive' : 'bg-orange-100 text-orange-600 dark:bg-orange-900/30'}`}>
            <Icon className="w-4 h-4" />
          </div>
          <div>
            <p className="text-sm font-medium">{name}</p>
            {service.latency_ms !== undefined && <p className="text-xs text-muted-foreground">{service.latency_ms}ms</p>}
          </div>
        </div>
        <Badge variant={healthy ? 'outline' : down ? 'destructive' : 'secondary'} className={healthy ? 'text-emerald-600 border-emerald-200' : ''}>
          {service.status}
        </Badge>
      </div>
    );
  };

  return (
    <div className="space-y-8 fade-in pb-10">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Command Center</h1>
          <p className="text-muted-foreground mt-2">MedNarrate Operations Overview</p>
        </div>
        <div className="flex items-center space-x-3 bg-card p-3 rounded-lg border shadow-sm">
          <span className="text-sm font-medium text-muted-foreground">Platform Status:</span>
          <div className="flex items-center space-x-1.5">
            {isHealthy ? (
              <CheckCircle className="h-4 w-4 text-emerald-500" />
            ) : (
              <AlertTriangle className="h-4 w-4 text-orange-500" />
            )}
            <span className={`font-semibold ${isHealthy ? 'text-emerald-500' : 'text-orange-500'}`}>
              {health.status.toUpperCase()}
            </span>
          </div>
        </div>
      </div>

      {/* SECTION 1 - SYSTEM STATUS */}
      <section>
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2"><Server className="w-5 h-5" /> System Status</h2>
        <div className="grid gap-4 grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6">
          <ServiceStatus name="API" icon={Activity} serviceKey="api" />
          <ServiceStatus name="Database" icon={Database} serviceKey="database" />
          <ServiceStatus name="Storage" icon={HardDrive} serviceKey="storage" />
          <ServiceStatus name="LLM Provider" icon={BrainCircuit} serviceKey="llm_provider" />
          <ServiceStatus name="RAG Service" icon={Bot} serviceKey="rag" />
          <ServiceStatus name="Scheduler" icon={Clock} serviceKey="scheduler" />
        </div>
      </section>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        
        {/* SECTION 2 - USER SUMMARY */}
        <Card className="shadow-sm">
          <CardHeader className="pb-3 border-b bg-slate-50/50 dark:bg-slate-900/50">
            <CardTitle className="flex items-center gap-2 text-lg">
              <Users className="h-5 w-5 text-blue-500" />
              User Summary
            </CardTitle>
          </CardHeader>
          <CardContent className="p-5 space-y-4">
            <div className="flex justify-between items-end border-b pb-4">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Accounts</p>
                <p className="text-3xl font-bold">{formatNumber(summary.users?.total_users)}</p>
              </div>
              <div className="text-right">
                <p className="text-sm font-medium text-emerald-600 dark:text-emerald-400">Active Users</p>
                <p className="text-xl font-bold">{formatNumber(summary.users?.active_users)}</p>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-2 text-center pt-2">
              <div className="bg-slate-50 dark:bg-slate-900 p-2 rounded">
                <p className="text-xs text-muted-foreground mb-1">Today</p>
                <p className="text-lg font-semibold">+{formatNumber(summary.users?.new_users_today)}</p>
              </div>
              <div className="bg-slate-50 dark:bg-slate-900 p-2 rounded">
                <p className="text-xs text-muted-foreground mb-1">This Week</p>
                <p className="text-lg font-semibold">+{formatNumber(summary.users?.new_users_this_week)}</p>
              </div>
              <div className="bg-slate-50 dark:bg-slate-900 p-2 rounded">
                <p className="text-xs text-muted-foreground mb-1">This Month</p>
                <p className="text-lg font-semibold">+{formatNumber(summary.users?.new_users_this_month)}</p>
              </div>
            </div>
            {summary.users?.suspended_users !== undefined && summary.users.suspended_users > 0 && (
              <div className="mt-4 flex items-center justify-between text-sm text-destructive bg-destructive/10 p-2 rounded">
                <span>Suspended Accounts</span>
                <span className="font-bold">{formatNumber(summary.users.suspended_users)}</span>
              </div>
            )}
          </CardContent>
        </Card>

        {/* SECTION 3 - REPORT SUMMARY */}
        <Card className="shadow-sm">
          <CardHeader className="pb-3 border-b bg-slate-50/50 dark:bg-slate-900/50">
            <CardTitle className="flex items-center gap-2 text-lg">
              <FileText className="h-5 w-5 text-indigo-500" />
              Report Processing
            </CardTitle>
          </CardHeader>
          <CardContent className="p-5 space-y-4">
            <div className="grid grid-cols-2 gap-4 border-b pb-4">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Reports Today</p>
                <p className="text-3xl font-bold">{formatNumber(summary.reports?.reports_today)}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Reports This Week</p>
                <p className="text-3xl font-bold">{formatNumber(summary.reports?.reports_this_week)}</p>
              </div>
            </div>
            <div className="space-y-3 pt-2">
              <div className="flex justify-between items-center text-sm">
                <span className="flex items-center gap-2"><Clock className="w-4 h-4 text-blue-500"/> Processing</span>
                <span className="font-medium">{formatNumber(summary.reports?.reports_processing)}</span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="flex items-center gap-2"><CheckCircle className="w-4 h-4 text-emerald-500"/> Completed</span>
                <span className="font-medium text-emerald-600">{summary.reports ? formatNumber(summary.reports.reports_today - summary.reports.reports_failed - summary.reports.reports_processing) : 'N/A'}</span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="flex items-center gap-2"><XCircle className="w-4 h-4 text-destructive"/> Failed</span>
                <span className="font-medium text-destructive">{formatNumber(summary.reports?.reports_failed)}</span>
              </div>
              <div className="pt-2 border-t mt-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Avg Processing Time</span>
                  <span className="font-mono text-sm">{summary.reports?.average_processing_time_ms ? `${(summary.reports.average_processing_time_ms / 1000).toFixed(1)}s` : 'N/A'}</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* SECTION 4 - SUPPORT */}
        <Card className="shadow-sm">
          <CardHeader className="pb-3 border-b bg-slate-50/50 dark:bg-slate-900/50">
            <CardTitle className="flex items-center gap-2 text-lg">
              <LifeBuoy className="h-5 w-5 text-teal-500" />
              Support Desk
            </CardTitle>
          </CardHeader>
          <CardContent className="p-5 space-y-4">
            <div className="flex items-center justify-between border-b pb-4">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Open Tickets</p>
                <p className="text-3xl font-bold">{formatNumber(summary.support?.open_support_tickets)}</p>
              </div>
              <div className="flex gap-2">
                <Badge variant="destructive" className="flex flex-col items-center p-2 h-auto w-16">
                  <span className="text-[10px] uppercase opacity-80">P1</span>
                  <span className="text-lg font-bold">{formatNumber(summary.support?.p1_tickets)}</span>
                </Badge>
                <Badge variant="secondary" className="flex flex-col items-center p-2 h-auto w-16 bg-orange-100 text-orange-700 dark:bg-orange-900/30">
                  <span className="text-[10px] uppercase opacity-80">P2</span>
                  <span className="text-lg font-bold">{formatNumber(summary.support?.p2_tickets)}</span>
                </Badge>
              </div>
            </div>
            <div className="space-y-3 pt-2">
              <div className="flex justify-between items-center text-sm">
                <span className="text-muted-foreground">Unassigned</span>
                <Badge variant="outline">{formatNumber(summary.support?.unassigned_tickets)}</Badge>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-muted-foreground">Waiting for User</span>
                <span className="font-medium">{formatNumber(summary.support?.waiting_for_user)}</span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-muted-foreground">Escalated (Eng)</span>
                <span className="font-medium text-orange-600">{formatNumber(summary.support?.escalated)}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* SECTION 5 - AI & ANALYSIS */}
        <Card className="shadow-sm md:col-span-2 lg:col-span-1">
          <CardHeader className="pb-3 border-b bg-slate-50/50 dark:bg-slate-900/50">
            <CardTitle className="flex items-center gap-2 text-lg">
              <Bot className="h-5 w-5 text-purple-500" />
              AI Operations
            </CardTitle>
          </CardHeader>
          <CardContent className="p-5 space-y-4">
             <div className="flex justify-between items-end pb-4 border-b">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Success Rate</p>
                <p className="text-3xl font-bold text-emerald-600">{formatPercent(summary.analysis?.analysis_success_rate)}</p>
              </div>
              <div className="text-right">
                <p className="text-sm font-medium text-destructive">Failures</p>
                <p className="text-xl font-bold">{formatNumber(summary.analysis?.analysis_failure_count)}</p>
              </div>
            </div>
            <div>
              <p className="text-sm font-medium mb-2">Failure Breakdown</p>
              {Object.keys(summary.analysis?.failure_categories || {}).length > 0 ? (
                <div className="space-y-2">
                  {Object.entries(summary.analysis?.failure_categories || {}).map(([cat, count]) => (
                    <div key={cat}>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="truncate w-3/4">{cat}</span>
                        <span className="font-bold">{formatNumber(count as number)}</span>
                      </div>
                      <Progress value={Math.min(((count as number) / Math.max(1, summary.analysis?.analysis_failure_count || 1)) * 100, 100)} className="h-1.5" />
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-emerald-600 bg-emerald-50 dark:bg-emerald-950/50 p-2 rounded text-center">No recent failures</p>
              )}
            </div>
            {health.services?.llm_provider && (
              <div className="pt-2 border-t text-sm">
                <div className="flex justify-between items-center">
                  <span className="text-muted-foreground">Provider: {health.services.llm_provider.details?.provider || 'auto'}</span>
                  <Badge variant={health.services.llm_provider.status === 'healthy' ? 'outline' : 'secondary'} className={health.services.llm_provider.status === 'healthy' ? 'text-emerald-600 border-emerald-200' : ''}>
                    {health.services.llm_provider.status}
                  </Badge>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* SECTION 6 - NEEDS ATTENTION */}
        <Card className="shadow-sm md:col-span-2 lg:col-span-2">
          <CardHeader className="pb-3 border-b bg-slate-50/50 dark:bg-slate-900/50 flex flex-row items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-lg">
              <ShieldAlert className="h-5 w-5 text-orange-500" />
              Needs Attention
            </CardTitle>
            {summary.incidents?.critical_incidents !== undefined && summary.incidents.critical_incidents > 0 && (
              <Badge variant="destructive" className="animate-pulse">
                {summary.incidents.critical_incidents} Critical
              </Badge>
            )}
          </CardHeader>
          <CardContent className="p-0 overflow-auto max-h-[350px]">
            {alertsData?.alerts && alertsData.alerts.length > 0 ? (
              <div className="divide-y">
                {alertsData.alerts.map((alert) => (
                  <div key={alert.id} className="p-4 hover:bg-slate-50 dark:hover:bg-slate-900 transition-colors">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-start gap-3">
                        <div className={`mt-0.5 p-1.5 rounded-full ${alert.severity === 'high' ? 'bg-destructive/10 text-destructive' : 'bg-orange-100 text-orange-600 dark:bg-orange-900/30'}`}>
                          {alert.severity === 'high' ? <XCircle className="h-4 w-4" /> : <AlertTriangle className="h-4 w-4" />}
                        </div>
                        <div>
                          <p className="text-sm font-semibold">{alert.title}</p>
                          <p className="text-sm text-muted-foreground mt-0.5">{alert.description}</p>
                        </div>
                      </div>
                      <div className="text-[11px] text-muted-foreground whitespace-nowrap">
                        {new Date(alert.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center p-10 text-center text-muted-foreground">
                <CheckCircle className="h-12 w-12 text-emerald-500/50 mb-3" />
                <p className="text-base font-medium text-emerald-700 dark:text-emerald-400">All Clear</p>
                <p className="text-sm mt-1">No alerts or open incidents require immediate attention.</p>
              </div>
            )}
          </CardContent>
        </Card>

      </div>
    </div>
  );
}
