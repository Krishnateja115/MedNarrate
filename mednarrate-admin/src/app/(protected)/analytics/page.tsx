'use client';

import { useState, useEffect } from 'react';
import { apiFetch } from '@/lib/api';
import { 
  BarChart3, 
  Users, 
  FileText, 
  Bot, 
  MessageSquare, 
  Bell, 
  RefreshCw, 
  TrendingUp, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  ShieldCheck,
  Loader2
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';

interface AnalyticsData {
  timeframe: string;
  period_start: string;
  period_end: string;
  product: {
    total_users: number;
    new_registrations: number;
    active_users: number;
    retention_rate_pct: number;
    feature_usage: {
      reports_uploaded: number;
      chat_messages: number;
      support_tickets: number;
    };
  };
  reports: {
    total_uploads: number;
    completed: number;
    processing: number;
    failed: number;
    failure_categories: Record<string, number>;
    avg_processing_time_sec: number;
  };
  ai: {
    total_requests: number;
    success_rate_pct: number;
    failure_rate_pct: number;
    timeout_rate_pct: number;
    avg_latency_ms: number;
    provider_distribution: Array<{ provider: string; model: string; count: number }>;
    fallback_usage_count: number;
    verification_status: Record<string, number>;
  };
  chat: {
    sessions: number;
    messages: number;
    safety_classifications: Record<string, number>;
    rag_usage_pct: number;
  };
  notifications: {
    sent: number;
    failed: number;
    delivery_rate_pct: number;
    retry_volume: number;
  };
}

export default function AnalyticsPage() {
  const [timeframe, setTimeframe] = useState<'24h' | '7d' | '30d' | '90d' | 'all'>('7d');
  const [activeTab, setActiveTab] = useState<'product' | 'reports' | 'ai' | 'chat' | 'notifications'>('product');
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalytics = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await apiFetch(`/api/v1/admin/analytics?timeframe=${timeframe}`);
      if (res && res.status === 'ok') {
        setData(res);
      } else {
        setError('Failed to load analytics data.');
      }
    } catch (err: any) {
      setError(err?.message || 'Error connecting to analytics endpoint.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, [timeframe]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-blue-600" /> System Analytics & Operational Telemetry
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Real backend aggregated metrics strictly calculated from database telemetry.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          {/* Timeframe selector */}
          <div className="bg-slate-100 dark:bg-slate-800 p-1 rounded-lg flex space-x-1 text-xs font-semibold">
            {(['24h', '7d', '30d', '90d', 'all'] as const).map((tf) => (
              <button
                key={tf}
                onClick={() => setTimeframe(tf)}
                className={`px-3 py-1.5 rounded-md transition-colors ${
                  timeframe === tf
                    ? 'bg-white dark:bg-slate-900 text-blue-600 dark:text-blue-400 shadow-sm'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
                }`}
              >
                {tf.toUpperCase()}
              </button>
            ))}
          </div>

          <Button variant="outline" size="sm" onClick={fetchAnalytics} disabled={isLoading}>
            <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} /> Refresh
          </Button>
        </div>
      </div>

      {/* Tabs Header */}
      <div className="border-b border-slate-200 dark:border-slate-800 flex space-x-6">
        {[
          { id: 'product', label: 'Product', icon: Users },
          { id: 'reports', label: 'Reports Pipeline', icon: FileText },
          { id: 'ai', label: 'AI Operations', icon: Bot },
          { id: 'chat', label: 'Chat Engine', icon: MessageSquare },
          { id: 'notifications', label: 'Notifications', icon: Bell },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`flex items-center space-x-2 py-3 border-b-2 text-sm font-semibold transition-colors ${
              activeTab === tab.id
                ? 'border-blue-600 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-300'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Error State */}
      {error && (
        <Card className="border-rose-200 bg-rose-50 dark:bg-rose-950/30">
          <CardContent className="p-6 flex items-center justify-between">
            <div className="flex items-center space-x-3 text-rose-800 dark:text-rose-300">
              <AlertTriangle className="w-5 h-5 shrink-0" />
              <div>
                <h4 className="font-semibold text-sm">Analytics Endpoint Error</h4>
                <p className="text-xs">{error}</p>
              </div>
            </div>
            <Button variant="outline" size="sm" onClick={fetchAnalytics}>Retry</Button>
          </CardContent>
        </Card>
      )}

      {/* Loading Skeleton */}
      {isLoading && !data && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Card key={i} className="animate-pulse">
              <CardHeader className="h-20 bg-slate-100 dark:bg-slate-800 rounded-t-lg" />
              <CardContent className="h-24 bg-slate-50 dark:bg-slate-900/50" />
            </Card>
          ))}
        </div>
      )}

      {/* Tab Content */}
      {data && !isLoading && (
        <div className="space-y-6">

          {/* 1. PRODUCT TAB */}
          {activeTab === 'product' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card>
                  <CardContent className="pt-6">
                    <div className="flex justify-between items-center">
                      <span className="text-xs font-semibold text-slate-500 uppercase">Total Registered Users</span>
                      <Users className="w-5 h-5 text-blue-600" />
                    </div>
                    <div className="text-3xl font-extrabold text-slate-900 dark:text-white mt-2">
                      {data.product.total_users}
                    </div>
                    <p className="text-xs text-slate-500 mt-1">Platform total</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="pt-6">
                    <div className="flex justify-between items-center">
                      <span className="text-xs font-semibold text-slate-500 uppercase">New Registrations</span>
                      <TrendingUp className="w-5 h-5 text-emerald-600" />
                    </div>
                    <div className="text-3xl font-extrabold text-slate-900 dark:text-white mt-2">
                      {data.product.new_registrations}
                    </div>
                    <p className="text-xs text-slate-500 mt-1">During selected timeframe ({data.timeframe})</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="pt-6">
                    <div className="flex justify-between items-center">
                      <span className="text-xs font-semibold text-slate-500 uppercase">Active Users</span>
                      <ShieldCheck className="w-5 h-5 text-purple-600" />
                    </div>
                    <div className="text-3xl font-extrabold text-slate-900 dark:text-white mt-2">
                      {data.product.active_users}
                    </div>
                    <p className="text-xs text-slate-500 mt-1">Active report uploaders / chatters</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="pt-6">
                    <div className="flex justify-between items-center">
                      <span className="text-xs font-semibold text-slate-500 uppercase">Retention Rate</span>
                      <BarChart3 className="w-5 h-5 text-amber-600" />
                    </div>
                    <div className="text-3xl font-extrabold text-slate-900 dark:text-white mt-2">
                      {data.product.retention_rate_pct}%
                    </div>
                    <p className="text-xs text-slate-500 mt-1">Active return rate from prior period</p>
                  </CardContent>
                </Card>
              </div>

              {/* Feature Usage Breakdown */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-base font-bold">Feature Usage Volume ({data.timeframe})</CardTitle>
                  <CardDescription>Aggregate usage breakdown across primary platform modules.</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="p-4 bg-slate-50 dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800">
                      <span className="text-xs text-slate-500 font-medium">Medical Reports Uploaded</span>
                      <div className="text-2xl font-bold text-blue-600 mt-1">{data.product.feature_usage.reports_uploaded}</div>
                    </div>
                    <div className="p-4 bg-slate-50 dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800">
                      <span className="text-xs text-slate-500 font-medium">AI Chat Messages Sent</span>
                      <div className="text-2xl font-bold text-purple-600 mt-1">{data.product.feature_usage.chat_messages}</div>
                    </div>
                    <div className="p-4 bg-slate-50 dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800">
                      <span className="text-xs text-slate-500 font-medium">Support Tickets Created</span>
                      <div className="text-2xl font-bold text-amber-600 mt-1">{data.product.feature_usage.support_tickets}</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* 2. REPORTS TAB */}
          {activeTab === 'reports' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card>
                  <CardContent className="pt-6">
                    <span className="text-xs font-semibold text-slate-500 uppercase">Total Uploads</span>
                    <div className="text-3xl font-extrabold text-slate-900 dark:text-white mt-2">{data.reports.total_uploads}</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <span className="text-xs font-semibold text-emerald-600 uppercase">Completed</span>
                    <div className="text-3xl font-extrabold text-emerald-600 mt-2">{data.reports.completed}</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <span className="text-xs font-semibold text-amber-600 uppercase">Processing</span>
                    <div className="text-3xl font-extrabold text-amber-600 mt-2">{data.reports.processing}</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <span className="text-xs font-semibold text-rose-600 uppercase">Failed</span>
                    <div className="text-3xl font-extrabold text-rose-600 mt-2">{data.reports.failed}</div>
                  </CardContent>
                </Card>
              </div>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base font-bold">Report Processing Telemetry</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex justify-between items-center p-3 bg-slate-50 dark:bg-slate-900 rounded">
                    <span className="text-sm font-medium">Average Processing Duration</span>
                    <span className="font-bold text-blue-600">{data.reports.avg_processing_time_sec}s</span>
                  </div>

                  <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mt-4">Failure Category Breakdown</h4>
                  <div className="space-y-2">
                    {Object.entries(data.reports.failure_categories).length === 0 ? (
                      <p className="text-xs text-slate-500">No report failures recorded in this timeframe.</p>
                    ) : (
                      Object.entries(data.reports.failure_categories).map(([cat, count]) => (
                        <div key={cat} className="flex justify-between items-center p-2 border border-slate-100 dark:border-slate-800 rounded">
                          <span className="text-xs font-medium">{cat}</span>
                          <span className="text-xs px-2 py-0.5 bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-300 font-bold rounded">
                            {count}
                          </span>
                        </div>
                      ))
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* 3. AI TAB */}
          {activeTab === 'ai' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card>
                  <CardContent className="pt-6">
                    <span className="text-xs font-semibold text-slate-500 uppercase">Total AI Requests</span>
                    <div className="text-3xl font-extrabold text-slate-900 dark:text-white mt-2">{data.ai.total_requests}</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <span className="text-xs font-semibold text-emerald-600 uppercase">Success Rate</span>
                    <div className="text-3xl font-extrabold text-emerald-600 mt-2">{data.ai.success_rate_pct}%</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <span className="text-xs font-semibold text-rose-600 uppercase">Failure Rate</span>
                    <div className="text-3xl font-extrabold text-rose-600 mt-2">{data.ai.failure_rate_pct}%</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <span className="text-xs font-semibold text-blue-600 uppercase">Average Latency</span>
                    <div className="text-3xl font-extrabold text-blue-600 mt-2">{data.ai.avg_latency_ms} ms</div>
                  </CardContent>
                </Card>
              </div>

              {/* Provider & Model Distribution Table */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-base font-bold">LLM Provider & Model Distribution</CardTitle>
                </CardHeader>
                <CardContent>
                  {data.ai.provider_distribution.length === 0 ? (
                    <p className="text-xs text-slate-500">No LLM telemetry events recorded during this timeframe.</p>
                  ) : (
                    <div className="border border-slate-200 dark:border-slate-800 rounded-lg overflow-hidden">
                      <table className="w-full text-sm text-left">
                        <thead className="bg-slate-50 dark:bg-slate-900 text-xs font-semibold text-slate-500 border-b border-slate-200 dark:border-slate-800">
                          <tr>
                            <th className="p-3">Provider</th>
                            <th className="p-3">Model</th>
                            <th className="p-3 text-right">Requests Count</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                          {data.ai.provider_distribution.map((p, idx) => (
                            <tr key={idx}>
                              <td className="p-3 font-semibold uppercase text-xs">{p.provider}</td>
                              <td className="p-3 text-slate-600 dark:text-slate-400">{p.model}</td>
                              <td className="p-3 text-right font-bold">{p.count}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          )}

          {/* 4. CHAT TAB */}
          {activeTab === 'chat' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <Card>
                  <CardContent className="pt-6">
                    <span className="text-xs font-semibold text-slate-500 uppercase">Chat Sessions</span>
                    <div className="text-3xl font-extrabold text-slate-900 dark:text-white mt-2">{data.chat.sessions}</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <span className="text-xs font-semibold text-purple-600 uppercase">Total Messages</span>
                    <div className="text-3xl font-extrabold text-purple-600 mt-2">{data.chat.messages}</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <span className="text-xs font-semibold text-blue-600 uppercase">RAG Injection Rate</span>
                    <div className="text-3xl font-extrabold text-blue-600 mt-2">{data.chat.rag_usage_pct}%</div>
                  </CardContent>
                </Card>
              </div>
            </div>
          )}

          {/* 5. NOTIFICATIONS TAB */}
          {activeTab === 'notifications' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <Card>
                  <CardContent className="pt-6">
                    <span className="text-xs font-semibold text-emerald-600 uppercase">Notifications Sent</span>
                    <div className="text-3xl font-extrabold text-emerald-600 mt-2">{data.notifications.sent}</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <span className="text-xs font-semibold text-rose-600 uppercase">Failed Notifications</span>
                    <div className="text-3xl font-extrabold text-rose-600 mt-2">{data.notifications.failed}</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <span className="text-xs font-semibold text-blue-600 uppercase">Delivery Rate</span>
                    <div className="text-3xl font-extrabold text-blue-600 mt-2">{data.notifications.delivery_rate_pct}%</div>
                  </CardContent>
                </Card>
              </div>
            </div>
          )}

        </div>
      )}
    </div>
  );
}
