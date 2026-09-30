'use client';

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";

export function Navigation() {
  const { token, doLogout } = useAuth();
  const pathname = usePathname();

  if (pathname === '/login') return null;

  return (
    <nav className="border-b p-4 flex gap-4 bg-slate-50 items-center">
      <Link href="/" className="font-bold text-lg">AutoRubric</Link>
      {token && (
        <>
          <Link href="/upload" className="text-sm text-blue-600 hover:underline">Upload</Link>
          <div className="flex-1"></div>
          <button onClick={doLogout} className="text-sm text-red-600 hover:underline">Logout</button>
        </>
      )}
    </nav>
  );
}
