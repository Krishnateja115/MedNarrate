'use client';

import { useQuery } from '@tanstack/react-query';
import { fetchApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Skeleton } from '@/components/ui/skeleton';
import { MessageSquare, ShieldAlert } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';

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

export default function ChatOpsPage() {
  const { data: sessionsData, isLoading: sessionsLoading } = useQuery<{status: string, sessions: ChatSession[]}>({
    queryKey: ['chat_sessions'],
    queryFn: () => fetchApi('/api/v1/admin/chat-ops/sessions'),
  });

  const { data: safetyData, isLoading: safetyLoading } = useQuery<{status: string, events: SafetyEvent[]}>({
    queryKey: ['chat_safety_events'],
    queryFn: () => fetchApi('/api/v1/admin/chat-ops/safety-events'),
  });

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
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <div className="space-y-1">
                <CardTitle>Recent Sessions</CardTitle>
                <CardDescription>View session metadata. Content is masked by default.</CardDescription>
              </div>
              <MessageSquare className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              {sessionsLoading ? (
                <Skeleton className="h-[400px] w-full" />
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Created At</TableHead>
                      <TableHead>Session ID</TableHead>
                      <TableHead>User ID</TableHead>
                      <TableHead>Report Related</TableHead>
                      <TableHead className="text-right">Action</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {sessionsData?.sessions.map(s => (
                      <TableRow key={s.id}>
                        <TableCell className="text-xs text-muted-foreground">{new Date(s.created_at).toLocaleString()}</TableCell>
                        <TableCell className="font-mono text-xs">{s.id.slice(0, 8)}</TableCell>
                        <TableCell className="font-mono text-xs text-primary">
                          <Link href={`/users/detail?id=${s.user_id}`} className="hover:underline">{s.user_id.slice(0, 8)}</Link>
                        </TableCell>
                        <TableCell>
                          {s.report_id ? (
                            <Link href={`/reports/detail?id=${s.report_id}`}>
                              <Badge variant="outline" className="text-blue-500 border-blue-500">Yes</Badge>
                            </Link>
                          ) : <span className="text-muted-foreground text-sm">No</span>}
                        </TableCell>
                        <TableCell className="text-right">
                          <Button variant="ghost" size="sm" disabled title="Requires sensitive access grant">
                            Inspect
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                    {(!sessionsData?.sessions || sessionsData.sessions.length === 0) && (
                      <TableRow>
                        <TableCell colSpan={5} className="text-center text-muted-foreground p-8">No active sessions.</TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="safety">
          <Card className="border-red-200">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <div className="space-y-1">
                <CardTitle className="text-destructive flex items-center gap-2">
                  <ShieldAlert className="h-5 w-5" /> Safety & Moderation Events
                </CardTitle>
                <CardDescription>Track prompt injections, emergencies, and flagged behaviors.</CardDescription>
              </div>
            </CardHeader>
            <CardContent>
              {safetyLoading ? (
                <Skeleton className="h-[400px] w-full" />
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Timestamp</TableHead>
                      <TableHead>Classification</TableHead>
                      <TableHead>Action Taken</TableHead>
                      <TableHead>User ID</TableHead>
                      <TableHead>Safe Summary</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {safetyData?.events.map(e => (
                      <TableRow key={e.id}>
                        <TableCell className="text-xs text-muted-foreground">{new Date(e.created_at).toLocaleString()}</TableCell>
                        <TableCell>
                          <Badge variant="destructive">{e.classification}</Badge>
                        </TableCell>
                        <TableCell className="font-medium text-sm">{e.action_taken}</TableCell>
                        <TableCell className="font-mono text-xs text-primary hover:underline">
                          <Link href={`/users/detail?id=${e.user_id}`}>{e.user_id.slice(0, 8)}</Link>
                        </TableCell>
                        <TableCell className="text-sm italic text-muted-foreground">{e.safe_summary || 'No summary available'}</TableCell>
                      </TableRow>
                    ))}
                    {(!safetyData?.events || safetyData.events.length === 0) && (
                      <TableRow>
                        <TableCell colSpan={5} className="text-center text-muted-foreground p-8">No safety events recorded.</TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
