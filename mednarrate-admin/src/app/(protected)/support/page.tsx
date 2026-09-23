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
import { Search, LifeBuoy, AlertCircle } from 'lucide-react';
import Link from 'next/link';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';

interface Ticket {
  id: string;
  user_email: string | null;
  title: string;
  category: string;
  priority: string;
  status: string;
  assigned_admin_id: string | null;
  updated_at: string;
}

interface SupportResponse {
  status: string;
  tickets: Ticket[];
}

export default function SupportQueuePage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [tabView, setTabView] = useState<string>('open'); // all, open, unassigned, critical
  
  const queryParams = new URLSearchParams();
  if (searchTerm) queryParams.set('search', searchTerm);
  
  if (tabView === 'unassigned') {
    queryParams.set('unassigned', 'true');
  } else if (tabView === 'critical') {
    queryParams.set('priority', 'P1 Critical');
  }
  
  if (statusFilter !== 'all' && tabView !== 'open') {
    queryParams.set('status', statusFilter);
  } else if (tabView === 'open') {
    // A simplified 'open' filter which the backend doesn't explicitly have, 
    // but we can filter on the frontend if needed, or backend can support 'open'
    // For now, if we don't pass status, we'll get all, and we'll frontend filter.
  }

  const { data, isLoading, error } = useQuery<SupportResponse>({
    queryKey: ['support_tickets', searchTerm, statusFilter, tabView],
    queryFn: () => fetchApi(`/api/v1/admin/support?${queryParams.toString()}`),
  });

  const getPriorityBadge = (priority: string) => {
    if (priority.includes('P1')) return <Badge variant="destructive">P1 Critical</Badge>;
    if (priority.includes('P2')) return <Badge className="bg-orange-500">P2 High</Badge>;
    if (priority.includes('P3')) return <Badge className="bg-blue-500">P3 Normal</Badge>;
    return <Badge variant="secondary">P4 General</Badge>;
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'New': return <Badge className="bg-purple-500">New</Badge>;
      case 'Triaged': return <Badge className="bg-indigo-500">Triaged</Badge>;
      case 'Investigating': return <Badge className="bg-amber-500">Investigating</Badge>;
      case 'Waiting for User': return <Badge variant="outline" className="border-amber-500 text-amber-600">Waiting for User</Badge>;
      case 'Waiting for Engineering': return <Badge variant="outline" className="border-red-500 text-red-600">Waiting for Eng</Badge>;
      case 'Resolved': return <Badge variant="outline" className="text-emerald-600 border-emerald-600/30">Resolved</Badge>;
      case 'Closed': return <Badge variant="secondary">Closed</Badge>;
      default: return <Badge variant="secondary">{status}</Badge>;
    }
  };

  let displayedTickets = data?.tickets || [];
  
  // Frontend filter for 'open' tab if the backend doesn't native support an 'open' status list
  if (tabView === 'open') {
    displayedTickets = displayedTickets.filter(t => t.status !== 'Resolved' && t.status !== 'Closed');
    if (statusFilter !== 'all') {
      displayedTickets = displayedTickets.filter(t => t.status === statusFilter);
    }
  }

  return (
    <div className="space-y-6 fade-in">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Support Queue</h1>
          <p className="text-muted-foreground">Manage user support requests and operational issues.</p>
        </div>
      </div>

      <Tabs value={tabView} onValueChange={setTabView} className="w-full">
        <TabsList className="mb-4">
          <TabsTrigger value="open">Open Tickets</TabsTrigger>
          <TabsTrigger value="unassigned">Unassigned</TabsTrigger>
          <TabsTrigger value="critical">Critical (P1)</TabsTrigger>
          <TabsTrigger value="all">All Tickets</TabsTrigger>
        </TabsList>
      
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
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="w-full sm:w-[150px]">
                    <SelectValue placeholder="Status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Statuses</SelectItem>
                    <SelectItem value="New">New</SelectItem>
                    <SelectItem value="Triaged">Triaged</SelectItem>
                    <SelectItem value="Investigating">Investigating</SelectItem>
                    <SelectItem value="Waiting for User">Waiting for User</SelectItem>
                    <SelectItem value="Waiting for Engineering">Waiting for Eng</SelectItem>
                    <SelectItem value="Resolved">Resolved</SelectItem>
                    <SelectItem value="Closed">Closed</SelectItem>
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
                Failed to load tickets.
              </div>
            ) : displayedTickets.length === 0 ? (
              <div className="p-8 text-center text-muted-foreground">
                <LifeBuoy className="mx-auto h-8 w-8 mb-3 opacity-50" />
                <p>No tickets found matching the current filters.</p>
              </div>
            ) : (
              <div className="relative w-full overflow-auto">
                <Table>
                  <TableHeader>
                    <TableRow className="bg-muted/50 hover:bg-muted/50">
                      <TableHead className="w-[100px]">Ticket ID</TableHead>
                      <TableHead>Title</TableHead>
                      <TableHead>User</TableHead>
                      <TableHead>Category</TableHead>
                      <TableHead>Priority</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="hidden md:table-cell">Updated</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {displayedTickets.map((ticket) => (
                      <TableRow key={ticket.id}>
                        <TableCell className="font-mono text-xs">
                          <Link href={`/support/${ticket.id}`} className="hover:underline text-primary">
                            {ticket.id.slice(0, 8)}
                          </Link>
                        </TableCell>
                        <TableCell className="font-medium max-w-[200px] truncate" title={ticket.title}>
                          <Link href={`/support/${ticket.id}`} className="hover:underline">
                            {ticket.title}
                          </Link>
                        </TableCell>
                        <TableCell className="text-sm truncate max-w-[150px]">
                          {ticket.user_email || <span className="text-muted-foreground italic">System</span>}
                        </TableCell>
                        <TableCell className="text-sm">{ticket.category}</TableCell>
                        <TableCell>{getPriorityBadge(ticket.priority)}</TableCell>
                        <TableCell>{getStatusBadge(ticket.status)}</TableCell>
                        <TableCell className="hidden md:table-cell text-muted-foreground text-xs">
                          {new Date(ticket.updated_at).toLocaleString()}
                        </TableCell>
                        <TableCell className="text-right">
                          <Link href={`/support/${ticket.id}`}>
                            <Button variant="ghost" size="sm">
                              <span className="sr-only">Investigate</span>
                              Investigate
                            </Button>
                          </Link>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
            
            {displayedTickets.length > 0 && (
              <div className="p-4 border-t flex items-center justify-between text-sm text-muted-foreground">
                <div>
                  Showing {displayedTickets.length} tickets
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </Tabs>
    </div>
  );
}
