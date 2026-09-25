'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import { Database, FileText, Upload, CheckCircle2, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useState } from 'react';
import { ColumnDef } from '@tanstack/react-table';
import { DataTable } from '@/components/ui/data-table';
import { useAuth } from '@/contexts/AuthContext';
import { Forbidden } from '@/components/ui/forbidden';
import { toast } from '@/components/ui/toast';

interface KnowledgeDocument {
  id: string;
  name: string;
  version: string;
  status: string;
  approval_state: string | null;
  created_at: string;
  updated_at: string;
}

interface RagOverview {
  index_status: string;
  error_summary: string | null;
  total_chunks: number;
  total_documents: number;
  published_documents: number;
  failed_documents: number;
}

interface RagStatusResponse {
  status: string;
  overview: RagOverview;
}

// Backend returns build_pagination_response shape: { items, total, page, limit }
interface DocsResponse {
  items: KnowledgeDocument[];
  total: number;
  page: number;
  limit: number;
}

const getStatusBadge = (status: string) => {
  switch (status) {
    case 'Draft': return <Badge variant="secondary">Draft</Badge>;
    case 'Review': return <Badge className="bg-amber-500 hover:bg-amber-600">In Review</Badge>;
    case 'Approved': return <Badge className="bg-blue-500 hover:bg-blue-600">Approved</Badge>;
    case 'Published': return <Badge className="bg-emerald-500 hover:bg-emerald-600">Published</Badge>;
    case 'Archived': return <Badge variant="outline">Archived</Badge>;
    case 'Failed': return <Badge variant="destructive">Failed</Badge>;
    default: return <Badge variant="secondary">{status}</Badge>;
  }
};

const MetricCard = ({ title, value, icon, warning }: { title: string; value: React.ReactNode; icon?: React.ReactNode; warning?: boolean }) => (
  <Card className={warning ? 'border-amber-300 dark:border-amber-700' : ''}>
    <CardHeader className="flex flex-row items-center justify-between pb-2">
      <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
      {icon}
    </CardHeader>
    <CardContent>
      <div className="text-2xl font-bold">{value}</div>
    </CardContent>
  </Card>
);

export default function RagOpsPage() {
  const { can } = useAuth();
  const queryClient = useQueryClient();
  const [updatingId, setUpdatingId] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [docsPage, setDocsPage] = useState(1);
  const [docsLimit, setDocsLimit] = useState(25);

  const { data: statusData, isLoading: statusLoading, error: statusError } = useQuery<RagStatusResponse>({
    queryKey: ['rag_status'],
    queryFn: () => fetchApi('/api/v1/admin/rag-ops/status'),
    enabled: can('knowledge_base.view'),
  });

  const { data: docsData, isLoading: docsLoading, error: docsError } = useQuery<DocsResponse>({
    queryKey: ['rag_documents', docsPage, docsLimit, statusFilter],
    queryFn: () => {
      const params = new URLSearchParams();
      params.set('page', docsPage.toString());
      params.set('limit', docsLimit.toString());
      if (statusFilter !== 'all') params.set('status', statusFilter);
      return fetchApi(`/api/v1/admin/rag-ops/documents?${params.toString()}`);
    },
    enabled: can('knowledge_base.view'),
  });

  const updateStatusMutation = useMutation({
    mutationFn: async ({ id, status }: { id: string; status: string }) => {
      setUpdatingId(id);
      return fetchApi(`/api/v1/admin/rag-ops/documents/${id}/status`, {
        method: 'PATCH',
        body: JSON.stringify({ status }),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rag_documents'] });
      queryClient.invalidateQueries({ queryKey: ['rag_status'] });
      setUpdatingId(null);
      toast.add({ title: 'Document status updated.', type: 'success' });
    },
    onError: () => {
      setUpdatingId(null);
      toast.add({ title: 'Failed to update status.', type: 'error' });
    },
  });

  const columns: ColumnDef<KnowledgeDocument>[] = [
    {
      accessorKey: 'name',
      header: 'Name',
      cell: ({ row }) => <span className="font-medium">{row.original.name}</span>,
    },
    {
      accessorKey: 'version',
      header: 'Version',
      cell: ({ row }) => <span className="text-sm font-mono text-muted-foreground">{row.original.version}</span>,
    },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: ({ row }) => getStatusBadge(row.original.status),
    },
    {
      accessorKey: 'approval_state',
      header: 'Approval',
      cell: ({ row }) => (
        <span className="text-sm text-muted-foreground capitalize">
          {row.original.approval_state?.replace(/_/g, ' ') || 'None'}
        </span>
      ),
    },
    {
      accessorKey: 'updated_at',
      header: 'Last Updated',
      cell: ({ row }) => (
        <span className="text-xs text-muted-foreground">
          {new Date(row.original.updated_at).toLocaleString()}
        </span>
      ),
    },
    {
      id: 'actions',
      header: 'Lifecycle',
      cell: ({ row }) => (
        <Select
          value={row.original.status}
          onValueChange={(val) => {
            if (val && val !== row.original.status) {
              updateStatusMutation.mutate({ id: row.original.id, status: val });
            }
          }}
          disabled={updatingId === row.original.id || !can('knowledge_base.manage')}
        >
          <SelectTrigger className="w-[130px] h-8 text-xs">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="Draft">Draft</SelectItem>
            <SelectItem value="Review">Send to Review</SelectItem>
            <SelectItem value="Approved">Approve</SelectItem>
            <SelectItem value="Published">Publish</SelectItem>
            <SelectItem value="Archived">Archive</SelectItem>
          </SelectContent>
        </Select>
      ),
    },
  ];

  if (!can('knowledge_base.view')) {
    return <Forbidden />;
  }

  const overview = statusData?.overview;

  return (
    <div className="space-y-6 fade-in">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Knowledge Base & RAG</h1>
          <p className="text-muted-foreground">Manage index health and document lifecycles.</p>
        </div>
        <Button disabled title="Document upload coming soon">
          <Upload className="mr-2 h-4 w-4" /> Upload Document
        </Button>
      </div>

      <Tabs defaultValue="status" className="space-y-4">
        <TabsList>
          <TabsTrigger value="status">Index Health</TabsTrigger>
          <TabsTrigger value="documents">Documents</TabsTrigger>
        </TabsList>

        {/* ── Index Health Tab ── */}
        <TabsContent value="status" className="space-y-6">
          {statusLoading ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-32 w-full" />)}
            </div>
          ) : statusError ? (
            <div className="p-8 text-center text-destructive">Failed to load RAG status.</div>
          ) : (
            <>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <MetricCard
                  title="Index Status"
                  warning={overview?.index_status !== 'healthy'}
                  value={
                    <div className="flex items-center gap-2">
                      {overview?.index_status === 'healthy'
                        ? <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                        : <AlertTriangle className="h-5 w-5 text-amber-500" />}
                      <span className="capitalize">{overview?.index_status ?? 'unknown'}</span>
                    </div>
                  }
                />
                <MetricCard
                  title="Total Documents"
                  value={(overview?.total_documents ?? 0).toLocaleString()}
                  icon={<FileText className="h-4 w-4 text-muted-foreground" />}
                />
                <MetricCard
                  title="Published"
                  value={(overview?.published_documents ?? 0).toLocaleString()}
                  icon={<CheckCircle2 className="h-4 w-4 text-emerald-500" />}
                />
                <MetricCard
                  title="Total Vector Chunks"
                  value={(overview?.total_chunks ?? 0).toLocaleString()}
                  icon={<Database className="h-4 w-4 text-blue-500" />}
                />
              </div>

              {/* Failed documents alert */}
              {(overview?.failed_documents ?? 0) > 0 && (
                <Card className="border-red-300 bg-red-50 dark:bg-red-950/20">
                  <CardContent className="pt-4 flex items-center gap-3">
                    <AlertTriangle className="h-5 w-5 text-destructive shrink-0" />
                    <div>
                      <p className="font-semibold text-sm text-destructive">
                        {overview?.failed_documents} document{(overview?.failed_documents ?? 0) > 1 ? 's' : ''} failed ingestion
                      </p>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        Review the Documents tab, then update lifecycle to re-trigger ingestion.
                      </p>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Error summary from vector store probe */}
              {overview?.error_summary && (
                <Card className="border-amber-300 bg-amber-50 dark:bg-amber-950/20">
                  <CardContent className="pt-4 flex items-center gap-3">
                    <AlertTriangle className="h-5 w-5 text-amber-600 shrink-0" />
                    <p className="text-sm text-amber-800 dark:text-amber-300">{overview.error_summary}</p>
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </TabsContent>

        {/* ── Documents Tab ── */}
        <TabsContent value="documents">
          <Card>
            <CardHeader className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-4 gap-4">
              <div className="space-y-1">
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5 text-muted-foreground" /> Knowledge Documents
                </CardTitle>
                <CardDescription>Manage the lifecycle of documents fed into the RAG vector store.</CardDescription>
              </div>
              <Select
                value={statusFilter}
                onValueChange={(val) => { setStatusFilter(val || 'all'); setDocsPage(1); }}
              >
                <SelectTrigger className="w-[140px]">
                  <SelectValue placeholder="Filter status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  <SelectItem value="Draft">Draft</SelectItem>
                  <SelectItem value="Review">In Review</SelectItem>
                  <SelectItem value="Approved">Approved</SelectItem>
                  <SelectItem value="Published">Published</SelectItem>
                  <SelectItem value="Archived">Archived</SelectItem>
                  <SelectItem value="Failed">Failed</SelectItem>
                </SelectContent>
              </Select>
            </CardHeader>
            <CardContent>
              {docsError ? (
                <div className="p-8 text-center text-destructive">Failed to load documents.</div>
              ) : (
                <DataTable
                  columns={columns}
                  data={docsData?.items || []}
                  pageCount={docsData ? Math.ceil(docsData.total / docsData.limit) : 0}
                  pageIndex={docsPage - 1}
                  pageSize={docsLimit}
                  total={docsData?.total || 0}
                  isLoading={docsLoading}
                  onPageChange={(p) => setDocsPage(p + 1)}
                  onPageSizeChange={(s) => { setDocsLimit(s); setDocsPage(1); }}
                  onSortChange={() => {}}
                />
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
