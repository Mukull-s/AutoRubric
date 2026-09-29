'use client';

import { useQuery } from '@tanstack/react-query';
import { getResult } from '@/lib/api';

export function CohortHeatmap({ jobs }: { jobs: any[] }) {
  const doneJobs = jobs.filter(j => j.status === 'DONE' && j.doc_id);
  
  // Fetch results for all done jobs
  const resultsQueries = useQuery({
    queryKey: ['cohortResults', doneJobs.map(j => j.doc_id)],
    queryFn: async () => {
      const results = await Promise.all(
        doneJobs.map(j => getResult(j.doc_id))
      );
      return results;
    },
    enabled: doneJobs.length > 0,
  });

  if (resultsQueries.isLoading) return <div className="p-4 bg-gray-50 rounded">Loading heatmap data...</div>;
  if (!resultsQueries.data || resultsQueries.data.length === 0) return null;

  const results = resultsQueries.data;
  
  // Calculate miss rates per criterion
  const criteriaStats: Record<string, { total: number, missed: number }> = {};
  
  for (const result of results) {
    if (!result.per_criterion) continue;
    for (const c of result.per_criterion) {
      if (!criteriaStats[c.criterion_id]) {
        criteriaStats[c.criterion_id] = { total: 0, missed: 0 };
      }
      criteriaStats[c.criterion_id].total += 1;
      // Missed if not FULL_CREDIT
      if (c.label !== 'FULL_CREDIT') {
        criteriaStats[c.criterion_id].missed += 1;
      }
    }
  }

  const criteriaArray = Object.entries(criteriaStats).map(([id, stats]) => ({
    id,
    missRate: stats.total > 0 ? stats.missed / stats.total : 0,
    ...stats
  })).sort((a, b) => b.missRate - a.missRate); // Sort by most missed

  return (
    <div className="mb-8" aria-label="Cohort Criteria Heatmap">
      <h2 className="text-xl font-bold mb-4">Class Performance Heatmap</h2>
      <p className="text-sm text-gray-600 mb-4">Criteria that students struggled with the most (missed full credit).</p>
      
      <div className="flex flex-col gap-2">
        {criteriaArray.map(c => {
          const percentage = Math.round(c.missRate * 100);
          return (
            <div key={c.id} className="flex items-center gap-4">
              <div className="w-24 text-sm font-semibold truncate" title={c.id}>{c.id}</div>
              <div className="flex-1 h-6 bg-gray-200 rounded overflow-hidden flex items-center relative" aria-label={`${percentage}% missed on ${c.id}`}>
                <div 
                  className={`h-full ${percentage > 50 ? 'bg-red-400' : percentage > 20 ? 'bg-yellow-400' : 'bg-green-400'}`}
                  style={{ width: `${percentage}%` }}
                />
                <span className="absolute left-2 text-xs font-bold text-gray-800 drop-shadow-sm">{percentage}% Missed ({c.missed}/{c.total})</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
