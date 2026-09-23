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
  Settings
} from 'lucide-react';

const NAV_ITEMS = [
  { name: 'Overview', href: '/', icon: LayoutDashboard },
  { name: 'Security Overview', href: '/security', icon: Shield },
  { name: 'Admin Accounts', href: '/admins', icon: Users },
  { name: 'Roles & Permissions', href: '/roles', icon: Lock },
  { name: 'Audit Logs', href: '/audit', icon: FileText },
  { name: 'Break-Glass Access', href: '/breakglass', icon: AlertTriangle },
  { name: 'Privacy Center', href: '/privacy', icon: Lock },
  { name: 'Feature Flags', href: '/feature-flags', icon: BarChart3 },
  { name: 'AI Configuration', href: '/ai-config', icon: Bot },
  { name: 'App Settings', href: '/settings', icon: Settings },
  { name: 'Announcements', href: '/announcements', icon: Bell },
  { name: 'System Health', href: '/health', icon: Activity },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 border-r border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 flex flex-col h-full overflow-y-auto">
      <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center h-16 shrink-0">
        <div className="w-8 h-8 bg-blue-600 rounded-md flex items-center justify-center mr-3">
          <Activity className="w-5 h-5 text-white" />
        </div>
        <span className="font-semibold text-lg tracking-tight">MedNarrate Admin</span>
      </div>
      <nav className="flex-1 p-4 space-y-1">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors",
                isActive
                  ? "bg-blue-50 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300"
                  : "text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-900 dark:hover:text-slate-200"
              )}
            >
              <item.icon className={cn("w-5 h-5 mr-3 shrink-0", isActive ? "text-blue-600 dark:text-blue-400" : "text-slate-400")} />
              {item.name}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
