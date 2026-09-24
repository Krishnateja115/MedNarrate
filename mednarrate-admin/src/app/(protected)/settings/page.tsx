/* eslint-disable */
'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { Settings, Wrench, ShieldAlert, CheckCircle, AlertTriangle } from 'lucide-react';

interface MaintenanceStatus {
  is_enabled: boolean;
  scope: string;
  reason: string | null;
  message: string | null;
  enabled_at: string | null;
}

export default function SettingsAndMaintenancePage() {
  const queryClient = useQueryClient();
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Maintenance states
  const [mScope, setMScope] = useState('all');
  const [mReason, setMReason] = useState('');
  const [mMessage, setMMessage] = useState('');

  const { data: maintenance, isLoading } = useQuery<MaintenanceStatus>({
    queryKey: ['maintenance-status'],
    queryFn: () => fetchApi('/api/v1/admin/maintenance'),
  });

  const toggleMaintenanceMutation = useMutation({
    mutationFn: (payload: any) => fetchApi('/api/v1/admin/maintenance', { data: payload }),
    onSuccess: (res: any) => {
      setSuccessMsg(res.message || 'Maintenance mode updated');
      setErrorMsg(null);
      queryClient.invalidateQueries({ queryKey: ['maintenance-status'] });
    },
    onError: (err: any) => {
      setErrorMsg(err.message || 'Failed to update maintenance mode');
      setSuccessMsg(null);
    }
  });

  const handleToggleMaintenance = (enable: boolean) => {
    toggleMaintenanceMutation.mutate({
      is_enabled: enable,
      scope: mScope,
      reason: mReason || undefined,
      message: mMessage || undefined
    });
  };

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 flex items-center gap-2">
          <Settings className="w-7 h-7 text-blue-600" /> Application Settings & Maintenance Mode
        </h1>
        <p className="text-slate-500 dark:text-slate-400 text-sm">
          Control application-wide settings and activate scoped maintenance windows for service components.
        </p>
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

      {/* Maintenance Mode Controller */}
      <Card className={maintenance?.is_enabled ? 'border-amber-500 dark:border-amber-700 bg-amber-50/20' : ''}>
        <CardHeader>
          <div className="flex justify-between items-center">
            <div>
              <CardTitle className="text-lg flex items-center gap-2">
                <Wrench className="w-5 h-5 text-amber-600" /> Scoped Maintenance Mode Controller
              </CardTitle>
              <CardDescription>
                When enabled, specified user-facing features will display an informative maintenance notice.
              </CardDescription>
            </div>
            {isLoading ? (
              <Skeleton className="h-6 w-20" />
            ) : (
              <Badge variant={maintenance?.is_enabled ? 'destructive' : 'default'}>
                {maintenance?.is_enabled ? 'MAINTENANCE ACTIVE' : 'SYSTEM OPERATIONAL'}
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Target Maintenance Scope</label>
              <select
                value={mScope}
                onChange={(e) => setMScope(e.target.value)}
                className="w-full px-3 py-2 border rounded-md dark:bg-slate-900 dark:border-slate-700 text-sm"
              >
                <option value="all">Entire Application (All Services)</option>
                <option value="report_analysis">Medical Report Analysis Pipeline</option>
                <option value="chat">Medical Assistant Chatbot</option>
                <option value="translation">Multi-lingual Translation Engine</option>
                <option value="notifications">Push Notifications</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Maintenance Reason (Internal Audit Log)</label>
              <input
                type="text"
                value={mReason}
                onChange={(e) => setMReason(e.target.value)}
                placeholder="Database schema migration / maintenance"
                className="w-full px-3 py-2 border rounded-md dark:bg-slate-900 dark:border-slate-700 text-sm"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">User Notice Message (Publicly Displayed)</label>
            <textarea
              rows={2}
              value={mMessage}
              onChange={(e) => setMMessage(e.target.value)}
              placeholder="MedNarrate report processing is undergoing scheduled maintenance. Please try again shortly."
              className="w-full px-3 py-2 border rounded-md dark:bg-slate-900 dark:border-slate-700 text-sm"
            />
          </div>

          <div className="flex gap-3 pt-2">
            {!maintenance?.is_enabled ? (
              <Button
                type="button"
                onClick={() => handleToggleMaintenance(true)}
                disabled={toggleMaintenanceMutation.isPending}
                className="bg-amber-600 hover:bg-amber-700 text-white"
              >
                Activate Maintenance Mode
              </Button>
            ) : (
              <Button
                type="button"
                onClick={() => handleToggleMaintenance(false)}
                disabled={toggleMaintenanceMutation.isPending}
                className="bg-emerald-600 hover:bg-emerald-700 text-white"
              >
                Disable Maintenance Mode & Resume Operations
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
