'use client';

import * as React from 'react';

interface DropdownContextType {
  open: boolean;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
}

const DropdownContext = React.createContext<DropdownContextType>({
  open: false,
  setOpen: () => {},
});

export function DropdownMenu({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = React.useState(false);
  return (
    <DropdownContext.Provider value={{ open, setOpen }}>
      <div className="relative inline-block text-left">{children}</div>
    </DropdownContext.Provider>
  );
}

export function DropdownMenuTrigger({ children, asChild }: { children: React.ReactNode; asChild?: boolean }) {
  const { open, setOpen } = React.useContext(DropdownContext);
  return (
    <div onClick={() => setOpen(!open)} className="cursor-pointer">
      {children}
    </div>
  );
}

export function DropdownMenuContent({ children, align = 'right', className = '' }: { children: React.ReactNode; align?: 'left' | 'right'; className?: string }) {
  const { open, setOpen } = React.useContext(DropdownContext);
  const ref = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    if (open) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [open, setOpen]);

  if (!open) return null;

  return (
    <div
      ref={ref}
      className={`absolute ${align === 'right' ? 'right-0' : 'left-0'} mt-2 w-56 rounded-md shadow-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 z-50 overflow-hidden py-1 ${className}`}
    >
      {children}
    </div>
  );
}

export function DropdownMenuItem({ children, onClick, className = '' }: { children: React.ReactNode; onClick?: () => void; className?: string }) {
  const { setOpen } = React.useContext(DropdownContext);
  return (
    <div
      onClick={() => {
        if (onClick) onClick();
        setOpen(false);
      }}
      className={`px-4 py-2 text-sm text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer flex items-center transition-colors ${className}`}
    >
      {children}
    </div>
  );
}

export function DropdownMenuLabel({ children }: { children: React.ReactNode }) {
  return <div className="px-4 py-1.5 text-xs font-semibold text-slate-400 uppercase tracking-wider">{children}</div>;
}

export function DropdownMenuSeparator() {
  return <div className="my-1 border-t border-slate-100 dark:border-slate-800" />;
}
