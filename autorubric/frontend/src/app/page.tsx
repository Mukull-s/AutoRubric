'use client';

import Link from "next/link";
import { useQuery } from '@tanstack/react-query';
import { getRubrics } from '@/lib/api';

export default function DashboardPage() {
  const { data: rubrics, isLoading, error } = useQuery({ queryKey: ['rubrics'], queryFn: getRubrics });

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <Link href="/rubrics/new" className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">Create New Rubric</Link>
      </div>

      <h2 className="text-xl font-semibold mb-2">Rubrics</h2>
      {isLoading && <p>Loading rubrics...</p>}
      {error && <p className="text-red-500">Failed to load rubrics.</p>}
      {!isLoading && !error && (
        <ul className="space-y-2">
          {rubrics?.map((r) => (
            <li key={r.id} className="p-4 border rounded shadow flex justify-between items-center bg-white hover:bg-gray-50 transition">
              <Link href={`/rubrics/${r.id}`} className="flex-1 font-medium text-blue-600 hover:underline">{r.title}</Link>
              <span className="text-sm text-gray-500">{r.criteria?.length || 0} criteria</span>
            </li>
          ))}
          {(!rubrics || rubrics.length === 0) && <p>No rubrics found.</p>}
        </ul>
      )}
    </div>
  );
}
