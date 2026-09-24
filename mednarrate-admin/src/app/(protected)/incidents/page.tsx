 
'use client';

import { useQuery } from '@tanstack/react-query';
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

export default function IncidentsPage() {
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
          <Link href={`/incidents/${row.original.id}`} className="font-semibold text-lg hover:underline text-primary">
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
          <Link href={`/incidents/${row.original.id}`}>
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
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          Declare Incident
        </Button>
      </div>

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
