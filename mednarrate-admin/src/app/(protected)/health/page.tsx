/* eslint-disable */
'use client';

import { useQuery } from '@tanstack/react-query';
import { fetchApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Activity, Server, Database, Brain, HardDrive, Clock, CheckCircle2, XCircle, AlertCircle } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';

interface ServiceHealth {
  status: 'healthy' | 'degraded' | 'down' | 'unknown';
  last_checked: string;
  latency_ms: number | null;
  error_summary: string | null;
}

interface SystemHealth {
  status: 'healthy' | 'degraded' | 'down';
  timestamp: string;
  services: {
    [key: string]: ServiceHealth;
  };
}

const serviceIcons: Record<string, React.ReactNode> = {
  api: <Server className="h-5 w-5" />,
  database: <Database className="h-5 w-5" />,
  llm_provider: <Brain className="h-5 w-5" />,
  storage: <HardDrive className="h-5 w-5" />,
  scheduler: <Clock className="h-5 w-5" />
};

const serviceNames: Record<string, string> = {
  api: 'API Server',
  database: 'PostgreSQL Database',
  llm_provider: 'Primary LLM Provider',
  storage: 'File Storage',
  scheduler: 'Background Jobs (APScheduler)'
};

export default function HealthPage() {
  const { data, isLoading, error, refetch, isFetching } = useQuery<SystemHealth>({
    queryKey: ['system-health'],
    queryFn: () => fetchApi('/api/v1/admin/health'),
    refetchInterval: 30000, // Auto-refresh every 30 seconds
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle2 className="h-5 w-5 text-emerald-500" />;
      case 'degraded':
        return <AlertCircle className="h-5 w-5 text-amber-500" />;
      case 'down':
        return <XCircle className="h-5 w-5 text-destructive" />;
      default:
        return <AlertCircle className="h-5 w-5 text-muted-foreground" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'healthy':
        return <Badge className="bg-emerald-500 hover:bg-emerald-600">Healthy</Badge>;
      case 'degraded':
        return <Badge variant="outline" className="text-amber-500 border-amber-500">Degraded</Badge>;
      case 'down':
        return <Badge variant="destructive">Down</Badge>;
      default:
        return <Badge variant="secondary">Unknown</Badge>;
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Service Health</h1>
          <p className="text-muted-foreground mt-2">Checking infrastructure status...</p>
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[...Array(5)].map((_, i) => (
            <Card key={i}>
              <CardContent className="p-6">
                <Skeleton className="h-6 w-1/3 mb-4" />
                <Skeleton className="h-4 w-full mb-2" />
                <Skeleton className="h-4 w-2/3" />
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
          <h1 className="text-3xl font-bold tracking-tight">Service Health</h1>
        </div>
        <div className="rounded-md bg-destructive/15 p-4 text-destructive border border-destructive/20">
          <div className="flex items-center space-x-2">
            <XCircle className="h-5 w-5" />
            <h3 className="font-semibold">Failed to load health status</h3>
          </div>
          <p className="mt-2 text-sm">Please check your connection or ensure you have the required permissions.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 fade-in">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Service Health</h1>
          <p className="text-muted-foreground mt-2">Monitor the status of core platform services.</p>
        </div>
        <div className="flex items-center space-x-3 bg-card p-3 rounded-lg border shadow-sm">
          <span className="text-sm font-medium text-muted-foreground">Overall System:</span>
          <div className="flex items-center space-x-1.5">
            {getStatusIcon(data.status)}
            <span className="font-semibold capitalize">
              {data.status}
            </span>
          </div>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {Object.entries(data.services).map(([key, service]) => (
          <Card key={key} className={`border-l-4 ${
            service.status === 'healthy' ? 'border-l-emerald-500' :
            service.status === 'degraded' ? 'border-l-amber-500' :
            'border-l-destructive'
          } hover:shadow-md transition-all duration-200`}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-base font-medium flex items-center gap-2">
                <span className="p-1.5 bg-slate-100 dark:bg-slate-800 rounded-md text-muted-foreground">
                  {serviceIcons[key] || <Activity className="h-5 w-5" />}
                </span>
                {serviceNames[key] || key}
              </CardTitle>
              {getStatusBadge(service.status)}
            </CardHeader>
            <CardContent className="pt-4">
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Latency</span>
                  <span className="font-medium">
                    {service.latency_ms !== null ? `${service.latency_ms} ms` : '—'}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Last Checked</span>
                  <span className="font-medium">
                    {new Date(service.last_checked).toLocaleTimeString()}
                  </span>
                </div>
                
                {service.error_summary && (
                  <div className="mt-4 p-3 bg-destructive/10 text-destructive text-xs rounded-md border border-destructive/20 font-mono break-words">
                    {service.error_summary}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
      
      <div className="flex justify-end pt-4">
        <button 
          onClick={() => refetch()} 
          disabled={isFetching}
          className="text-sm px-4 py-2 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80 disabled:opacity-50 transition-colors"
        >
          {isFetching ? 'Checking...' : 'Refresh Status'}
        </button>
      </div>
    </div>
  );
}
