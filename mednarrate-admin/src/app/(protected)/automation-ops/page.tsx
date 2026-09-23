'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { Bell, Pill, CalendarClock, RotateCcw } from 'lucide-react';
import Link from 'next/link';

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

  const { data: notifsData, isLoading: notifsLoading } = useQuery<{status: string, notifications: NotificationLog[]}>({
    queryKey: ['automation_notifications'],
    queryFn: () => fetchApi('/api/v1/admin/automation-ops/notifications'),
  });

  const { data: medsData, isLoading: medsLoading } = useQuery<{status: string, schedules: MedicationSchedule[]}>({
    queryKey: ['automation_medications'],
    queryFn: () => fetchApi('/api/v1/admin/automation-ops/medications'),
  });

  const { data: jobsData, isLoading: jobsLoading } = useQuery<{status: string, jobs: JobExecution[]}>({
    queryKey: ['automation_jobs'],
    queryFn: () => fetchApi('/api/v1/admin/automation-ops/jobs'),
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
            <CardContent>
              {notifsLoading ? (
                <Skeleton className="h-[400px] w-full" />
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Sent At</TableHead>
                      <TableHead>User ID</TableHead>
                      <TableHead>Title</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Error</TableHead>
                      <TableHead className="text-right">Action</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {notifsData?.notifications.map(n => (
                      <TableRow key={n.id}>
                        <TableCell className="text-xs text-muted-foreground">{new Date(n.sent_at).toLocaleString()}</TableCell>
                        <TableCell className="font-mono text-xs text-primary hover:underline">
                          <Link href={`/users/${n.user_id}`}>{n.user_id.slice(0, 8)}</Link>
                        </TableCell>
                        <TableCell className="font-medium">{n.title}</TableCell>
                        <TableCell>
                          {n.status === 'sent' ? <Badge className="bg-emerald-500">Sent</Badge> : 
                           n.status === 'failed' ? <Badge variant="destructive">Failed</Badge> :
                           n.status === 'retrying' ? <Badge className="bg-amber-500">Retrying</Badge> :
                           <Badge variant="secondary">{n.status}</Badge>}
                        </TableCell>
                        <TableCell className="text-xs text-muted-foreground">{n.error_message || '-'}</TableCell>
                        <TableCell className="text-right">
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            disabled={n.status === 'sent' || n.status === 'retrying'}
                            onClick={() => retryNotificationMutation.mutate(n.id)}
                          >
                            <RotateCcw className="h-4 w-4 mr-1" /> Retry
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                    {(!notifsData?.notifications || notifsData.notifications.length === 0) && (
                      <TableRow>
                        <TableCell colSpan={6} className="text-center text-muted-foreground p-8">No notifications found.</TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="medications">
          <Card>
            <CardHeader>
              <CardTitle>Medication Schedules</CardTitle>
              <CardDescription>View operational state of user reminders.</CardDescription>
            </CardHeader>
            <CardContent>
              {medsLoading ? (
                <Skeleton className="h-[400px] w-full" />
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Created At</TableHead>
                      <TableHead>User ID</TableHead>
                      <TableHead>Medication</TableHead>
                      <TableHead>Times</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {medsData?.schedules.map(m => (
                      <TableRow key={m.id}>
                        <TableCell className="text-xs text-muted-foreground">{new Date(m.created_at).toLocaleString()}</TableCell>
                        <TableCell className="font-mono text-xs text-primary hover:underline">
                          <Link href={`/users/${m.user_id}`}>{m.user_id.slice(0, 8)}</Link>
                        </TableCell>
                        <TableCell className="font-medium">{m.medication_name}</TableCell>
                        <TableCell className="text-xs">{m.times_of_day?.join(', ') || '-'}</TableCell>
                        <TableCell>
                          {m.is_active ? <Badge className="bg-emerald-500">Active</Badge> : <Badge variant="secondary">Paused</Badge>}
                        </TableCell>
                      </TableRow>
                    ))}
                    {(!medsData?.schedules || medsData.schedules.length === 0) && (
                      <TableRow>
                        <TableCell colSpan={5} className="text-center text-muted-foreground p-8">No schedules found.</TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="jobs">
          <Card>
            <CardHeader>
              <CardTitle>Background Jobs</CardTitle>
              <CardDescription>Execution history for async scheduler.</CardDescription>
            </CardHeader>
            <CardContent>
              {jobsLoading ? (
                <Skeleton className="h-[400px] w-full" />
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Started</TableHead>
                      <TableHead>Job Name</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Duration</TableHead>
                      <TableHead>Failure Reason</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {jobsData?.jobs.map(j => (
                      <TableRow key={j.id}>
                        <TableCell className="text-xs text-muted-foreground">{new Date(j.started_at).toLocaleString()}</TableCell>
                        <TableCell className="font-mono text-xs font-semibold">{j.job_name}</TableCell>
                        <TableCell>
                          {j.status === 'completed' ? <Badge className="bg-emerald-500">Completed</Badge> : 
                           j.status === 'failed' ? <Badge variant="destructive">Failed</Badge> :
                           <Badge className="bg-blue-500 animate-pulse">Running</Badge>}
                        </TableCell>
                        <TableCell className="text-xs">{j.duration_seconds ? `${j.duration_seconds.toFixed(2)}s` : '-'}</TableCell>
                        <TableCell className="text-xs text-destructive">{j.failure_category || '-'}</TableCell>
                      </TableRow>
                    ))}
                    {(!jobsData?.jobs || jobsData.jobs.length === 0) && (
                      <TableRow>
                        <TableCell colSpan={5} className="text-center text-muted-foreground p-8">No jobs executed yet.</TableCell>
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
