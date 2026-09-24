 
'use client';

import { useQuery } from '@tanstack/react-query';
import { fetchApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Clock, PlayCircle, CheckCircle2, XCircle, Settings, AlertTriangle } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import { ColumnDef } from '@tanstack/react-table';
import { DataTable } from '@/components/ui/data-table';
import { useState } from 'react';

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
  items: JobHistory[];
  total: number;
  page: number;
  limit: number;
  scheduler_jobs: ActiveJob[];
}

export default function JobsPage() {
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(25);
  const [sortState, setSortState] = useState<{id: string, desc: boolean}>({ id: 'started_at', desc: true });

  const queryParams = new URLSearchParams();
  queryParams.set('page', page.toString());
  queryParams.set('limit', limit.toString());
  queryParams.set('sort_by', sortState.id);
  // Note: the backend for jobs uses whitelist string without sort_desc bool in current codebase, but let's assume it accepts sort_by
  
  const { data, isLoading, error } = useQuery<JobsResponse>({
    queryKey: ['background-jobs', page, limit, sortState],
    queryFn: () => fetchApi(`/api/v1/admin/jobs?${queryParams.toString()}`),
    refetchInterval: 15000,
  });

  const columns: ColumnDef<JobHistory>[] = [
    {
      accessorKey: 'job_name',
      header: 'Job Name',
      cell: ({ row }) => <span className="font-medium">{row.getValue('job_name')}</span>,
    },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: ({ row }) => {
        const status = row.getValue('status') as string;
        return (
          <div className="flex items-center gap-1.5">
            {status === 'completed' && <CheckCircle2 className="h-4 w-4 text-emerald-500" />}
            {status === 'failed' && <XCircle className="h-4 w-4 text-destructive" />}
            {status === 'running' && <PlayCircle className="h-4 w-4 text-blue-500" />}
            <span className="capitalize">{status}</span>
          </div>
        );
      },
    },
    {
      accessorKey: 'started_at',
      header: 'Started At',
      cell: ({ row }) => <span className="text-muted-foreground whitespace-nowrap">{new Date(row.getValue('started_at')).toLocaleString()}</span>,
    },
    {
      accessorKey: 'duration_seconds',
      header: 'Duration',
      cell: ({ row }) => {
        const val = row.getValue('duration_seconds') as number;
        return <span className="font-mono text-muted-foreground">{val ? `${val.toFixed(2)}s` : '—'}</span>;
      }
    },
    {
      accessorKey: 'error_message',
      header: 'Message',
      cell: ({ row }) => {
        const msg = row.getValue('error_message') as string;
        return msg ? (
          <span className="text-destructive text-xs break-all line-clamp-2" title={msg}>
            {msg}
          </span>
        ) : (
          <span className="text-muted-foreground">—</span>
        );
      },
      enableSorting: false,
    }
  ];

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Background Jobs</h1>
          <Skeleton className="h-4 w-64 mt-2" />
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
            {data.scheduler_jobs.length === 0 ? (
              <div className="p-8 text-center text-muted-foreground">
                <p>No active schedules found.</p>
              </div>
            ) : (
              <div className="divide-y">
                {data.scheduler_jobs.map((job) => (
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
          <CardContent className="p-4">
            <DataTable
              columns={columns}
              data={data.items || []}
              pageCount={Math.ceil(data.total / data.limit) || 1}
              pageIndex={page - 1}
              pageSize={limit}
              total={data.total || 0}
              isLoading={isLoading}
              onPageChange={(p) => setPage(p + 1)}
              onPageSizeChange={(s) => { setLimit(s); setPage(1); }}
              onSortChange={(s) => setSortState(s)}
              sortState={sortState}
            />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
