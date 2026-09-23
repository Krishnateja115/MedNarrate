'use client';

import { useQuery } from '@tanstack/react-query';
import { fetchApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Skeleton } from '@/components/ui/skeleton';
import { Activity, Server, AlertTriangle, Search, ActivitySquare } from 'lucide-react';

interface AIOverview {
  total_requests: number;
  success_rate: number;
  failure_rate: number;
  timeout_rate: number;
  avg_latency_ms: number;
  fallback_usage: number;
  providers: { provider: string; requests: number }[];
}

interface AITrace {
  id: string;
  request_id: string;
  feature: string;
  provider: string;
  model_name: string;
  status: string;
  latency_ms: number;
  fallback_used: boolean;
  error_category: string | null;
  timestamp: string;
}

export default function AIOperationsPage() {
  const { data: overviewData, isLoading: overviewLoading } = useQuery<{status: string, overview: AIOverview}>({
    queryKey: ['ai_overview'],
    queryFn: () => fetchApi('/api/v1/admin/ai-ops/overview'),
  });

  const { data: tracesData, isLoading: tracesLoading } = useQuery<{status: string, traces: AITrace[]}>({
    queryKey: ['ai_traces'],
    queryFn: () => fetchApi('/api/v1/admin/ai-ops/traces'),
  });

  const { data: failuresData, isLoading: failuresLoading } = useQuery<{status: string, failures: {category: string, count: number}[]}>({
    queryKey: ['ai_failures'],
    queryFn: () => fetchApi('/api/v1/admin/ai-ops/failures'),
  });

  const MetricCard = ({ title, value, icon, description }: any) => (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
        {icon}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {description && <p className="text-xs text-muted-foreground mt-1">{description}</p>}
      </CardContent>
    </Card>
  );

  return (
    <div className="space-y-6 fade-in">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">AI Operations</h1>
        <p className="text-muted-foreground">Monitor LLM telemetry, view request traces, and analyze failures.</p>
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="traces">Request Traces</TabsTrigger>
          <TabsTrigger value="failures">Failure Analysis</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {overviewLoading ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-32 w-full" />)}
            </div>
          ) : (
            <>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <MetricCard 
                  title="Total Requests" 
                  value={overviewData?.overview.total_requests.toLocaleString() || '0'} 
                  icon={<Activity className="h-4 w-4 text-muted-foreground" />}
                />
                <MetricCard 
                  title="Success Rate" 
                  value={`${overviewData?.overview.success_rate.toFixed(1) || '0'}%`} 
                  icon={<ActivitySquare className="h-4 w-4 text-emerald-500" />}
                />
                <MetricCard 
                  title="Avg Latency" 
                  value={`${overviewData?.overview.avg_latency_ms.toFixed(0) || '0'} ms`} 
                  icon={<Server className="h-4 w-4 text-blue-500" />}
                />
                <MetricCard 
                  title="Fallback Usage" 
                  value={overviewData?.overview.fallback_usage.toLocaleString() || '0'} 
                  icon={<AlertTriangle className="h-4 w-4 text-amber-500" />}
                />
              </div>
              <Card>
                <CardHeader>
                  <CardTitle>Provider Usage</CardTitle>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Provider</TableHead>
                        <TableHead className="text-right">Requests</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {overviewData?.overview.providers.map(p => (
                        <TableRow key={p.provider}>
                          <TableCell className="font-medium capitalize">{p.provider}</TableCell>
                          <TableCell className="text-right">{p.requests.toLocaleString()}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>

        <TabsContent value="traces">
          <Card>
            <CardHeader>
              <CardTitle>Request Traces</CardTitle>
              <CardDescription>Recent LLM interactions. Raw prompts are masked for safety.</CardDescription>
            </CardHeader>
            <CardContent>
              {tracesLoading ? (
                <Skeleton className="h-[400px] w-full" />
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Timestamp</TableHead>
                      <TableHead>Request ID</TableHead>
                      <TableHead>Provider/Model</TableHead>
                      <TableHead>Feature</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="text-right">Latency</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {tracesData?.traces.map(trace => (
                      <TableRow key={trace.id}>
                        <TableCell className="text-xs text-muted-foreground">{new Date(trace.timestamp).toLocaleString()}</TableCell>
                        <TableCell className="font-mono text-xs">{trace.request_id || '-'}</TableCell>
                        <TableCell>
                          <div className="font-medium capitalize">{trace.provider}</div>
                          <div className="text-xs text-muted-foreground">{trace.model_name || 'default'}</div>
                        </TableCell>
                        <TableCell>{trace.feature || 'unknown'}</TableCell>
                        <TableCell>
                          {trace.status === 'success' ? <Badge className="bg-emerald-500">Success</Badge> :
                           trace.status === 'error' ? <Badge variant="destructive">Error</Badge> :
                           trace.status === 'timeout' ? <Badge className="bg-amber-500">Timeout</Badge> :
                           <Badge variant="secondary">{trace.status}</Badge>}
                        </TableCell>
                        <TableCell className="text-right">{trace.latency_ms ? `${Math.round(trace.latency_ms)}ms` : '-'}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="failures">
          <Card>
            <CardHeader>
              <CardTitle>Failure Analysis</CardTitle>
              <CardDescription>Aggregated errors from telemetry events.</CardDescription>
            </CardHeader>
            <CardContent>
              {failuresLoading ? (
                <Skeleton className="h-[400px] w-full" />
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Error Category</TableHead>
                      <TableHead className="text-right">Count</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {failuresData?.failures.map(f => (
                      <TableRow key={f.category}>
                        <TableCell className="font-mono text-sm text-destructive">{f.category}</TableCell>
                        <TableCell className="text-right">{f.count.toLocaleString()}</TableCell>
                      </TableRow>
                    ))}
                    {(!failuresData?.failures || failuresData.failures.length === 0) && (
                      <TableRow>
                        <TableCell colSpan={2} className="text-center text-muted-foreground p-8">No failures recorded.</TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
