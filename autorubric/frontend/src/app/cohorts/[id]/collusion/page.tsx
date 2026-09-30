'use client';

import { useParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { getCollusion } from '@/lib/api';
import Link from 'next/link';

export default function CollusionPage() {
  const params = useParams();
  const cohortId = params.id as string;

  const { data: report, isLoading, error } = useQuery({
    queryKey: ['collusion', cohortId],
    queryFn: () => getCollusion(cohortId),
  }) as { data: { doc_pairs?: { a: string, b: string, similarity: number, matching_props?: string[] }[] } | undefined, isLoading: boolean, error: unknown };

  if (isLoading) return <div className="p-6">Loading collusion report...</div>;
  if (error || !report) return <div className="p-6 text-red-500">Failed to load collusion report</div>;

  const docPairs = report?.doc_pairs || [];

  return (
    <div className="max-w-6xl mx-auto p-6 bg-white shadow rounded border">
      <div className="mb-4">
        <Link href={`/cohorts/${cohortId}`} className="text-blue-600 hover:underline">&larr; Back to Cohort</Link>
      </div>
      <h1 className="text-3xl font-bold mb-6">Collusion Report for Cohort {cohortId}</h1>

      {docPairs.length === 0 ? (
        <div className="p-4 bg-gray-50 border rounded text-gray-600">
          No suspicious pairs above threshold found.
        </div>
      ) : (
        <div className="flex flex-col gap-6">
          <div className="p-4 bg-yellow-50 border border-yellow-200 text-yellow-800 rounded">
            Found {docPairs.length} suspicious pair{docPairs.length > 1 ? 's' : ''}.
          </div>
          
          {docPairs.map((pair: { a: string, b: string, similarity: number, matching_props?: string[] }, index: number) => (
            <div key={index} className="border rounded overflow-hidden">
              <div className="bg-gray-100 p-4 border-b flex justify-between items-center">
                <div>
                  <h3 className="font-bold text-lg">Pair Similarity: {(pair.similarity * 100).toFixed(1)}%</h3>
                  <div className="text-sm text-gray-600">{pair.matching_props?.length || 0} matching propositions</div>
                </div>
                <div className="flex gap-4">
                  <Link href={`/results/${pair.a}`} className="text-blue-600 hover:underline">View {pair.a}</Link>
                  <Link href={`/results/${pair.b}`} className="text-blue-600 hover:underline">View {pair.b}</Link>
                </div>
              </div>
              <div className="p-4 grid grid-cols-2 gap-4">
                <div>
                  <h4 className="font-semibold mb-2">Document A ({pair.a})</h4>
                  <ul className="list-disc pl-5 text-sm">
                    {pair.matching_props?.map((m: string, i: number) => (
                      <li key={i}>{m.split('::')[0]}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h4 className="font-semibold mb-2">Document B ({pair.b})</h4>
                  <ul className="list-disc pl-5 text-sm">
                    {pair.matching_props?.map((m: string, i: number) => (
                      <li key={i}>{m.split('::')[1]}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
