'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { token } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (mounted && !token && pathname !== '/login') {
      router.push('/login');
    }
  }, [mounted, token, pathname, router]);

  if (!mounted) return null; // Avoid hydration mismatch

  if (!token && pathname !== '/login') {
    return null; // Wait for redirect
  }

  return <>{children}</>;
}
