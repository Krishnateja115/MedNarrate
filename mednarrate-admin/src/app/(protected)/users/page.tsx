/* eslint-disable */
'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { Search, MoreHorizontal, User as UserIcon } from 'lucide-react';
import Link from 'next/link';
import { ColumnDef } from '@tanstack/react-table';
import { DataTable } from '@/components/ui/data-table';

interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  preferred_language: string;
  is_active: boolean;
  created_at: string;
}

interface UsersResponse {
  items: User[];
  total: number;
  page: number;
  limit: number;
  has_next: boolean;
  has_previous: boolean;
}

import { useAuth } from '@/contexts/AuthContext';
import { Forbidden } from '@/components/ui/forbidden';

export default function UsersPage() {
  const { can } = useAuth();
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(25);
  const [sortState, setSortState] = useState<{id: string, desc: boolean}>({ id: 'created_at', desc: true });
  
  const queryParams = new URLSearchParams();
  if (searchTerm) queryParams.set('search', searchTerm);
  if (roleFilter !== 'all') queryParams.set('role', roleFilter);
  if (statusFilter !== 'all') queryParams.set('is_active', statusFilter === 'active' ? 'true' : 'false');
  queryParams.set('page', page.toString());
  queryParams.set('limit', limit.toString());
  queryParams.set('sort_by', sortState.id);
  queryParams.set('sort_desc', sortState.desc.toString());
  
  const { data, isLoading, error } = useQuery<UsersResponse>({
    queryKey: ['users', searchTerm, roleFilter, statusFilter, page, limit, sortState],
    queryFn: () => fetchApi(`/api/v1/admin/users?${queryParams.toString()}`),
    enabled: can('users.view'),
  });

  const getRoleBadge = (role: string) => {
    switch (role) {
      case 'admin':
        return <Badge className="bg-purple-500 hover:bg-purple-600">Admin</Badge>;
      case 'clinician':
        return <Badge className="bg-blue-500 hover:bg-blue-600">Clinician</Badge>;
      case 'patient':
        return <Badge variant="outline">Patient</Badge>;
      case 'caregiver':
        return <Badge className="bg-orange-500 hover:bg-orange-600">Caregiver</Badge>;
      default:
        return <Badge variant="secondary">{role}</Badge>;
    }
  };

  const columns: ColumnDef<User>[] = [
    {
      accessorKey: 'full_name',
      header: 'Name',
      cell: ({ row }) => (
        <Link href={`/users/${row.original.id}`} className="hover:underline text-primary font-medium">
          {row.getValue('full_name')}
        </Link>
      ),
    },
    {
      accessorKey: 'email',
      header: 'Email',
      cell: ({ row }) => <span className="text-muted-foreground text-sm">{row.getValue('email')}</span>,
    },
    {
      accessorKey: 'role',
      header: 'Role',
      cell: ({ row }) => getRoleBadge(row.getValue('role')),
    },
    {
      accessorKey: 'is_active',
      header: 'Status',
      cell: ({ row }) => row.getValue('is_active') ? (
        <Badge variant="outline" className="text-emerald-600 border-emerald-600/30 bg-emerald-50 dark:bg-emerald-950/20">Active</Badge>
      ) : (
        <Badge variant="destructive">Suspended</Badge>
      ),
    },
    {
      accessorKey: 'created_at',
      header: 'Joined',
      cell: ({ row }) => <span className="text-muted-foreground text-sm font-mono">{new Date(row.getValue('created_at')).toLocaleDateString()}</span>,
    },
    {
      id: 'actions',
      cell: ({ row }) => (
        <div className="text-right">
          <Link href={`/users/${row.original.id}`}>
            <Button variant="ghost" size="sm">
              View Details
            </Button>
          </Link>
        </div>
      ),
      enableSorting: false,
    },
  ];

  if (!can('users.view')) {
    return <Forbidden />;
  }

  return (
    <div className="space-y-6 fade-in">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Users</h1>
          <p className="text-muted-foreground">Manage and investigate user accounts.</p>
        </div>
      </div>

      <Card>
        <CardHeader className="pb-3 border-b">
          <div className="flex flex-col sm:flex-row gap-4 justify-between items-start sm:items-center">
            <div className="relative w-full sm:max-w-sm">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                type="search"
                placeholder="Search by name, email, or ID..."
                className="pl-8"
                value={searchTerm}
                onChange={(e) => { setSearchTerm(e.target.value); setPage(1); }}
              />
            </div>
            <div className="flex gap-2 w-full sm:w-auto">
              <Select value={roleFilter} onValueChange={(val) => { setRoleFilter(val || 'all'); setPage(1); }}>
                <SelectTrigger className="w-full sm:w-[130px]">
                  <SelectValue placeholder="Role" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Roles</SelectItem>
                  <SelectItem value="admin">Admin</SelectItem>
                  <SelectItem value="clinician">Clinician</SelectItem>
                  <SelectItem value="patient">Patient</SelectItem>
                  <SelectItem value="caregiver">Caregiver</SelectItem>
                </SelectContent>
              </Select>
              
              <Select value={statusFilter} onValueChange={(val) => { setStatusFilter(val || 'all'); setPage(1); }}>
                <SelectTrigger className="w-full sm:w-[130px]">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="suspended">Suspended</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0 sm:p-4">
          {error ? (
            <div className="p-8 text-center text-destructive">
              Failed to load users.
            </div>
          ) : (
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
          )}
        </CardContent>
      </Card>
    </div>
  );
}
