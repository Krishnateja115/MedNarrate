/* eslint-disable */
'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { FileText, Search, Filter, Eye, ShieldAlert, Lock } from 'lucide-react';
import { ColumnDef } from '@tanstack/react-table';
import { DataTable } from '@/components/ui/data-table';

interface AuditLogItem {
  id: string;
  timestamp: string | null;
  actor: {
    id: string | null;
    email: string;
    full_name: string | null;
  };
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  permission_used: string | null;
  result: string;
  reason: string | null;
  request_id: string | null;
  ip_address: string | null;
  user_agent: string | null;
  metadata: Record<string, any>;
  sensitive_access_flag: boolean;
}

interface AuditResponse {
  items: AuditLogItem[];
  total: number;
  page: number;
  limit: number;
}

export default function AuditLogsPage() {
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(25);
  const [sortState, setSortState] = useState<{id: string, desc: boolean}>({ id: 'timestamp', desc: true });
  const [search, setSearch] = useState('');
  const [actionFilter, setActionFilter] = useState('');
  const [resultFilter, setResultFilter] = useState('');
  const [selectedLog, setSelectedLog] = useState<AuditLogItem | null>(null);

  const { data, isLoading } = useQuery<AuditResponse>({
    queryKey: ['audit-logs', page, limit, sortState, search, actionFilter, resultFilter],
    queryFn: () => {
      const params: Record<string, string> = { 
        page: page.toString(), 
        limit: limit.toString(),
        sort_by: sortState.id,
        sort_desc: sortState.desc.toString()
      };
      if (search) params.search = search;
      if (actionFilter) params.action = actionFilter;
      if (resultFilter) params.result_status = resultFilter;
      return fetchApi('/api/v1/admin/audit-logs', { params });
    },
  });

  const columns: ColumnDef<AuditLogItem>[] = [
    {
      accessorKey: 'timestamp',
      header: 'Timestamp',
      cell: ({ row }) => <span className="text-slate-500 whitespace-nowrap text-xs">{row.getValue('timestamp') ? new Date(row.getValue('timestamp')).toLocaleString() : 'N/A'}</span>,
    },
    {
      id: 'actor',
      header: 'Actor Admin',
      cell: ({ row }) => <span className="font-medium text-slate-900 dark:text-slate-100">{row.original.actor.email}</span>,
      enableSorting: false,
    },
    {
      accessorKey: 'action',
      header: 'Action',
      cell: ({ row }) => <span className="font-mono text-xs text-blue-600 dark:text-blue-400">{row.getValue('action')}</span>,
    },
    {
      id: 'resource',
      header: 'Resource',
      cell: ({ row }) => <span className="text-xs text-slate-600 dark:text-slate-400">{row.original.resource_type ? `${row.original.resource_type}:${row.original.resource_id || '*'}` : '-'}</span>,
      enableSorting: false,
    },
    {
      accessorKey: 'result',
      header: 'Result',
      cell: ({ row }) => {
        const res = row.getValue('result') as string;
        return (
          <Badge
            variant={res === 'success' ? 'default' : 'destructive'}
            className={res === 'success' ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300' : ''}
          >
            {res}
          </Badge>
        );
      },
    },
    {
      id: 'actions',
      header: () => <div className="text-right">Details</div>,
      cell: ({ row }) => (
        <div className="text-right">
          <Button variant="ghost" size="sm" onClick={() => setSelectedLog(row.original)}>
            <Eye className="w-4 h-4 mr-1" /> View Payload
          </Button>
        </div>
      ),
      enableSorting: false,
    },
  ];

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 flex items-center gap-2">
          <FileText className="w-7 h-7 text-blue-600" /> Immutable Audit Logs Reader
        </h1>
        <p className="text-slate-500 dark:text-slate-400 text-sm">
          Append-only compliance audit trails with sanitized request metadata and tamper-evident history.
        </p>
      </div>

      {/* Filters Bar */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row gap-4 justify-between items-center">
            <div className="flex-1 w-full md:w-auto relative">
              <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
              <input
                type="text"
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setPage(1);
                }}
                placeholder="Search action, resource ID, or reason..."
                className="w-full pl-9 pr-4 py-2 border rounded-md dark:bg-slate-900 dark:border-slate-700 text-sm"
              />
            </div>
            <div className="flex gap-2 w-full md:w-auto">
              <select
                value={resultFilter}
                onChange={(e) => {
                  setResultFilter(e.target.value);
                  setPage(1);
                }}
                className="px-3 py-2 border rounded-md dark:bg-slate-900 dark:border-slate-700 text-sm"
              >
                <option value="">All Results</option>
                <option value="success">Success</option>
                <option value="failure">Failure</option>
                <option value="denied">Denied</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Audit Log Table */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-lg">Audit Events ({data?.total ?? 0})</CardTitle>
            <CardDescription>Strictly read-only audit log entries.</CardDescription>
          </div>
          <Badge variant="outline" className="flex items-center gap-1">
            <Lock className="w-3.5 h-3.5 text-slate-500" /> Immutable Read-Only
          </Badge>
        </CardHeader>
        <CardContent className="p-4">
          <DataTable
            columns={columns}
            data={data?.items || []}
            pageCount={data ? Math.ceil(data.total / data.limit) : 0}
            pageIndex={page - 1}
            pageSize={limit}
            total={data?.total || 0}
            isLoading={isLoading}
            onPageChange={(p) => setPage(p + 1)}
            onPageSizeChange={(s) => { setLimit(s); setPage(1); }}
            onSortChange={(s) => setSortState(s)}
            sortState={sortState}
          />
        </CardContent>
      </Card>

      {/* Detail Drawer Modal */}
      {selectedLog && (
        <div className="fixed inset-0 bg-black/50 z-50 flex justify-end">
          <div className="w-full max-w-xl bg-white dark:bg-slate-950 h-full p-6 overflow-y-auto space-y-4 shadow-xl border-l dark:border-slate-800">
            <div className="flex justify-between items-center border-b pb-3">
              <h2 className="text-lg font-bold">Audit Event Detail Drawer</h2>
              <Button variant="ghost" size="sm" onClick={() => setSelectedLog(null)}>
                Close
              </Button>
            </div>
            <div className="space-y-3 text-sm">
              <div>
                <span className="font-semibold text-slate-500">Event ID:</span>
                <div className="font-mono text-xs">{selectedLog.id}</div>
              </div>
              <div>
                <span className="font-semibold text-slate-500">Actor Email:</span>
                <div>{selectedLog.actor.email}</div>
              </div>
              <div>
                <span className="font-semibold text-slate-500">Action:</span>
                <div className="font-mono text-blue-600">{selectedLog.action}</div>
              </div>
              <div>
                <span className="font-semibold text-slate-500">IP Address & User Agent:</span>
                <div className="font-mono text-xs">{selectedLog.ip_address || 'Internal'}</div>
                <div className="text-xs text-slate-500">{selectedLog.user_agent || '-'}</div>
              </div>
              <div>
                <span className="font-semibold text-slate-500">Sanitized Metadata Payload:</span>
                <pre className="p-3 bg-slate-900 text-slate-100 rounded-md font-mono text-xs overflow-x-auto mt-1">
                  {JSON.stringify(selectedLog.metadata, null, 2)}
                </pre>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
