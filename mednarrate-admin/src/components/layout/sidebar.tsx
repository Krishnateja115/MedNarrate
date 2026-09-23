'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { useAuth } from '@/contexts/AuthContext';
import {
  LayoutDashboard,
  LifeBuoy,
  Users,
  FileText,
  Bot,
  MessageSquare,
  Bell,
  BookOpen,
  Activity,
  AlertTriangle,
  BarChart3,
  Shield,
  Lock,
  Settings,
  Database,
  Sliders,
  Radio,
  Clock,
  PieChart
} from 'lucide-react';

const NAV_GROUPS = [
  {
    title: 'Core Operations',
    items: [
      { name: 'Command Center', href: '/', icon: LayoutDashboard, permissions: ['dashboard.view'] },
      { name: 'Analytics', href: '/analytics', icon: PieChart, permissions: ['analytics.view'] },
      { name: 'User Management', href: '/users', icon: Users, permissions: ['users.view'] },
      { name: 'Medical Reports', href: '/reports', icon: FileText, permissions: ['reports.view'] },
      { name: 'Support Desk', href: '/support', icon: LifeBuoy, permissions: ['support.view'] },
      { name: 'System Incidents', href: '/incidents', icon: AlertTriangle, permissions: ['incidents.view'] },
    ]
  },
  {
    title: 'AI & Data Ops',
    items: [
      { name: 'AI Operations', href: '/ai-ops', icon: Bot, permissions: ['ai.view', 'ai.manage'] },
      { name: 'Chat Operations', href: '/chat-ops', icon: MessageSquare, permissions: ['chat.view'] },
      { name: 'RAG Knowledge Ops', href: '/rag-ops', icon: Database, permissions: ['knowledge_base.view'] },
      { name: 'Automation Jobs', href: '/automation-ops', icon: Clock, permissions: ['automation.view'] },
      { name: 'Help Center', href: '/help-center', icon: BookOpen, permissions: ['help_center.view'] },
    ]
  },
  {
    title: 'Governance & Security',
    items: [
      { name: 'Security Overview', href: '/security', icon: Shield, permissions: ['security.view', 'audit_logs.view'] },
      { name: 'Admin Accounts', href: '/admins', icon: Users, permissions: ['roles.view', 'users.manage'] },
      { name: 'Roles & Permissions', href: '/roles', icon: Lock, permissions: ['roles.view'] },
      { name: 'Audit Logs', href: '/audit', icon: FileText, permissions: ['audit_logs.view'] },
      { name: 'Break-Glass Access', href: '/breakglass', icon: AlertTriangle, permissions: ['security.view'] },
      { name: 'Privacy Center', href: '/privacy', icon: Lock, permissions: ['privacy.view'] },
      { name: 'Feature Flags', href: '/feature-flags', icon: Sliders, permissions: ['configuration.view', 'feature_flags.view'] },
      { name: 'AI Configuration', href: '/ai-config', icon: Bot, permissions: ['ai.manage'] },
      { name: 'System Health', href: '/health', icon: Activity, permissions: ['system.health.view'] },
      { name: 'App Settings', href: '/settings', icon: Settings, permissions: ['configuration.view'] },
      { name: 'Announcements', href: '/announcements', icon: Radio, permissions: ['support.manage'] },
    ]
  }
];

export function Sidebar() {
  const pathname = usePathname();
  const { hasAnyPermission } = useAuth();

  return (
    <aside className="w-64 border-r border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 flex flex-col h-full overflow-y-auto">
      <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center h-16 shrink-0">
        <div className="w-8 h-8 bg-blue-600 rounded-md flex items-center justify-center mr-3 shadow-sm">
          <Activity className="w-5 h-5 text-white" />
        </div>
        <span className="font-bold text-lg tracking-tight text-slate-900 dark:text-white">MedNarrate Admin</span>
      </div>
      <nav className="flex-1 p-4 space-y-6">
        {NAV_GROUPS.map((group) => {
          // Filter items based on permissions
          const visibleItems = group.items.filter(item => hasAnyPermission(item.permissions));
          if (visibleItems.length === 0) return null;

          return (
            <div key={group.title} className="space-y-1">
              <h3 className="px-3 text-xs font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500 mb-2">
                {group.title}
              </h3>
              {visibleItems.map((item) => {
                const isActive = item.href === '/' ? pathname === '/' : pathname === item.href || pathname.startsWith(`${item.href}/`);
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={cn(
                      "flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors",
                      isActive
                        ? "bg-blue-50 text-blue-700 dark:bg-blue-950/60 dark:text-blue-300 font-semibold"
                        : "text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-900 dark:hover:text-slate-200"
                    )}
                  >
                    <item.icon className={cn("w-4 h-4 mr-3 shrink-0", isActive ? "text-blue-600 dark:text-blue-400" : "text-slate-400")} />
                    {item.name}
                  </Link>
                );
              })}
            </div>
          );
        })}
      </nav>
    </aside>
  );
}
