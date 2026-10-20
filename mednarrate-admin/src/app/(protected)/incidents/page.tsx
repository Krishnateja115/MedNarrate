 
'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { fetchApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Activity, Plus, AlertTriangle } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import Link from 'next/link';
import { formatDistanceToNow } from 'date-fns';
import { useState } from 'react';
import { ColumnDef } from '@tanstack/react-table';
import { DataTable } from '@/components/ui/data-table';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from '@/components/ui/toast';
import { useRouter } from 'next/navigation';

interface Incident {
  id: string;
  title: string;
  severity: string;
  status: string;
  affected_service: string | null;
  started_at: string;
  resolved_at: string | null;
  summary: string | null;
}

interface IncidentsResponse {
  items: Incident[];
  total: number;
  page: number;
  limit: number;
}

const SEVERITIES = ['SEV-1', 'SEV-2', 'SEV-3', 'SEV-4'] as const;
const EMPTY_FORM = { title: '', severity: 'SEV-3', affected_service: '', summary: '' };

export default function IncidentsPage() {
  const { can } = useAuth();
  const router = useRouter();
  const queryClient = useQueryClient();
  const canManage = can('incidents.manage');
  const [declareOpen, setDeclareOpen] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [formError, setFormError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(25);
  const [sortState, setSortState] = useState<{id: string, desc: boolean}>({ id: 'started_at', desc: true });

  const queryParams = new URLSearchParams();
  queryParams.set('page', page.toString());
  queryParams.set('limit', limit.toString());
  queryParams.set('sort_by', sortState.id);
  queryParams.set('sort_desc', sortState.desc.toString());

  const { data, isLoading, error } = useQuery<IncidentsResponse>({
    queryKey: ['incidents', page, limit, sortState],
    queryFn: () => fetchApi(`/api/v1/admin/incidents?${queryParams.toString()}`),
  });

  const declareMutation = useMutation<{ status: string; incident_id: string }, Error, void>({
    mutationFn: () =>
      fetchApi('/api/v1/admin/incidents', {
        method: 'POST',
        data: {
          title: form.title.trim(),
          severity: form.severity,
          affected_service: form.affected_service.trim() || null,
          summary: form.summary.trim() || null,
        },
      }),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['incidents'] });
      setDeclareOpen(false);
      setForm(EMPTY_FORM);
      setFormError(null);
      toast.add({ title: 'Incident declared.', type: 'success' });
      if (result?.incident_id) router.push(`/incidents/detail?id=${result.incident_id}`);
    },
    onError: (err) => setFormError(err.message || 'Could not declare the incident.'),
  });

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'SEV-1':
        return <Badge variant="destructive" className="font-mono">SEV-1</Badge>;
      case 'SEV-2':
        return <Badge variant="destructive" className="bg-orange-600 hover:bg-orange-700 font-mono">SEV-2</Badge>;
      case 'SEV-3':
        return <Badge variant="outline" className="text-amber-600 border-amber-600 font-mono">SEV-3</Badge>;
      default:
        return <Badge variant="secondary" className="font-mono">{severity}</Badge>;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'open':
        return <Badge variant="destructive">Open</Badge>;
      case 'investigating':
        return <Badge className="bg-amber-500 hover:bg-amber-600">Investigating</Badge>;
      case 'identified':
        return <Badge className="bg-blue-500 hover:bg-blue-600">Identified</Badge>;
      case 'resolved':
        return <Badge className="bg-emerald-500 hover:bg-emerald-600">Resolved</Badge>;
      case 'closed':
        return <Badge variant="secondary">Closed</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const columns: ColumnDef<Incident>[] = [
    {
      accessorKey: 'title',
      header: 'Incident',
      cell: ({ row }) => (
        <div className="space-y-1">
          <Link href={`/incidents/detail?id=${row.original.id}`} className="font-semibold text-lg hover:underline text-primary">
            {row.getValue('title')}
          </Link>
          <div className="text-sm text-muted-foreground line-clamp-1">
            {row.original.summary || 'No summary provided.'}
          </div>
          {row.original.affected_service && (
            <div className="mt-1 text-xs font-medium text-slate-500 bg-slate-100 dark:bg-slate-800 dark:text-slate-400 inline-block px-2 py-0.5 rounded">
              Service: {row.original.affected_service}
            </div>
          )}
        </div>
      ),
    },
    {
      accessorKey: 'severity',
      header: 'Severity',
      cell: ({ row }) => getSeverityBadge(row.getValue('severity')),
    },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: ({ row }) => getStatusBadge(row.getValue('status')),
    },
    {
      accessorKey: 'started_at',
      header: 'Started At',
      cell: ({ row }) => (
        <div className="text-sm">
          <div>{new Date(row.getValue('started_at')).toLocaleDateString()} {new Date(row.getValue('started_at')).toLocaleTimeString()}</div>
          <div className="text-xs text-muted-foreground mt-1">
            {row.original.resolved_at ? (
              <span>Resolved: {new Date(row.original.resolved_at).toLocaleDateString()}</span>
            ) : (
              <span className="text-orange-500 font-medium">
                Active for {formatDistanceToNow(new Date(row.getValue('started_at')))}
              </span>
            )}
          </div>
        </div>
      ),
    },
    {
      id: 'actions',
      header: () => <div className="text-right">Details</div>,
      cell: ({ row }) => (
        <div className="text-right">
          <Link href={`/incidents/detail?id=${row.original.id}`}>
            <Button variant="ghost" size="sm">View</Button>
          </Link>
        </div>
      ),
      enableSorting: false,
    },
  ];

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Incidents</h1>
            <Skeleton className="h-4 w-48 mt-2" />
          </div>
        </div>
        <Card>
          <CardContent className="p-6 space-y-4">
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Incidents</h1>
        </div>
        <div className="rounded-md bg-destructive/15 p-4 text-destructive border border-destructive/20">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="h-5 w-5" />
            <h3 className="font-semibold">Failed to load incidents</h3>
          </div>
          <p className="mt-2 text-sm">Please check your connection or ensure you have the required permissions.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Incidents</h1>
          <p className="text-muted-foreground mt-2">Track, investigate, and resolve system anomalies.</p>
        </div>
        {canManage && (
          <Button onClick={() => { setForm(EMPTY_FORM); setFormError(null); setDeclareOpen(true); }}>
            <Plus className="mr-2 h-4 w-4" />
            Declare Incident
          </Button>
        )}
      </div>

      <Dialog open={declareOpen} onOpenChange={setDeclareOpen}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>Declare incident</DialogTitle>
            <DialogDescription>Record a new system problem so the team can track it to resolution.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="incident-title">Title</Label>
              <Input id="incident-title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="Report analysis is failing" />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="incident-severity">Severity</Label>
                <select
                  id="incident-severity"
                  className="h-8 w-full rounded-lg border border-input bg-background px-2.5 text-sm"
                  value={form.severity}
                  onChange={(e) => setForm({ ...form, severity: e.target.value })}
                >
                  {SEVERITIES.map((sev) => <option key={sev} value={sev}>{sev}</option>)}
                </select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="incident-service">Affected service (optional)</Label>
                <Input id="incident-service" value={form.affected_service} onChange={(e) => setForm({ ...form, affected_service: e.target.value })} placeholder="worker" />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="incident-summary">Summary (optional)</Label>
              <Textarea id="incident-summary" value={form.summary} onChange={(e) => setForm({ ...form, summary: e.target.value })} />
            </div>
            {formError && <p className="text-sm text-destructive">{formError}</p>}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeclareOpen(false)}>Cancel</Button>
            <Button onClick={() => declareMutation.mutate()} disabled={declareMutation.isPending || !form.title.trim()}>
              {declareMutation.isPending ? 'Declaring...' : 'Declare incident'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Card>
        <CardHeader className="border-b bg-slate-50/50 dark:bg-slate-900/50">
          <CardTitle className="text-base flex items-center gap-2">
            <Activity className="h-4 w-4" />
            Incident Log
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4">
          <DataTable
            columns={columns}
            data={data.items || []}
            pageCount={Math.ceil(data.total / data.limit) || 1}
            pageIndex={page - 1}
            pageSize={limit}
            total={data.total || 0}
            isLoading={isLoading}
            onPageChange={(p) => setPage(p + 1)}
            onPageSizeChange={(s) => { setLimit(s); setPage(1); }}
            onSortChange={(s) => setSortState(s)}
            sortState={sortState}
          />
        </CardContent>
      </Card>
    </div>
  );
}
