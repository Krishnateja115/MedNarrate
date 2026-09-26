'use client';

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Archive, BookOpen, Clock3, Eye, FilePenLine, Plus, Search } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { fetchApi } from '@/lib/api';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Textarea } from '@/components/ui/textarea';

type ArticleStatus = 'draft' | 'published' | 'archived';

interface HelpArticle {
  id: string;
  title: string;
  slug: string;
  category: string;
  summary: string;
  content: string;
  status: ArticleStatus;
  author: string;
  created_at: string;
  updated_at: string;
  published_at: string | null;
}

interface HelpResponse {
  status: string;
  categories: string[];
  articles: HelpArticle[];
}

interface ArticleForm {
  title: string;
  slug: string;
  category: string;
  summary: string;
  content: string;
  status: ArticleStatus;
}

interface ArticleVersion extends ArticleForm {
  id: string;
  version: number;
  created_by: string;
  created_at: string;
}

const FALLBACK_CATEGORIES = [
  'Account', 'Reports', 'Report Analysis', 'AI/Chat', 'RAG', 'Notifications',
  'Medication Reminders', 'Security', 'Privacy', 'Troubleshooting',
];

const EMPTY_FORM: ArticleForm = {
  title: '',
  slug: '',
  category: 'Account',
  summary: '',
  content: '',
  status: 'draft',
};

function statusBadge(status: ArticleStatus) {
  if (status === 'published') return <Badge className="bg-emerald-600">Published</Badge>;
  if (status === 'archived') return <Badge variant="outline">Archived</Badge>;
  return <Badge variant="secondary">Draft</Badge>;
}

export default function HelpCenterPage() {
  const { can } = useAuth();
  const queryClient = useQueryClient();
  const canManage = can('help_center.manage');
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [editingArticle, setEditingArticle] = useState<HelpArticle | null>(null);
  const [previewArticle, setPreviewArticle] = useState<HelpArticle | null>(null);
  const [historyArticle, setHistoryArticle] = useState<HelpArticle | null>(null);
  const [editorOpen, setEditorOpen] = useState(false);
  const [form, setForm] = useState<ArticleForm>(EMPTY_FORM);
  const [formError, setFormError] = useState('');

  const queryParams = new URLSearchParams();
  if (search.trim()) queryParams.set('search', search.trim());
  if (statusFilter !== 'all') queryParams.set('status', statusFilter);
  if (categoryFilter !== 'all') queryParams.set('category', categoryFilter);
  const queryString = queryParams.toString();

  const { data, isLoading, error } = useQuery<HelpResponse>({
    queryKey: ['help-articles', search, statusFilter, categoryFilter],
    queryFn: () => fetchApi(`/api/v1/admin/help-center${queryString ? `?${queryString}` : ''}`),
    staleTime: 30_000,
  });

  const { data: historyData, isLoading: historyLoading } = useQuery<{
    status: string;
    versions: ArticleVersion[];
  }>({
    queryKey: ['help-article-versions', historyArticle?.id],
    queryFn: () => fetchApi(`/api/v1/admin/help-center/${historyArticle?.id}/versions`),
    enabled: !!historyArticle,
  });

  const saveMutation = useMutation({
    mutationFn: () => editingArticle
      ? fetchApi(`/api/v1/admin/help-center/${editingArticle.id}`, { method: 'PATCH', data: form })
      : fetchApi('/api/v1/admin/help-center', { method: 'POST', data: form }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['help-articles'] });
      setEditorOpen(false);
      setEditingArticle(null);
      setForm(EMPTY_FORM);
      setFormError('');
    },
    onError: (mutationError: Error) => setFormError(mutationError.message),
  });

  const statusMutation = useMutation({
    mutationFn: ({ articleId, status }: { articleId: string; status: ArticleStatus }) =>
      fetchApi(`/api/v1/admin/help-center/${articleId}`, {
        method: 'PATCH',
        data: { status },
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['help-articles'] }),
  });

  const openNew = () => {
    setEditingArticle(null);
    setForm(EMPTY_FORM);
    setFormError('');
    setEditorOpen(true);
  };

  const openEdit = (article: HelpArticle) => {
    setEditingArticle(article);
    setForm({
      title: article.title,
      slug: article.slug,
      category: article.category,
      summary: article.summary,
      content: article.content,
      status: article.status,
    });
    setFormError('');
    setEditorOpen(true);
  };

  const updateForm = (field: keyof ArticleForm, value: string) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  const categories = data?.categories || FALLBACK_CATEGORIES;

  return (
    <div className="space-y-6 fade-in">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Help Center</h1>
          <p className="text-muted-foreground">Create and maintain support guidance grounded in MedNarrate.</p>
        </div>
        {canManage && (
          <Button onClick={openNew}>
            <Plus className="mr-2 h-4 w-4" /> New Article
          </Button>
        )}
      </div>

      <Card>
        <CardHeader className="border-b pb-4">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <CardTitle className="flex items-center gap-2 text-base">
              <BookOpen className="h-4 w-4" /> Articles
            </CardTitle>
            <div className="flex flex-col gap-2 sm:flex-row">
              <div className="relative sm:w-72">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  aria-label="Search articles"
                  className="pl-8"
                  placeholder="Search article content..."
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                />
              </div>
              <select
                aria-label="Filter by category"
                className="h-8 rounded-lg border border-input bg-background px-2.5 text-sm"
                value={categoryFilter}
                onChange={(event) => setCategoryFilter(event.target.value)}
              >
                <option value="all">All categories</option>
                {categories.map((category) => <option key={category} value={category}>{category}</option>)}
              </select>
              <select
                aria-label="Filter by status"
                className="h-8 rounded-lg border border-input bg-background px-2.5 text-sm"
                value={statusFilter}
                onChange={(event) => setStatusFilter(event.target.value)}
              >
                <option value="all">All statuses</option>
                <option value="draft">Draft</option>
                <option value="published">Published</option>
                <option value="archived">Archived</option>
              </select>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="space-y-3 p-8" data-testid="help-center-loading">
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
            </div>
          ) : error ? (
            <div className="p-8 text-center text-destructive">Failed to load articles.</div>
          ) : !data?.articles.length ? (
            <div className="p-10 text-center text-muted-foreground">
              <BookOpen className="mx-auto mb-3 h-8 w-8 opacity-50" />
              <p>No articles match these filters.</p>
            </div>
          ) : (
            <div className="w-full overflow-auto">
              <Table>
                <TableHeader>
                  <TableRow className="bg-muted/50 hover:bg-muted/50">
                    <TableHead>Article</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="hidden lg:table-cell">Author</TableHead>
                    <TableHead className="hidden md:table-cell">Updated</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.articles.map((article) => (
                    <TableRow key={article.id}>
                      <TableCell className="max-w-md">
                        <div className="font-medium">{article.title}</div>
                        <div className="mt-1 line-clamp-1 text-xs text-muted-foreground">{article.summary}</div>
                        <div className="mt-1 font-mono text-[11px] text-muted-foreground">/{article.slug}</div>
                      </TableCell>
                      <TableCell className="text-sm">{article.category}</TableCell>
                      <TableCell>{statusBadge(article.status)}</TableCell>
                      <TableCell className="hidden text-sm lg:table-cell">{article.author}</TableCell>
                      <TableCell className="hidden text-xs text-muted-foreground md:table-cell">
                        {new Date(article.updated_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <div className="flex justify-end gap-1">
                          <Button variant="ghost" size="sm" onClick={() => setPreviewArticle(article)}>
                            <Eye className="mr-1 h-4 w-4" /> Preview
                          </Button>
                          <Button variant="ghost" size="sm" onClick={() => setHistoryArticle(article)}>
                            <Clock3 className="mr-1 h-4 w-4" /> History
                          </Button>
                          {canManage && (
                            <>
                              <Button variant="ghost" size="sm" onClick={() => openEdit(article)}>
                                <FilePenLine className="mr-1 h-4 w-4" /> Edit
                              </Button>
                              {article.status === 'published' ? (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => statusMutation.mutate({ articleId: article.id, status: 'draft' })}
                                >
                                  Unpublish
                                </Button>
                              ) : article.status === 'draft' ? (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => statusMutation.mutate({ articleId: article.id, status: 'published' })}
                                >
                                  Publish
                                </Button>
                              ) : null}
                              {article.status !== 'archived' && (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => statusMutation.mutate({ articleId: article.id, status: 'archived' })}
                                >
                                  <Archive className="mr-1 h-4 w-4" /> Archive
                                </Button>
                              )}
                            </>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog open={editorOpen} onOpenChange={setEditorOpen}>
        <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-3xl">
          <DialogHeader>
            <DialogTitle>{editingArticle ? 'Edit article' : 'Create article'}</DialogTitle>
            <DialogDescription>Save as a draft or publish when the guidance is ready for support use.</DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-2 sm:grid-cols-2">
            <div className="space-y-2 sm:col-span-2">
              <Label htmlFor="article-title">Title</Label>
              <Input id="article-title" value={form.title} onChange={(event) => updateForm('title', event.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="article-slug">Slug</Label>
              <Input id="article-slug" value={form.slug} onChange={(event) => updateForm('slug', event.target.value)} placeholder="why-is-my-report-processing" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="article-category">Category</Label>
              <select
                id="article-category"
                className="h-8 w-full rounded-lg border border-input bg-background px-2.5 text-sm"
                value={form.category}
                onChange={(event) => updateForm('category', event.target.value)}
              >
                {categories.map((category) => <option key={category} value={category}>{category}</option>)}
              </select>
            </div>
            <div className="space-y-2 sm:col-span-2">
              <Label htmlFor="article-summary">Summary</Label>
              <Textarea id="article-summary" value={form.summary} onChange={(event) => updateForm('summary', event.target.value)} />
            </div>
            <div className="space-y-2 sm:col-span-2">
              <Label htmlFor="article-content">Content</Label>
              <Textarea id="article-content" className="min-h-64" value={form.content} onChange={(event) => updateForm('content', event.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="article-status">Status</Label>
              <select
                id="article-status"
                className="h-8 w-full rounded-lg border border-input bg-background px-2.5 text-sm"
                value={form.status}
                onChange={(event) => updateForm('status', event.target.value)}
              >
                <option value="draft">Draft</option>
                <option value="published">Published</option>
                <option value="archived">Archived</option>
              </select>
            </div>
          </div>
          {formError && <p className="text-sm text-destructive">{formError}</p>}
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditorOpen(false)}>Cancel</Button>
            <Button
              onClick={() => saveMutation.mutate()}
              disabled={saveMutation.isPending || !form.title || !form.slug || !form.summary || !form.content}
            >
              {saveMutation.isPending ? 'Saving...' : 'Save article'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={!!previewArticle} onOpenChange={(open) => !open && setPreviewArticle(null)}>
        <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-3xl">
          {previewArticle && (
            <>
              <DialogHeader>
                <div className="mb-2 flex items-center gap-2">
                  {statusBadge(previewArticle.status)}
                  <Badge variant="outline">{previewArticle.category}</Badge>
                </div>
                <DialogTitle className="text-xl">{previewArticle.title}</DialogTitle>
                <DialogDescription>{previewArticle.summary}</DialogDescription>
              </DialogHeader>
              <article className="whitespace-pre-wrap rounded-lg border bg-muted/20 p-5 leading-7">
                {previewArticle.content}
              </article>
              <p className="text-xs text-muted-foreground">
                By {previewArticle.author} · Updated {new Date(previewArticle.updated_at).toLocaleString()}
              </p>
            </>
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={!!historyArticle} onOpenChange={(open) => !open && setHistoryArticle(null)}>
        <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>Version history</DialogTitle>
            <DialogDescription>{historyArticle?.title}</DialogDescription>
          </DialogHeader>
          {historyLoading ? (
            <div className="space-y-2"><Skeleton className="h-16 w-full" /><Skeleton className="h-16 w-full" /></div>
          ) : !historyData?.versions?.length ? (
            <p className="rounded-lg border border-dashed p-6 text-center text-sm text-muted-foreground">
              No earlier versions have been recorded yet.
            </p>
          ) : (
            <div className="space-y-3">
              {historyData.versions.map((version) => (
                <div key={version.id} className="rounded-lg border p-4">
                  <div className="flex items-center justify-between gap-3">
                    <div className="font-medium">Version {version.version}: {version.title}</div>
                    {statusBadge(version.status)}
                  </div>
                  <p className="mt-2 text-sm text-muted-foreground">{version.summary}</p>
                  <p className="mt-2 text-xs text-muted-foreground">
                    Saved {new Date(version.created_at).toLocaleString()}
                  </p>
                </div>
              ))}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
