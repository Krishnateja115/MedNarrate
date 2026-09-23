'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Skeleton } from '@/components/ui/skeleton';
import { Database, FileText, Upload, CheckCircle2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useState } from 'react';

interface KnowledgeDocument {
  id: string;
  name: string;
  version: string;
  status: string;
  approval_state: string | null;
  created_at: string;
  updated_at: string;
}

interface RagStatus {
  index_status: string;
  total_chunks: number;
  total_documents: number;
  published_documents: number;
}

export default function RagOpsPage() {
  const queryClient = useQueryClient();
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  const { data: statusData, isLoading: statusLoading } = useQuery<{status: string, overview: RagStatus}>({
    queryKey: ['rag_status'],
    queryFn: () => fetchApi('/api/v1/admin/rag-ops/status'),
  });

  const { data: docsData, isLoading: docsLoading } = useQuery<{status: string, documents: KnowledgeDocument[]}>({
    queryKey: ['rag_documents'],
    queryFn: () => fetchApi('/api/v1/admin/rag-ops/documents'),
  });

  const updateStatusMutation = useMutation({
    mutationFn: async ({ id, status }: { id: string, status: string }) => {
      setUpdatingId(id);
      const res = await fetch(`/api/v1/admin/rag-ops/documents/${id}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status })
      });
      if (!res.ok) throw new Error('Failed to update status');
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rag_documents'] });
      queryClient.invalidateQueries({ queryKey: ['rag_status'] });
      setUpdatingId(null);
    },
    onError: () => setUpdatingId(null)
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'Draft': return <Badge variant="secondary">Draft</Badge>;
      case 'Review': return <Badge className="bg-amber-500">In Review</Badge>;
      case 'Approved': return <Badge className="bg-blue-500">Approved</Badge>;
      case 'Published': return <Badge className="bg-emerald-500">Published</Badge>;
      case 'Archived': return <Badge variant="outline">Archived</Badge>;
      default: return <Badge variant="secondary">{status}</Badge>;
    }
  };

  const MetricCard = ({ title, value, icon }: any) => (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
        {icon}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
      </CardContent>
    </Card>
  );

  return (
    <div className="space-y-6 fade-in">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Knowledge Base & RAG</h1>
          <p className="text-muted-foreground">Manage index health and document lifecycles.</p>
        </div>
        <Button disabled>
          <Upload className="mr-2 h-4 w-4" /> Upload Document
        </Button>
      </div>

      <Tabs defaultValue="documents" className="space-y-4">
        <TabsList>
          <TabsTrigger value="documents">Documents</TabsTrigger>
          <TabsTrigger value="status">Index Health</TabsTrigger>
        </TabsList>

        <TabsContent value="status" className="space-y-6">
          {statusLoading ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-32 w-full" />)}
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <MetricCard 
                title="Index Status" 
                value={
                  <div className="flex items-center gap-2">
                    {statusData?.overview.index_status === 'healthy' ? <CheckCircle2 className="h-5 w-5 text-emerald-500" /> : <Database className="h-5 w-5 text-amber-500" />}
                    <span className="capitalize">{statusData?.overview.index_status || 'Unknown'}</span>
                  </div>
                }
              />
              <MetricCard 
                title="Total Documents" 
                value={statusData?.overview.total_documents.toLocaleString() || '0'} 
                icon={<FileText className="h-4 w-4 text-muted-foreground" />}
              />
              <MetricCard 
                title="Published" 
                value={statusData?.overview.published_documents.toLocaleString() || '0'} 
                icon={<CheckCircle2 className="h-4 w-4 text-emerald-500" />}
              />
              <MetricCard 
                title="Total Vector Chunks" 
                value={statusData?.overview.total_chunks.toLocaleString() || '0'} 
                icon={<Database className="h-4 w-4 text-blue-500" />}
              />
            </div>
          )}
        </TabsContent>

        <TabsContent value="documents">
          <Card>
            <CardHeader>
              <CardTitle>Knowledge Documents</CardTitle>
              <CardDescription>Manage the lifecycle of documents fed into the RAG vector store.</CardDescription>
            </CardHeader>
            <CardContent>
              {docsLoading ? (
                <Skeleton className="h-[400px] w-full" />
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Version</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Approval</TableHead>
                      <TableHead>Updated At</TableHead>
                      <TableHead className="text-right">Action</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {docsData?.documents.map(doc => (
                      <TableRow key={doc.id}>
                        <TableCell className="font-medium">{doc.name}</TableCell>
                        <TableCell className="text-sm font-mono">{doc.version}</TableCell>
                        <TableCell>{getStatusBadge(doc.status)}</TableCell>
                        <TableCell className="text-sm text-muted-foreground capitalize">{doc.approval_state?.replace('_', ' ') || 'None'}</TableCell>
                        <TableCell className="text-xs text-muted-foreground">{new Date(doc.updated_at).toLocaleString()}</TableCell>
                        <TableCell className="text-right">
                          <Select 
                            value={doc.status} 
                            onValueChange={(val) => updateStatusMutation.mutate({ id: doc.id, status: val })}
                            disabled={updatingId === doc.id}
                          >
                            <SelectTrigger className="w-[130px] ml-auto h-8 text-xs">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="Draft">Draft</SelectItem>
                              <SelectItem value="Review">Review</SelectItem>
                              <SelectItem value="Approved">Approve</SelectItem>
                              <SelectItem value="Published">Publish</SelectItem>
                              <SelectItem value="Archived">Archive</SelectItem>
                            </SelectContent>
                          </Select>
                        </TableCell>
                      </TableRow>
                    ))}
                    {(!docsData?.documents || docsData.documents.length === 0) && (
                      <TableRow>
                        <TableCell colSpan={6} className="text-center text-muted-foreground p-8">No knowledge documents found.</TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
