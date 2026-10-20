/* eslint-disable */
'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { Key, ShieldAlert, CheckCircle } from 'lucide-react';
import { providerLabel } from '@/lib/provider-labels';

interface AIConfigResponse {
  primary_provider: string;
  model_name: string;
  temperature: number;
  max_tokens: number;
  fallback_provider: string;
  api_key_status: {
    is_set: boolean;
  };
  overridden?: string[];
}

// Cloud providers need their API key in the backend .env; Groq models are separate so one model's limit does not block the other.
const PRIMARY_OPTIONS = ['gemini', 'groq', 'groq_qwen', 'openrouter', 'vertex_ai', 'ollama'];
const FALLBACK_OPTIONS: { value: string; label: string }[] = [
  { value: 'groq', label: providerLabel('groq') },
  { value: 'groq_qwen', label: providerLabel('groq_qwen') },
  { value: 'openrouter', label: providerLabel('openrouter') },
  { value: 'fallback', label: 'Built-in safe fallback (no AI)' },
  { value: 'ollama', label: 'Local Ollama' },
  { value: 'none', label: 'None (fail fast)' },
];

// The server reports its Gemini setting as either id; both run the same provider.
const normalizeProvider = (p: string) => (p === 'dev_gemini' ? 'gemini' : p);

export default function AIConfigPage() {
  const queryClient = useQueryClient();
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Editable fields
  const [primaryProvider, setPrimaryProvider] = useState('gemini');
  const [modelName, setModelName] = useState('');
  const [temperature, setTemperature] = useState(0.2);
  const [maxTokens, setMaxTokens] = useState(2048);
  const [fallbackProvider, setFallbackProvider] = useState('fallback');
  const [newApiKey, setNewApiKey] = useState('');

  const { data, isLoading } = useQuery<AIConfigResponse>({
    queryKey: ['ai-config'],
    queryFn: () => fetchApi('/api/v1/admin/ai-config'),
  });

  useEffect(() => {
    if (data) {
      setPrimaryProvider(normalizeProvider(data.primary_provider || 'gemini'));
      setModelName(data.model_name || '');
      setTemperature(data.temperature ?? 0.2);
      setMaxTokens(data.max_tokens ?? 2048);
      setFallbackProvider(data.fallback_provider || 'fallback');
    }
  }, [data]);

  const updateConfigMutation = useMutation({
    mutationFn: (payload: any) => fetchApi('/api/v1/admin/ai-config', { method: 'PUT', data: payload }),
    onSuccess: () => {
      setSuccessMsg('AI operational configuration updated successfully');
      setErrorMsg(null);
      setNewApiKey('');
      queryClient.invalidateQueries({ queryKey: ['ai-config'] });
    },
    onError: (err: any) => {
      setErrorMsg(err.message || 'Failed to update AI configuration');
      setSuccessMsg(null);
    }
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateConfigMutation.mutate({
      primary_provider: primaryProvider,
      model_name: modelName,
      temperature,
      max_tokens: Number.isFinite(maxTokens) ? maxTokens : 2048,
      fallback_provider: fallbackProvider,
      api_key: newApiKey.trim() ? newApiKey.trim() : undefined,
    });
  };

  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">AI Configuration</h1>
          <p className="text-muted-foreground">Choose the AI provider and model, and store its API key securely.</p>
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

      {isLoading ? (
        <Skeleton className="h-64 w-full" />
      ) : (
        <form onSubmit={handleSubmit} className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Provider &amp; model</CardTitle>
              <CardDescription>What the app is using right now. Saved changes apply to new requests.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Primary LLM Provider</label>
                  <select
                    value={primaryProvider}
                    onChange={(e) => setPrimaryProvider(e.target.value)}
                    className="w-full px-3 py-2 border rounded-md dark:bg-slate-900 dark:border-slate-700 text-sm"
                  >
                    {(PRIMARY_OPTIONS.includes(primaryProvider) ? PRIMARY_OPTIONS : [primaryProvider, ...PRIMARY_OPTIONS]).map((p) => (
                      <option key={p} value={p}>{providerLabel(p)}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Model Name</label>
                  <input
                    type="text"
                    value={modelName}
                    onChange={(e) => setModelName(e.target.value)}
                    className="w-full px-3 py-2 border rounded-md dark:bg-slate-900 dark:border-slate-700 text-sm font-mono"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Temperature ({temperature})</label>
                  <input
                    type="range"
                    min="0.0"
                    max="1.0"
                    step="0.05"
                    value={temperature}
                    onChange={(e) => setTemperature(parseFloat(e.target.value))}
                    className="w-full"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Max Token Output Limit</label>
                  <input
                    type="number"
                    min={256}
                    max={16384}
                    value={maxTokens}
                    onChange={(e) => setMaxTokens(parseInt(e.target.value, 10) || 0)}
                    className="w-full px-3 py-2 border rounded-md dark:bg-slate-900 dark:border-slate-700 text-sm"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Fallback if the primary fails</label>
                  <select
                    value={fallbackProvider}
                    onChange={(e) => setFallbackProvider(e.target.value)}
                    className="w-full px-3 py-2 border rounded-md dark:bg-slate-900 dark:border-slate-700 text-sm"
                  >
                    {(FALLBACK_OPTIONS.some((o) => o.value === fallbackProvider) ? FALLBACK_OPTIONS : [{ value: fallbackProvider, label: providerLabel(fallbackProvider) }, ...FALLBACK_OPTIONS]).map((o) => (
                      <option key={o.value} value={o.value}>{o.label}</option>
                    ))}
                  </select>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Masked Secret API Key Card */}
          <Card className="border-slate-200 dark:border-slate-800">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Key className="w-5 h-5 text-amber-500" /> Provider Secret Key
              </CardTitle>
              <CardDescription>
                The key is stored encrypted and is never shown again after saving.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-3">
                <Badge variant={data?.api_key_status.is_set ? 'default' : 'destructive'}>
                  {data?.api_key_status.is_set ? 'CONFIGURED' : 'MISSING'}
                </Badge>
                <span className="text-sm text-muted-foreground">
                  {data?.overridden?.length ? `Overridden here: ${data.overridden.join(', ')}. Other values come from the server environment.` : 'All values currently come from the server environment.'}
                </span>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Update Secret API Key</label>
                <input
                  type="password"
                  value={newApiKey}
                  onChange={(e) => setNewApiKey(e.target.value)}
                  placeholder="Enter new secret key to update (leave blank to keep current)..."
                  className="w-full px-3 py-2 border rounded-md dark:bg-slate-900 dark:border-slate-700 text-sm font-mono"
                />
              </div>
            </CardContent>
          </Card>

          <Button type="submit" disabled={updateConfigMutation.isPending} className="w-full md:w-auto">
            {updateConfigMutation.isPending ? 'Saving Settings...' : 'Save AI Configuration'}
          </Button>
        </form>
      )}
    </div>
  );
}
