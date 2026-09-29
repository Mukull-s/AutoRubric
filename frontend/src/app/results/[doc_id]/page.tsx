'use client';

import { useParams } from 'next/navigation';
import { useQuery, useMutation } from '@tanstack/react-query';
import { getResult, verifyResult } from '@/lib/api';
import Link from 'next/link';
import { AlertCircle, CheckCircle2, ShieldAlert } from 'lucide-react';

export default function ResultPage() {
  const params = useParams();
  const docId = params.doc_id as string;

  const { data: result, isLoading, error, refetch } = useQuery({
    queryKey: ['result', docId],
    queryFn: () => getResult(docId),
  });

  const verifyMutation = useMutation({
    mutationFn: () => verifyResult(docId)
  });

  if (isLoading) return <div className="p-6">Loading result...</div>;
  if (error) return <div className="p-6 text-red-500">Failed to load result</div>;

  return (
    <div className="max-w-6xl mx-auto p-6 bg-white shadow rounded border">
      <div className="mb-4 flex justify-between items-center">
        <Link href="/" className="text-blue-600 hover:underline">&larr; Back to Dashboard</Link>
        <button 
          onClick={() => verifyMutation.mutate()} 
          disabled={verifyMutation.isPending}
          className="bg-gray-200 text-gray-800 px-4 py-2 rounded hover:bg-gray-300"
        >
          {verifyMutation.isPending ? 'Verifying...' : 'Verify Score'}
        </button>
      </div>

      <div className="flex justify-between items-end mb-6">
        <div>
          <h1 className="text-3xl font-bold">Result for {docId}</h1>
          <div className="text-gray-500 mt-1">Rubric ID: {result.rubric_id}</div>
        </div>
        <div className="text-right">
          <div className="text-3xl font-bold">{result.total} / {result.max_total}</div>
          <div className="text-gray-500 uppercase text-xs tracking-wider font-semibold">Total Score</div>
        </div>
      </div>

      {result.needs_review && (
        <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded flex gap-3">
          <AlertCircle className="text-yellow-600" />
          <div>
            <h3 className="font-bold text-yellow-800">Needs Review</h3>
            <ul className="list-disc ml-4 text-yellow-700 text-sm">
              {(result.review_reasons || []).map((r: string, i: number) => <li key={i}>{r}</li>)}
            </ul>
          </div>
        </div>
      )}

      {verifyMutation.isSuccess && verifyMutation.data && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded">
          <h3 className="font-bold text-green-800">Verification</h3>
          <p className="text-green-700 text-sm">
            {verifyMutation.data.match ? "Scores match the verifiable proof." : "Scores DO NOT match the verifiable proof! (See console for differences)"}
          </p>
        </div>
      )}

      <table className="w-full text-left border-collapse mt-4">
        <thead>
          <tr className="bg-gray-50 border-b">
            <th className="p-3 font-medium text-gray-600">Criterion</th>
            <th className="p-3 font-medium text-gray-600">Label</th>
            <th className="p-3 font-medium text-gray-600">Marks</th>
            <th className="p-3 font-medium text-gray-600">Trust</th>
            <th className="p-3 font-medium text-gray-600">Evidence</th>
          </tr>
        </thead>
        <tbody>
          {result.per_criterion?.map((c: any) => (
            <tr key={c.criterion_id} className={`border-b ${!c.trusted ? 'bg-red-50' : ''}`}>
              <td className="p-3 font-medium">{c.criterion_id}</td>
              <td className="p-3">
                <span className={`inline-block px-2 py-1 rounded text-xs font-semibold
                  ${c.label === 'FULL_CREDIT' ? 'bg-green-100 text-green-800' : 
                    c.label === 'PARTIAL_CREDIT' ? 'bg-blue-100 text-blue-800' : 
                    c.label === 'MISCONCEPTION' ? 'bg-purple-100 text-purple-800' : 
                    'bg-gray-100 text-gray-800'}`}>
                  {c.label}
                </span>
              </td>
              <td className="p-3">
                <div className="font-bold">{c.marks}</div>
                <div className="text-xs text-gray-500">Credit: {c.credit}</div>
                {c.capped && <div className="text-xs text-orange-500">Capped</div>}
              </td>
              <td className="p-3">
                {c.trusted ? (
                  <span title="Trusted"><CheckCircle2 className="text-green-500" size={20} /></span>
                ) : (
                  <span title="Untrusted"><ShieldAlert className="text-red-500" size={20} /></span>
                )}
                {c.flags && c.flags.length > 0 && (
                  <div className="mt-1 flex flex-col gap-1">
                    {c.flags.map((f: any, i: number) => (
                      <span key={i} className="text-[10px] bg-red-100 text-red-800 px-1 py-0.5 rounded" title={f.reason}>
                        {f.code}
                      </span>
                    ))}
                  </div>
                )}
              </td>
              <td className="p-3 text-sm text-gray-600">
                {/* Fallback to boxes since proposition text is a future contract */}
                {c.evidence_bboxes?.length > 0 ? (
                  c.evidence_bboxes.map((box: any, i: number) => (
                    <div key={i}>Page {box.page} (x:{box.x}, y:{box.y})</div>
                  ))
                ) : (
                  "No evidence"
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
