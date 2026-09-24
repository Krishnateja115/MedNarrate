/* eslint-disable */
'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { BarChart3, Plus, ShieldAlert, CheckCircle, Trash2 } from 'lucide-react';

interface FeatureFlag {
  id: string;
  name: string;
  description: string | null;
  enabled: boolean;
  rollout_percentage: number;
  target_environment: string;
  target_segment: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export default function FeatureFlagsPage() {
  const queryClient = useQueryClient();
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const [showCreateForm, setShowCreateForm] = useState(false);
  const [flagName, setFlagName] = useState('');
  const [description, setDescription] = useState('');
  const [rolloutPercentage, setRolloutPercentage] = useState(100);
  const [targetEnv, setTargetEnv] = useState('all');

  const { data, isLoading } = useQuery<{ flags: FeatureFlag[] }>({
    queryKey: ['feature-flags'],
    queryFn: () => fetchApi('/api/v1/admin/feature-flags'),
  });

  const createFlagMutation = useMutation({
    mutationFn: (newFlag: any) => fetchApi('/api/v1/admin/feature-flags', { data: newFlag }),
    onSuccess: () => {
      setSuccessMsg('Feature flag created successfully');
      setErrorMsg(null);
      setShowCreateForm(false);
      setFlagName('');
      setDescription('');
      queryClient.invalidateQueries({ queryKey: ['feature-flags'] });
    },
    onError: (err: any) => {
      setErrorMsg(err.message || 'Failed to create feature flag');
      setSuccessMsg(null);
    }
  });

  const toggleFlagMutation = useMutation({
    mutationFn: ({ id, enabled }: { id: string; enabled: boolean }) =>
      fetchApi(`/api/v1/admin/feature-flags/${id}`, { method: 'PUT', data: { enabled } }),
    onSuccess: () => {
      setSuccessMsg('Feature flag updated with audit trail');
      setErrorMsg(null);
      queryClient.invalidateQueries({ queryKey: ['feature-flags'] });
    },
    onError: (err: any) => {
      setErrorMsg(err.message || 'Failed to toggle feature flag');
      setSuccessMsg(null);
    }
  });

  const deleteFlagMutation = useMutation({
    mutationFn: (id: string) => fetchApi(`/api/v1/admin/feature-flags/${id}`, { method: 'DELETE' }),
    onSuccess: () => {
      setSuccessMsg('Feature flag deleted');
      setErrorMsg(null);
      queryClient.invalidateQueries({ queryKey: ['feature-flags'] });
    },
    onError: (err: any) => {
      setErrorMsg(err.message || 'Failed to delete flag');
      setSuccessMsg(null);
    }
  });

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!flagName) return;
    createFlagMutation.mutate({
      name: flagName,
      description,
      rollout_percentage: rolloutPercentage,
      target_environment: targetEnv,
      enabled: false
    });
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <BarChart3 className="w-7 h-7 text-blue-600" /> Feature Flags & Progressive Rollouts
          </h1>
          <p className="text-slate-500 dark:text-slate-400 text-sm">
            Control feature availability, set percentage rollouts, and monitor feature flag mutation audits.
          </p>
        </div>
        <Button onClick={() => setShowCreateForm(!showCreateForm)} className="flex items-center gap-2">
          <Plus className="w-4 h-4" /> {showCreateForm ? 'Cancel' : 'New Feature Flag'}
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
            <CardTitle className="text-lg">Create Feature Flag</CardTitle>
            <CardDescription>Name, description, environment targeting, and rollout percentage.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreate} className="space-y-4 max-w-lg">
              <div>
                <label className="block text-sm font-medium mb-1">Flag Name (Unique)</label>
                <input
                  type="text"
                  required
                  value={flagName}
                  onChange={(e) => setFlagName(e.target.value)}
                  placeholder="enable_ai_summary_v2"
                  className="w-full px-3 py-2 border rounded-md dark:bg-slate-900 dark:border-slate-700 text-sm font-mono"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Description</label>
                <input
                  type="text"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Enables V2 medical summary generation engine"
                  className="w-full px-3 py-2 border rounded-md dark:bg-slate-900 dark:border-slate-700 text-sm"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Target Environment</label>
                  <select
                    value={targetEnv}
                    onChange={(e) => setTargetEnv(e.target.value)}
                    className="w-full px-3 py-2 border rounded-md dark:bg-slate-900 dark:border-slate-700 text-sm"
                  >
                    <option value="all">All Environments</option>
                    <option value="development">Development</option>
                    <option value="staging">Staging</option>
                    <option value="production">Production</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Rollout Percentage</label>
                  <input
                    type="number"
                    min={0}
                    max={100}
                    value={rolloutPercentage}
                    onChange={(e) => setRolloutPercentage(Number(e.target.value))}
                    className="w-full px-3 py-2 border rounded-md dark:bg-slate-900 dark:border-slate-700 text-sm"
                  />
                </div>
              </div>

              <Button type="submit" disabled={createFlagMutation.isPending}>
                {createFlagMutation.isPending ? 'Creating...' : 'Create Flag'}
              </Button>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Feature Flags Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">System Feature Flags</CardTitle>
          <CardDescription>All changes to feature flags are logged with full audit trails.</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : !data?.flags || data.flags.length === 0 ? (
            <div className="text-center py-8 text-slate-500">No feature flags configured.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="text-xs uppercase bg-slate-50 dark:bg-slate-900 text-slate-500">
                  <tr>
                    <th className="px-4 py-3">Flag Name</th>
                    <th className="px-4 py-3">Target Env</th>
                    <th className="px-4 py-3">Rollout %</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                  {data.flags.map((flag) => (
                    <tr key={flag.id} className="hover:bg-slate-50 dark:hover:bg-slate-900/50">
                      <td className="px-4 py-3 font-medium">
                        <div className="font-mono text-blue-600 dark:text-blue-400">{flag.name}</div>
                        <div className="text-xs text-slate-500 font-sans">{flag.description || '-'}</div>
                      </td>
                      <td className="px-4 py-3 text-xs uppercase font-mono">{flag.target_environment}</td>
                      <td className="px-4 py-3 font-semibold">{flag.rollout_percentage}%</td>
                      <td className="px-4 py-3">
                        <Badge
                          variant={flag.enabled ? 'default' : 'secondary'}
                          className={flag.enabled ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300' : ''}
                        >
                          {flag.enabled ? 'ENABLED' : 'DISABLED'}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-right space-x-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => toggleFlagMutation.mutate({ id: flag.id, enabled: !flag.enabled })}
                          disabled={toggleFlagMutation.isPending}
                        >
                          {flag.enabled ? 'Disable' : 'Enable'}
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => deleteFlagMutation.mutate(flag.id)}
                          className="text-red-600 hover:text-red-700"
                        >
                          <Trash2 className="w-4 h-4" />
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
