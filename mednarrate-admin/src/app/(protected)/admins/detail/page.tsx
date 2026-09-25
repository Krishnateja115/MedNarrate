/* eslint-disable */
'use client';
import { useSearchParams } from 'next/navigation';
import { Suspense, useState } from 'react';

import { useQuery } from '@tanstack/react-query';
import { fetchApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ArrowLeft, UserIcon, Activity, ShieldAlert, LifeBuoy } from 'lucide-react';
import Link from 'next/link';

function AdminDetailPageContent() {
  const searchParams = useSearchParams();
  const extractedId = searchParams.get('id');
  
  const adminId = extractedId;
  
  const { data: admin, isLoading: isLoadingAdmin } = useQuery<any>({
    queryKey: ['admin', adminId],
    queryFn: async () => {
      // Find the specific admin in the list
      const data = await fetchApi('/api/v1/admin/admins');
      return data.admins?.find((a: any) => a.id === adminId);
    },
  });

  const { data: auditLogs, isLoading: isLoadingLogs } = useQuery({
    queryKey: ['admin-audit-logs', adminId],
    queryFn: () => fetchApi(`/api/v1/admin/admins/${adminId}/audit_logs`),
  });

  const { data: supportTickets, isLoading: isLoadingTickets } = useQuery({
    queryKey: ['admin-support-tickets', adminId],
    queryFn: () => fetchApi(`/api/v1/admin/admins/${adminId}/support_tickets`),
  });

  if (isLoadingAdmin) {
    return (
      <div className="space-y-6">
        <div><Skeleton className="h-4 w-24 mb-4" /><Skeleton className="h-10 w-1/3" /></div>
        <Card><CardContent className="p-6"><Skeleton className="h-[200px] w-full" /></CardContent></Card>
      </div>
    );
  }

  if (!admin) {
    return (
      <div className="space-y-6">
        <Link href="/admins" className="inline-flex items-center text-sm font-medium text-muted-foreground hover:text-foreground">
          <ArrowLeft className="mr-2 h-4 w-4" /> Back to Admins
        </Link>
        <div className="rounded-md bg-destructive/15 p-4 text-destructive border border-destructive/20 flex items-center gap-2">
          <ShieldAlert className="h-5 w-5" /> <h3 className="font-semibold">Admin Not Found</h3>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 fade-in w-full pb-10">
      <div>
        <Link href="/admins" className="inline-flex items-center text-sm font-medium text-muted-foreground hover:text-foreground mb-4">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Admins
        </Link>
        
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="h-16 w-16 rounded-full bg-blue-100 text-blue-600 dark:bg-blue-900/30 flex items-center justify-center">
              <UserIcon className="h-8 w-8" />
            </div>
            <div>
              <div className="flex items-center gap-3 mb-1">
                <h1 className="text-3xl font-bold tracking-tight">{admin.full_name || 'Unnamed Admin'}</h1>
                {!admin.is_active && <Badge variant="destructive">Deactivated</Badge>}
                {admin.is_super_admin && <Badge className="bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-300">Super Admin</Badge>}
              </div>
              <p className="text-muted-foreground font-mono text-sm">{admin.email}</p>
            </div>
          </div>
        </div>
      </div>

      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="flex flex-wrap h-auto">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="audit">Audit Log</TabsTrigger>
          <TabsTrigger value="support">Assigned Tickets</TabsTrigger>
        </TabsList>
        
        <TabsContent value="overview" className="space-y-6 mt-6">
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader className="pb-3 border-b">
                <CardTitle className="text-base flex items-center gap-2">
                  <UserIcon className="h-4 w-4" /> Admin Identity
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4 space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="col-span-2">
                    <span className="text-xs text-muted-foreground uppercase font-medium">Admin ID</span>
                    <div className="text-sm font-mono mt-1">{admin.id}</div>
                  </div>
                  <div>
                    <span className="text-xs text-muted-foreground uppercase font-medium">Assigned Roles</span>
                    <div className="mt-1 flex flex-wrap gap-1">
                      {admin.roles.length > 0 ? admin.roles.map((r: string) => (
                        <Badge key={r} variant="outline">{r}</Badge>
                      )) : <span className="text-sm text-muted-foreground">None</span>}
                    </div>
                  </div>
                  <div>
                    <span className="text-xs text-muted-foreground uppercase font-medium">Created</span>
                    <div className="text-sm mt-1">{admin.created_at ? new Date(admin.created_at).toLocaleString() : 'Unknown'}</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3 border-b">
                <CardTitle className="text-base flex items-center gap-2">
                  <Activity className="h-4 w-4" /> Activity Summary
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4 space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <span className="text-xs text-muted-foreground uppercase font-medium">Last Login</span>
                    <div className="text-sm mt-2 font-medium">
                      {admin.last_login_at ? new Date(admin.last_login_at).toLocaleString() : 'Never'}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="audit" className="mt-6">
          <Card>
            <CardHeader className="pb-3 border-b">
              <CardTitle>Audit Log</CardTitle>
              <CardDescription>Actions taken by this administrator on the platform.</CardDescription>
            </CardHeader>
            <CardContent className="pt-4">
              {isLoadingLogs ? <Skeleton className="h-32 w-full" /> : auditLogs?.logs ? (
                <div className="divide-y">
                  {auditLogs.logs.length > 0 ? auditLogs.logs.map((log: any) => (
                    <div key={log.id} className="py-3 flex justify-between items-start">
                      <div>
                        <div className="font-medium text-sm font-mono text-indigo-600 dark:text-indigo-400">{log.action}</div>
                        <div className="text-xs bg-slate-100 dark:bg-slate-900 p-2 rounded mt-1 overflow-auto max-w-lg font-mono">
                          {JSON.stringify(log.metadata_payload, null, 2)}
                        </div>
                        <div className="text-xs text-muted-foreground mt-2 flex gap-2">
                          <span>{new Date(log.timestamp).toLocaleString()}</span>
                          <span>•</span>
                          <span>Target: {log.resource_type} ({log.resource_id})</span>
                        </div>
                      </div>
                    </div>
                  )) : <p className="text-sm text-muted-foreground py-4 text-center">No actions recorded.</p>}
                </div>
              ) : <p className="text-sm text-destructive py-4">Failed to load audit logs.</p>}
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="support" className="mt-6">
          <Card>
            <CardHeader className="pb-3 border-b">
              <CardTitle className="flex items-center gap-2">
                <LifeBuoy className="h-5 w-5" />
                Assigned Tickets
              </CardTitle>
              <CardDescription>Support tickets currently assigned to this administrator.</CardDescription>
            </CardHeader>
            <CardContent className="pt-4">
              {isLoadingTickets ? <Skeleton className="h-32 w-full" /> : supportTickets?.tickets ? (
                <div className="divide-y">
                  {supportTickets.tickets.length > 0 ? supportTickets.tickets.map((ticket: any) => (
                    <div key={ticket.id} className="py-3 flex justify-between items-center">
                      <div>
                        <div className="font-medium text-sm">{ticket.subject}</div>
                        <div className="text-xs text-muted-foreground mt-1">{new Date(ticket.created_at).toLocaleString()}</div>
                      </div>
                      <div className="flex gap-2">
                        <Badge variant="outline">{ticket.priority}</Badge>
                        <Badge variant="secondary">{ticket.status}</Badge>
                      </div>
                    </div>
                  )) : <p className="text-sm text-muted-foreground py-4 text-center">No assigned tickets.</p>}
                </div>
              ) : <p className="text-sm text-destructive py-4">Failed to load tickets.</p>}
            </CardContent>
          </Card>
        </TabsContent>

      </Tabs>
    </div>
  );
}

export default function Page() {
  return (
    <Suspense fallback={<div className="p-8">Loading...</div>}>
      <AdminDetailPageContent />
    </Suspense>
  );
}
