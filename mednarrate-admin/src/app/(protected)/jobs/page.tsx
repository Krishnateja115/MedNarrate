'use client';

import { useQuery } from '@tanstack/react-query';
import { fetchApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Clock, PlayCircle, CheckCircle2, XCircle, Settings, AlertTriangle } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';

interface ActiveJob {
  id: string;
  name: string;
  next_run_time: string | null;
  status: string;
}

interface JobHistory {
  id: string;
  job_name: string;
  status: 'completed' | 'failed' | 'running';
  started_at: string;
  finished_at: string | null;
  duration_seconds: number | null;
  error_message: string | null;
}

interface JobsResponse {
  status: string;
  jobs: ActiveJob[];
  history: JobHistory[];
}

export default function JobsPage() {
  const { data, isLoading, error } = useQuery<JobsResponse>({
    queryKey: ['background-jobs'],
    queryFn: () => fetchApi('/api/v1/admin/jobs'),
    refetchInterval: 15000,
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Background Jobs</h1>
          <p className="text-muted-foreground mt-2">Loading active jobs and execution history...</p>
        </div>
        <div className="space-y-4">
          <Skeleton className="h-[200px] w-full" />
          <Skeleton className="h-[400px] w-full" />
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Background Jobs</h1>
        </div>
        <div className="rounded-md bg-destructive/15 p-4 text-destructive border border-destructive/20">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="h-5 w-5" />
            <h3 className="font-semibold">Failed to load jobs</h3>
          </div>
          <p className="mt-2 text-sm">Please check your connection or ensure you have the required permissions.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 fade-in">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Background Jobs</h1>
        <p className="text-muted-foreground mt-2">Monitor scheduled tasks, active processes, and recent executions.</p>
      </div>

      <div className="grid gap-6 md:grid-cols-1">
        {/* Active Jobs */}
        <Card>
          <CardHeader className="border-b bg-slate-50/50 dark:bg-slate-900/50">
            <CardTitle className="text-base flex items-center gap-2">
              <Settings className="h-4 w-4" />
              Active Schedules
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {data.jobs.length === 0 ? (
              <div className="p-8 text-center text-muted-foreground">
                <p>No active schedules found.</p>
              </div>
            ) : (
              <div className="divide-y">
                {data.jobs.map((job) => (
                  <div key={job.id} className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-slate-50 dark:hover:bg-slate-900/50 transition-colors">
                    <div>
                      <div className="flex items-center gap-2">
                        <h4 className="font-medium">{job.name}</h4>
                        <Badge variant={job.status === 'running' ? 'default' : 'secondary'} className={job.status === 'running' ? 'bg-emerald-500 hover:bg-emerald-600' : ''}>
                          {job.status}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground mt-1 font-mono">{job.id}</p>
                    </div>
                    
                    <div className="flex items-center gap-2 text-sm text-muted-foreground bg-slate-100 dark:bg-slate-800 px-3 py-1.5 rounded-md">
                      <Clock className="h-4 w-4" />
                      {job.next_run_time ? (
                        <span>Next run: {new Date(job.next_run_time).toLocaleString()}</span>
                      ) : (
                        <span>Not scheduled</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Job History */}
        <Card>
          <CardHeader className="border-b bg-slate-50/50 dark:bg-slate-900/50">
            <CardTitle className="text-base flex items-center gap-2">
              <PlayCircle className="h-4 w-4" />
              Recent Executions
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {data.history.length === 0 ? (
              <div className="p-8 text-center text-muted-foreground">
                <p>No execution history available.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
                  <thead className="text-xs text-muted-foreground bg-slate-50 dark:bg-slate-900 uppercase">
                    <tr>
                      <th className="px-4 py-3 font-medium">Job Name</th>
                      <th className="px-4 py-3 font-medium">Status</th>
                      <th className="px-4 py-3 font-medium">Started At</th>
                      <th className="px-4 py-3 font-medium">Duration</th>
                      <th className="px-4 py-3 font-medium">Message</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {data.history.map((exec) => (
                      <tr key={exec.id} className="hover:bg-slate-50 dark:hover:bg-slate-900/50">
                        <td className="px-4 py-3 font-medium">{exec.job_name}</td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-1.5">
                            {exec.status === 'completed' && <CheckCircle2 className="h-4 w-4 text-emerald-500" />}
                            {exec.status === 'failed' && <XCircle className="h-4 w-4 text-destructive" />}
                            {exec.status === 'running' && <PlayCircle className="h-4 w-4 text-blue-500" />}
                            <span className="capitalize">{exec.status}</span>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-muted-foreground whitespace-nowrap">
                          {new Date(exec.started_at).toLocaleString()}
                        </td>
                        <td className="px-4 py-3 font-mono text-muted-foreground">
                          {exec.duration_seconds ? `${exec.duration_seconds.toFixed(2)}s` : '—'}
                        </td>
                        <td className="px-4 py-3">
                          {exec.error_message ? (
                            <span className="text-destructive text-xs break-all line-clamp-2" title={exec.error_message}>
                              {exec.error_message}
                            </span>
                          ) : (
                            <span className="text-muted-foreground">—</span>
                          )}
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
    </div>
  );
}
