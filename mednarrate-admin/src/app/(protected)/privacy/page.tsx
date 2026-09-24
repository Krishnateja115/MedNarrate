/* eslint-disable */
'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { Lock, ShieldAlert, CheckCircle, FileText } from 'lucide-react';

interface PrivacyRequest {
  id: string;
  user_id: string;
  user_email: string;
  user_full_name: string | null;
  request_type: string; // access, export, deletion
  status: string; // requested, under_review, approved, processing, completed, rejected
  reason: string | null;
  admin_notes: string | null;
  requested_at: string | null;
  reviewed_at: string | null;
  completed_at: string | null;
}

export default function PrivacyCenterPage() {
  const queryClient = useQueryClient();
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'requests' | 'history'>('requests');

  const { data, isLoading } = useQuery<{ requests: PrivacyRequest[] }>({
    queryKey: ['privacy-requests'],
    queryFn: () => fetchApi('/api/v1/admin/privacy/requests'),
  });

  const { data: historyData, isLoading: isLoadingHistory } = useQuery<{ sensitive_access_logs: any[] }>({
    queryKey: ['privacy-history'],
    queryFn: () => fetchApi('/api/v1/admin/privacy/sensitive-access-history'),
  });

  const updateStatusMutation = useMutation({
    mutationFn: ({ id, status, notes }: { id: string; status: string; notes?: string }) =>
      fetchApi(`/api/v1/admin/privacy/requests/${id}/status`, {
        method: 'PATCH',
        data: { status, admin_notes: notes }
      }),
    onSuccess: () => {
      setSuccessMsg('Privacy request status updated successfully');
      setErrorMsg(null);
      queryClient.invalidateQueries({ queryKey: ['privacy-requests'] });
    },
    onError: (err: any) => {
      setErrorMsg(err.message || 'Failed to update request status');
      setSuccessMsg(null);
    }
  });

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 flex items-center gap-2">
          <Lock className="w-7 h-7 text-blue-600" /> Privacy & Data Requests Center
        </h1>
        <p className="text-slate-500 dark:text-slate-400 text-sm">
          GDPR/HIPAA compliance requests (Data Access, Export, Deletion) and Sensitive Access Audit History.
        </p>
      </div>

      <div className="flex border-b border-slate-200 dark:border-slate-800 gap-4">
        <button
          onClick={() => setActiveTab('requests')}
          className={`pb-3 text-sm font-semibold border-b-2 transition-colors ${
            activeTab === 'requests'
              ? 'border-blue-600 text-blue-600 dark:text-blue-400'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          Data Access / Export / Deletion Requests
        </button>
        <button
          onClick={() => setActiveTab('history')}
          className={`pb-3 text-sm font-semibold border-b-2 transition-colors ${
            activeTab === 'history'
              ? 'border-blue-600 text-blue-600 dark:text-blue-400'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          Sensitive Access Audit History
        </button>
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

      {activeTab === 'requests' ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">User Privacy Requests</CardTitle>
            <CardDescription>Review and process user data export and account deletion requests.</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            ) : !data?.requests || data.requests.length === 0 ? (
              <div className="text-center py-8 text-slate-500">No user privacy requests submitted.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
                  <thead className="text-xs uppercase bg-slate-50 dark:bg-slate-900 text-slate-500">
                    <tr>
                      <th className="px-4 py-3">User</th>
                      <th className="px-4 py-3">Request Type</th>
                      <th className="px-4 py-3">Requested At</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                    {data.requests.map((r) => (
                      <tr key={r.id} className="hover:bg-slate-50 dark:hover:bg-slate-900/50">
                        <td className="px-4 py-3 font-medium">
                          <div>{r.user_full_name || 'Patient'}</div>
                          <div className="text-xs text-slate-500 font-mono">{r.user_email}</div>
                        </td>
                        <td className="px-4 py-3 uppercase font-mono text-xs text-blue-600">
                          {r.request_type}
                        </td>
                        <td className="px-4 py-3 text-xs text-slate-500">
                          {r.requested_at ? new Date(r.requested_at).toLocaleString() : 'N/A'}
                        </td>
                        <td className="px-4 py-3">
                          <Badge variant="outline">{r.status}</Badge>
                        </td>
                        <td className="px-4 py-3 text-right space-x-1">
                          {r.status === 'requested' && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => updateStatusMutation.mutate({ id: r.id, status: 'under_review' })}
                            >
                              Review
                            </Button>
                          )}
                          {(r.status === 'requested' || r.status === 'under_review') && (
                            <Button
                              size="sm"
                              className="bg-emerald-600 hover:bg-emerald-700 text-white"
                              onClick={() => updateStatusMutation.mutate({ id: r.id, status: 'approved' })}
                            >
                              Approve
                            </Button>
                          )}
                          {r.status === 'approved' && (
                            <Button
                              size="sm"
                              className="bg-blue-600 hover:bg-blue-700 text-white"
                              onClick={() => updateStatusMutation.mutate({ id: r.id, status: 'completed' })}
                            >
                              Mark Completed
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
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Sensitive Access History</CardTitle>
            <CardDescription>Audit log of all sensitive patient data access events.</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoadingHistory ? (
              <Skeleton className="h-24 w-full" />
            ) : !historyData?.sensitive_access_logs || historyData.sensitive_access_logs.length === 0 ? (
              <div className="text-center py-8 text-slate-500">No sensitive data access events recorded.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
                  <thead className="text-xs uppercase bg-slate-50 dark:bg-slate-900 text-slate-500">
                    <tr>
                      <th className="px-4 py-3">Timestamp</th>
                      <th className="px-4 py-3">Admin ID</th>
                      <th className="px-4 py-3">Action</th>
                      <th className="px-4 py-3">Target Resource</th>
                      <th className="px-4 py-3">Reason</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                    {historyData.sensitive_access_logs.map((log) => (
                      <tr key={log.id}>
                        <td className="px-4 py-3 text-xs text-slate-500 font-mono">
                          {log.timestamp ? new Date(log.timestamp).toLocaleString() : 'N/A'}
                        </td>
                        <td className="px-4 py-3 font-mono text-xs">{log.actor_admin_id || 'System'}</td>
                        <td className="px-4 py-3 font-semibold text-blue-600">{log.action}</td>
                        <td className="px-4 py-3 text-xs font-mono">{log.resource_type}:{log.resource_id}</td>
                        <td className="px-4 py-3 text-xs text-slate-600 dark:text-slate-400">{log.reason || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
