'use client';

import { useQuery } from '@tanstack/react-query';
import { fetchApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Users, FileText, Activity, AlertTriangle, Bot } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';

interface DashboardSummary {
  total_users: number;
  active_users_24h: number;
  total_reports: number;
  reports_today: number;
  processing_reports: number;
  failed_reports: number;
  analysis_success_rate: number;
  open_incidents: number;
  critical_incidents: number;
  system_status: string;
}

export default function OverviewPage() {
  const { data, isLoading, error } = useQuery<DashboardSummary>({
    queryKey: ['dashboard-summary'],
    queryFn: () => fetchApi('/api/v1/admin/dashboard/summary'),
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Overview</h1>
          <p className="text-muted-foreground mt-2">Loading system metrics...</p>
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
          <h1 className="text-3xl font-bold tracking-tight">Overview</h1>
        </div>
        <div className="rounded-md bg-destructive/15 p-4 text-destructive border border-destructive/20">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="h-5 w-5" />
            <h3 className="font-semibold">Failed to load dashboard metrics</h3>
          </div>
          <p className="mt-2 text-sm">Please check your connection or ensure you have the required permissions.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Overview</h1>
          <p className="text-muted-foreground mt-2">Command center for MedNarrate operations.</p>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-sm font-medium">System Status:</span>
          <Badge variant={data.system_status === 'Healthy' ? 'default' : 'destructive'} className={data.system_status === 'Healthy' ? 'bg-green-600 hover:bg-green-700' : ''}>
            {data.system_status}
          </Badge>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {/* Users Metric */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Users</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.total_users.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground mt-1">
              <span className="text-emerald-600 font-medium">{data.active_users_24h.toLocaleString()}</span> active in last 24h
            </p>
          </CardContent>
        </Card>

        {/* Reports Metric */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Reports Processed</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.total_reports.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {data.reports_today.toLocaleString()} today
            </p>
          </CardContent>
        </Card>

        {/* AI Success Rate */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">AI Analysis Success Rate</CardTitle>
            <Bot className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.analysis_success_rate.toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground mt-1 flex gap-2">
              <span><span className="text-blue-600 font-medium">{data.processing_reports}</span> processing</span>
              <span><span className="text-red-600 font-medium">{data.failed_reports}</span> failed</span>
            </p>
          </CardContent>
        </Card>

        {/* Incidents Metric */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Open Incidents</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.open_incidents}</div>
            <p className="text-xs text-muted-foreground mt-1">
              <span className={data.critical_incidents > 0 ? "text-red-600 font-medium" : ""}>
                {data.critical_incidents} critical
              </span>
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
