'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Activity } from 'lucide-react';
import { fetchApi } from '@/lib/api';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

interface ActiveModel {
  provider: string;
  model: string;
  location: 'local' | 'hosted' | 'internal';
  successful_calls: number;
  avg_latency_ms: number | null;
  last_used: string | null;
  features: Record<string, number>;
}

interface LiveActivity {
  generated_at: string;
  window_hours: number;
  total_successful_calls: number;
  models: ActiveModel[];
}

const WINDOWS = [1, 24, 168] as const;

export function ModelLiveActivity() {
  const [hours, setHours] = useState<number>(24);
  const { data, isPending, isFetching, error, refetch } = useQuery<LiveActivity>({
    queryKey: ['live_model_activity', hours],
    queryFn: () => fetchApi<LiveActivity>(`/api/v1/admin/ml/live-activity?hours=${hours}`),
    refetchInterval: 15_000,
    refetchOnWindowFocus: true,
  });
  const activity = data && typeof data.total_successful_calls === 'number' && Array.isArray(data.models)
    ? data : null;

  return (
    <Card data-testid="model-live-activity">
      <CardHeader className="gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-1.5">
          <CardTitle className="flex items-center gap-2 text-base"><Activity className="h-4 w-4 text-blue-500" />Live model activity</CardTitle>
          <CardDescription>
            Successful app model calls, refreshed every 15 seconds. New providers and models appear after their first recorded call.
          </CardDescription>
        </div>
        <div className="flex flex-wrap items-center gap-1" aria-label="Activity window">
          {WINDOWS.map((windowHours) => (
            <Button
              key={windowHours}
              size="sm"
              variant={hours === windowHours ? 'default' : 'outline'}
              onClick={() => setHours(windowHours)}
              aria-pressed={hours === windowHours}
            >
              {windowHours === 1 ? '1 hour' : windowHours === 24 ? '24 hours' : '7 days'}
            </Button>
          ))}
          <Button size="sm" variant="ghost" onClick={() => void refetch()} disabled={isFetching}>Refresh</Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        {error && <p role="alert" className="text-destructive">Could not refresh model activity. {activity ? 'Showing the last available data.' : 'Try again shortly.'}</p>}
        {isPending && !activity ? <p className="text-muted-foreground">Loading model activity…</p> : null}
        {activity && (
          <>
            <div className="flex flex-wrap items-center gap-3 text-muted-foreground">
              <span><strong className="text-foreground">{activity.total_successful_calls}</strong> successful calls</span>
              <span>{activity.models.length} {activity.models.length === 1 ? 'model' : 'models'}</span>
              <span>Updated {new Date(activity.generated_at).toLocaleTimeString()}</span>
              {isFetching && <span>Refreshing…</span>}
            </div>
            {activity.models.length === 0 ? (
              <p className="rounded border p-4 text-muted-foreground">No successful model calls were recorded in this period. Use an AI feature in the app, then check again.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[650px] text-left">
                  <thead><tr className="border-b text-muted-foreground">
                    <th className="py-2 pr-3 font-medium">Provider / model</th>
                    <th className="py-2 pr-3 font-medium">Calls</th>
                    <th className="py-2 pr-3 font-medium">Avg. time</th>
                    <th className="py-2 pr-3 font-medium">Used for</th>
                    <th className="py-2 font-medium">Last used</th>
                  </tr></thead>
                  <tbody>
                    {activity.models.map((item) => (
                      <tr key={`${item.provider}/${item.model}`} className="border-b last:border-0">
                        <td className="py-2 pr-3"><div className="font-medium">{item.model}</div><div className="flex items-center gap-2 text-xs text-muted-foreground">{item.provider}<Badge variant="outline" className="capitalize">{item.location}</Badge></div></td>
                        <td className="py-2 pr-3">{item.successful_calls}</td>
                        <td className="py-2 pr-3">{item.avg_latency_ms === null ? '—' : `${Math.round(item.avg_latency_ms).toLocaleString()} ms`}</td>
                        <td className="py-2 pr-3">{Object.entries(item.features).map(([feature, count]) => `${feature} ${count}`).join(', ') || '—'}</td>
                        <td className="py-2">{item.last_used ? new Date(item.last_used).toLocaleString() : '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
        <p className="text-xs text-muted-foreground">
          Calls and response time show operational use, not answer accuracy or clinical quality. The benchmark comparison below changes only after an evaluation is run.
        </p>
      </CardContent>
    </Card>
  );
}
