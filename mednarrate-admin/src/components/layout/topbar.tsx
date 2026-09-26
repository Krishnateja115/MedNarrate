'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '@/contexts/AuthContext';
import { fetchApi } from '@/lib/api';
import type { ApiError } from '@/lib/api';
import {
  Search, Bell, LogOut, ShieldAlert, AlertTriangle, Info,
  Loader2, X, CheckCircle2, Activity, Users, FileText,
  HeartPulse, MessageSquare, Database,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

interface SearchResult {
  type: 'user' | 'report' | 'ticket' | 'incident' | 'audit';
  id: string;
  title: string;
  subtitle: string;
  status: string;
  url: string;
}

interface AlertItem {
  id: string;
  category: string;
  severity: 'critical' | 'warning' | 'info';
  title: string;
  message: string;
  target_url: string;
  timestamp: string;
  acknowledged: boolean;
}

interface AlertsResponse {
  alerts: AlertItem[];
  unread_count: number;
}

interface BreakGlassSummaryResponse {
  status: 'ok' | 'attention';
  active_count: number;
}

// Severity → color/icon map
const SEVERITY_CONFIG = {
  critical: {
    icon: ShieldAlert,
    iconCls: 'text-rose-500',
    rowCls: 'border-l-2 border-rose-400',
  },
  warning: {
    icon: AlertTriangle,
    iconCls: 'text-amber-500',
    rowCls: 'border-l-2 border-amber-400',
  },
  info: {
    icon: Info,
    iconCls: 'text-blue-500',
    rowCls: 'border-l-2 border-blue-400',
  },
};

// Category → navigation target (fallback to alert.target_url)
const CATEGORY_ICON: Record<string, React.ComponentType<{ className?: string }>> = {
  incident: Activity,
  security: ShieldAlert,
  user: Users,
  report: FileText,
  support: MessageSquare,
  ai: Database,
  health: HeartPulse,
  chat: MessageSquare,
  rag: Database,
};

export function Topbar() {
  const { user, logout, isAuthenticated, isLoading: authLoading, can } = useAuth();
  const router = useRouter();
  const queryClient = useQueryClient();

  // Search state (local — not cached globally)
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showSearchModal, setShowSearchModal] = useState(false);
  const [showAlertsPopover, setShowAlertsPopover] = useState(false);

  const searchRef = useRef<HTMLDivElement>(null);
  const alertsRef = useRef<HTMLDivElement>(null);

  // ── Alerts query ────────────────────────────────────────────────────────────
  // Gated on: authenticated AND not still initializing
  // Polling every 60s (reduced from 30s to halve DB load)
  const {
    data: alertsData,
    isError: alertsError,
    error: alertsQueryError,
    isLoading: alertsLoading,
  } = useQuery<AlertsResponse>({
    queryKey: ['topbar-alerts'],
    queryFn: () => fetchApi('/api/v1/admin/alerts'),
    enabled: isAuthenticated && !authLoading,
    refetchInterval: 60_000,
    staleTime: 30_000,
    retry: false, // Don't retry 401s — that would re-trigger auth:unauthorized
  });

  // ── Break-glass count query ─────────────────────────────────────────────────
  // Only fetch the non-sensitive global count. Full grants stay on Security.
  const {
    data: breakGlassData,
  } = useQuery<BreakGlassSummaryResponse>({
    queryKey: ['topbar-breakglass-count'],
    queryFn: () => fetchApi('/api/v1/admin/break-glass/summary'),
    enabled: isAuthenticated && !authLoading
      && (can('security.view') || can('break_glass.read') || can('super_admin')),
    refetchInterval: 60_000,
    staleTime: 30_000,
    retry: false,
  });

  const alerts = alertsData?.alerts || [];
  const unreadCount = alertsData?.unread_count || 0;
  const isBreakGlassActive = (breakGlassData?.active_count ?? 0) > 0;
  const hasCriticalAlerts = alerts.some((alert) => alert.severity === 'critical' && !alert.acknowledged);
  const hasOperationalAlerts = alerts.some((alert) => !alert.acknowledged);
  const alertsForbidden = (alertsQueryError as ApiError | null)?.status === 403;
  const systemStatus = alertsError
    ? 'Status unavailable'
    : hasCriticalAlerts
      ? 'Critical attention'
      : hasOperationalAlerts
        ? 'Attention required'
        : 'Systems operational';

  // ── Search debounce ─────────────────────────────────────────────────────────
  useEffect(() => {
    if (!isAuthenticated) return;

    const trimmed = searchQuery.trim();
    let timer: ReturnType<typeof setTimeout>;

    if (trimmed.length === 0) {
      // Clear asynchronously to satisfy react-hooks/set-state-in-effect
      timer = setTimeout(() => {
        setSearchResults([]);
        setIsSearching(false);
      }, 0);
      return () => clearTimeout(timer);
    }

    timer = setTimeout(async () => {
      setIsSearching(true);
      try {
        const data = await fetchApi<{ results: SearchResult[] }>(
          `/api/v1/admin/search?q=${encodeURIComponent(trimmed)}`
        );
        setSearchResults(data?.results || []);
      } catch {
        setSearchResults([]);
      } finally {
        setIsSearching(false);
      }
    }, 400);

    return () => clearTimeout(timer);
  }, [searchQuery, isAuthenticated]);

  // ── Click-outside handlers ──────────────────────────────────────────────────
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setShowSearchModal(false);
      }
      if (alertsRef.current && !alertsRef.current.contains(e.target as Node)) {
        setShowAlertsPopover(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // ── Acknowledge alert ───────────────────────────────────────────────────────
  const handleAcknowledge = async (alertId: string) => {
    try {
      await fetchApi(`/api/v1/admin/alerts/${alertId}/acknowledge`, { method: 'POST' });
      queryClient.invalidateQueries({ queryKey: ['topbar-alerts'] });
    } catch {
      // Silent — bell will refresh next cycle
    }
  };

  const getResultBadgeColor = (type: string) => {
    switch (type) {
      case 'user': return 'bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-300';
      case 'report': return 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300';
      case 'ticket': return 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300';
      case 'incident': return 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-300';
      default: return 'bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300';
    }
  };

  return (
    <header
      className={`h-16 border-b flex items-center justify-between px-6 shrink-0 relative z-30 transition-colors duration-300
        ${isBreakGlassActive
          ? 'bg-red-600 dark:bg-red-700 border-red-700'
          : 'bg-white dark:bg-slate-950 border-slate-200 dark:border-slate-800'
        }`}
    >
      <img
        src="/brand/mednarrate-logo.png"
        alt=""
        aria-hidden="true"
        className="mr-3 h-7 w-7 shrink-0 rounded-md object-contain sm:hidden"
      />

      {/* ── Global Search ─────────────────────────────────────────────────── */}
      <div className="flex-1 flex items-center max-w-2xl relative" ref={searchRef}>
        <div className="relative w-full">
          <Search
            className={`absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4
              ${isBreakGlassActive ? 'text-red-200' : 'text-slate-400'}`}
          />
          <Input
            placeholder="Search users, reports, tickets, incidents, request IDs..."
            value={searchQuery}
            onChange={(e) => { setSearchQuery(e.target.value); setShowSearchModal(true); }}
            onFocus={() => setShowSearchModal(true)}
            className={`w-full pl-10 pr-8 border-none focus-visible:ring-1
              ${isBreakGlassActive
                ? 'bg-red-700/50 text-white placeholder:text-red-200 focus-visible:ring-red-400'
                : 'bg-slate-50 dark:bg-slate-900 focus-visible:ring-blue-500'
              }`}
          />
          {searchQuery && (
            <button
              onClick={() => { setSearchQuery(''); setSearchResults([]); }}
              className={`absolute right-3 top-1/2 -translate-y-1/2
                ${isBreakGlassActive ? 'text-red-200 hover:text-white' : 'text-slate-400 hover:text-slate-600'}`}
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Search Results Dropdown */}
        {showSearchModal && searchQuery.trim().length > 0 && (
          <div className="absolute top-12 left-0 right-0 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg shadow-xl overflow-hidden max-h-96 overflow-y-auto z-50 animate-in fade-in slide-in-from-top-2 duration-200">
            {isSearching ? (
              <div className="p-4 text-center text-sm text-slate-500 flex items-center justify-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                <span>Searching resources...</span>
              </div>
            ) : searchResults.length === 0 ? (
              <div className="p-4 text-center text-sm text-slate-500">
                No matching records found for &ldquo;{searchQuery}&rdquo;
              </div>
            ) : (
              <div className="divide-y divide-slate-100 dark:divide-slate-800">
                {searchResults.map((res) => {
                  const CategoryIcon = CATEGORY_ICON[res.type] || FileText;
                  return (
                    <button
                      key={`${res.type}-${res.id}`}
                      onClick={() => {
                        setShowSearchModal(false);
                        setSearchQuery('');
                        router.push(res.url);
                      }}
                      className="w-full text-left p-3 hover:bg-slate-50 dark:hover:bg-slate-800/60 flex items-center justify-between transition-colors"
                    >
                      <div>
                        <div className="flex items-center gap-2">
                          <CategoryIcon className="w-3.5 h-3.5 text-slate-400" />
                          <span className={`text-xs px-2 py-0.5 rounded font-semibold uppercase ${getResultBadgeColor(res.type)}`}>
                            {res.type}
                          </span>
                          <span className="font-semibold text-sm text-slate-900 dark:text-white">{res.title}</span>
                        </div>
                        <p className="text-xs text-slate-500 mt-0.5 pl-6">{res.subtitle}</p>
                      </div>
                      <span className="text-xs px-2 py-1 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 rounded shrink-0">
                        {res.status}
                      </span>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>

      {/* ── Right Controls ────────────────────────────────────────────────── */}
      <div className="flex items-center gap-3 ml-4">

        {/* Break-glass active banner */}
        {isBreakGlassActive && (
          <button
            onClick={() => router.push('/security')}
            className="hidden md:flex items-center px-3 py-1 bg-red-800 text-white rounded-full text-xs font-bold border border-red-900 animate-pulse uppercase tracking-wider hover:bg-red-900 transition-colors"
          >
            <AlertTriangle className="w-4 h-4 mr-2" />
            Break-Glass Active
          </button>
        )}

        {/* Lightweight system status derived from the shared alerts query. */}
        {!isBreakGlassActive && isAuthenticated && !authLoading && (
          <div className={`hidden md:flex items-center px-3 py-1 rounded-full text-xs font-semibold border gap-1.5
            ${alertsError
              ? 'bg-slate-50 text-slate-600 border-slate-200 dark:bg-slate-900 dark:text-slate-300 dark:border-slate-700'
              : hasCriticalAlerts
                ? 'bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/30 dark:text-rose-300 dark:border-rose-800'
                : hasOperationalAlerts
                  ? 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/30 dark:text-amber-300 dark:border-amber-800'
                  : 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-900/20 dark:text-emerald-300 dark:border-emerald-800'
            }`}>
            {alertsLoading ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : hasCriticalAlerts || hasOperationalAlerts || alertsError ? (
              <AlertTriangle className="w-3.5 h-3.5" />
            ) : (
              <CheckCircle2 className="w-3.5 h-3.5" />
            )}
            {alertsLoading ? 'Checking systems' : systemStatus}
          </div>
        )}

        {/* Initializing spinner */}
        {authLoading && (
          <Loader2 className="w-4 h-4 animate-spin text-slate-400" />
        )}

        {/* ── Alerts Bell ──────────────────────────────────────────────── */}
        <div className="relative" ref={alertsRef}>
          <Button
            variant="ghost"
            size="icon"
            className={`relative ${isBreakGlassActive ? 'hover:bg-red-700 text-white' : ''}`}
            onClick={() => setShowAlertsPopover(!showAlertsPopover)}
            disabled={!isAuthenticated}
            title="System alerts"
          >
            <Bell className={`w-5 h-5 ${isBreakGlassActive ? 'text-white' : 'text-slate-600 dark:text-slate-400'}`} />
            {unreadCount > 0 && (
              <span className="absolute top-1.5 right-1.5 w-4 h-4 bg-rose-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center">
                {unreadCount > 9 ? '9+' : unreadCount}
              </span>
            )}
          </Button>

          {/* Alerts Popover */}
          {showAlertsPopover && isAuthenticated && (
            <div className="absolute right-0 top-12 w-96 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg shadow-xl z-50 overflow-hidden animate-in fade-in zoom-in-95 duration-200">
              <div className="p-3 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50 dark:bg-slate-900/50">
                <span className="font-semibold text-sm text-slate-900 dark:text-white">System Alerts</span>
                <div className="flex items-center gap-2">
                  {unreadCount > 0 && (
                    <span className="text-xs px-2 py-0.5 bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-300 rounded font-semibold">
                      {unreadCount} unread
                    </span>
                  )}
                  <button
                    onClick={() => { setShowAlertsPopover(false); router.push('/incidents'); }}
                    className="text-xs text-blue-600 hover:underline font-medium"
                  >
                    View all →
                  </button>
                </div>
              </div>

              <div className="max-h-80 overflow-y-auto divide-y divide-slate-100 dark:divide-slate-800">
                {alertsForbidden ? (
                  <div className="p-4 text-center text-sm text-amber-700 dark:text-amber-300">
                    You do not have permission to view global alerts.
                  </div>
                ) : alertsError ? (
                  <div className="p-4 text-center text-sm text-destructive">
                    Alerts are temporarily unavailable. Other controls remain active.
                  </div>
                ) : alerts.length === 0 ? (
                  <div className="p-6 text-center">
                    <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
                    <p className="text-sm text-slate-500">No active alerts. All services optimal.</p>
                  </div>
                ) : (
                  alerts.map((alert) => {
                    const cfg = SEVERITY_CONFIG[alert.severity] || SEVERITY_CONFIG.info;
                    const SevIcon = cfg.icon;
                    const CategoryIcon = CATEGORY_ICON[alert.category] || Activity;
                    return (
                      <div
                        key={alert.id}
                        className={`p-3 transition-colors ${cfg.rowCls} ${alert.acknowledged ? 'opacity-50' : 'bg-white dark:bg-slate-900'}`}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex items-center gap-2 min-w-0">
                            <SevIcon className={`w-4 h-4 shrink-0 ${cfg.iconCls}`} />
                            <span className="font-semibold text-xs text-slate-900 dark:text-white truncate">{alert.title}</span>
                          </div>
                          {!alert.acknowledged && (
                            <button
                              onClick={() => handleAcknowledge(alert.id)}
                              className="text-[11px] text-blue-600 hover:text-blue-800 dark:text-blue-400 font-medium shrink-0"
                            >
                              Dismiss
                            </button>
                          )}
                        </div>
                        <p className="text-xs text-slate-600 dark:text-slate-400 mt-1 pl-6 line-clamp-2">{alert.message}</p>
                        <div className="mt-2 pl-6 flex items-center justify-between">
                          <div className="flex items-center gap-1 text-[10px] text-slate-400">
                            <CategoryIcon className="w-3 h-3" />
                            <span>{alert.category}</span>
                            <span className="mx-1">·</span>
                            <span>{new Date(alert.timestamp).toLocaleTimeString()}</span>
                          </div>
                          {alert.target_url && (
                            <button
                              onClick={() => {
                                setShowAlertsPopover(false);
                                router.push(alert.target_url);
                              }}
                              className="text-xs text-blue-600 hover:underline font-semibold"
                            >
                              View →
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          )}
        </div>

        {/* ── User Info & Logout ────────────────────────────────────────── */}
        <div className={`flex items-center gap-3 border-l pl-3
          ${isBreakGlassActive ? 'border-red-500' : 'border-slate-200 dark:border-slate-800'}`}>
          <div className="hidden sm:flex flex-col items-end">
            <span className={`text-sm font-medium ${isBreakGlassActive ? 'text-white' : 'text-slate-900 dark:text-white'}`}>
              {user?.full_name || 'Admin'}
            </span>
            <span className={`text-xs capitalize ${isBreakGlassActive ? 'text-red-200' : 'text-slate-500'}`}>
              {user?.role || '—'}
            </span>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={logout}
            title="Log out"
            className={isBreakGlassActive ? 'hover:bg-red-700 text-white' : ''}
          >
            <LogOut className={`w-5 h-5 ${isBreakGlassActive ? 'text-white' : 'text-slate-600 dark:text-slate-400'}`} />
          </Button>
        </div>
      </div>
    </header>
  );
}
