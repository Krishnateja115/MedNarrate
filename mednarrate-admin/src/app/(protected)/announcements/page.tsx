'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { Bell, Plus, ShieldAlert, CheckCircle, Trash2 } from 'lucide-react';

interface Announcement {
  id: string;
  title: string;
  message: string;
  audience: string;
  language: string;
  start_time: string;
  end_time: string;
  status: string;
  created_at: string | null;
}

export default function AnnouncementsPage() {
  const queryClient = useQueryClient();
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const [showCreateForm, setShowCreateForm] = useState(false);
  const [title, setTitle] = useState('');
  const [message, setMessage] = useState('');
  const [audience, setAudience] = useState('all');
  const [language, setLanguage] = useState('en');
  const [startTime, setStartTime] = useState(new Date().toISOString().slice(0, 16));
  const [endTime, setEndTime] = useState(new Date(Date.now() + 7 * 86400000).toISOString().slice(0, 16));

  const { data, isLoading } = useQuery<{ announcements: Announcement[] }>({
    queryKey: ['announcements'],
    queryFn: () => fetchApi('/api/v1/admin/announcements'),
  });

  const createAnnouncementMutation = useMutation({
    mutationFn: (newAnn: any) => fetchApi('/api/v1/admin/announcements', { data: newAnn }),
    onSuccess: () => {
      setSuccessMsg('Announcement created and scheduled');
      setErrorMsg(null);
      setShowCreateForm(false);
      setTitle('');
      setMessage('');
      queryClient.invalidateQueries({ queryKey: ['announcements'] });
    },
    onError: (err: any) => {
      setErrorMsg(err.message || 'Failed to create announcement');
      setSuccessMsg(null);
    }
  });

  const deleteAnnouncementMutation = useMutation({
    mutationFn: (id: string) => fetchApi(`/api/v1/admin/announcements/${id}`, { method: 'DELETE' }),
    onSuccess: () => {
      setSuccessMsg('Announcement deleted');
      setErrorMsg(null);
      queryClient.invalidateQueries({ queryKey: ['announcements'] });
    },
    onError: (err: any) => {
      setErrorMsg(err.message || 'Failed to delete announcement');
      setSuccessMsg(null);
    }
  });

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title || !message) return;
    createAnnouncementMutation.mutate({
      title,
      message,
      audience,
      language,
      start_time: new Date(startTime).toISOString(),
      end_time: new Date(endTime).toISOString(),
      status: 'published'
    });
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <Bell className="w-7 h-7 text-blue-600" /> Platform Announcements & Broadcasts
          </h1>
          <p className="text-slate-500 dark:text-slate-400 text-sm">
            Publish targeted system announcements for patient mobile app and web users.
          </p>
        </div>
        <Button onClick={() => setShowCreateForm(!showCreateForm)} className="flex items-center gap-2">
          <Plus className="w-4 h-4" /> {showCreateForm ? 'Cancel' : 'New Announcement'}
        </Button>
      </div>

      {errorMsg && (
        <div className="p-4 bg-red-50 text-red-700 dark:bg-red-950/50 dark:text-red-300 rounded-md border border-red-200 dark:border-red-800 text-sm flex items-center gap-2">
          <ShieldAlert className="w-5 h-5 shrink-0" /> {errorMsg}
        </div>
      )}

      {successMsg && (
        <div className="p-4 bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300 rounded-md border border-emerald-200 dark:border-emerald-800 text-sm flex items-center gap-2">
          <CheckCircle className="w-5 h-5 shrink-0" /> {successMsg}
        </div>
      )}

      {showCreateForm && (
        <Card className="border-blue-200 dark:border-blue-900 bg-blue-50/30 dark:bg-blue-950/20">
          <CardHeader>
            <CardTitle className="text-lg">Publish Targeted Announcement</CardTitle>
            <CardDescription>Audience, language, schedule range, and announcement message.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreate} className="space-y-4 max-w-xl">
              <div>
                <label className="block text-sm font-medium mb-1">Title</label>
                <input
                  type="text"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="New AI Feature Release: Enhanced Blood Panel Insights"
                  className="w-full px-3 py-2 border rounded-md dark:bg-slate-900 dark:border-slate-700 text-sm"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Announcement Message Body</label>
                <textarea
                  required
                  rows={3}
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="We are excited to launch automatic interpretation for specialized blood chemistry markers!"
                  className="w-full px-3 py-2 border rounded-md dark:bg-slate-900 dark:border-slate-700 text-sm"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Target Audience</label>
                  <select
                    value={audience}
                    onChange={(e) => setAudience(e.target.value)}
                    className="w-full px-3 py-2 border rounded-md dark:bg-slate-900 dark:border-slate-700 text-sm"
                  >
                    <option value="all">All App Users</option>
                    <option value="patients">Patients</option>
                    <option value="doctors">Physicians / Clinicians</option>
                    <option value="caregivers">Caregivers</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Language</label>
                  <select
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    className="w-full px-3 py-2 border rounded-md dark:bg-slate-900 dark:border-slate-700 text-sm"
                  >
                    <option value="en">English (en)</option>
                    <option value="es">Spanish (es)</option>
                    <option value="hi">Hindi (hi)</option>
                    <option value="te">Telugu (te)</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Start Time</label>
                  <input
                    type="datetime-local"
                    value={startTime}
                    onChange={(e) => setStartTime(e.target.value)}
                    className="w-full px-3 py-2 border rounded-md dark:bg-slate-900 dark:border-slate-700 text-sm"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">End Time</label>
                  <input
                    type="datetime-local"
                    value={endTime}
                    onChange={(e) => setEndTime(e.target.value)}
                    className="w-full px-3 py-2 border rounded-md dark:bg-slate-900 dark:border-slate-700 text-sm"
                  />
                </div>
              </div>

              <Button type="submit" disabled={createAnnouncementMutation.isPending}>
                {createAnnouncementMutation.isPending ? 'Publishing...' : 'Publish Announcement'}
              </Button>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Announcements List */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Announcements History</CardTitle>
          <CardDescription>Active and scheduled platform broadcasts.</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : !data?.announcements || data.announcements.length === 0 ? (
            <div className="text-center py-8 text-slate-500">No announcements published yet.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="text-xs uppercase bg-slate-50 dark:bg-slate-900 text-slate-500">
                  <tr>
                    <th className="px-4 py-3">Title & Message</th>
                    <th className="px-4 py-3">Audience / Language</th>
                    <th className="px-4 py-3">Schedule Range</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                  {data.announcements.map((ann) => (
                    <tr key={ann.id} className="hover:bg-slate-50 dark:hover:bg-slate-900/50">
                      <td className="px-4 py-3 font-medium max-w-sm">
                        <div className="font-semibold text-slate-900 dark:text-slate-100">{ann.title}</div>
                        <div className="text-xs text-slate-500 truncate">{ann.message}</div>
                      </td>
                      <td className="px-4 py-3 font-mono text-xs">
                        <Badge variant="outline">{ann.audience.toUpperCase()}</Badge>{' '}
                        <Badge variant="outline">{ann.language}</Badge>
                      </td>
                      <td className="px-4 py-3 text-xs text-slate-500 font-mono">
                        <div>From: {new Date(ann.start_time).toLocaleDateString()}</div>
                        <div>To: {new Date(ann.end_time).toLocaleDateString()}</div>
                      </td>
                      <td className="px-4 py-3">
                        <Badge className="bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300">
                          {ann.status.toUpperCase()}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => deleteAnnouncementMutation.mutate(ann.id)}
                          className="text-red-600 hover:text-red-700"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
