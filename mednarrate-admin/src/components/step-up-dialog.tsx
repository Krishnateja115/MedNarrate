'use client';

import { useCallback, useRef, useState, type FormEvent } from 'react';
import { fetchApi } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

export const STEP_UP_CANCELLED = 'Step-up cancelled';

type Pending = { resolve: (token: string) => void; reject: (error: Error) => void };

/**
 * Sensitive admin actions (resetting a password, approving break-glass access) need a fresh
 * password + authenticator code. `requestStepUp()` asks for them and resolves with the token the
 * API expects in the `X-Step-Up-Token` header. It rejects with STEP_UP_CANCELLED if dismissed.
 */
export function useStepUp() {
  const pending = useRef<Pending | null>(null);
  const [open, setOpen] = useState(false);
  const [purpose, setPurpose] = useState('');
  const [password, setPassword] = useState('');
  const [code, setCode] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const close = useCallback(() => {
    setOpen(false);
    setPassword('');
    setCode('');
    setError(null);
    setBusy(false);
  }, []);

  const requestStepUp = useCallback((why: string) => {
    return new Promise<string>((resolve, reject) => {
      pending.current = { resolve, reject };
      setPurpose(why);
      setOpen(true);
    });
  }, []);

  const cancel = useCallback(() => {
    pending.current?.reject(new Error(STEP_UP_CANCELLED));
    pending.current = null;
    close();
  }, [close]);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = await fetchApi<{ step_up_token: string }>('/api/v1/auth/step-up', {
        method: 'POST',
        data: { password, code: code.trim() || undefined },
      });
      pending.current?.resolve(res.step_up_token);
      pending.current = null;
      close();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Verification failed');
      setBusy(false);
    }
  };

  const stepUpDialog = (
    <Dialog open={open} onOpenChange={(next) => { if (!next) cancel(); }}>
      <DialogContent>
        <form onSubmit={submit} className="space-y-4">
          <DialogHeader>
            <DialogTitle>Confirm it&apos;s you</DialogTitle>
            <DialogDescription>{purpose}</DialogDescription>
          </DialogHeader>
          {error && (
            <div role="alert" className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
              {error}
            </div>
          )}
          <div className="space-y-1.5">
            <label htmlFor="step-up-password" className="text-sm font-medium">Your password</label>
            <Input id="step-up-password" type="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <label htmlFor="step-up-code" className="text-sm font-medium">Authenticator code</label>
            <Input id="step-up-code" inputMode="numeric" autoComplete="one-time-code" placeholder="6-digit code" maxLength={8} value={code} onChange={(e) => setCode(e.target.value)} />
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={cancel} disabled={busy}>Cancel</Button>
            <Button type="submit" disabled={busy || !password}>{busy ? 'Checking…' : 'Confirm'}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );

  return { requestStepUp, stepUpDialog };
}
