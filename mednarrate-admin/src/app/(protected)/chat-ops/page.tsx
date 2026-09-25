'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { MessageSquare, ShieldAlert, Search } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ColumnDef } from '@tanstack/react-table';
import { DataTable } from '@/components/ui/data-table';
import { useAuth } from '@/contexts/AuthContext';
import { Forbidden } from '@/components/ui/forbidden';

interface ChatSession {
  id: string;
  user_id: string;
  report_id: string | null;
  title: string | null;
  created_at: string;
}

interface SafetyEvent {
  id: string;
  chat_session_id: string;
  user_id: string;
  classification: string;
  action_taken: string;
  safe_summary: string | null;
  created_at: string;
}

interface ChatResponse {
  items: ChatSession[];
  total: number;
  page: number;
  limit: number;
}

interface SafetyResponse {
  items: SafetyEvent[];
  total: number;
  page: number;
  limit: number;
}

export default function ChatOpsPage() {
  const { can } = useAuth();
  const [sessionsPage, setSessionsPage] = useState(1);
  const [sessionsLimit, setSessionsLimit] = useState(25);
  const [searchTerm, setSearchTerm] = useState('');
  
  const [safetyPage, setSafetyPage] = useState(1);
  const [safetyLimit, setSafetyLimit] = useState(25);

  const { data: sessionsData, isLoading: sessionsLoading, error: sessionsError } = useQuery<ChatResponse>({
    queryKey: ['chat_sessions', sessionsPage, sessionsLimit, searchTerm],
    queryFn: () => {
      const params = new URLSearchParams();
      params.set('page', sessionsPage.toString());
      params.set('limit', sessionsLimit.toString());
      if (searchTerm) params.set('search', searchTerm);
      return fetchApi(`/api/v1/admin/chat-ops/sessions?${params.toString()}`);
    },
    enabled: can('chat.view'),
  });

  const { data: safetyData, isLoading: safetyLoading, error: safetyError } = useQuery<SafetyResponse>({
    queryKey: ['chat_safety_events', safetyPage, safetyLimit],
    queryFn: () => fetchApi(`/api/v1/admin/chat-ops/safety-events?page=${safetyPage}&limit=${safetyLimit}`),
    enabled: can('chat.view'),
  });

  const sessionColumns: ColumnDef<ChatSession>[] = [
    {
      accessorKey: 'created_at',
      header: 'Created At',
      cell: ({ row }) => <span className="text-xs text-muted-foreground">{new Date(row.getValue('created_at')).toLocaleString()}</span>,
    },
    {
      accessorKey: 'id',
      header: 'Session ID',
      cell: ({ row }) => <span className="font-mono text-xs">{row.original.id.slice(0, 8)}</span>,
    },
    {
      accessorKey: 'user_id',
      header: 'User ID',
      cell: ({ row }) => (
        <Link href={`/users/detail?id=${row.original.user_id}`} className="font-mono text-xs text-primary hover:underline">
          {row.original.user_id.slice(0, 8)}
        </Link>
      ),
    },
    {
      accessorKey: 'report_id',
      header: 'Report Related',
      cell: ({ row }) => row.original.report_id ? (
        <Link href={`/reports/detail?id=${row.original.report_id}`}>
          <Badge variant="outline" className="text-blue-500 border-blue-500">Yes</Badge>
        </Link>
      ) : <span className="text-muted-foreground text-sm">No</span>,
    },
    {
      id: 'actions',
      cell: () => (
        <div className="text-right">
          <Button variant="ghost" size="sm" disabled title="Requires sensitive access grant">
            Inspect
          </Button>
        </div>
      ),
    }
  ];

  const safetyColumns: ColumnDef<SafetyEvent>[] = [
    {
      accessorKey: 'created_at',
      header: 'Timestamp',
      cell: ({ row }) => <span className="text-xs text-muted-foreground">{new Date(row.getValue('created_at')).toLocaleString()}</span>,
    },
    {
      accessorKey: 'classification',
      header: 'Classification',
      cell: ({ row }) => <Badge variant="destructive">{row.original.classification}</Badge>,
    },
    {
      accessorKey: 'action_taken',
      header: 'Action Taken',
      cell: ({ row }) => <span className="font-medium text-sm">{row.original.action_taken}</span>,
    },
    {
      accessorKey: 'user_id',
      header: 'User ID',
      cell: ({ row }) => (
        <Link href={`/users/detail?id=${row.original.user_id}`} className="font-mono text-xs text-primary hover:underline">
          {row.original.user_id.slice(0, 8)}
        </Link>
      ),
    },
    {
      accessorKey: 'safe_summary',
      header: 'Safe Summary',
      cell: ({ row }) => <span className="text-sm italic text-muted-foreground">{row.original.safe_summary || 'No summary available'}</span>,
    }
  ];

  if (!can('chat.view')) {
    return <Forbidden />;
  }

  return (
    <div className="space-y-6 fade-in">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Chat & Safety Operations</h1>
        <p className="text-muted-foreground">Monitor chat volumes and investigate safety incidents without exposing raw PHI.</p>
      </div>

      <Tabs defaultValue="sessions" className="space-y-4">
        <TabsList>
          <TabsTrigger value="sessions">Active Sessions</TabsTrigger>
          <TabsTrigger value="safety">Safety Events</TabsTrigger>
        </TabsList>

        <TabsContent value="sessions">
          <Card>
            <CardHeader className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-4 gap-4">
              <div className="space-y-1">
                <CardTitle className="flex items-center gap-2">
                  <MessageSquare className="h-5 w-5 text-muted-foreground" /> Recent Sessions
                </CardTitle>
                <CardDescription>View session metadata. Content is masked by default.</CardDescription>
              </div>
              <div className="relative w-full sm:max-w-sm">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  type="search"
                  placeholder="Search sessions..."
                  className="pl-8"
                  value={searchTerm}
                  onChange={(e) => { setSearchTerm(e.target.value); setSessionsPage(1); }}
                />
              </div>
            </CardHeader>
            <CardContent>
              {sessionsError ? (
                <div className="p-8 text-center text-destructive">Failed to load sessions.</div>
              ) : (
                <DataTable
                  columns={sessionColumns}
                  data={sessionsData?.items || []}
                  pageCount={sessionsData ? Math.ceil(sessionsData.total / sessionsData.limit) : 0}
                  pageIndex={sessionsPage - 1}
                  pageSize={sessionsLimit}
                  total={sessionsData?.total || 0}
                  isLoading={sessionsLoading}
                  onPageChange={(p) => setSessionsPage(p + 1)}
                  onPageSizeChange={(s) => { setSessionsLimit(s); setSessionsPage(1); }}
                  onSortChange={() => {}}
                />
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="safety">
          <Card className="border-red-200">
            <CardHeader className="flex flex-row items-center justify-between pb-4">
              <div className="space-y-1">
                <CardTitle className="text-destructive flex items-center gap-2">
                  <ShieldAlert className="h-5 w-5" /> Safety & Moderation Events
                </CardTitle>
                <CardDescription>Track prompt injections, emergencies, and flagged behaviors.</CardDescription>
              </div>
            </CardHeader>
            <CardContent>
              {safetyError ? (
                <div className="p-8 text-center text-destructive">Failed to load safety events.</div>
              ) : (
                <DataTable
                  columns={safetyColumns}
                  data={safetyData?.items || []}
                  pageCount={safetyData ? Math.ceil(safetyData.total / safetyData.limit) : 0}
                  pageIndex={safetyPage - 1}
                  pageSize={safetyLimit}
                  total={safetyData?.total || 0}
                  isLoading={safetyLoading}
                  onPageChange={(p) => setSafetyPage(p + 1)}
                  onPageSizeChange={(s) => { setSafetyLimit(s); setSafetyPage(1); }}
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
