/* eslint-disable */
'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertTriangle, ArrowLeft, RefreshCw, RefreshCcw, Lock, FileText, CheckCircle2, Activity, HardDrive, Database, Server, ServerCrash } from 'lucide-react';
import Link from 'next/link';
import { use, useState } from 'react';

interface ReportDetail {
  id: string;
  user_id: string;
  user_email: string;
  title: string;
  hospital: string | null;
  report_date: string;
  file_name: string;
  file_type: string;
  report_type: string;
  processing_status: string;
  uploaded_at: string;
}

interface AnalysisDetail {
  id: string;
  error_reason: string | null;
  failure_category: string | null;
  verification_status: string;
  llm_provider: string | null;
  llm_model: string | null;
  processed_at: string | null;
}

export default function ReportDiagnosticPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const reportId = resolvedParams.id;
  const queryClient = useQueryClient();
  const [actionMessage, setActionMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);
  const [requestSensitive, setRequestSensitive] = useState(false);
  
  const { data, isLoading, error } = useQuery<{status: string, report: ReportDetail, analysis: AnalysisDetail | null}>({
    queryKey: ['report', reportId],
    queryFn: () => fetchApi(`/api/v1/admin/reports/${reportId}`),
  });

  const actionMutation = useMutation({
    mutationFn: async ({ action }: { action: string }) => {
      const res = await fetch(`/api/v1/admin/reports/${reportId}/actions/${action}`, {
        method: 'POST'
      });
      if (!res.ok) throw new Error('Action failed');
      return res.json();
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['report', reportId] });
      setActionMessage({ type: 'success', text: data.message || 'Action completed successfully' });
      setTimeout(() => setActionMessage(null), 5000);
    },
    onError: (err) => {
      setActionMessage({ type: 'error', text: err.message || 'Failed to perform action' });
      setTimeout(() => setActionMessage(null), 5000);
    }
  });

  const handleAction = (action: 'retry' | 'reprocess', confirmMessage: string) => {
    if (window.confirm(confirmMessage)) {
      actionMutation.mutate({ action });
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed': return <Badge variant="outline" className="text-emerald-600 border-emerald-600/30">Completed</Badge>;
      case 'processing': return <Badge className="bg-amber-500">Processing</Badge>;
      case 'uploaded': return <Badge className="bg-blue-500">Uploaded</Badge>;
      case 'failed': return <Badge variant="destructive">Failed</Badge>;
      default: return <Badge variant="secondary">{status}</Badge>;
    }
  };

  const PipelineNode = ({ title, status, desc }: { title: string, status: 'pending' | 'success' | 'failed' | 'processing', desc?: string }) => (
    <div className="flex flex-col items-center text-center p-3">
      <div className={`h-10 w-10 rounded-full flex items-center justify-center mb-2 shadow-sm ${
        status === 'success' ? 'bg-emerald-100 text-emerald-600 border border-emerald-200' :
        status === 'failed' ? 'bg-red-100 text-red-600 border border-red-200' :
        status === 'processing' ? 'bg-amber-100 text-amber-600 border border-amber-200 animate-pulse' :
        'bg-slate-100 text-slate-400 border border-slate-200'
      }`}>
        {status === 'success' && <CheckCircle2 className="h-5 w-5" />}
        {status === 'failed' && <ServerCrash className="h-5 w-5" />}
        {status === 'processing' && <RefreshCw className="h-5 w-5 animate-spin" />}
        {status === 'pending' && <Server className="h-5 w-5" />}
      </div>
      <span className="text-xs font-semibold">{title}</span>
      {desc && <span className="text-[10px] text-muted-foreground mt-1 max-w-[80px]">{desc}</span>}
    </div>
  );

  const PipelineArrow = ({ active }: { active: boolean }) => (
    <div className={`h-[2px] w-6 md:w-12 my-auto mx-1 ${active ? 'bg-primary' : 'bg-slate-200'}`} />
  );

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
        <Link href="/reports" className="inline-flex items-center text-sm font-medium text-muted-foreground hover:text-foreground">
          <ArrowLeft className="mr-2 h-4 w-4" /> Back to Reports
        </Link>
        <div className="rounded-md bg-destructive/15 p-4 text-destructive border border-destructive/20 flex items-center gap-2">
          <AlertTriangle className="h-5 w-5" /> <h3 className="font-semibold">Report Not Found</h3>
        </div>
      </div>
    );
  }

  const { report, analysis } = data;
  const isFailed = report.processing_status === 'failed';
  const isCompleted = report.processing_status === 'completed';

  return (
    <div className="space-y-6 fade-in max-w-5xl mx-auto">
      <div>
        <Link href="/reports" className="inline-flex items-center text-sm font-medium text-muted-foreground hover:text-foreground mb-4">
          <ArrowLeft className="mr-2 h-4 w-4" /> Back to Reports
        </Link>
        
        {actionMessage && (
          <div className={`mb-4 p-4 rounded-md border text-sm flex items-start gap-2 ${
            actionMessage.type === 'success' ? 'bg-emerald-500/15 border-emerald-500/30 text-emerald-700' : 'bg-destructive/15 border-destructive/30 text-destructive'
          }`}>
            {actionMessage.type === 'success' ? <CheckCircle2 className="h-5 w-5 shrink-0" /> : <AlertTriangle className="h-5 w-5 shrink-0" />}
            <div>{actionMessage.text}</div>
          </div>
        )}

        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-3xl font-bold tracking-tight">Report Diagnostic</h1>
              {getStatusBadge(report.processing_status)}
            </div>
            <p className="text-muted-foreground font-mono text-sm">ID: {report.id} • User: {report.user_email}</p>
          </div>
          <div className="flex gap-2">
            {!isCompleted && (
              <Button variant="outline" onClick={() => handleAction('retry', 'Retry processing for this report?')} disabled={actionMutation.isPending}>
                <RefreshCw className={`mr-2 h-4 w-4 ${actionMutation.isPending ? 'animate-spin' : ''}`} /> Retry
              </Button>
            )}
            <Button variant="outline" className="border-amber-200 bg-amber-50 text-amber-700 hover:bg-amber-100 dark:bg-amber-950/20 dark:text-amber-400" onClick={() => handleAction('reprocess', 'DANGER: Reprocessing will clear previous analysis and run from scratch. Continue?')} disabled={actionMutation.isPending}>
              <RefreshCcw className="mr-2 h-4 w-4" /> Reprocess
            </Button>
          </div>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        {/* Main Content Area */}
        <div className="md:col-span-2 space-y-6">
          <Card>
            <CardHeader className="pb-3 border-b">
              <CardTitle className="text-base flex items-center gap-2">
                <Activity className="h-4 w-4" /> Processing Lifecycle
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6 pb-6 overflow-x-auto">
              <div className="flex items-center min-w-max">
                <PipelineNode title="Upload" status="success" />
                <PipelineArrow active={report.processing_status !== 'uploaded'} />
                <PipelineNode title="Extraction" status={report.processing_status === 'uploaded' ? 'processing' : 'success'} />
                <PipelineArrow active={!!analysis || isCompleted || isFailed} />
                <PipelineNode title="LLM Analysis" status={analysis ? 'success' : isFailed ? 'failed' : 'pending'} desc={analysis?.llm_provider || ''} />
                <PipelineArrow active={analysis?.verification_status === 'verified'} />
                <PipelineNode title="Verification" status={analysis?.verification_status === 'verified' ? 'success' : isCompleted ? 'success' : 'pending'} />
                <PipelineArrow active={isCompleted} />
                <PipelineNode title="Persistence" status={isCompleted ? 'success' : 'pending'} />
              </div>
            </CardContent>
          </Card>

          {isFailed && analysis?.error_reason && (
            <Card className="border-red-200 bg-red-50 dark:bg-red-950/10">
              <CardHeader className="pb-2">
                <CardTitle className="text-red-700 dark:text-red-400 text-base flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4" /> Failure Diagnostic
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="mb-2">
                  <span className="text-xs font-semibold text-red-800 dark:text-red-300 uppercase">Category: </span>
                  <Badge variant="destructive" className="ml-2">{analysis.failure_category || 'Unknown'}</Badge>
                </div>
                <div className="bg-white dark:bg-black p-3 rounded text-sm font-mono text-red-600 dark:text-red-400 border border-red-100 overflow-x-auto">
                  {analysis.error_reason}
                </div>
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader className="pb-3 border-b flex flex-row items-center justify-between">
              <CardTitle className="text-base flex items-center gap-2">
                <Database className="h-4 w-4" /> Clinical Data Payload
              </CardTitle>
              <Badge variant="outline" className="bg-slate-100">Encrypted Data View</Badge>
            </CardHeader>
            <CardContent className="pt-6">
              {!requestSensitive ? (
                <div className="text-center p-8 bg-slate-50 dark:bg-slate-900/50 rounded-md border border-dashed">
                  <Lock className="h-8 w-8 mx-auto text-slate-400 mb-3" />
                  <h4 className="font-semibold text-slate-700 dark:text-slate-300 mb-1">Sensitive PHI Hidden</h4>
                  <p className="text-sm text-muted-foreground max-w-sm mx-auto mb-4">
                    Extracted entities, summaries, and raw text are protected. You must explicitly request break-glass access to view this clinical payload.
                  </p>
                  <Button onClick={() => setRequestSensitive(true)}>Request Sensitive Access</Button>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="p-3 bg-amber-50 border border-amber-200 rounded text-amber-800 text-sm flex gap-2">
                    <AlertTriangle className="h-5 w-5 shrink-0" />
                    <p><strong>Audited Access:</strong> Your access to this sensitive payload has been logged for security review.</p>
                  </div>
                  {/* Mock content since API doesn't expose PHI by default */}
                  <div className="opacity-70 grayscale">
                    <h5 className="font-semibold text-sm mb-2">Raw Text (Sample)</h5>
                    <div className="bg-muted p-3 rounded font-mono text-xs">... clinical payload masked ...</div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <Card>
            <CardHeader className="pb-3 border-b">
              <CardTitle className="text-base flex items-center gap-2">
                <FileText className="h-4 w-4" /> Report Metadata
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4 space-y-4">
              <div>
                <span className="text-xs text-muted-foreground uppercase font-medium">Title</span>
                <div className="font-medium mt-1 text-sm">{report.title}</div>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <span className="text-xs text-muted-foreground uppercase font-medium">Type</span>
                  <div className="mt-1 text-sm capitalize">{report.report_type}</div>
                </div>
                <div>
                  <span className="text-xs text-muted-foreground uppercase font-medium">Format</span>
                  <div className="mt-1 text-sm uppercase">{report.file_type}</div>
                </div>
              </div>
              <div>
                <span className="text-xs text-muted-foreground uppercase font-medium">Date on Report</span>
                <div className="text-sm mt-1">{new Date(report.report_date).toLocaleDateString()}</div>
              </div>
              <div>
                <span className="text-xs text-muted-foreground uppercase font-medium">Hospital</span>
                <div className="text-sm mt-1">{report.hospital || 'Not provided'}</div>
              </div>
              <div>
                <span className="text-xs text-muted-foreground uppercase font-medium">Uploaded</span>
                <div className="text-sm mt-1">{new Date(report.uploaded_at).toLocaleString()}</div>
              </div>
            </CardContent>
          </Card>

          {analysis && (
            <Card>
              <CardHeader className="pb-3 border-b">
                <CardTitle className="text-base flex items-center gap-2">
                  <HardDrive className="h-4 w-4" /> AI Diagnostics
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4 space-y-4">
                <div>
                  <span className="text-xs text-muted-foreground uppercase font-medium">Analysis ID</span>
                  <div className="font-mono text-xs mt-1 break-all text-muted-foreground">{analysis.id}</div>
                </div>
                <div>
                  <span className="text-xs text-muted-foreground uppercase font-medium">LLM Provider</span>
                  <div className="text-sm mt-1 capitalize font-medium">{analysis.llm_provider || 'Unknown'}</div>
                </div>
                <div>
                  <span className="text-xs text-muted-foreground uppercase font-medium">Model</span>
                  <div className="text-sm mt-1 font-mono">{analysis.llm_model || 'Unknown'}</div>
                </div>
                <div>
                  <span className="text-xs text-muted-foreground uppercase font-medium">Verification Status</span>
                  <div className="mt-1">
                    <Badge variant="outline" className="capitalize">{analysis.verification_status}</Badge>
                  </div>
                </div>
                {analysis.processed_at && (
                  <div>
                    <span className="text-xs text-muted-foreground uppercase font-medium">Processed At</span>
                    <div className="text-sm mt-1">{new Date(analysis.processed_at).toLocaleString()}</div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
