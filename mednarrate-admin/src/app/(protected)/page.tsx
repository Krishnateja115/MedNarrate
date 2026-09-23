'use client';

import { useQuery } from '@tanstack/react-query';
import { fetchApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Users, FileText, Activity, AlertTriangle, Bot, CheckCircle, XCircle } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';

interface DashboardSummary {
  status: string;
  timestamp: string;
  users: {
    total_users: number;
    active_users: number;
  };
  reports: {
    reports_today: number;
    reports_processing: number;
    reports_failed: number;
  };
  analysis: {
    analysis_success_rate: number;
    analysis_failure_count: number;
  };
  support: {
    open_support_tickets: number | null;
  };
  incidents: {
    critical_incidents: number;
    open_incidents: number;
  };
}

interface Alert {
  id: string;
  type: 'job_failure' | 'incident';
  title: string;
  description: string;
  severity: 'high' | 'medium';
  timestamp: string;
}

interface AlertsResponse {
  status: string;
  alerts: Alert[];
}

export default function OverviewPage() {
  const { data, isLoading, error } = useQuery<DashboardSummary>({
    queryKey: ['dashboard-summary'],
    queryFn: () => fetchApi('/api/v1/admin/dashboard/summary'),
  });

  const { data: alertsData, isLoading: isLoadingAlerts } = useQuery<AlertsResponse>({
    queryKey: ['dashboard-alerts'],
    queryFn: () => fetchApi('/api/v1/admin/dashboard/alerts'),
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Command Center</h1>
          <p className="text-muted-foreground mt-2">Loading operational data...</p>
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Card key={i}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <Skeleton className="h-4 w-1/2" />
                <Skeleton className="h-4 w-4" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-8 w-1/3 mb-2" />
                <Skeleton className="h-3 w-2/3" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Command Center</h1>
        </div>
        <div className="rounded-md bg-destructive/15 p-4 text-destructive border border-destructive/20">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="h-5 w-5" />
            <h3 className="font-semibold">Failed to load command center</h3>
          </div>
          <p className="mt-2 text-sm">Please check your connection or ensure you have the required permissions.</p>
        </div>
      </div>
    );
  }

  const isHealthy = data.incidents.critical_incidents === 0;

  return (
    <div className="space-y-6 fade-in">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Command Center</h1>
          <p className="text-muted-foreground mt-2">Operational overview of MedNarrate platform.</p>
        </div>
        <div className="flex items-center space-x-3 bg-card p-3 rounded-lg border shadow-sm">
          <span className="text-sm font-medium text-muted-foreground">Platform Status:</span>
          <div className="flex items-center space-x-1.5">
            {isHealthy ? (
              <CheckCircle className="h-4 w-4 text-emerald-500" />
            ) : (
              <AlertTriangle className="h-4 w-4 text-destructive" />
            )}
            <span className={`font-semibold ${isHealthy ? 'text-emerald-500' : 'text-destructive'}`}>
              {isHealthy ? 'Healthy' : 'Needs Attention'}
            </span>
          </div>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="hover:shadow-md transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Users</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.users.total_users.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground mt-1">
              <span className="text-emerald-600 font-medium">{data.users.active_users.toLocaleString()}</span> active accounts
            </p>
          </CardContent>
        </Card>

        <Card className="hover:shadow-md transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Reports Today</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.reports.reports_today.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground mt-1 flex gap-2">
              <span><span className="text-blue-600 font-medium">{data.reports.reports_processing}</span> processing</span>
              <span><span className="text-destructive font-medium">{data.reports.reports_failed}</span> failed</span>
            </p>
          </CardContent>
        </Card>

        <Card className="hover:shadow-md transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">AI Analysis Success Rate</CardTitle>
            <Bot className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.analysis.analysis_success_rate.toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground mt-1">
              {data.analysis.analysis_failure_count > 0 ? (
                <span className="text-destructive font-medium">{data.analysis.analysis_failure_count} total failures</span>
              ) : (
                <span className="text-emerald-600 font-medium">0 failures today</span>
              )}
            </p>
          </CardContent>
        </Card>

        <Card className="hover:shadow-md transition-shadow border-l-4 border-l-orange-500">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Open Incidents</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.incidents.open_incidents}</div>
            <p className="text-xs text-muted-foreground mt-1">
              <span className={data.incidents.critical_incidents > 0 ? "text-destructive font-bold" : ""}>
                {data.incidents.critical_incidents} critical
              </span>
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-7">
        <Card className="md:col-span-4 lg:col-span-5 flex flex-col h-[500px]">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-primary" />
              System Activity (Placeholder)
            </CardTitle>
          </CardHeader>
          <CardContent className="flex-1 flex items-center justify-center text-muted-foreground bg-slate-50/50 dark:bg-slate-900/50 rounded-b-lg border-t border-dashed">
            [Chart Area: Daily Analysis Volume / Success Rate]
          </CardContent>
        </Card>
        
        <Card className="md:col-span-3 lg:col-span-2 flex flex-col h-[500px]">
          <CardHeader className="pb-3 border-b">
            <CardTitle className="flex items-center gap-2 text-base">
              <AlertTriangle className="h-4 w-4 text-orange-500" />
              Needs Attention
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0 overflow-auto">
            {isLoadingAlerts ? (
              <div className="p-4 space-y-4">
                <Skeleton className="h-16 w-full" />
                <Skeleton className="h-16 w-full" />
                <Skeleton className="h-16 w-full" />
              </div>
            ) : alertsData?.alerts && alertsData.alerts.length > 0 ? (
              <div className="divide-y">
                {alertsData.alerts.map((alert) => (
                  <div key={alert.id} className="p-4 hover:bg-slate-50 dark:hover:bg-slate-900 transition-colors">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-start gap-2">
                        {alert.severity === 'high' ? (
                          <XCircle className="h-4 w-4 text-destructive mt-0.5 shrink-0" />
                        ) : (
                          <AlertTriangle className="h-4 w-4 text-orange-500 mt-0.5 shrink-0" />
                        )}
                        <div>
                          <p className="text-sm font-medium leading-tight">{alert.title}</p>
                          <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{alert.description}</p>
                        </div>
                      </div>
                    </div>
                    <div className="mt-2 text-[10px] text-muted-foreground flex justify-end">
                      {new Date(alert.timestamp).toLocaleString()}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center p-6 text-center text-muted-foreground">
                <CheckCircle className="h-10 w-10 text-emerald-500/50 mb-3" />
                <p className="text-sm font-medium">All clear</p>
                <p className="text-xs mt-1">No alerts or open incidents.</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
