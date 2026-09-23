'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
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
      { name: 'Command Center', href: '/', icon: LayoutDashboard },
      { name: 'Analytics', href: '/analytics', icon: PieChart },
      { name: 'User Management', href: '/users', icon: Users },
      { name: 'Medical Reports', href: '/reports', icon: FileText },
      { name: 'Support Desk', href: '/support', icon: LifeBuoy },
      { name: 'System Incidents', href: '/incidents', icon: AlertTriangle },
    ]
  },
  {
    title: 'AI & Data Ops',
    items: [
      { name: 'AI Operations', href: '/ai-ops', icon: Bot },
      { name: 'Chat Operations', href: '/chat-ops', icon: MessageSquare },
      { name: 'RAG Knowledge Ops', href: '/rag-ops', icon: Database },
      { name: 'Automation Jobs', href: '/automation-ops', icon: Clock },
      { name: 'Help Center', href: '/help-center', icon: BookOpen },
    ]
  },
  {
    title: 'Governance & Security',
    items: [
      { name: 'Security Overview', href: '/security', icon: Shield },
      { name: 'Admin Accounts', href: '/admins', icon: Users },
      { name: 'Roles & Permissions', href: '/roles', icon: Lock },
      { name: 'Audit Logs', href: '/audit', icon: FileText },
      { name: 'Break-Glass Access', href: '/breakglass', icon: AlertTriangle },
      { name: 'Privacy Center', href: '/privacy', icon: Lock },
      { name: 'Feature Flags', href: '/feature-flags', icon: Sliders },
      { name: 'AI Configuration', href: '/ai-config', icon: Bot },
      { name: 'System Health', href: '/health', icon: Activity },
      { name: 'App Settings', href: '/settings', icon: Settings },
      { name: 'Announcements', href: '/announcements', icon: Radio },
    ]
  }
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 border-r border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 flex flex-col h-full overflow-y-auto">
      <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center h-16 shrink-0">
        <div className="w-8 h-8 bg-blue-600 rounded-md flex items-center justify-center mr-3 shadow-sm">
          <Activity className="w-5 h-5 text-white" />
        </div>
        <span className="font-bold text-lg tracking-tight text-slate-900 dark:text-white">MedNarrate Admin</span>
      </div>
      <nav className="flex-1 p-4 space-y-6">
        {NAV_GROUPS.map((group) => (
          <div key={group.title} className="space-y-1">
            <h3 className="px-3 text-xs font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500 mb-2">
              {group.title}
            </h3>
            {group.items.map((item) => {
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
        ))}
      </nav>
    </aside>
  );
}
