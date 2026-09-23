'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';

export interface SwitchProps {
  checked?: boolean;
  onCheckedChange?: (checked: boolean) => void;
  disabled?: boolean;
  className?: string;
  id?: string;
}

export function Switch({ checked = false, onCheckedChange, disabled = false, className = '', id }: SwitchProps) {
  return (
    <button
      id={id}
      type="button"
      role="switch"
      aria-checked={checked}
      disabled={disabled}
      onClick={() => !disabled && onCheckedChange && onCheckedChange(!checked)}
      className={cn(
        'relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
        checked ? 'bg-blue-600' : 'bg-slate-200 dark:bg-slate-700',
        disabled && 'opacity-50 cursor-not-allowed',
        className
      )}
    >
      <span
        className={cn(
          'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out',
          checked ? 'translate-x-5' : 'translate-x-0'
        )}
      />
    </button>
  );
}
