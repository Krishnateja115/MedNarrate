'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { Users, UserPlus, LogOut, ShieldAlert, CheckCircle, XCircle } from 'lucide-react';

interface AdminUser {
  id: string;
  email: string;
  full_name: string | null;
  role: string;
  is_active: boolean;
  is_super_admin: boolean;
  created_at: string | null;
  last_login_at: string | null;
  roles: string[];
}

export default function AdminManagementPage() {
  const queryClient = useQueryClient();
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Form states for creating admin
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newEmail, setNewEmail] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newName, setNewName] = useState('');

  const { data: adminsData, isLoading } = useQuery<{ admins: AdminUser[] }>({
    queryKey: ['admin-users'],
    queryFn: () => fetchApi('/api/v1/admin/admins'),
  });

  const createAdminMutation = useMutation({
    mutationFn: (newAdmin: any) => fetchApi('/api/v1/admin/admins', { data: newAdmin }),
    onSuccess: () => {
      setSuccessMsg('Admin user created successfully');
      setErrorMsg(null);
      setShowCreateForm(false);
      setNewEmail('');
      setNewPassword('');
      setNewName('');
      queryClient.invalidateQueries({ queryKey: ['admin-users'] });
    },
    onError: (err: any) => {
      setErrorMsg(err.message || 'Failed to create admin');
      setSuccessMsg(null);
    }
  });

  const toggleActiveMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      fetchApi(`/api/v1/admin/admins/${id}/active`, { method: 'PATCH', data: { is_active } }),
    onSuccess: () => {
      setSuccessMsg('Admin status updated successfully');
      setErrorMsg(null);
      queryClient.invalidateQueries({ queryKey: ['admin-users'] });
    },
    onError: (err: any) => {
      setErrorMsg(err.message || 'Failed to update admin status');
      setSuccessMsg(null);
    }
  });

  const forceLogoutMutation = useMutation({
    mutationFn: (id: string) => fetchApi(`/api/v1/admin/admins/${id}/force-logout`, { method: 'POST' }),
    onSuccess: () => {
      setSuccessMsg('Force logout issued successfully. Tokens revoked.');
      setErrorMsg(null);
    },
    onError: (err: any) => {
      setErrorMsg(err.message || 'Failed to force logout');
      setSuccessMsg(null);
    }
  });

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newEmail || !newPassword) return;
    createAdminMutation.mutate({
      email: newEmail,
      password: newPassword,
      full_name: newName || undefined
    });
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <Users className="w-7 h-7 text-blue-600" /> Admin Accounts Management
          </h1>
          <p className="text-slate-500 dark:text-slate-400 text-sm">
            Provision administrators, manage role assignments, toggle account status, and invalidate active sessions.
          </p>
        </div>
        <Button onClick={() => setShowCreateForm(!showCreateForm)} className="flex items-center gap-2">
          <UserPlus className="w-4 h-4" /> {showCreateForm ? 'Cancel' : 'Create Admin Account'}
        </Button>
      </div>

      {errorMsg && (
        <div className="p-4 bg-red-50 text-red-700 dark:bg-red-950/50 dark:text-red-300 rounded-md border border-red-200 dark:border-red-800 text-sm flex items-center gap-2">
          <ShieldAlert className="w-5 h-5 shrink-0" /> {errorMsg}
        </div>
      )}

      {successMsg && (
        <div className="p-4 bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300 rounded-md border border-emerald-200 dark:border-emerald-800 text-sm flex items-center gap-2">
          <CheckCircle className="w-5 h-5 shrink-0" /> {successMsg}
        </div>
      )}

      {showCreateForm && (
        <Card className="border-blue-200 dark:border-blue-900 bg-blue-50/30 dark:bg-blue-950/20">
          <CardHeader>
            <CardTitle className="text-lg">Create New Admin Account</CardTitle>
            <CardDescription>Enter details to provision a new administrative user.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreate} className="space-y-4 max-w-lg">
              <div>
                <label className="block text-sm font-medium mb-1">Email Address</label>
                <input
                  type="email"
                  required
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                  className="w-full px-3 py-2 border rounded-md dark:bg-slate-900 dark:border-slate-700 text-sm"
                  placeholder="admin@mednarrate.com"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Full Name</label>
                <input
                  type="text"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="w-full px-3 py-2 border rounded-md dark:bg-slate-900 dark:border-slate-700 text-sm"
                  placeholder="Dr. Admin Smith"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Temporary Password</label>
                <input
                  type="password"
                  required
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full px-3 py-2 border rounded-md dark:bg-slate-900 dark:border-slate-700 text-sm"
                  placeholder="••••••••••••"
                />
              </div>
              <Button type="submit" disabled={createAdminMutation.isPending}>
                {createAdminMutation.isPending ? 'Provisioning...' : 'Provision Admin'}
              </Button>
            </form>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Administrator Accounts</CardTitle>
          <CardDescription>All accounts with administrative privileges in the system.</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : !adminsData?.admins || adminsData.admins.length === 0 ? (
            <div className="text-center py-8 text-slate-500">No admin accounts found.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="text-xs uppercase bg-slate-50 dark:bg-slate-900 text-slate-500">
                  <tr>
                    <th className="px-4 py-3">Admin Name / Email</th>
                    <th className="px-4 py-3">Roles</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Last Login</th>
                    <th className="px-4 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                  {adminsData.admins.map((adm) => (
                    <tr key={adm.id} className="hover:bg-slate-50 dark:hover:bg-slate-900/50">
                      <td className="px-4 py-3 font-medium text-slate-900 dark:text-slate-100">
                        <div>{adm.full_name || 'Unnamed Admin'}</div>
                        <div className="text-xs text-slate-500 font-mono">{adm.email}</div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap gap-1">
                          {adm.is_super_admin && (
                            <Badge className="bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-300">
                              Super Admin
                            </Badge>
                          )}
                          {adm.roles.map((r) => (
                            <Badge key={r} variant="outline" className="text-xs">
                              {r}
                            </Badge>
                          ))}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant={adm.is_active ? 'default' : 'destructive'}>
                          {adm.is_active ? 'Active' : 'Deactivated'}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-slate-500 text-xs">
                        {adm.last_login_at ? new Date(adm.last_login_at).toLocaleString() : 'Never'}
                      </td>
                      <td className="px-4 py-3 text-right space-x-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => toggleActiveMutation.mutate({ id: adm.id, is_active: !adm.is_active })}
                          disabled={toggleActiveMutation.isPending}
                        >
                          {adm.is_active ? 'Deactivate' : 'Reactivate'}
                        </Button>
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() => forceLogoutMutation.mutate(adm.id)}
                          disabled={forceLogoutMutation.isPending}
                          className="flex items-center gap-1"
                        >
                          <LogOut className="w-3.5 h-3.5" /> Force Logout
                        </Button>
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
  );
}
