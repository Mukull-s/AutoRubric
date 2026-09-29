'use client';

import { useParams } from 'next/navigation';
import { useQuery, useMutation } from '@tanstack/react-query';
import { getCohort, getJob, retryJob } from '@/lib/api';
import Link from 'next/link';
import { useQueryClient } from '@tanstack/react-query';
import { CohortHeatmap } from '@/components/Heatmap';

const STAGES = ['QUEUED', 'EXTRACTING', 'SEGMENTING', 'RETRIEVING', 'EVALUATING', 'AUDITING', 'SCORING', 'ANNOTATING', 'DONE'];

function JobRow({ jobInitial }: { jobInitial: any }) {
  const queryClient = useQueryClient();
  const { data: job, error } = useQuery({
    queryKey: ['job', jobInitial.job_id],
    queryFn: () => getJob(jobInitial.job_id),
    initialData: jobInitial,
    refetchInterval: (query) => {
      const state = query.state.data;
      if (!state) return 2000;
      const term = ['DONE', 'FAILED', 'NEEDS_REVIEW'].includes(state.status);
      return term ? false : 2000;
    }
  });

  const retryMutation = useMutation({
    mutationFn: () => retryJob(jobInitial.job_id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['job', jobInitial.job_id] })
  });

  const currentStatus = job?.status || jobInitial.status;
  const currentStageIdx = STAGES.indexOf(currentStatus);
  const isFailed = currentStatus === 'FAILED';
  const needsReview = currentStatus === 'NEEDS_REVIEW';
  const isDone = currentStatus === 'DONE';

  return (
    <tr className="border-b">
      <td className="p-3">
        {jobInitial.file_name}
        {needsReview && <span className="ml-2 bg-yellow-100 text-yellow-800 text-xs px-2 py-1 rounded">NEEDS_REVIEW</span>}
      </td>
      <td className="p-3">
        <span className={`text-xs px-2 py-1 rounded text-white ${isFailed ? 'bg-red-500' : isDone ? 'bg-green-500' : needsReview ? 'bg-yellow-500' : 'bg-blue-500'}`}>
          {currentStatus}
        </span>
        {isFailed && job?.error && <div className="text-red-500 text-xs mt-1">{job.error}</div>}
      </td>
      <td className="p-3">
        <div className="flex text-xs space-x-1">
          {STAGES.map((s, i) => {
            const active = i <= currentStageIdx;
            return <div key={s} className={`h-2 w-4 rounded ${active ? 'bg-blue-500' : 'bg-gray-200'}`} title={s}></div>;
          })}
        </div>
      </td>
      <td className="p-3 text-right">
        {isDone && job?.doc_id && (
          <Link href={`/results/${job.doc_id}`} className="text-blue-600 hover:underline">View Result</Link>
        )}
        {needsReview && job?.doc_id && (
          <Link href={`/results/${job.doc_id}`} className="text-blue-600 hover:underline">Review Result</Link>
        )}
        {isFailed && (
          <button onClick={() => retryMutation.mutate()} disabled={retryMutation.isPending} className="text-sm bg-gray-200 hover:bg-gray-300 px-3 py-1 rounded">
            {retryMutation.isPending ? 'Retrying...' : 'Retry'}
          </button>
        )}
      </td>
    </tr>
  );
}

export default function CohortPage() {
  const params = useParams();
  const id = params.id as string;

  const { data: cohort, isLoading, error } = useQuery({
    queryKey: ['cohort', id],
    queryFn: () => getCohort(id),
  });

  if (isLoading) return <div className="p-6">Loading cohort...</div>;
  if (error) return <div className="p-6 text-red-500">Failed to load cohort</div>;

  return (
    <div className="max-w-5xl mx-auto p-6 bg-white shadow rounded border">
      <Link href="/" className="text-blue-600 hover:underline mb-4 inline-block">&larr; Back to Dashboard</Link>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Cohort: {cohort.name || id}</h1>
        <Link href={`/cohorts/${id}/collusion`} className="bg-purple-100 text-purple-800 px-4 py-2 rounded hover:bg-purple-200">
          View Collusion Report
        </Link>
      </div>

      {cohort.jobs && <CohortHeatmap jobs={cohort.jobs} />}
      
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="bg-gray-50 border-b">
            <th className="p-3 font-medium text-gray-600">Document</th>
            <th className="p-3 font-medium text-gray-600">Status</th>
            <th className="p-3 font-medium text-gray-600">Progress</th>
            <th className="p-3 font-medium text-gray-600 text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          {cohort.jobs?.map((job: any) => (
            <JobRow key={job.job_id} jobInitial={job} />
          ))}
        </tbody>
      </table>
    </div>
  );
}
