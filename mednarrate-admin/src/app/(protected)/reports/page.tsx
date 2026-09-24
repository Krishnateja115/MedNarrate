/* eslint-disable */
'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Skeleton } from '@/components/ui/skeleton';
import { Search, FileText } from 'lucide-react';
import Link from 'next/link';

interface Report {
  id: string;
  user_id: string;
  user_email: string;
  title: string;
  report_type: string;
  processing_status: string;
  uploaded_at: string;
}

interface ReportsResponse {
  status: string;
  reports: Report[];
  pagination: {
    total: number;
    limit: number;
    offset: number;
  };
}

export default function ReportsPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  
  const queryParams = new URLSearchParams();
  if (searchTerm) queryParams.set('search', searchTerm);
  if (typeFilter !== 'all') queryParams.set('report_type', typeFilter);
  if (statusFilter !== 'all') queryParams.set('processing_status', statusFilter);
  
  const { data, isLoading, error } = useQuery<ReportsResponse>({
    queryKey: ['reports', searchTerm, typeFilter, statusFilter],
    queryFn: () => fetchApi(`/api/v1/admin/reports?${queryParams.toString()}`),
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge variant="outline" className="text-emerald-600 border-emerald-600/30 bg-emerald-50 dark:bg-emerald-950/20">Completed</Badge>;
      case 'processing':
        return <Badge className="bg-amber-500 hover:bg-amber-600">Processing</Badge>;
      case 'uploaded':
        return <Badge className="bg-blue-500 hover:bg-blue-600">Uploaded</Badge>;
      case 'failed':
        return <Badge variant="destructive">Failed</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  return (
    <div className="space-y-6 fade-in">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Reports</h1>
          <p className="text-muted-foreground">Monitor uploaded reports and processing pipeline status.</p>
        </div>
      </div>

      <Card>
        <CardHeader className="pb-3 border-b">
          <div className="flex flex-col sm:flex-row gap-4 justify-between items-start sm:items-center">
            <div className="relative w-full sm:max-w-sm">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                type="search"
                placeholder="Search by ID, title, or user email..."
                className="pl-8"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <div className="flex gap-2 w-full sm:w-auto">
              <Select value={typeFilter} onValueChange={(val) => setTypeFilter(val || 'all')}>
                <SelectTrigger className="w-full sm:w-[130px]">
                  <SelectValue placeholder="Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="blood">Blood</SelectItem>
                  <SelectItem value="pathology">Pathology</SelectItem>
                  <SelectItem value="health">Health</SelectItem>
                  <SelectItem value="other">Other</SelectItem>
                </SelectContent>
              </Select>
              
              <Select value={statusFilter} onValueChange={(val) => setStatusFilter(val || 'all')}>
                <SelectTrigger className="w-full sm:w-[130px]">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  <SelectItem value="completed">Completed</SelectItem>
                  <SelectItem value="processing">Processing</SelectItem>
                  <SelectItem value="uploaded">Uploaded</SelectItem>
                  <SelectItem value="failed">Failed</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-8 space-y-4">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : error ? (
            <div className="p-8 text-center text-destructive">
              Failed to load reports.
            </div>
          ) : data?.reports.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">
              <FileText className="mx-auto h-8 w-8 mb-3 opacity-50" />
              <p>No reports found matching the current filters.</p>
            </div>
          ) : (
            <div className="relative w-full overflow-auto">
              <Table>
                <TableHeader>
                  <TableRow className="bg-muted/50 hover:bg-muted/50">
                    <TableHead>Report ID</TableHead>
                    <TableHead>User</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="hidden md:table-cell">Uploaded</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data?.reports.map((report) => (
                    <TableRow key={report.id}>
                      <TableCell className="font-mono text-sm">
                        <Link href={`/reports/${report.id}`} className="hover:underline text-primary">
                          {report.id.slice(0, 8)}...
                        </Link>
                      </TableCell>
                      <TableCell>
                        <div className="font-medium text-sm">{report.user_email}</div>
                      </TableCell>
                      <TableCell className="capitalize">{report.report_type}</TableCell>
                      <TableCell>{getStatusBadge(report.processing_status)}</TableCell>
                      <TableCell className="hidden md:table-cell text-muted-foreground text-sm font-mono">
                        {new Date(report.uploaded_at).toLocaleString()}
                      </TableCell>
                      <TableCell className="text-right">
                        <Link href={`/reports/${report.id}`}>
                          <Button variant="ghost" size="sm">
                            <span className="sr-only">Diagnostic</span>
                            Diagnostic
                          </Button>
                        </Link>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
          
          {data && data.pagination.total > 0 && (
            <div className="p-4 border-t flex items-center justify-between text-sm text-muted-foreground">
              <div>
                Showing {data.reports.length} of {data.pagination.total} reports
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
