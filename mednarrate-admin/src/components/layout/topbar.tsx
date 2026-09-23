'use client';

import { useAuth } from '@/contexts/AuthContext';
import { Search, Bell, LogOut, User } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

export function Topbar() {
  const { user, logout } = useAuth();

  return (
    <header className="h-16 border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 flex items-center justify-between px-6 shrink-0">
      <div className="flex-1 flex items-center max-w-2xl">
        <div className="relative w-full">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <Input 
            placeholder="Search users, reports, incidents... (Cmd+K)" 
            className="w-full pl-10 bg-slate-50 dark:bg-slate-900 border-none focus-visible:ring-1 focus-visible:ring-slate-300"
          />
        </div>
      </div>
      
      <div className="flex items-center space-x-4 ml-4">
        <div className="hidden md:flex items-center px-3 py-1 bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400 rounded-full text-xs font-semibold">
          Development Environment
        </div>
        
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="w-5 h-5 text-slate-600 dark:text-slate-400" />
          <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full"></span>
        </Button>
        
        <div className="flex items-center space-x-3 border-l border-slate-200 dark:border-slate-800 pl-4">
          <div className="flex flex-col items-end hidden sm:flex">
            <span className="text-sm font-medium">{user?.full_name || 'Admin User'}</span>
            <span className="text-xs text-slate-500 capitalize">{user?.role || 'Admin'}</span>
          </div>
          <Button variant="ghost" size="icon" onClick={logout} title="Log out">
            <LogOut className="w-5 h-5 text-slate-600 dark:text-slate-400" />
          </Button>
        </div>
      </div>
    </header>
  );
}
