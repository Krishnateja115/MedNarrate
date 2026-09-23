'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { ArrowLeft, UserIcon, Shield, Activity, FileText, AlertTriangle, Key, LogOut, CheckCircle2 } from 'lucide-react';
import Link from 'next/link';
import { use, useState } from 'react';

interface UserDetail {
  id: string;
  email: string;
  full_name: string;
  role: string;
  preferred_language: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  reports_count: number;
  last_login: string | null;
}

export default function UserDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const userId = resolvedParams.id;
  const queryClient = useQueryClient();
  const [actionMessage, setActionMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);
  
  const { data, isLoading, error } = useQuery<{status: string, user: UserDetail}>({
    queryKey: ['user', userId],
    queryFn: () => fetchApi(`/api/v1/admin/users/${userId}`),
  });

  const actionMutation = useMutation({
    mutationFn: async ({ action, payload }: { action: string, payload?: any }) => {
      const res = await fetch(`/api/v1/admin/users/${userId}/actions/${action}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: payload ? JSON.stringify(payload) : undefined
      });
      if (!res.ok) throw new Error('Action failed');
      return res.json();
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['user', userId] });
      setActionMessage({ type: 'success', text: data.message || 'Action completed successfully' });
      if (data.reset_link) {
        // Display reset link securely for admin to copy
        setActionMessage({ type: 'success', text: `Reset Link Generated: ${data.reset_link}` });
      }
      setTimeout(() => setActionMessage(null), 10000);
    },
    onError: (err) => {
      setActionMessage({ type: 'error', text: err.message || 'Failed to perform action' });
      setTimeout(() => setActionMessage(null), 5000);
    }
  });

  const handleAction = (action: string, confirmMessage: string) => {
    if (window.confirm(confirmMessage)) {
      actionMutation.mutate({ action });
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div><Skeleton className="h-4 w-24 mb-4" /><Skeleton className="h-10 w-1/3" /></div>
        <Card><CardContent className="p-6"><Skeleton className="h-[200px] w-full" /></CardContent></Card>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="space-y-6">
        <Link href="/users" className="inline-flex items-center text-sm font-medium text-muted-foreground hover:text-foreground">
          <ArrowLeft className="mr-2 h-4 w-4" /> Back to Users
        </Link>
        <div className="rounded-md bg-destructive/15 p-4 text-destructive border border-destructive/20 flex items-center gap-2">
          <AlertTriangle className="h-5 w-5" /> <h3 className="font-semibold">User Not Found</h3>
        </div>
      </div>
    );
  }

  const { user } = data;

  return (
    <div className="space-y-6 fade-in max-w-5xl mx-auto">
      <div>
        <Link href="/users" className="inline-flex items-center text-sm font-medium text-muted-foreground hover:text-foreground mb-4">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Users
        </Link>
        
        {actionMessage && (
          <div className={`mb-4 p-4 rounded-md border text-sm flex items-start gap-2 break-all ${
            actionMessage.type === 'success' 
              ? 'bg-emerald-500/15 border-emerald-500/30 text-emerald-700 dark:text-emerald-400' 
              : 'bg-destructive/15 border-destructive/30 text-destructive'
          }`}>
            {actionMessage.type === 'success' ? <CheckCircle2 className="h-5 w-5 shrink-0" /> : <AlertTriangle className="h-5 w-5 shrink-0" />}
            <div>{actionMessage.text}</div>
          </div>
        )}

        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center text-primary">
              <UserIcon className="h-8 w-8" />
            </div>
            <div>
              <div className="flex items-center gap-3 mb-1">
                <h1 className="text-3xl font-bold tracking-tight">{user.full_name}</h1>
                {!user.is_active && <Badge variant="destructive">Suspended</Badge>}
              </div>
              <p className="text-muted-foreground font-mono text-sm">{user.email}</p>
            </div>
          </div>
          <div className="flex gap-2">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline">
                  <Shield className="mr-2 h-4 w-4" /> Manage Security
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="right" className="w-56">
                <DropdownMenuLabel>Account Actions</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => handleAction('reset_password', 'Generate a one-time password reset link?')}>
                  <Key className="mr-2 h-4 w-4" /> Reset Password
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => handleAction('force_logout', 'Force logout this user from all devices?')}>
                  <LogOut className="mr-2 h-4 w-4" /> Force Logout All Sessions
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                {user.is_active ? (
                  <DropdownMenuItem className="text-destructive focus:bg-destructive focus:text-destructive-foreground" onClick={() => handleAction('suspend', 'Are you sure you want to suspend this user? They will lose all access immediately.')}>
                    <AlertTriangle className="mr-2 h-4 w-4" /> Suspend Account
                  </DropdownMenuItem>
                ) : (
                  <DropdownMenuItem className="text-emerald-600 focus:bg-emerald-600 focus:text-white" onClick={() => handleAction('activate', 'Reactivate this user account?')}>
                    <CheckCircle2 className="mr-2 h-4 w-4" /> Reactivate Account
                  </DropdownMenuItem>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </div>

      <Tabs defaultValue="overview" className="w-full">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="reports">Reports ({user.reports_count})</TabsTrigger>
        </TabsList>
        
        <TabsContent value="overview" className="space-y-6 mt-6">
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader className="pb-3 border-b">
                <CardTitle className="text-base flex items-center gap-2">
                  <UserIcon className="h-4 w-4" /> Identity & Profile
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4 space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <span className="text-xs text-muted-foreground uppercase font-medium">User ID</span>
                    <div className="text-sm font-mono mt-1 break-all">{user.id}</div>
                  </div>
                  <div>
                    <span className="text-xs text-muted-foreground uppercase font-medium">Role</span>
                    <div className="mt-1 capitalize text-sm">{user.role}</div>
                  </div>
                  <div>
                    <span className="text-xs text-muted-foreground uppercase font-medium">Language</span>
                    <div className="text-sm mt-1 uppercase">{user.preferred_language}</div>
                  </div>
                  <div>
                    <span className="text-xs text-muted-foreground uppercase font-medium">Joined Date</span>
                    <div className="text-sm mt-1">{new Date(user.created_at).toLocaleDateString()}</div>
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
                    <span className="text-xs text-muted-foreground uppercase font-medium">Total Reports</span>
                    <div className="text-2xl font-bold mt-1">{user.reports_count}</div>
                  </div>
                  <div>
                    <span className="text-xs text-muted-foreground uppercase font-medium">Last Login</span>
                    <div className="text-sm mt-2 font-medium">
                      {user.last_login ? new Date(user.last_login).toLocaleString() : 'Never / Unknown'}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
        
        <TabsContent value="reports" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>User Reports</CardTitle>
              <CardDescription>View all reports uploaded by {user.full_name}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center p-8 text-muted-foreground border border-dashed rounded-md">
                <FileText className="mx-auto h-8 w-8 mb-3 opacity-50" />
                <p>Navigate to the Reports dashboard and filter by this user to view their reports.</p>
                <Link href={`/reports?user_id=${user.id}`}>
                  <Button variant="outline" className="mt-4">Go to Reports Filter</Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
