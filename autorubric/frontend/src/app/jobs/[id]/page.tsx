'use client';

import { useParams } from 'next/navigation';
import { useQuery, useMutation } from '@tanstack/react-query';
import { getJob, retryJob } from '@/lib/api';
import Link from 'next/link';

const STAGES = ['QUEUED', 'EXTRACTING', 'SEGMENTING', 'RETRIEVING', 'EVALUATING', 'AUDITING', 'SCORING', 'ANNOTATING', 'DONE'];

export default function JobPage() {
  const params = useParams();
  const id = params.id as string;

  const { data: job, isLoading, error, refetch, isFetching } = useQuery({
    queryKey: ['job', id],
    queryFn: () => getJob(id),
    refetchInterval: (query) => {
      const state = query.state.data;
      if (!state) return 1500;
      const term = ['DONE', 'FAILED', 'NEEDS_REVIEW'].includes(state.status);
      return term ? false : 1500;
    },
    refetchIntervalInBackground: true,
  });

  const retryMutation = useMutation({
    mutationFn: () => retryJob(id),
    onSuccess: () => refetch()
  });

  if (isLoading) return <div className="p-6">Loading job...</div>;
  if (error) return <div className="p-6 text-red-500">Failed to load job</div>;

  const currentStatus = job?.status || 'QUEUED';
  const currentStageIdx = STAGES.indexOf(currentStatus);
  const isFailed = currentStatus === 'FAILED';
  const needsReview = currentStatus === 'NEEDS_REVIEW';
  const isDone = currentStatus === 'DONE';

  return (
    <div className="max-w-2xl mx-auto p-6 bg-white shadow rounded border">
      <Link href="/" className="text-blue-600 hover:underline mb-4 inline-block">&larr; Back to Dashboard</Link>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Job Status: {id}</h1>
        <button 
          onClick={() => refetch()} 
          disabled={isFetching}
          className="text-xs px-3 py-1.5 rounded border border-gray-300 hover:bg-gray-50 text-gray-600 flex items-center gap-1.5 transition-colors disabled:opacity-50"
        >
          <span>{isFetching ? 'Refreshing...' : 'Refresh Status'}</span>
        </button>
      </div>
      
      <div className="mb-6 flex items-center gap-3">
        <span className="font-medium">Status:</span>
        <span className={`px-2.5 py-1 rounded text-xs font-semibold text-white ${isFailed ? 'bg-red-500' : isDone ? 'bg-green-600' : needsReview ? 'bg-yellow-500' : 'bg-blue-600'}`}>
          {currentStatus}
        </span>
        {!isDone && !isFailed && (
          <span className="text-xs text-gray-400 animate-pulse">Running autonomous grading pipeline...</span>
        )}
      </div>

      <div className="mb-6">
        <div className="flex justify-between text-sm text-gray-500 mb-2">
          <span>Progress</span>
          <span>{currentStageIdx >= 0 ? Math.round(((currentStageIdx + 1) / STAGES.length) * 100) : 0}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded h-4 overflow-hidden flex">
          {STAGES.map((s, i) => {
            const active = i <= currentStageIdx;
            return <div key={s} className={`h-full flex-1 ${active ? 'bg-blue-500' : 'bg-transparent border-l border-gray-300'}`} title={s}></div>;
          })}
        </div>
      </div>

      {isFailed && job?.error && (
        <div className="mb-6 p-4 bg-red-50 text-red-700 rounded">
          <p className="font-bold">Error</p>
          <p>{job.error}</p>
        </div>
      )}

      <div className="flex gap-4">
        {isDone && job?.doc_id && (
          <Link href={`/results/${job.doc_id}`} className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">View Result</Link>
        )}
        {needsReview && job?.doc_id && (
          <Link href={`/results/${job.doc_id}`} className="bg-yellow-500 text-white px-4 py-2 rounded hover:bg-yellow-600">Review Result</Link>
        )}
        {isFailed && (
          <button onClick={() => retryMutation.mutate()} disabled={retryMutation.isPending} className="bg-gray-200 hover:bg-gray-300 px-4 py-2 rounded">
            {retryMutation.isPending ? 'Retrying...' : 'Retry Job'}
          </button>
        )}
      </div>
    </div>
  );
}
