'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Skeleton } from '@/components/ui/skeleton';
import { BookOpen, Plus } from 'lucide-react';

interface HelpArticle {
  id: string;
  title: string;
  slug: string;
  category: string;
  status: string;
  updated_at: string;
}

interface HelpResponse {
  status: string;
  articles: HelpArticle[];
}

export default function HelpCenterPage() {
  const { data, isLoading, error } = useQuery<HelpResponse>({
    queryKey: ['help_articles'],
    queryFn: () => fetchApi(`/api/v1/admin/help-center`),
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'published': return <Badge className="bg-emerald-500">Published</Badge>;
      case 'draft': return <Badge variant="secondary">Draft</Badge>;
      case 'archived': return <Badge variant="outline">Archived</Badge>;
      default: return <Badge variant="secondary">{status}</Badge>;
    }
  };

  return (
    <div className="space-y-6 fade-in">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Help Center</h1>
          <p className="text-muted-foreground">Manage knowledge base articles for users.</p>
        </div>
        <Button>
          <Plus className="mr-2 h-4 w-4" /> New Article
        </Button>
      </div>

      <Card>
        <CardHeader className="pb-3 border-b">
          <CardTitle className="text-base flex items-center gap-2">
            <BookOpen className="h-4 w-4" /> Articles
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-8 space-y-4">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : error ? (
            <div className="p-8 text-center text-destructive">
              Failed to load articles.
            </div>
          ) : data?.articles.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">
              <BookOpen className="mx-auto h-8 w-8 mb-3 opacity-50" />
              <p>No articles found.</p>
            </div>
          ) : (
            <div className="relative w-full overflow-auto">
              <Table>
                <TableHeader>
                  <TableRow className="bg-muted/50 hover:bg-muted/50">
                    <TableHead>Title</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="hidden md:table-cell">Updated</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data?.articles.map((article) => (
                    <TableRow key={article.id}>
                      <TableCell className="font-medium">
                        {article.title}
                        <div className="text-xs text-muted-foreground font-mono mt-1">{article.slug}</div>
                      </TableCell>
                      <TableCell className="text-sm">{article.category}</TableCell>
                      <TableCell>{getStatusBadge(article.status)}</TableCell>
                      <TableCell className="hidden md:table-cell text-muted-foreground text-xs">
                        {new Date(article.updated_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button variant="ghost" size="sm">
                          Edit
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
