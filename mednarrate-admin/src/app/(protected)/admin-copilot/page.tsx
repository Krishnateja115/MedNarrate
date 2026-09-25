/* eslint-disable */
'use client';

import { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Bot, User, Send, Loader2, Database, ShieldAlert, FileText } from 'lucide-react';
import { fetchApi } from '@/lib/api';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  isStreaming?: boolean;
}

export default function AdminCopilotPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: 'Hello! I am your Admin Copilot. I can help you analyze system health, query the knowledge base, review recent incidents, and provide security context. How can I assist you today?'
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = { id: Date.now().toString(), role: 'user', content: input.trim() };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetchApi('/api/v1/admin/copilot/chat', {
        method: 'POST',
        body: JSON.stringify({ message: userMessage.content, history: messages.slice(1).map(m => ({ role: m.role, content: m.content })) })
      });

      setMessages(prev => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: response.reply
        }
      ]);
    } catch (error: any) {
      setMessages(prev => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: `Error: ${error.message || 'Failed to connect to Copilot.'}`
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6 fade-in h-[calc(100vh-8rem)] flex flex-col">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Admin Copilot</h1>
        <p className="text-muted-foreground">Your AI assistant for system administration and diagnostics.</p>
      </div>

      <Card className="flex-1 flex flex-col min-h-0">
        <CardHeader className="py-3 px-4 border-b shrink-0 bg-slate-50 dark:bg-slate-900/50">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="bg-primary/10 p-1.5 rounded-md text-primary">
                <Bot className="h-4 w-4" />
              </div>
              <CardTitle className="text-sm font-medium">Assistant Chat</CardTitle>
            </div>
            <div className="flex gap-2 text-xs text-muted-foreground">
              <div className="flex items-center gap-1 bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded"><Database className="h-3 w-3" /> Metrics</div>
              <div className="flex items-center gap-1 bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded"><ShieldAlert className="h-3 w-3" /> Security</div>
              <div className="flex items-center gap-1 bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded"><FileText className="h-3 w-3" /> Logs</div>
            </div>
          </div>
        </CardHeader>
        <CardContent className="flex-1 p-0 flex flex-col min-h-0">
          <div 
            ref={scrollRef}
            className="flex-1 overflow-y-auto p-4 space-y-4"
          >
            {messages.map((message) => (
              <div 
                key={message.id} 
                className={`flex gap-3 max-w-[85%] ${message.role === 'user' ? 'ml-auto flex-row-reverse' : ''}`}
              >
                <div className={`shrink-0 h-8 w-8 rounded-full flex items-center justify-center ${
                  message.role === 'user' 
                    ? 'bg-blue-100 text-blue-600 dark:bg-blue-900 dark:text-blue-300' 
                    : 'bg-primary/10 text-primary'
                }`}>
                  {message.role === 'user' ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                </div>
                <div className={`p-3 rounded-lg text-sm ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white dark:bg-blue-600'
                    : message.content.startsWith('Error:') 
                      ? 'bg-destructive/10 text-destructive border border-destructive/20'
                      : 'bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200'
                }`}>
                  <div className="whitespace-pre-wrap leading-relaxed">{message.content}</div>
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex gap-3 max-w-[85%]">
                <div className="shrink-0 h-8 w-8 rounded-full bg-primary/10 text-primary flex items-center justify-center">
                  <Bot className="h-4 w-4" />
                </div>
                <div className="p-3 rounded-lg bg-slate-100 dark:bg-slate-800 flex items-center">
                  <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                  <span className="ml-2 text-sm text-muted-foreground">Thinking...</span>
                </div>
              </div>
            )}
          </div>
          
          <div className="p-4 border-t bg-white dark:bg-slate-950 shrink-0">
            <form 
              onSubmit={(e) => { e.preventDefault(); handleSend(); }}
              className="flex gap-2 items-center relative"
            >
              <Input 
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about system health, recent incidents, or security logs..."
                className="flex-1 pr-10"
                disabled={isLoading}
              />
              <Button 
                type="submit" 
                size="icon" 
                disabled={!input.trim() || isLoading}
                className="absolute right-1 h-8 w-8 rounded-sm"
              >
                <Send className="h-4 w-4" />
              </Button>
            </form>
            <div className="text-center mt-2">
              <span className="text-[10px] text-muted-foreground">
                Copilot queries are logged for audit purposes. Do not enter sensitive PHI.
              </span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
