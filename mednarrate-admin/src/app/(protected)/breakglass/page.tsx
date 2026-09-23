'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { Key, AlertTriangle, ShieldAlert, CheckCircle, Clock, XCircle } from 'lucide-react';

interface BreakGlassGrant {
  id: string;
  admin_id: string;
  admin_email: string;
  resource_type: string;
  resource_id: string;
  reason: string;
  status: string; // active, expired, revoked
  created_at: string | null;
  expires_at: string | null;
  revoked_at: string | null;
}

export default function BreakGlassPage() {
  const queryClient = useQueryClient();
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const [showRequestForm, setShowRequestForm] = useState(false);
  const [resourceType, setResourceType] = useState('patient_medical_record');
  const [resourceId, setResourceId] = useState('');
  const [reason, setReason] = useState('');
  const [durationMinutes, setDurationMinutes] = useState(30);

  const { data, isLoading } = useQuery<{ grants: BreakGlassGrant[] }>({
    queryKey: ['break-glass-grants'],
    queryFn: () => fetchApi('/api/v1/admin/break-glass/grants'),
  });

  const requestGrantMutation = useMutation({
    mutationFn: (newReq: any) => fetchApi('/api/v1/admin/break-glass/request', { data: newReq }),
    onSuccess: () => {
      setSuccessMsg('Temporary sensitive access grant issued successfully');
      setErrorMsg(null);
      setShowRequestForm(false);
      setResourceId('');
      setReason('');
      queryClient.invalidateQueries({ queryKey: ['break-glass-grants'] });
    },
    onError: (err: any) => {
      setErrorMsg(err.message || 'Failed to request break-glass access');
      setSuccessMsg(null);
    }
  });

  const revokeGrantMutation = useMutation({
    mutationFn: (grantId: string) => fetchApi(`/api/v1/admin/break-glass/grants/${grantId}/revoke`, { method: 'POST' }),
    onSuccess: () => {
      setSuccessMsg('Sensitive access grant revoked successfully');
      setErrorMsg(null);
      queryClient.invalidateQueries({ queryKey: ['break-glass-grants'] });
    },
    onError: (err: any) => {
      setErrorMsg(err.message || 'Failed to revoke access grant');
      setSuccessMsg(null);
    }
  });

  const handleRequestSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!resourceId || reason.length < 10) {
      setErrorMsg('Please provide a valid resource ID and a detailed reason (at least 10 characters)');
      return;
    }

    requestGrantMutation.mutate({
      resource_type: resourceType,
      resource_id: resourceId,
      reason: reason,
      duration_minutes: durationMinutes
    });
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <Key className="w-7 h-7 text-amber-500" /> Temporary Sensitive Access (Break-Glass)
          </h1>
          <p className="text-slate-500 dark:text-slate-400 text-sm">
            Time-bound, emergency access requests with mandatory audit justification and automatic backend expiration.
          </p>
        </div>
        <Button onClick={() => setShowRequestForm(!showRequestForm)} className="flex items-center gap-2 bg-amber-600 hover:bg-amber-700 text-white">
          <AlertTriangle className="w-4 h-4" /> {showRequestForm ? 'Cancel Request' : 'Request Break-Glass Access'}
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

      {showRequestForm && (
        <Card className="border-amber-300 dark:border-amber-900 bg-amber-50/40 dark:bg-amber-950/20">
          <CardHeader>
            <CardTitle className="text-lg font-bold text-amber-900 dark:text-amber-200 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5" /> Emergency Sensitive Access Request Form
            </CardTitle>
            <CardDescription>
              All emergency break-glass requests are logged permanently in audit records.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleRequestSubmit} className="space-y-4 max-w-xl">
              <div>
                <label className="block text-sm font-medium mb-1">Target Resource Type</label>
                <select
                  value={resourceType}
                  onChange={(e) => setResourceType(e.target.value)}
                  className="w-full px-3 py-2 border rounded-md dark:bg-slate-900 dark:border-slate-700 text-sm"
                >
                  <option value="patient_medical_record">Patient Medical Record / Report</option>
                  <option value="user_pii">User PII / Identity Data</option>
                  <option value="raw_llm_transcript">Raw LLM Diagnostic Transcript</option>
                  <option value="system_encryption_key">System Key / Config Vault</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Target Resource ID</label>
                <input
                  type="text"
                  required
                  value={resourceId}
                  onChange={(e) => setResourceId(e.target.value)}
                  placeholder="e.g. rep_8f92a40b"
                  className="w-full px-3 py-2 border rounded-md dark:bg-slate-900 dark:border-slate-700 text-sm font-mono"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Duration (Minutes)</label>
                <select
                  value={durationMinutes}
                  onChange={(e) => setDurationMinutes(Number(e.target.value))}
                  className="w-full px-3 py-2 border rounded-md dark:bg-slate-900 dark:border-slate-700 text-sm"
                >
                  <option value={15}>15 Minutes</option>
                  <option value={30}>30 Minutes (Recommended)</option>
                  <option value={60}>60 Minutes</option>
                  <option value={120}>120 Minutes (Max Limit)</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Clinical / Operational Justification (Reason)</label>
                <textarea
                  required
                  rows={3}
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="Enter detailed reason for emergency access..."
                  className="w-full px-3 py-2 border rounded-md dark:bg-slate-900 dark:border-slate-700 text-sm"
                />
              </div>

              <Button type="submit" disabled={requestGrantMutation.isPending} className="bg-amber-600 hover:bg-amber-700 text-white">
                {requestGrantMutation.isPending ? 'Submitting Request...' : 'Issue Temporary Access Grant'}
              </Button>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Access Grants Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Sensitive Access Grants</CardTitle>
          <CardDescription>
            Grants automatically expire on the backend when duration elapses. Administrators can manually revoke grants.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : !data?.grants || data.grants.length === 0 ? (
            <div className="text-center py-8 text-slate-500">No break-glass access grants issued.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="text-xs uppercase bg-slate-50 dark:bg-slate-900 text-slate-500">
                  <tr>
                    <th className="px-4 py-3">Admin Email</th>
                    <th className="px-4 py-3">Resource Target</th>
                    <th className="px-4 py-3">Justification</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Expires At</th>
                    <th className="px-4 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                  {data.grants.map((grant) => (
                    <tr key={grant.id} className="hover:bg-slate-50 dark:hover:bg-slate-900/50">
                      <td className="px-4 py-3 font-medium">{grant.admin_email}</td>
                      <td className="px-4 py-3 font-mono text-xs">
                        <span className="text-slate-500">{grant.resource_type}:</span> {grant.resource_id}
                      </td>
                      <td className="px-4 py-3 text-xs text-slate-600 dark:text-slate-400 max-w-xs truncate">
                        {grant.reason}
                      </td>
                      <td className="px-4 py-3">
                        <Badge
                          variant={
                            grant.status === 'active'
                              ? 'default'
                              : grant.status === 'expired'
                              ? 'secondary'
                              : 'destructive'
                          }
                          className={
                            grant.status === 'active'
                              ? 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300'
                              : ''
                          }
                        >
                          {grant.status.toUpperCase()}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-xs font-mono text-slate-500">
                        {grant.expires_at ? new Date(grant.expires_at).toLocaleTimeString() : 'N/A'}
                      </td>
                      <td className="px-4 py-3 text-right">
                        {grant.status === 'active' && (
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => revokeGrantMutation.mutate(grant.id)}
                            disabled={revokeGrantMutation.isPending}
                          >
                            Revoke Now
                          </Button>
                        )}
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
