'use client';

import { useQuery } from '@tanstack/react-query';
import { fetchApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Activity, Plus, AlertTriangle } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import Link from 'next/link';
import { formatDistanceToNow } from 'date-fns';

interface Incident {
  id: string;
  title: string;
  severity: string;
  status: string;
  affected_service: string | null;
  started_at: string;
  resolved_at: string | null;
  summary: string | null;
}

interface IncidentsResponse {
  status: string;
  incidents: Incident[];
  pagination: {
    limit: number;
    offset: number;
  };
}

export default function IncidentsPage() {
  const { data, isLoading, error } = useQuery<IncidentsResponse>({
    queryKey: ['incidents'],
    queryFn: () => fetchApi('/api/v1/admin/incidents'),
  });

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'SEV-1':
        return <Badge variant="destructive" className="font-mono">SEV-1</Badge>;
      case 'SEV-2':
        return <Badge variant="destructive" className="bg-orange-600 hover:bg-orange-700 font-mono">SEV-2</Badge>;
      case 'SEV-3':
        return <Badge variant="outline" className="text-amber-600 border-amber-600 font-mono">SEV-3</Badge>;
      default:
        return <Badge variant="secondary" className="font-mono">{severity}</Badge>;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'open':
        return <Badge variant="destructive">Open</Badge>;
      case 'investigating':
        return <Badge className="bg-amber-500 hover:bg-amber-600">Investigating</Badge>;
      case 'identified':
        return <Badge className="bg-blue-500 hover:bg-blue-600">Identified</Badge>;
      case 'resolved':
        return <Badge className="bg-emerald-500 hover:bg-emerald-600">Resolved</Badge>;
      case 'closed':
        return <Badge variant="secondary">Closed</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Incidents</h1>
            <p className="text-muted-foreground mt-2">Loading incident history...</p>
          </div>
        </div>
        <Card>
          <CardContent className="p-6 space-y-4">
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Incidents</h1>
        </div>
        <div className="rounded-md bg-destructive/15 p-4 text-destructive border border-destructive/20">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="h-5 w-5" />
            <h3 className="font-semibold">Failed to load incidents</h3>
          </div>
          <p className="mt-2 text-sm">Please check your connection or ensure you have the required permissions.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Incidents</h1>
          <p className="text-muted-foreground mt-2">Track, investigate, and resolve system anomalies.</p>
        </div>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          Declare Incident
        </Button>
      </div>

      <Card>
        <CardHeader className="border-b bg-slate-50/50 dark:bg-slate-900/50">
          <CardTitle className="text-base flex items-center gap-2">
            <Activity className="h-4 w-4" />
            Incident Log
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {data.incidents.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">
              <p>No incidents recorded.</p>
            </div>
          ) : (
            <div className="divide-y">
              {data.incidents.map((incident) => (
                <Link 
                  key={incident.id} 
                  href={`/incidents/${incident.id}`}
                  className="block p-4 hover:bg-slate-50 dark:hover:bg-slate-900/50 transition-colors"
                >
                  <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
                    <div className="space-y-1">
                      <div className="flex items-center gap-3">
                        <h4 className="font-semibold text-lg hover:underline">{incident.title}</h4>
                        {getSeverityBadge(incident.severity)}
                        {getStatusBadge(incident.status)}
                      </div>
                      <p className="text-sm text-muted-foreground line-clamp-2">
                        {incident.summary || 'No summary provided.'}
                      </p>
                      {incident.affected_service && (
                        <div className="mt-2 text-xs font-medium text-slate-500 bg-slate-100 dark:bg-slate-800 dark:text-slate-400 inline-block px-2 py-0.5 rounded">
                          Service: {incident.affected_service}
                        </div>
                      )}
                    </div>
                    
                    <div className="flex flex-col items-start md:items-end text-sm text-muted-foreground shrink-0 gap-1">
                      <div>
                        Started: {new Date(incident.started_at).toLocaleDateString()} {new Date(incident.started_at).toLocaleTimeString()}
                      </div>
                      <div className="text-xs">
                        {incident.resolved_at ? (
                          <span>Resolved: {new Date(incident.resolved_at).toLocaleDateString()}</span>
                        ) : (
                          <span className="text-orange-500 font-medium">
                            Active for {formatDistanceToNow(new Date(incident.started_at))}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
