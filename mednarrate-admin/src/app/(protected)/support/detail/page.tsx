/* eslint-disable */
'use client';
import { useSearchParams } from 'next/navigation';
import { Suspense, useState } from 'react';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { AlertTriangle, ArrowLeft, Send, ShieldAlert, User, Shield, CheckCircle2, Bot, AlertCircle } from 'lucide-react';
import Link from 'next/link';

interface TicketMessage {
  id: string;
  sender_id: string | null;
  is_internal: boolean;
  content: string;
  created_at: string;
}

interface TicketEvent {
  id: string;
  event_type: string;
  content: string;
  created_at: string;
}

interface TicketDetail {
  id: string;
  user_id: string;
  user_email: string | null;
  title: string;
  description: string;
  category: string;
  priority: string;
  status: string;
  assigned_admin_id: string | null;
  related_report_id: string | null;
  related_incident_id: string | null;
  created_at: string;
  updated_at: string;
}

function TicketInvestigationPageContent() {
  const searchParams = useSearchParams();
  const extractedId = searchParams.get('id');
  
  const ticketId = extractedId;
  const queryClient = useQueryClient();
  if (!extractedId) return <div className="p-8">No ID provided</div>;
  
  const [replyContent, setReplyContent] = useState('');
  const [isInternal, setIsInternal] = useState(false);
  const [actionMessage, setActionMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);
  
  const { data, isLoading, error } = useQuery<{status: string, ticket: TicketDetail, messages: TicketMessage[], events: TicketEvent[]}>({
    queryKey: ['support_ticket', ticketId],
    queryFn: () => fetchApi(`/api/v1/admin/support/${ticketId}`),
  });

  const replyMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(`/api/v1/admin/support/${ticketId}/reply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: replyContent, is_internal: isInternal })
      });
      if (!res.ok) throw new Error('Failed to send reply');
      return res.json();
    },
    onSuccess: () => {
      setReplyContent('');
      queryClient.invalidateQueries({ queryKey: ['support_ticket', ticketId] });
      setActionMessage({ type: 'success', text: isInternal ? 'Internal note added' : 'Reply sent to user' });
      setTimeout(() => setActionMessage(null), 3000);
    },
    onError: (err) => {
      setActionMessage({ type: 'error', text: err.message });
      setTimeout(() => setActionMessage(null), 3000);
    }
  });

  const updateMutation = useMutation({
    mutationFn: async (updates: any) => {
      const res = await fetch(`/api/v1/admin/support/${ticketId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
      });
      if (!res.ok) throw new Error('Update failed');
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['support_ticket', ticketId] });
    }
  });

  const escalateMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(`/api/v1/admin/support/${ticketId}/escalate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ escalation_type: 'incident', reason: 'Escalated by admin from ticket UI' })
      });
      if (!res.ok) throw new Error('Escalation failed');
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['support_ticket', ticketId] });
      setActionMessage({ type: 'success', text: 'Ticket escalated to Incident' });
      setTimeout(() => setActionMessage(null), 3000);
    }
  });

  const handleSendReply = () => {
    if (!replyContent.trim()) return;
    replyMutation.mutate();
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div><Skeleton className="h-4 w-24 mb-4" /><Skeleton className="h-10 w-1/3" /></div>
        <div className="grid grid-cols-3 gap-6">
          <div className="col-span-2"><Card><CardContent className="h-[400px]"><Skeleton className="h-full w-full" /></CardContent></Card></div>
          <div className="col-span-1"><Card><CardContent className="h-[400px]"><Skeleton className="h-full w-full" /></CardContent></Card></div>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="space-y-6">
        <Link href="/support" className="inline-flex items-center text-sm font-medium text-muted-foreground hover:text-foreground">
          <ArrowLeft className="mr-2 h-4 w-4" /> Back to Queue
        </Link>
        <div className="rounded-md bg-destructive/15 p-4 text-destructive border border-destructive/20 flex items-center gap-2">
          <AlertTriangle className="h-5 w-5" /> <h3 className="font-semibold">Ticket Not Found</h3>
        </div>
      </div>
    );
  }

  const { ticket, messages, events } = data;
  
  // Combine and sort messages and events for a unified timeline
  const timeline = [
    ...messages.map(m => ({ ...m, type: 'message' as const })),
    ...events.map(e => ({ ...e, type: 'event' as const }))
  ].sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());

  return (
    <div className="space-y-6 fade-in max-w-6xl mx-auto pb-12">
      <div>
        <Link href="/support" className="inline-flex items-center text-sm font-medium text-muted-foreground hover:text-foreground mb-4">
          <ArrowLeft className="mr-2 h-4 w-4" /> Back to Queue
        </Link>
        
        {actionMessage && (
          <div className={`mb-4 p-4 rounded-md border text-sm flex items-start gap-2 ${
            actionMessage.type === 'success' ? 'bg-emerald-500/15 border-emerald-500/30 text-emerald-700' : 'bg-destructive/15 border-destructive/30 text-destructive'
          }`}>
            {actionMessage.type === 'success' ? <CheckCircle2 className="h-5 w-5 shrink-0" /> : <AlertTriangle className="h-5 w-5 shrink-0" />}
            <div>{actionMessage.text}</div>
          </div>
        )}

        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-3xl font-bold tracking-tight">{ticket.title}</h1>
              {ticket.status === 'Resolved' && <Badge variant="outline" className="text-emerald-600 border-emerald-600">Resolved</Badge>}
              {ticket.status === 'Waiting for User' && <Badge variant="outline" className="text-amber-600 border-amber-600">Waiting for User</Badge>}
              {ticket.status === 'New' && <Badge className="bg-purple-500">New</Badge>}
            </div>
            <p className="text-muted-foreground text-sm font-mono">
              Ticket ID: {ticket.id} • User: {ticket.user_email || 'System'}
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => escalateMutation.mutate()} disabled={escalateMutation.isPending || !!ticket.related_incident_id}>
              <ShieldAlert className="mr-2 h-4 w-4" /> Escalate to Incident
            </Button>
            <Button variant="default" onClick={() => updateMutation.mutate({ status: 'Resolved' })} disabled={ticket.status === 'Resolved'}>
              <CheckCircle2 className="mr-2 h-4 w-4" /> Mark Resolved
            </Button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Timeline & Chat */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="flex flex-col h-[600px]">
            <CardHeader className="border-b pb-3 shrink-0">
              <CardTitle className="text-base flex items-center gap-2">
                Investigation Timeline
              </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
              {timeline.map((item) => {
                if (item.type === 'event') {
                  const ev = item as TicketEvent;
                  return (
                    <div key={ev.id} className="flex items-center justify-center py-2">
                      <div className="bg-muted px-4 py-1.5 rounded-full text-xs text-muted-foreground flex items-center gap-2">
                        <AlertCircle className="h-3 w-3" />
                        {ev.content}
                      </div>
                    </div>
                  );
                } else {
                  const msg = item as TicketMessage;
                  const isUser = msg.sender_id === ticket.user_id;
                  const isAdmin = !isUser;
                  
                  return (
                    <div key={msg.id} className={`flex gap-3 max-w-[85%] ${isUser ? 'mr-auto' : 'ml-auto flex-row-reverse'}`}>
                      <div className={`h-8 w-8 shrink-0 rounded-full flex items-center justify-center ${isUser ? 'bg-primary/10 text-primary' : msg.is_internal ? 'bg-amber-100 text-amber-600' : 'bg-slate-800 text-white'}`}>
                        {isUser ? <User className="h-4 w-4" /> : <Shield className="h-4 w-4" />}
                      </div>
                      <div className={`rounded-lg p-3 ${
                        isUser ? 'bg-muted border text-foreground' : 
                        msg.is_internal ? 'bg-amber-50 border-amber-200 text-amber-900 shadow-sm' : 
                        'bg-primary text-primary-foreground shadow-sm'
                      }`}>
                        {msg.is_internal && <div className="text-[10px] font-bold uppercase mb-1 opacity-70 flex items-center gap-1"><ShieldAlert className="h-3 w-3" /> Internal Note</div>}
                        <div className="text-sm whitespace-pre-wrap">{msg.content}</div>
                        <div className={`text-[10px] mt-2 opacity-70 text-right`}>
                          {new Date(msg.created_at).toLocaleString()}
                        </div>
                      </div>
                    </div>
                  );
                }
              })}
            </CardContent>
            <CardFooter className="border-t p-4 shrink-0 flex flex-col gap-3 bg-muted/30">
              <div className="flex items-center gap-4 w-full">
                <div className="flex items-center space-x-2">
                  <Switch 
                    id="internal-mode" 
                    checked={isInternal} 
                    onCheckedChange={setIsInternal}
                    className={isInternal ? 'data-[state=checked]:bg-amber-500' : ''}
                  />
                  <Label htmlFor="internal-mode" className={`font-semibold text-xs uppercase ${isInternal ? 'text-amber-600' : 'text-muted-foreground'}`}>
                    Internal Note
                  </Label>
                </div>
                {isInternal && <span className="text-xs text-amber-600 italic">User will not see this message.</span>}
              </div>
              <div className="flex gap-2 w-full relative">
                <Textarea 
                  placeholder={isInternal ? "Type an internal note for other admins..." : "Type a reply to the user..."}
                  className={`min-h-[80px] resize-none pr-12 ${isInternal ? 'border-amber-300 focus-visible:ring-amber-500 bg-amber-50/30' : ''}`}
                  value={replyContent}
                  onChange={(e) => setReplyContent(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSendReply();
                    }
                  }}
                />
                <Button 
                  size="icon" 
                  className={`absolute bottom-2 right-2 h-8 w-8 ${isInternal ? 'bg-amber-500 hover:bg-amber-600 text-white' : ''}`} 
                  onClick={handleSendReply}
                  disabled={replyMutation.isPending || !replyContent.trim()}
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </CardFooter>
          </Card>
        </div>

        {/* Right Column: Metadata & Actions */}
        <div className="space-y-6">
          <Card>
            <CardHeader className="pb-3 border-b">
              <CardTitle className="text-base">Metadata</CardTitle>
            </CardHeader>
            <CardContent className="pt-4 space-y-4">
              <div className="space-y-1">
                <Label className="text-xs text-muted-foreground uppercase">Status</Label>
                <Select value={ticket.status} onValueChange={(val) => updateMutation.mutate({ status: val })}>
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
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

              <div className="space-y-1">
                <Label className="text-xs text-muted-foreground uppercase">Priority</Label>
                <Select value={ticket.priority} onValueChange={(val) => updateMutation.mutate({ priority: val })}>
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="P1 Critical">P1 Critical</SelectItem>
                    <SelectItem value="P2 High">P2 High</SelectItem>
                    <SelectItem value="P3 Normal">P3 Normal</SelectItem>
                    <SelectItem value="P4 General">P4 General</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="pt-2 border-t">
                <span className="text-xs text-muted-foreground uppercase font-medium">Category</span>
                <div className="font-medium mt-1 text-sm">{ticket.category}</div>
              </div>

              <div>
                <span className="text-xs text-muted-foreground uppercase font-medium">Created</span>
                <div className="text-sm mt-1">{new Date(ticket.created_at).toLocaleString()}</div>
              </div>
            </CardContent>
          </Card>

          {ticket.related_report_id && (
            <Card className="border-blue-200 bg-blue-50/50 dark:bg-blue-950/20 dark:border-blue-900">
              <CardHeader className="pb-3 border-b border-blue-100 dark:border-blue-900/50">
                <CardTitle className="text-base flex items-center gap-2 text-blue-800 dark:text-blue-400">
                  <Bot className="h-4 w-4" /> Diagnostic Snapshot
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4 space-y-3">
                <div className="text-xs text-blue-800/80 dark:text-blue-300">
                  This ticket is linked to a specific report processing job.
                </div>
                <div className="font-mono text-xs bg-white dark:bg-black p-2 rounded border break-all">
                  Report ID: {ticket.related_report_id}
                </div>
                <Link href={`/reports/detail?id=${ticket.related_report_id}`} className="block">
                  <Button variant="outline" className="w-full bg-white dark:bg-black">
                    View Full Diagnostic Trace
                  </Button>
                </Link>
              </CardContent>
            </Card>
          )}

          {ticket.related_incident_id && (
            <Card className="border-red-200 bg-red-50/50 dark:bg-red-950/20 dark:border-red-900">
              <CardHeader className="pb-3 border-b border-red-100 dark:border-red-900/50">
                <CardTitle className="text-base flex items-center gap-2 text-red-800 dark:text-red-400">
                  <ShieldAlert className="h-4 w-4" /> Incident Escalate
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4 space-y-3">
                <div className="text-xs text-red-800/80 dark:text-red-300">
                  This ticket has been escalated to a platform incident.
                </div>
                <div className="font-mono text-xs bg-white dark:bg-black p-2 rounded border break-all">
                  Incident: {ticket.related_incident_id}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

export default function Page() {
  return (
    <Suspense fallback={<div className="p-8">Loading...</div>}>
      <TicketInvestigationPageContent />
    </Suspense>
  );
}
