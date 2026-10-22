'use client';

import { Suspense, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, LockKeyhole, ShieldAlert } from 'lucide-react';
import { ApiError, fetchApi } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { Forbidden } from '@/components/ui/forbidden';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

interface SessionDetail {
  session: {
    id: string;
    user_id: string;
    report_id: string | null;
    created_at: string;
    message_count: number;
    sensitive_content_available: boolean;
  };
  safety_events: Array<{
    id: string;
    classification: string;
    action_taken: string;
    safe_summary: string | null;
    created_at: string;
  }>;
}

interface SensitiveMessages {
  grant_expires_at: string;
  messages: Array<{ id: string; role: string; content: string; created_at: string }>;
}

function ChatSessionDetailContent() {
  const sessionId = useSearchParams().get('id');
  const { can } = useAuth();
  const [messages, setMessages] = useState<SensitiveMessages | null>(null);
  const [messagesError, setMessagesError] = useState<string | null>(null);
  const [messagesLoading, setMessagesLoading] = useState(false);

  const { data, isLoading, error } = useQuery<SessionDetail>({
    queryKey: ['chat-session-detail', sessionId],
    queryFn: () => fetchApi(`/api/v1/admin/chat-ops/sessions/${encodeURIComponent(sessionId!)}`),
    enabled: can('chat.view') && Boolean(sessionId),
    retry: false,
  });

  if (!can('chat.view')) return <Forbidden />;

  const viewMessages = async () => {
    if (!sessionId || !can('chat.sensitive_view')) return;
    setMessagesLoading(true);
    setMessagesError(null);
    setMessages(null);
    try {
      const result = await fetchApi<SensitiveMessages>(`/api/v1/admin/chat-ops/sessions/${encodeURIComponent(sessionId)}/messages`);
      setMessages(result);
    } catch (err) {
      setMessagesError(err instanceof ApiError && err.status === 403
        ? 'An active break-glass grant for this chat session is required. Request access below and have another administrator approve it.'
        : err instanceof Error ? err.message : 'Could not load messages.');
    } finally {
      setMessagesLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <Link href="/chat-ops" className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="mr-2 h-4 w-4" /> Back to Chat Operations
      </Link>
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Inspect Chat Session</h1>
        <p className="text-muted-foreground">Session details and safety events are visible without opening private messages.</p>
      </div>

      {!sessionId ? <p role="alert">No session ID was provided.</p> : isLoading ? (
        <Card><CardContent className="space-y-3 pt-6"><Skeleton className="h-6 w-1/2" /><Skeleton className="h-24 w-full" /></CardContent></Card>
      ) : error || !data ? (
        <p role="alert" className="text-destructive">Could not load this session. Check that it still exists and try again.</p>
      ) : (
        <>
          <Card>
            <CardHeader><CardTitle>Session metadata</CardTitle><CardDescription>No message text is loaded on this page by default.</CardDescription></CardHeader>
            <CardContent className="grid gap-4 text-sm sm:grid-cols-2">
              <div><span className="text-muted-foreground">Session ID</span><p className="break-all font-mono">{data.session.id}</p></div>
              <div><span className="text-muted-foreground">Created</span><p>{new Date(data.session.created_at).toLocaleString()}</p></div>
              <div><span className="text-muted-foreground">User</span><p><Link href={`/users/detail?id=${encodeURIComponent(data.session.user_id)}`} className="break-all font-mono text-primary hover:underline">{data.session.user_id}</Link></p></div>
              <div><span className="text-muted-foreground">Messages</span><p>{data.session.message_count}</p></div>
              <div><span className="text-muted-foreground">Related report</span><p>{data.session.report_id ? <Link href={`/reports/detail?id=${encodeURIComponent(data.session.report_id)}`} className="break-all font-mono text-primary hover:underline">{data.session.report_id}</Link> : 'None'}</p></div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>Safety events</CardTitle><CardDescription>Only redacted summaries are shown here.</CardDescription></CardHeader>
            <CardContent>{data.safety_events.length === 0 ? <p className="text-sm text-muted-foreground">No safety events recorded for this session.</p> : (
              <ul className="space-y-3">{data.safety_events.map((event) => (
                <li key={event.id} className="rounded-md border p-3 text-sm">
                  <div className="flex flex-wrap gap-2 font-medium"><span>{event.classification}</span><span>·</span><span>{event.action_taken}</span><span className="text-muted-foreground">{new Date(event.created_at).toLocaleString()}</span></div>
                  <p className="mt-1 text-muted-foreground">{event.safe_summary || 'No redacted summary available.'}</p>
                </li>
              ))}</ul>
            )}</CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle className="flex items-center gap-2"><LockKeyhole className="h-5 w-5" /> Private messages</CardTitle><CardDescription>Opening messages is permission gated, requires an active grant for this exact session, and is recorded in the audit log.</CardDescription></CardHeader>
            <CardContent className="space-y-4">
              {!can('chat.sensitive_view') ? <p className="text-sm text-muted-foreground">Your role cannot view private chat messages. Session metadata and safety events remain available above.</p> : (
                <>
                  <div className="flex flex-wrap gap-3"><Button onClick={viewMessages} disabled={messagesLoading || !data.session.sensitive_content_available}>{messagesLoading ? 'Loading messages…' : 'View private messages'}</Button><Link href={`/breakglass?resource_type=chat_session&resource_id=${encodeURIComponent(data.session.id)}`} className="inline-flex h-8 items-center rounded-lg border px-3 text-sm hover:bg-muted">Request break-glass access</Link></div>
                  <p className="text-xs text-muted-foreground">Use resource type Chat Session and this session ID: <span className="break-all font-mono">{data.session.id}</span></p>
                  {messagesError && <p role="alert" className="flex gap-2 text-sm text-destructive"><ShieldAlert className="h-4 w-4 shrink-0" />{messagesError}</p>}
                  {messages && <div className="space-y-3"><p className="text-xs text-muted-foreground">Access expires {new Date(messages.grant_expires_at).toLocaleString()}.</p>{messages.messages.map((message) => <div key={message.id} className="rounded-md border p-3 text-sm"><div className="mb-2 flex gap-2 font-medium"><span>{message.role}</span><span className="text-muted-foreground">{new Date(message.created_at).toLocaleString()}</span></div><p className="whitespace-pre-wrap break-words">{message.content}</p></div>)}</div>}
                </>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}

export default function ChatSessionDetailPage() {
  return <Suspense fallback={<div className="p-6">Loading session…</div>}><ChatSessionDetailContent /></Suspense>;
}
