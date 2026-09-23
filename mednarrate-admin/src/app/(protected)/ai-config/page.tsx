'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { Bot, Key, ShieldAlert, CheckCircle, Lock } from 'lucide-react';

interface AIConfigResponse {
  primary_provider: string;
  model_name: string;
  temperature: number;
  max_tokens: number;
  fallback_provider: string;
  api_key_status: {
    is_set: boolean;
    masked_key: string | null;
  };
}

export default function AIConfigPage() {
  const queryClient = useQueryClient();
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Editable fields
  const [primaryProvider, setPrimaryProvider] = useState('gemini');
  const [modelName, setModelName] = useState('gemini-1.5-flash');
  const [temperature, setTemperature] = useState(0.2);
  const [maxTokens, setMaxTokens] = useState(2048);
  const [fallbackProvider, setFallbackProvider] = useState('ollama');
  const [newApiKey, setNewApiKey] = useState('');

  const { data, isLoading } = useQuery<AIConfigResponse>({
    queryKey: ['ai-config'],
    queryFn: () => fetchApi('/api/v1/admin/ai-config'),
  });

  useEffect(() => {
    if (data) {
      setPrimaryProvider(data.primary_provider || 'gemini');
      setModelName(data.model_name || 'gemini-1.5-flash');
      setTemperature(data.temperature ?? 0.2);
      setMaxTokens(data.max_tokens ?? 2048);
      setFallbackProvider(data.fallback_provider || 'ollama');
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
      max_tokens: maxTokens,
      fallback_provider: fallbackProvider,
      api_key: newApiKey.trim() ? newApiKey.trim() : undefined,
    });
  };

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 flex items-center gap-2">
          <Bot className="w-7 h-7 text-blue-600" /> AI Provider & Model Configuration
        </h1>
        <p className="text-slate-500 dark:text-slate-400 text-sm">
          Configure primary AI providers, model parameters, offline fallbacks, and securely store masked credentials.
        </p>
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
              <CardTitle className="text-lg">LLM Provider & Model Parameters</CardTitle>
              <CardDescription>Select primary provider, model family, and sampling parameters.</CardDescription>
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
                    <option value="gemini">Google Gemini</option>
                    <option value="openai">OpenAI GPT-4o</option>
                    <option value="anthropic">Anthropic Claude 3.5</option>
                    <option value="ollama">Local Ollama (Offline)</option>
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
                    onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                    className="w-full px-3 py-2 border rounded-md dark:bg-slate-900 dark:border-slate-700 text-sm"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Fallback Provider (Offline Mode)</label>
                  <select
                    value={fallbackProvider}
                    onChange={(e) => setFallbackProvider(e.target.value)}
                    className="w-full px-3 py-2 border rounded-md dark:bg-slate-900 dark:border-slate-700 text-sm"
                  >
                    <option value="ollama">Local Ollama Engine</option>
                    <option value="rule_based">Rule-Based Extraction Engine</option>
                    <option value="none">None (Fail fast)</option>
                  </select>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Masked Secret API Key Card */}
          <Card className="border-slate-200 dark:border-slate-800">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Key className="w-5 h-5 text-amber-500" /> Provider Secret Key (Masked)
              </CardTitle>
              <CardDescription>
                API keys are encrypted and NEVER exposed plain-text in GET responses.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-3">
                <Badge variant={data?.api_key_status.is_set ? 'default' : 'destructive'}>
                  {data?.api_key_status.is_set ? 'CONFIGURED' : 'MISSING'}
                </Badge>
                {data?.api_key_status.masked_key && (
                  <span className="font-mono text-sm text-slate-600 dark:text-slate-400">
                    Current Key: {data.api_key_status.masked_key}
                  </span>
                )}
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
