 
import React from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ShieldAlert } from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export function Forbidden() {
  const router = useRouter();

  return (
    <div className="flex h-[calc(100vh-4rem)] w-full items-center justify-center p-4">
      <Card className="w-full max-w-md border-destructive/20 bg-destructive/5">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            <ShieldAlert className="h-12 w-12 text-destructive" />
          </div>
          <CardTitle className="text-2xl text-destructive">403 — Access Restricted</CardTitle>
          <CardDescription className="text-base mt-2">
            You are authenticated, but your administrator account does not have permission to access this resource.
          </CardDescription>
        </CardHeader>
        <CardFooter className="flex justify-center gap-4">
          <Button variant="outline" onClick={() => router.back()}>
            Go Back
          </Button>
          <Button>
            <Link href="/">
              Go to Overview
            </Link>
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}
