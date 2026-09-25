/* eslint-disable */
'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { apiFetch } from '@/lib/api';
import { Search, Bell, LogOut, ShieldAlert, CheckCircle, AlertTriangle, Info, Loader2, X } from 'lucide-react';
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

export function Topbar() {
  const { user, logout } = useAuth();
  const router = useRouter();

  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showSearchModal, setShowSearchModal] = useState(false);

  // Alerts state
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showAlertsPopover, setShowAlertsPopover] = useState(false);

  const searchRef = useRef<HTMLDivElement>(null);
  const alertsRef = useRef<HTMLDivElement>(null);

  // Fetch alerts on load & interval
  const fetchAlerts = async () => {
    try {
      const data = await apiFetch('/api/v1/admin/alerts');
      if (data && data.alerts) {
        setAlerts(data.alerts);
        setUnreadCount(data.unread_count || 0);
      }
    } catch (e) {
      console.error('Failed to fetch alerts', e);
    }
  };

  const [isBreakGlassActive, setIsBreakGlassActive] = useState(false);
  const fetchBreakGlass = async () => {
    try {
      const data = await apiFetch('/api/v1/admin/break-glass/grants');
      if (data && data.grants) {
        setIsBreakGlassActive(data.grants.some((g: any) => g.status === 'active'));
      }
    } catch (e) {
      console.error('Failed to fetch break glass status', e);
    }
  };

  useEffect(() => {
    fetchAlerts();
    fetchBreakGlass();
    const interval = setInterval(() => {
      fetchAlerts();
      fetchBreakGlass();
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  // Handle Search Debounce
  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      setIsSearching(false);
      return;
    }

    setIsSearching(true);
    const timer = setTimeout(async () => {
      try {
        const data = await apiFetch(`/api/v1/admin/search?q=${encodeURIComponent(searchQuery.trim())}`);
        if (data && data.results) {
          setSearchResults(data.results);
        }
      } catch (err) {
        console.error('Global search error', err);
      } finally {
        setIsSearching(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Click Outside Handlers
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

  const handleAcknowledge = async (alertId: string) => {
    try {
      await apiFetch(`/api/v1/admin/alerts/${alertId}/acknowledge`, { method: 'POST' });
      fetchAlerts();
    } catch (err) {
      console.error('Failed to acknowledge alert', err);
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
    <header className={`h-16 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between px-6 shrink-0 relative z-30 transition-colors ${isBreakGlassActive ? 'bg-red-600 dark:bg-red-700 border-red-700' : 'bg-white dark:bg-slate-950'}`}>
      
      {/* Global Search Input */}
      <div className="flex-1 flex items-center max-w-2xl relative" ref={searchRef}>
        <div className="relative w-full">
          <Search className={`absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 ${isBreakGlassActive ? 'text-red-200' : 'text-slate-400'}`} />
          <Input 
            placeholder="Global search users, reports, tickets, incidents, request IDs..." 
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setShowSearchModal(true);
            }}
            onFocus={() => setShowSearchModal(true)}
            className={`w-full pl-10 pr-8 border-none focus-visible:ring-1 ${isBreakGlassActive ? 'bg-red-700/50 text-white placeholder:text-red-200 focus-visible:ring-red-400' : 'bg-slate-50 dark:bg-slate-900 focus-visible:ring-blue-500'}`}
          />
          {searchQuery && (
            <button 
              onClick={() => { setSearchQuery(''); setSearchResults([]); }}
              className={`absolute right-3 top-1/2 -translate-y-1/2 ${isBreakGlassActive ? 'text-red-200 hover:text-white' : 'text-slate-400 hover:text-slate-600'}`}
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Search Results Dropdown */}
        {showSearchModal && (searchQuery.trim().length > 0) && (
          <div className="absolute top-12 left-0 right-0 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg shadow-xl overflow-hidden max-h-96 overflow-y-auto z-50 animate-in fade-in slide-in-from-top-2 duration-200">
            {isSearching ? (
              <div className="p-4 text-center text-sm text-slate-500 flex items-center justify-center space-x-2">
                <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                <span>Searching resources...</span>
              </div>
            ) : searchResults.length === 0 ? (
              <div className="p-4 text-center text-sm text-slate-500">
                No matching records found for "{searchQuery}"
              </div>
            ) : (
              <div className="divide-y divide-slate-100 dark:divide-slate-800">
                {searchResults.map((res) => (
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
                      <div className="flex items-center space-x-2">
                        <span className={`text-xs px-2 py-0.5 rounded font-semibold uppercase ${getResultBadgeColor(res.type)}`}>
                          {res.type}
                        </span>
                        <span className="font-semibold text-sm text-slate-900 dark:text-white">{res.title}</span>
                      </div>
                      <p className="text-xs text-slate-500 mt-0.5">{res.subtitle}</p>
                    </div>
                    <span className="text-xs px-2 py-1 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 rounded">
                      {res.status}
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Right Controls */}
      <div className="flex items-center space-x-4 ml-4">
        {isBreakGlassActive && (
          <div className="hidden md:flex items-center px-3 py-1 bg-red-800 text-white rounded-full text-xs font-bold border border-red-900 animate-pulse uppercase tracking-wider">
            <AlertTriangle className="w-4 h-4 mr-2" />
            Break-Glass Protocol Active
          </div>
        )}
        {!isBreakGlassActive && (
          <div className="hidden md:flex items-center px-3 py-1 bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 rounded-full text-xs font-semibold border border-blue-200 dark:border-blue-800">
            Governance Operational
          </div>
        )}

        {/* Notifications / Alerts Bell */}
        <div className="relative" ref={alertsRef}>
          <Button 
            variant="ghost" 
            size="icon" 
            className={`relative ${isBreakGlassActive ? 'hover:bg-red-700 text-white' : ''}`}
            onClick={() => setShowAlertsPopover(!showAlertsPopover)}
          >
            <Bell className={`w-5 h-5 ${isBreakGlassActive ? 'text-white' : 'text-slate-600 dark:text-slate-400'}`} />
            {unreadCount > 0 && (
              <span className="absolute top-1.5 right-1.5 w-4 h-4 bg-rose-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center">
                {unreadCount}
              </span>
            )}
          </Button>

          {/* Alerts Popover */}
          {showAlertsPopover && (
            <div className="absolute right-0 top-12 w-96 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg shadow-xl z-50 overflow-hidden animate-in fade-in zoom-in-95 duration-200">
              <div className="p-3 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50 dark:bg-slate-900/50">
                <span className="font-semibold text-sm text-slate-900 dark:text-white">System Alerts & Notifications</span>
                <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300 rounded font-semibold">
                  {unreadCount} unread
                </span>
              </div>
              <div className="max-h-80 overflow-y-auto divide-y divide-slate-100 dark:divide-slate-800">
                {alerts.length === 0 ? (
                  <div className="p-4 text-center text-sm text-slate-500">
                    No active system alerts. All services optimal.
                  </div>
                ) : (
                  alerts.map((alert) => (
                    <div 
                      key={alert.id}
                      className={`p-3 transition-colors ${alert.acknowledged ? 'bg-slate-50/50 dark:bg-slate-900/30 opacity-60' : 'bg-white dark:bg-slate-900'}`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-center space-x-2">
                          {alert.severity === 'critical' ? (
                            <ShieldAlert className="w-4 h-4 text-rose-500 shrink-0" />
                          ) : alert.severity === 'warning' ? (
                            <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0" />
                          ) : (
                            <Info className="w-4 h-4 text-blue-500 shrink-0" />
                          )}
                          <span className="font-semibold text-xs text-slate-900 dark:text-white">{alert.title}</span>
                        </div>
                        {!alert.acknowledged && (
                          <button
                            onClick={() => handleAcknowledge(alert.id)}
                            className="text-[11px] text-blue-600 hover:text-blue-800 dark:text-blue-400 font-medium"
                          >
                            Mark Read
                          </button>
                        )}
                      </div>
                      <p className="text-xs text-slate-600 dark:text-slate-400 mt-1 pl-6">{alert.message}</p>
                      <div className="mt-2 pl-6 flex items-center justify-between">
                        <span className="text-[10px] text-slate-400">{new Date(alert.timestamp).toLocaleTimeString()}</span>
                        <button
                          onClick={() => {
                            setShowAlertsPopover(false);
                            router.push(alert.target_url);
                          }}
                          className="text-xs text-blue-600 hover:underline font-semibold"
                        >
                          View Resource &rarr;
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* User Profile / Logout */}
        <div className={`flex items-center space-x-3 border-l pl-4 ${isBreakGlassActive ? 'border-red-500' : 'border-slate-200 dark:border-slate-800'}`}>
          <div className="flex flex-col items-end hidden sm:flex">
            <span className={`text-sm font-medium ${isBreakGlassActive ? 'text-white' : 'text-slate-900 dark:text-white'}`}>{user?.full_name || 'Admin User'}</span>
            <span className={`text-xs capitalize ${isBreakGlassActive ? 'text-red-200' : 'text-slate-500'}`}>{user?.role || 'Admin'}</span>
          </div>
          <Button variant="ghost" size="icon" onClick={logout} title="Log out" className={isBreakGlassActive ? 'hover:bg-red-700 text-white' : ''}>
            <LogOut className={`w-5 h-5 ${isBreakGlassActive ? 'text-white' : 'text-slate-600 dark:text-slate-400'}`} />
          </Button>
        </div>
      </div>
    </header>
  );
}
