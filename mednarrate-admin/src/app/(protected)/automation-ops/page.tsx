/* eslint-disable */
'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { Bell, Pill, CalendarClock, RotateCcw } from 'lucide-react';
import Link from 'next/link';
import { useState } from 'react';
import { ColumnDef } from '@tanstack/react-table';
import { DataTable } from '@/components/ui/data-table';

interface NotificationLog {
  id: string;
  user_id: string;
  title: string;
  status: string;
  error_message: string | null;
  sent_at: string;
}

interface MedicationSchedule {
  id: string;
  user_id: string;
  medication_name: string;
  is_active: boolean;
  times_of_day: string[];
  created_at: string;
}

interface JobExecution {
  id: string;
  job_name: string;
  status: string;
  duration_seconds: number | null;
  failure_category: string | null;
  started_at: string;
  finished_at: string | null;
}

export default function AutomationOpsPage() {
  const queryClient = useQueryClient();

  const [notifsPage, setNotifsPage] = useState(1);
  const [notifsLimit, setNotifsLimit] = useState(25);
  const [notifsSort, setNotifsSort] = useState({id: 'sent_at', desc: true});

  const [medsPage, setMedsPage] = useState(1);
  const [medsLimit, setMedsLimit] = useState(25);
  const [medsSort, setMedsSort] = useState({id: 'created_at', desc: true});

  const [jobsPage, setJobsPage] = useState(1);
  const [jobsLimit, setJobsLimit] = useState(25);
  const [jobsSort, setJobsSort] = useState({id: 'started_at', desc: true});

  const { data: notifsData, isLoading: notifsLoading } = useQuery<{items: NotificationLog[], total: number, page: number, limit: number}>({
    queryKey: ['automation_notifications', notifsPage, notifsLimit, notifsSort],
    queryFn: () => fetchApi(`/api/v1/admin/automation-ops/notifications?page=${notifsPage}&limit=${notifsLimit}&sort_by=${notifsSort.id}&sort_desc=${notifsSort.desc}`),
  });

  const { data: medsData, isLoading: medsLoading } = useQuery<{items: MedicationSchedule[], total: number, page: number, limit: number}>({
    queryKey: ['automation_medications', medsPage, medsLimit, medsSort],
    queryFn: () => fetchApi(`/api/v1/admin/automation-ops/medications?page=${medsPage}&limit=${medsLimit}&sort_by=${medsSort.id}&sort_desc=${medsSort.desc}`),
  });

  const { data: jobsData, isLoading: jobsLoading } = useQuery<{items: JobExecution[], total: number, page: number, limit: number}>({
    queryKey: ['automation_jobs', jobsPage, jobsLimit, jobsSort],
    queryFn: () => fetchApi(`/api/v1/admin/automation-ops/jobs?page=${jobsPage}&limit=${jobsLimit}&sort_by=${jobsSort.id}&sort_desc=${jobsSort.desc}`),
  });

  const retryNotificationMutation = useMutation({
    mutationFn: async (id: string) => {
      const res = await fetch(`/api/v1/admin/automation-ops/notifications/${id}/retry`, {
        method: 'POST',
      });
      if (!res.ok) throw new Error('Failed to retry');
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['automation_notifications'] });
    }
  });

  const notifsColumns: ColumnDef<NotificationLog>[] = [
    {
      accessorKey: 'sent_at',
      header: 'Sent At',
      cell: ({ row }) => <span className="text-xs text-muted-foreground">{row.original.sent_at ? new Date(row.original.sent_at).toLocaleString() : '-'}</span>,
    },
    {
      accessorKey: 'user_id',
      header: 'User ID',
      cell: ({ row }) => (
        <Link href={`/users/detail?id=${row.original.user_id}`} className="font-mono text-xs text-primary hover:underline">
          {row.original.user_id.slice(0, 8)}
        </Link>
      ),
      enableSorting: false,
    },
    {
      accessorKey: 'title',
      header: 'Title',
      cell: ({ row }) => <span className="font-medium">{row.original.title}</span>,
    },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: ({ row }) => {
        const status = row.original.status;
        return status === 'sent' ? <Badge className="bg-emerald-500">Sent</Badge> : 
               status === 'failed' ? <Badge variant="destructive">Failed</Badge> :
               status === 'retrying' ? <Badge className="bg-amber-500">Retrying</Badge> :
               <Badge variant="secondary">{status}</Badge>;
      }
    },
    {
      accessorKey: 'error_message',
      header: 'Error',
      cell: ({ row }) => <span className="text-xs text-muted-foreground">{row.original.error_message || '-'}</span>,
    },
    {
      id: 'actions',
      header: () => <div className="text-right">Action</div>,
      cell: ({ row }) => (
        <div className="text-right">
          <Button 
            variant="ghost" 
            size="sm" 
            disabled={row.original.status === 'sent' || row.original.status === 'retrying'}
            onClick={() => retryNotificationMutation.mutate(row.original.id)}
          >
            <RotateCcw className="h-4 w-4 mr-1" /> Retry
          </Button>
        </div>
      ),
      enableSorting: false,
    }
  ];

  const medsColumns: ColumnDef<MedicationSchedule>[] = [
    {
      accessorKey: 'created_at',
      header: 'Created At',
      cell: ({ row }) => <span className="text-xs text-muted-foreground">{new Date(row.original.created_at).toLocaleString()}</span>,
    },
    {
      accessorKey: 'user_id',
      header: 'User ID',
      cell: ({ row }) => (
        <Link href={`/users/detail?id=${row.original.user_id}`} className="font-mono text-xs text-primary hover:underline">
          {row.original.user_id.slice(0, 8)}
        </Link>
      ),
      enableSorting: false,
    },
    {
      accessorKey: 'medication_name',
      header: 'Medication',
      cell: ({ row }) => <span className="font-medium">{row.original.medication_name}</span>,
    },
    {
      accessorKey: 'times_of_day',
      header: 'Times',
      cell: ({ row }) => <span className="text-xs">{row.original.times_of_day?.join(', ') || '-'}</span>,
      enableSorting: false,
    },
    {
      accessorKey: 'is_active',
      header: 'Status',
      cell: ({ row }) => row.original.is_active ? <Badge className="bg-emerald-500">Active</Badge> : <Badge variant="secondary">Paused</Badge>
    }
  ];

  const jobsColumns: ColumnDef<JobExecution>[] = [
    {
      accessorKey: 'started_at',
      header: 'Started At',
      cell: ({ row }) => <span className="text-xs text-muted-foreground">{new Date(row.original.started_at).toLocaleString()}</span>,
    },
    {
      accessorKey: 'job_name',
      header: 'Job Name',
      cell: ({ row }) => <span className="font-mono text-xs font-semibold">{row.original.job_name}</span>,
    },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: ({ row }) => {
        const s = row.original.status;
        return s === 'completed' ? <Badge className="bg-emerald-500">Completed</Badge> : 
               s === 'failed' ? <Badge variant="destructive">Failed</Badge> :
               <Badge className="bg-blue-500 animate-pulse">Running</Badge>;
      }
    },
    {
      accessorKey: 'duration_seconds',
      header: 'Duration',
      cell: ({ row }) => <span className="text-xs">{row.original.duration_seconds ? `${row.original.duration_seconds.toFixed(2)}s` : '-'}</span>,
    },
    {
      accessorKey: 'failure_category',
      header: 'Failure Reason',
      cell: ({ row }) => <span className="text-xs text-destructive">{row.original.failure_category || '-'}</span>,
    }
  ];

  return (
    <div className="space-y-6 fade-in">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Automation Operations</h1>
        <p className="text-muted-foreground">Manage background jobs, notifications, and medication reminders.</p>
      </div>

      <Tabs defaultValue="notifications" className="space-y-4">
        <TabsList>
          <TabsTrigger value="notifications" className="flex items-center gap-2"><Bell className="h-4 w-4" /> Notifications</TabsTrigger>
          <TabsTrigger value="medications" className="flex items-center gap-2"><Pill className="h-4 w-4" /> Medications</TabsTrigger>
          <TabsTrigger value="jobs" className="flex items-center gap-2"><CalendarClock className="h-4 w-4" /> Scheduler Jobs</TabsTrigger>
        </TabsList>

        <TabsContent value="notifications">
          <Card>
            <CardHeader>
              <CardTitle>Delivery History</CardTitle>
              <CardDescription>View and retry failed push notifications.</CardDescription>
            </CardHeader>
            <CardContent className="p-4">
              <DataTable
                columns={notifsColumns}
                data={notifsData?.items || []}
                pageCount={Math.ceil((notifsData?.total || 0) / notifsLimit) || 1}
                pageIndex={notifsPage - 1}
                pageSize={notifsLimit}
                total={notifsData?.total || 0}
                isLoading={notifsLoading}
                onPageChange={(p) => setNotifsPage(p + 1)}
                onPageSizeChange={(s) => { setNotifsLimit(s); setNotifsPage(1); }}
                onSortChange={(s) => setNotifsSort(s)}
                sortState={notifsSort}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="medications">
          <Card>
            <CardHeader>
              <CardTitle>Medication Schedules</CardTitle>
              <CardDescription>View operational state of user reminders.</CardDescription>
            </CardHeader>
            <CardContent className="p-4">
              <DataTable
                columns={medsColumns}
                data={medsData?.items || []}
                pageCount={Math.ceil((medsData?.total || 0) / medsLimit) || 1}
                pageIndex={medsPage - 1}
                pageSize={medsLimit}
                total={medsData?.total || 0}
                isLoading={medsLoading}
                onPageChange={(p) => setMedsPage(p + 1)}
                onPageSizeChange={(s) => { setMedsLimit(s); setMedsPage(1); }}
                onSortChange={(s) => setMedsSort(s)}
                sortState={medsSort}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="jobs">
          <Card>
            <CardHeader>
              <CardTitle>Background Jobs</CardTitle>
              <CardDescription>Execution history for async scheduler.</CardDescription>
            </CardHeader>
            <CardContent className="p-4">
              <DataTable
                columns={jobsColumns}
                data={jobsData?.items || []}
                pageCount={Math.ceil((jobsData?.total || 0) / jobsLimit) || 1}
                pageIndex={jobsPage - 1}
                pageSize={jobsLimit}
                total={jobsData?.total || 0}
                isLoading={jobsLoading}
                onPageChange={(p) => setJobsPage(p + 1)}
                onPageSizeChange={(s) => { setJobsLimit(s); setJobsPage(1); }}
                onSortChange={(s) => setJobsSort(s)}
                sortState={jobsSort}
              />
            </CardContent>
          </Card>
        </TabsContent>

      </Tabs>
    </div>
  );
}
