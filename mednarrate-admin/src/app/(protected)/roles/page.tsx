/* eslint-disable */
'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { Lock, ShieldAlert, CheckCircle, Plus } from 'lucide-react';

interface Permission {
  id: string;
  name: string;
  description: string | null;
}

interface Role {
  id: string;
  name: string;
  description: string | null;
  permissions: string[];
}

export default function RolesAndPermissionsPage() {
  const queryClient = useQueryClient();
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const [selectedRole, setSelectedRole] = useState<Role | null>(null);
  const [showCreateRole, setShowCreateRole] = useState(false);
  const [newRoleName, setNewRoleName] = useState('');
  const [newRoleDesc, setNewRoleDesc] = useState('');

  const { data: rolesData, isLoading: isLoadingRoles } = useQuery<Role[]>({
    queryKey: ['admin-roles'],
    queryFn: () => fetchApi('/api/v1/admin/roles'),
  });

  const { data: permsData, isLoading: isLoadingPerms } = useQuery<Permission[]>({
    queryKey: ['admin-permissions'],
    queryFn: () => fetchApi('/api/v1/admin/roles/permissions'),
  });

  const createRoleMutation = useMutation({
    mutationFn: (data: any) => fetchApi('/api/v1/admin/roles', { data }),
    onSuccess: () => {
      setSuccessMsg('Role created successfully');
      setErrorMsg(null);
      setShowCreateRole(false);
      setNewRoleName('');
      setNewRoleDesc('');
      queryClient.invalidateQueries({ queryKey: ['admin-roles'] });
    },
    onError: (err: any) => {
      setErrorMsg(err.message || 'Failed to create role');
      setSuccessMsg(null);
    }
  });

  const updateRolePermsMutation = useMutation({
    mutationFn: ({ roleId, permissions }: { roleId: string; permissions: string[] }) =>
      fetchApi(`/api/v1/admin/roles/${roleId}/permissions`, { method: 'PUT', data: { permission_names: permissions } }),
    onSuccess: () => {
      setSuccessMsg('Role permissions updated successfully');
      setErrorMsg(null);
      queryClient.invalidateQueries({ queryKey: ['admin-roles'] });
    },
    onError: (err: any) => {
      setErrorMsg(err.message || 'Failed to update role permissions (Self-escalation check may have blocked this)');
      setSuccessMsg(null);
    }
  });

  const handleTogglePermission = (role: Role, permName: string) => {
    const hasPerm = role.permissions.includes(permName);
    const updated = hasPerm
      ? role.permissions.filter((p) => p !== permName)
      : [...role.permissions, permName];

    updateRolePermsMutation.mutate({ roleId: role.id, permissions: updated });
  };

  const handleCreateRole = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newRoleName) return;
    createRoleMutation.mutate({ name: newRoleName, description: newRoleDesc });
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <Lock className="w-7 h-7 text-blue-600" /> Roles & Permission Matrix UI
          </h1>
          <p className="text-slate-500 dark:text-slate-400 text-sm">
            Define fine-grained roles, inspect granular permissions, and prevent self-escalation server-side.
          </p>
        </div>
        <Button onClick={() => setShowCreateRole(!showCreateRole)} className="flex items-center gap-2">
          <Plus className="w-4 h-4" /> {showCreateRole ? 'Cancel' : 'Create Custom Role'}
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

      {showCreateRole && (
        <Card className="border-blue-200 dark:border-blue-900 bg-blue-50/30 dark:bg-blue-950/20">
          <CardHeader>
            <CardTitle className="text-lg">Create New RBAC Role</CardTitle>
            <CardDescription>Specify role name and description.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreateRole} className="space-y-4 max-w-lg">
              <div>
                <label className="block text-sm font-medium mb-1">Role Name</label>
                <input
                  type="text"
                  required
                  value={newRoleName}
                  onChange={(e) => setNewRoleName(e.target.value)}
                  className="w-full px-3 py-2 border rounded-md dark:bg-slate-900 dark:border-slate-700 text-sm"
                  placeholder="Compliance_Auditor"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Description</label>
                <input
                  type="text"
                  value={newRoleDesc}
                  onChange={(e) => setNewRoleDesc(e.target.value)}
                  className="w-full px-3 py-2 border rounded-md dark:bg-slate-900 dark:border-slate-700 text-sm"
                  placeholder="Can read audit logs and break-glass history"
                />
              </div>
              <Button type="submit" disabled={createRoleMutation.isPending}>
                {createRoleMutation.isPending ? 'Creating...' : 'Create Role'}
              </Button>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Permission Matrix */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Permission Matrix</CardTitle>
          <CardDescription>
            Matrix mapping system roles to granular administrative permissions. Server-side self-escalation blocks unauthorized grants.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoadingRoles || isLoadingPerms ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left border-collapse">
                <thead className="text-xs uppercase bg-slate-50 dark:bg-slate-900 text-slate-500 border-b">
                  <tr>
                    <th className="px-4 py-3 border-r min-w-[200px]">Granular Permission</th>
                    {rolesData?.map((r) => (
                      <th key={r.id} className="px-4 py-3 text-center min-w-[140px]">
                        <div>{r.name}</div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                  {permsData?.map((p) => (
                    <tr key={p.id} className="hover:bg-slate-50 dark:hover:bg-slate-900/50">
                      <td className="px-4 py-3 border-r font-mono text-xs text-slate-800 dark:text-slate-200">
                        <div className="font-semibold text-blue-600 dark:text-blue-400">{p.name}</div>
                        <div className="text-[11px] text-slate-500 font-sans">{p.description}</div>
                      </td>
                      {rolesData?.map((role) => {
                        const isAssigned = role.permissions.includes(p.name);
                        return (
                          <td key={role.id} className="px-4 py-3 text-center">
                            <input
                              type="checkbox"
                              checked={isAssigned}
                              onChange={() => handleTogglePermission(role, p.name)}
                              disabled={role.name === 'SuperAdmin'}
                              className="w-4 h-4 text-blue-600 rounded cursor-pointer disabled:opacity-50"
                            />
                          </td>
                        );
                      })}
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
