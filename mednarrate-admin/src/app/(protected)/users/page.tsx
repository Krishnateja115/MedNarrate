'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Skeleton } from '@/components/ui/skeleton';
import { Search, MoreHorizontal, User as UserIcon } from 'lucide-react';
import Link from 'next/link';

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
  status: string;
  users: User[];
  pagination: {
    total: number;
    limit: number;
    offset: number;
  };
}

export default function UsersPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  
  // Debounce search term would be ideal here in a real app, 
  // but we'll fetch on every keystroke for simplicity if using react-query with short staleTime
  const queryParams = new URLSearchParams();
  if (searchTerm) queryParams.set('search', searchTerm);
  if (roleFilter !== 'all') queryParams.set('role', roleFilter);
  if (statusFilter !== 'all') queryParams.set('is_active', statusFilter === 'active' ? 'true' : 'false');
  
  const { data, isLoading, error } = useQuery<UsersResponse>({
    queryKey: ['users', searchTerm, roleFilter, statusFilter],
    queryFn: () => fetchApi(`/api/v1/admin/users?${queryParams.toString()}`),
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
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <div className="flex gap-2 w-full sm:w-auto">
              <Select value={roleFilter} onValueChange={(val) => setRoleFilter(val || 'all')}>
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
              
              <Select value={statusFilter} onValueChange={(val) => setStatusFilter(val || 'all')}>
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
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-8 space-y-4">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : error ? (
            <div className="p-8 text-center text-destructive">
              Failed to load users.
            </div>
          ) : data?.users.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">
              <UserIcon className="mx-auto h-8 w-8 mb-3 opacity-50" />
              <p>No users found matching the current filters.</p>
            </div>
          ) : (
            <div className="relative w-full overflow-auto">
              <Table>
                <TableHeader>
                  <TableRow className="bg-muted/50 hover:bg-muted/50">
                    <TableHead>Name</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>Role</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="hidden md:table-cell">Joined</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data?.users.map((user) => (
                    <TableRow key={user.id}>
                      <TableCell className="font-medium">
                        <Link href={`/users/${user.id}`} className="hover:underline text-primary">
                          {user.full_name}
                        </Link>
                      </TableCell>
                      <TableCell className="text-muted-foreground text-sm">{user.email}</TableCell>
                      <TableCell>{getRoleBadge(user.role)}</TableCell>
                      <TableCell>
                        {user.is_active ? (
                          <Badge variant="outline" className="text-emerald-600 border-emerald-600/30 bg-emerald-50 dark:bg-emerald-950/20">Active</Badge>
                        ) : (
                          <Badge variant="destructive">Suspended</Badge>
                        )}
                      </TableCell>
                      <TableCell className="hidden md:table-cell text-muted-foreground text-sm font-mono">
                        {new Date(user.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell className="text-right">
                        <Link href={`/users/${user.id}`}>
                          <Button variant="ghost" size="sm">
                            <span className="sr-only">View</span>
                            View Details
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
                Showing {data.users.length} of {data.pagination.total} users
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
