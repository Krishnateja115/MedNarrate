/* eslint-disable */
'use client';
import { useSearchParams } from 'next/navigation';
import { Suspense, useState } from 'react';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { ArrowLeft, UserIcon, Shield, Activity, FileText, AlertTriangle, Key, LogOut, CheckCircle2, MessageSquare, Bell, Clock, Cpu, Calendar } from 'lucide-react';
import Link from 'next/link';
import { Progress } from '@/components/ui/progress';

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

function UserDetailPageContent() {
  const searchParams = useSearchParams();
  const extractedId = searchParams.get('id');
  
  const userId = extractedId;
  const queryClient = useQueryClient();
  if (!extractedId) return <div className="p-8">No ID provided</div>;
  const [actionMessage, setActionMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);
  
  const { data, isLoading, error } = useQuery<{status: string, user: UserDetail}>({
    queryKey: ['user', userId],
    queryFn: () => fetchApi(`/api/v1/admin/users/${userId}`),
  });

  const { data: sessions } = useQuery({
    queryKey: ['user-sessions', userId],
    queryFn: () => fetchApi(`/api/v1/admin/users/${userId}/sessions`),
  });

  const { data: reports } = useQuery({
    queryKey: ['user-reports', userId],
    queryFn: () => fetchApi(`/api/v1/admin/users/${userId}/reports`),
  });

  const { data: analyses } = useQuery({
    queryKey: ['user-analyses', userId],
    queryFn: () => fetchApi(`/api/v1/admin/users/${userId}/analyses`),
  });

  const { data: chats } = useQuery({
    queryKey: ['user-chats', userId],
    queryFn: () => fetchApi(`/api/v1/admin/users/${userId}/chats`),
  });

  const { data: reminders } = useQuery({
    queryKey: ['user-reminders', userId],
    queryFn: () => fetchApi(`/api/v1/admin/users/${userId}/reminders`),
  });

  const { data: notifications } = useQuery({
    queryKey: ['user-notifications', userId],
    queryFn: () => fetchApi(`/api/v1/admin/users/${userId}/notifications`),
  });

  const { data: support } = useQuery({
    queryKey: ['user-support', userId],
    queryFn: () => fetchApi(`/api/v1/admin/users/${userId}/support`),
  });

  const { data: securityLogs } = useQuery({
    queryKey: ['user-security', userId],
    queryFn: () => fetchApi(`/api/v1/admin/users/${userId}/security`),
  });

  const { data: medicalProfile, isLoading: mpLoading } = useQuery({
    queryKey: ['user-medical', userId],
    queryFn: () => fetchApi(`/api/v1/admin/users/${userId}/medical_profile`),
    retry: false
  });

  const { data: doctorProfile, isLoading: dpLoading } = useQuery({
    queryKey: ['user-doctor', userId],
    queryFn: () => fetchApi(`/api/v1/admin/users/${userId}/doctor_profile`),
    retry: false
  });

  const { data: caregiverProfile, isLoading: cpLoading } = useQuery({
    queryKey: ['user-caregiver', userId],
    queryFn: () => fetchApi(`/api/v1/admin/users/${userId}/caregiver_profile`),
    retry: false
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
      queryClient.invalidateQueries({ queryKey: ['user-sessions', userId] });
      queryClient.invalidateQueries({ queryKey: ['user-security', userId] });
      queryClient.invalidateQueries({ queryKey: ['user-doctor', userId] });
      queryClient.invalidateQueries({ queryKey: ['user-caregiver', userId] });
      setActionMessage({ type: 'success', text: data.message || 'Action completed successfully' });
      if (data.reset_link) {
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
    <div className="space-y-6 fade-in w-full pb-10">
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

      <Tabs defaultValue="profile" className="w-full">
        <TabsList className="flex flex-wrap h-auto">
          <TabsTrigger value="profile">Profile</TabsTrigger>
          <TabsTrigger value="auth">Authentication</TabsTrigger>
          <TabsTrigger value="reports">Reports ({user.reports_count})</TabsTrigger>
          <TabsTrigger value="analyses">Analyses</TabsTrigger>
          <TabsTrigger value="chats">Chats</TabsTrigger>
          <TabsTrigger value="reminders">Reminders</TabsTrigger>
          <TabsTrigger value="notifications">Notifications</TabsTrigger>
          <TabsTrigger value="support">Support</TabsTrigger>
          <TabsTrigger value="security">Security</TabsTrigger>
        </TabsList>
        
        <TabsContent value="profile" className="space-y-6 mt-6">
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader className="pb-3 border-b">
                <CardTitle className="text-base flex items-center gap-2">
                  <UserIcon className="h-4 w-4" /> Identity & Profile
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4 space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="col-span-2">
                    <span className="text-xs text-muted-foreground uppercase font-medium">User ID</span>
                    <div className="text-sm font-mono mt-1">{user.id}</div>
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
                    <div className="text-sm mt-1">{new Date(user.created_at).toLocaleString()}</div>
                  </div>
                  <div>
                    <span className="text-xs text-muted-foreground uppercase font-medium">Last Updated</span>
                    <div className="text-sm mt-1">{new Date(user.updated_at).toLocaleString()}</div>
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
                      {user.last_login ? new Date(user.last_login).toLocaleString() : 'Never'}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {(medicalProfile?.profile || doctorProfile?.profile || caregiverProfile?.profile) && (
            <div className="mt-6 space-y-6">
              {medicalProfile?.profile && (
                <Card>
                  <CardHeader className="pb-3 border-b">
                    <CardTitle className="text-base flex items-center gap-2">
                      <Activity className="h-4 w-4 text-rose-500" /> Medical Profile
                    </CardTitle>
                    <CardDescription>Sensitive patient details. Access is audited.</CardDescription>
                  </CardHeader>
                  <CardContent className="pt-4">
                    <div className="grid gap-4 md:grid-cols-3">
                      <div>
                        <span className="text-xs text-muted-foreground uppercase font-medium">Date of Birth</span>
                        <div className="text-sm mt-1">{medicalProfile.profile.date_of_birth || 'Not provided'}</div>
                      </div>
                      <div>
                        <span className="text-xs text-muted-foreground uppercase font-medium">Gender</span>
                        <div className="text-sm mt-1 capitalize">{medicalProfile.profile.gender || 'Not provided'}</div>
                      </div>
                      <div>
                        <span className="text-xs text-muted-foreground uppercase font-medium">Blood Type</span>
                        <div className="text-sm mt-1">{medicalProfile.profile.blood_type || 'Not provided'}</div>
                      </div>
                      <div className="md:col-span-3">
                        <span className="text-xs text-muted-foreground uppercase font-medium">Allergies</span>
                        <div className="text-sm mt-1">{medicalProfile.profile.allergies?.join(', ') || 'None reported'}</div>
                      </div>
                      <div className="md:col-span-3">
                        <span className="text-xs text-muted-foreground uppercase font-medium">Chronic Conditions</span>
                        <div className="text-sm mt-1">{medicalProfile.profile.chronic_conditions?.join(', ') || 'None reported'}</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {doctorProfile?.profile && (
                <Card>
                  <CardHeader className="pb-3 border-b flex flex-row items-center justify-between">
                    <div>
                      <CardTitle className="text-base flex items-center gap-2">
                        <UserIcon className="h-4 w-4 text-blue-500" /> Doctor / Clinician Profile
                      </CardTitle>
                      <CardDescription>Professional credentials and verification status.</CardDescription>
                    </div>
                    <Badge variant={doctorProfile.profile.is_verified ? 'outline' : 'secondary'} className={doctorProfile.profile.is_verified ? 'text-emerald-600 border-emerald-600/30' : ''}>
                      {doctorProfile.profile.is_verified ? 'Verified Clinician' : 'Unverified'}
                    </Badge>
                  </CardHeader>
                  <CardContent className="pt-4 space-y-4">
                    <div className="grid gap-4 md:grid-cols-2">
                      <div>
                        <span className="text-xs text-muted-foreground uppercase font-medium">Specialty</span>
                        <div className="text-sm mt-1 capitalize">{doctorProfile.profile.specialty}</div>
                      </div>
                      <div>
                        <span className="text-xs text-muted-foreground uppercase font-medium">License Number</span>
                        <div className="text-sm mt-1 font-mono">{doctorProfile.profile.license_number}</div>
                      </div>
                      <div>
                        <span className="text-xs text-muted-foreground uppercase font-medium">Hospital Affiliation</span>
                        <div className="text-sm mt-1">{doctorProfile.profile.hospital_affiliation || 'Independent'}</div>
                      </div>
                    </div>
                    {!doctorProfile.profile.is_verified && (
                      <div className="pt-4 border-t flex justify-end">
                        <Button size="sm" onClick={() => handleAction('verify_doctor', 'Approve and verify this clinician profile?')} disabled={actionMutation.isPending}>
                          Verify Credentials
                        </Button>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}

              {caregiverProfile?.profile && (
                <Card>
                  <CardHeader className="pb-3 border-b flex flex-row items-center justify-between">
                    <div>
                      <CardTitle className="text-base flex items-center gap-2">
                        <UserIcon className="h-4 w-4 text-orange-500" /> Caregiver Profile
                      </CardTitle>
                      <CardDescription>Caregiver relationship and verification status.</CardDescription>
                    </div>
                    <Badge variant={caregiverProfile.profile.is_verified ? 'outline' : 'secondary'} className={caregiverProfile.profile.is_verified ? 'text-emerald-600 border-emerald-600/30' : ''}>
                      {caregiverProfile.profile.is_verified ? 'Verified Caregiver' : 'Unverified'}
                    </Badge>
                  </CardHeader>
                  <CardContent className="pt-4 space-y-4">
                    <div className="grid gap-4 md:grid-cols-2">
                      <div>
                        <span className="text-xs text-muted-foreground uppercase font-medium">Relationship to Patient</span>
                        <div className="text-sm mt-1 capitalize">{caregiverProfile.profile.relationship_to_patient}</div>
                      </div>
                    </div>
                    {!caregiverProfile.profile.is_verified && (
                      <div className="pt-4 border-t flex justify-end">
                        <Button size="sm" onClick={() => handleAction('verify_caregiver', 'Approve and verify this caregiver profile?')} disabled={actionMutation.isPending}>
                          Verify Caregiver
                        </Button>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </TabsContent>

        <TabsContent value="auth" className="mt-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-3 border-b">
              <div>
                <CardTitle>Active Sessions</CardTitle>
                <CardDescription>Recent login sessions and refresh tokens</CardDescription>
              </div>
              <Button variant="destructive" size="sm" onClick={() => handleAction('force_logout', 'Force logout this user from all devices?')}>
                Revoke All
              </Button>
            </CardHeader>
            <CardContent className="pt-4">
              {sessions?.sessions ? (
                <div className="divide-y">
                  {sessions.sessions.length > 0 ? sessions.sessions.map((session: any) => (
                    <div key={session.id} className="py-3 flex justify-between items-center">
                      <div>
                        <div className="font-mono text-xs">{session.id}</div>
                        <div className="text-sm text-muted-foreground mt-1">Created: {new Date(session.created_at).toLocaleString()}</div>
                      </div>
                      <Badge variant={session.revoked ? 'destructive' : 'outline'} className={!session.revoked ? 'border-emerald-200 text-emerald-600' : ''}>
                        {session.revoked ? 'Revoked' : 'Active'}
                      </Badge>
                    </div>
                  )) : <p className="text-sm text-muted-foreground py-4 text-center">No session history found.</p>}
                </div>
              ) : <Skeleton className="h-32 w-full" />}
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="reports" className="mt-6">
          <Card>
            <CardHeader className="pb-3 border-b">
              <CardTitle>Reports Uploaded</CardTitle>
            </CardHeader>
            <CardContent className="pt-4">
              {reports?.items ? (
                <div className="divide-y">
                  {reports.items.length > 0 ? reports.items.map((report: any) => (
                    <div key={report.id} className="py-3 flex justify-between items-center">
                      <div>
                        <div className="font-medium text-sm">{report.title}</div>
                        <div className="text-xs text-muted-foreground mt-1">
                          {report.report_type.toUpperCase()} • {new Date(report.uploaded_at).toLocaleString()}
                        </div>
                      </div>
                      <Badge variant="outline">{report.processing_status}</Badge>
                    </div>
                  )) : <p className="text-sm text-muted-foreground py-4 text-center">No reports uploaded.</p>}
                </div>
              ) : <Skeleton className="h-32 w-full" />}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="analyses" className="mt-6">
          <Card>
            <CardHeader className="pb-3 border-b">
              <CardTitle>AI Analyses</CardTitle>
            </CardHeader>
            <CardContent className="pt-4">
              {analyses?.items ? (
                <div className="divide-y">
                  {analyses.items.length > 0 ? analyses.items.map((analysis: any) => (
                    <div key={analysis.id} className="py-3">
                      <div className="flex justify-between items-center">
                        <div className="font-mono text-xs text-muted-foreground">Report: {analysis.report_id}</div>
                        <Badge variant={analysis.status === 'completed' ? 'outline' : 'destructive'} className={analysis.status === 'completed' ? 'border-emerald-200 text-emerald-600' : ''}>{analysis.status}</Badge>
                      </div>
                      {analysis.error_message && <div className="text-xs text-destructive mt-1">{analysis.error_message}</div>}
                      <div className="text-xs text-muted-foreground mt-1">{new Date(analysis.created_at).toLocaleString()}</div>
                    </div>
                  )) : <p className="text-sm text-muted-foreground py-4 text-center">No analyses found.</p>}
                </div>
              ) : <Skeleton className="h-32 w-full" />}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="chats" className="mt-6">
          <Card>
            <CardHeader className="pb-3 border-b">
              <CardTitle>Chat Sessions</CardTitle>
            </CardHeader>
            <CardContent className="pt-4">
              {chats?.items ? (
                <div className="divide-y">
                  {chats.items.length > 0 ? chats.items.map((chat: any) => (
                    <div key={chat.id} className="py-3 flex justify-between items-center">
                      <div>
                        <div className="font-medium text-sm">{chat.title || 'Untitled Chat'}</div>
                        <div className="text-xs text-muted-foreground mt-1">Created: {new Date(chat.created_at).toLocaleString()}</div>
                      </div>
                    </div>
                  )) : <p className="text-sm text-muted-foreground py-4 text-center">No chats found.</p>}
                </div>
              ) : <Skeleton className="h-32 w-full" />}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="reminders" className="mt-6">
          <Card>
            <CardHeader className="pb-3 border-b">
              <CardTitle>Medication Schedules</CardTitle>
            </CardHeader>
            <CardContent className="pt-4">
              {reminders?.reminders ? (
                <div className="divide-y">
                  {reminders.reminders.length > 0 ? reminders.reminders.map((reminder: any) => (
                    <div key={reminder.id} className="py-3 flex justify-between items-center">
                      <div>
                        <div className="font-medium text-sm">{reminder.medication_name}</div>
                        <div className="text-xs text-muted-foreground mt-1">{reminder.dosage} • {reminder.frequency}</div>
                      </div>
                      <Badge variant={reminder.is_active ? 'outline' : 'secondary'}>{reminder.is_active ? 'Active' : 'Inactive'}</Badge>
                    </div>
                  )) : <p className="text-sm text-muted-foreground py-4 text-center">No reminders found.</p>}
                </div>
              ) : <Skeleton className="h-32 w-full" />}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="notifications" className="mt-6">
          <Card>
            <CardHeader className="pb-3 border-b">
              <CardTitle>Notification History</CardTitle>
            </CardHeader>
            <CardContent className="pt-4">
              {notifications?.items ? (
                <div className="divide-y">
                  {notifications.items.length > 0 ? notifications.items.map((note: any) => (
                    <div key={note.id} className="py-3 flex justify-between items-center">
                      <div>
                        <div className="font-medium text-sm uppercase">{note.notification_type}</div>
                        {note.error_message && <div className="text-xs text-destructive mt-1">{note.error_message}</div>}
                        <div className="text-xs text-muted-foreground mt-1">{new Date(note.sent_at).toLocaleString()}</div>
                      </div>
                      <Badge variant={note.status === 'sent' ? 'outline' : 'destructive'} className={note.status === 'sent' ? 'border-emerald-200 text-emerald-600' : ''}>{note.status}</Badge>
                    </div>
                  )) : <p className="text-sm text-muted-foreground py-4 text-center">No notifications found.</p>}
                </div>
              ) : <Skeleton className="h-32 w-full" />}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="support" className="mt-6">
          <Card>
            <CardHeader className="pb-3 border-b">
              <CardTitle>Support Tickets</CardTitle>
            </CardHeader>
            <CardContent className="pt-4">
              {support?.items ? (
                <div className="divide-y">
                  {support.items.length > 0 ? support.items.map((ticket: any) => (
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
                  )) : <p className="text-sm text-muted-foreground py-4 text-center">No support tickets found.</p>}
                </div>
              ) : <Skeleton className="h-32 w-full" />}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="security" className="mt-6">
          <Card>
            <CardHeader className="pb-3 border-b">
              <CardTitle>Admin Security Actions</CardTitle>
              <CardDescription>Audit log of actions taken by administrators on this user account.</CardDescription>
            </CardHeader>
            <CardContent className="pt-4">
              {securityLogs?.logs ? (
                <div className="divide-y">
                  {securityLogs.logs.length > 0 ? securityLogs.logs.map((log: any) => (
                    <div key={log.id} className="py-3 flex justify-between items-start">
                      <div>
                        <div className="font-medium text-sm font-mono text-indigo-600 dark:text-indigo-400">{log.action}</div>
                        <div className="text-xs bg-slate-100 dark:bg-slate-900 p-2 rounded mt-1 overflow-auto max-w-lg font-mono">
                          {JSON.stringify(log.metadata_payload, null, 2)}
                        </div>
                        <div className="text-xs text-muted-foreground mt-2 flex gap-2">
                          <span>{new Date(log.timestamp).toLocaleString()}</span>
                          <span>•</span>
                          <span>Admin: {log.actor_admin_id}</span>
                        </div>
                      </div>
                    </div>
                  )) : <p className="text-sm text-muted-foreground py-4 text-center">No security actions recorded.</p>}
                </div>
              ) : <Skeleton className="h-32 w-full" />}
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
      <UserDetailPageContent />
    </Suspense>
  );
}
