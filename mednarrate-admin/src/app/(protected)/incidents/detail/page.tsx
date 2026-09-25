/* eslint-disable */
'use client';
import { useSearchParams } from 'next/navigation';
import { Suspense, useState } from 'react';

import { useQuery } from '@tanstack/react-query';
import { fetchApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { ArrowLeft, Clock, Activity, MessageSquare, AlertTriangle, CheckCircle2 } from 'lucide-react';
import Link from 'next/link';

interface IncidentEvent {
  id: string;
  event_type: string;
  message: string;
  actor_id: string;
  timestamp: string;
}

interface IncidentDetail {
  id: string;
  title: string;
  severity: string;
  status: string;
  affected_service: string | null;
  started_at: string;
  resolved_at: string | null;
  summary: string | null;
  resolution: string | null;
}

interface IncidentDetailResponse {
  status: string;
  incident: IncidentDetail;
  events: IncidentEvent[];
}

function IncidentDetailPageContent() {
  const searchParams = useSearchParams();
  const extractedId = searchParams.get('id');
  
  const incidentId = extractedId;
  
  const { data, isLoading, error } = useQuery<IncidentDetailResponse>({
    queryKey: ['incident', incidentId],
    queryFn: () => fetchApi(`/api/v1/admin/incidents/${incidentId}`),
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
        <div>
          <Skeleton className="h-4 w-24 mb-4" />
          <Skeleton className="h-10 w-2/3" />
        </div>
        <Card>
          <CardContent className="p-6">
            <Skeleton className="h-[200px] w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="space-y-6">
        <Link href="/incidents" className="inline-flex items-center text-sm font-medium text-muted-foreground hover:text-foreground">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Incidents
        </Link>
        <div className="rounded-md bg-destructive/15 p-4 text-destructive border border-destructive/20">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="h-5 w-5" />
            <h3 className="font-semibold">Incident Not Found</h3>
          </div>
          <p className="mt-2 text-sm">The incident you requested could not be loaded.</p>
        </div>
      </div>
    );
  }

  const { incident, events } = data;

  return (
    <div className="space-y-6 fade-in max-w-5xl mx-auto">
      <div>
        <Link href="/incidents" className="inline-flex items-center text-sm font-medium text-muted-foreground hover:text-foreground mb-4">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Incidents
        </Link>
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-3xl font-bold tracking-tight">{incident.title}</h1>
              {getSeverityBadge(incident.severity)}
              {getStatusBadge(incident.status)}
            </div>
            <p className="text-muted-foreground font-mono text-sm">ID: {incident.id}</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline">Update Status</Button>
            {incident.status !== 'resolved' && incident.status !== 'closed' && (
              <Button variant="default" className="bg-emerald-600 hover:bg-emerald-700">Resolve Incident</Button>
            )}
          </div>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        {/* Main Content Area */}
        <div className="md:col-span-2 space-y-6">
          <Card>
            <CardHeader className="pb-3 border-b">
              <CardTitle className="text-base flex items-center gap-2">
                <AlertTriangle className="h-4 w-4" />
                Incident Overview
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4 space-y-4">
              <div>
                <h4 className="text-sm font-medium text-muted-foreground mb-1">Summary</h4>
                <p className="text-sm">{incident.summary || 'No summary provided.'}</p>
              </div>
              
              {incident.resolution && (
                <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-md">
                  <h4 className="text-sm font-semibold text-emerald-700 dark:text-emerald-400 mb-1 flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4" />
                    Resolution
                  </h4>
                  <p className="text-sm text-emerald-800 dark:text-emerald-200">{incident.resolution}</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Timeline */}
          <Card>
            <CardHeader className="pb-3 border-b">
              <CardTitle className="text-base flex items-center gap-2">
                <Clock className="h-4 w-4" />
                Event Timeline
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              {events.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-4">No events recorded.</p>
              ) : (
                <div className="relative space-y-0 pl-4 border-l-2 border-slate-200 dark:border-slate-800 ml-3">
                  {events.map((event, index) => (
                    <div key={event.id} className={`relative pl-6 ${index !== events.length - 1 ? 'pb-8' : ''}`}>
                      {/* Timeline dot */}
                      <span className="absolute left-[-5px] top-1 h-2 w-2 rounded-full bg-primary ring-4 ring-background" />
                      
                      <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-1 mb-1">
                        <span className="font-semibold text-sm">
                          {event.event_type}
                        </span>
                        <time className="text-xs text-muted-foreground font-mono">
                          {new Date(event.timestamp).toLocaleString()}
                        </time>
                      </div>
                      
                      <div className="text-sm bg-slate-50 dark:bg-slate-900/50 p-3 rounded-md border text-muted-foreground mt-2">
                        {event.message}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <Card>
            <CardHeader className="pb-3 border-b">
              <CardTitle className="text-base flex items-center gap-2">
                <Activity className="h-4 w-4" />
                Details
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4 space-y-4">
              <div>
                <span className="text-xs text-muted-foreground uppercase font-medium">Affected Service</span>
                <div className="font-medium mt-1">
                  {incident.affected_service ? (
                    <Badge variant="outline">{incident.affected_service}</Badge>
                  ) : (
                    <span className="text-muted-foreground text-sm">Unknown</span>
                  )}
                </div>
              </div>
              
              <div>
                <span className="text-xs text-muted-foreground uppercase font-medium">Started At</span>
                <div className="text-sm font-medium mt-1">
                  {new Date(incident.started_at).toLocaleString()}
                </div>
              </div>
              
              {incident.resolved_at && (
                <div>
                  <span className="text-xs text-muted-foreground uppercase font-medium">Resolved At</span>
                  <div className="text-sm font-medium mt-1">
                    {new Date(incident.resolved_at).toLocaleString()}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

export default function Page() {
  return (
    <Suspense fallback={<div className="p-8">Loading...</div>}>
      <IncidentDetailPageContent />
    </Suspense>
  );
}
