'use client';

import { useMemo, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { getCollusion } from '@/lib/api';
import { Job } from '@/lib/api/schemas';

export function CohortHeatmap({ jobs }: { jobs: Job[] }) {
  const router = useRouter();
  const [hoveredCell, setHoveredCell] = useState<string | null>(null);

  const doneJobs = jobs.filter(j => j.status === 'DONE' && j.doc_id);
  const docIds = doneJobs.map(j => j.doc_id!);
  const cohortId = jobs.length > 0 ? (jobs[0] as unknown as { cohort_id: string }).cohort_id : null;

  const { data: report } = useQuery({
    queryKey: ['collusion', cohortId],
    queryFn: () => getCollusion(cohortId!),
    enabled: !!cohortId,
  }) as { data: { doc_pairs?: { a: string, b: string, similarity: number }[] } | undefined };

  const { matrix } = useMemo(() => {
    const mat: Record<string, Record<string, number>> = {};
    let max = 0;
    for (const d of docIds) {
      mat[d] = {};
      for (const d2 of docIds) {
        mat[d][d2] = d === d2 ? 1 : 0;
      }
    }

    if (report?.doc_pairs) {
      for (const pair of report.doc_pairs) {
        if (mat[pair.a] && mat[pair.b]) {
          mat[pair.a][pair.b] = pair.similarity;
          mat[pair.b][pair.a] = pair.similarity;
          if (pair.similarity > max) max = pair.similarity;
        }
      }
    }
    return { matrix: mat, maxSim: max || 1 };
  }, [docIds, report]);

  if (docIds.length < 2) return null;

  return (
    <div className="mb-8 overflow-x-auto" aria-label="Collusion Heatmap">
      <h2 className="text-xl font-bold mb-4">Collusion Heatmap</h2>
      <p className="text-sm text-gray-600 mb-4">Documents similarity matrix. Click a flagged cell to view the pair.</p>
      
      <div className="inline-block relative">
        <div className="flex">
          <div className="w-20" /> {/* Top-left corner */}
          {docIds.map(d => (
            <div key={d} className="w-12 h-20 writing-vertical-lr transform rotate-180 text-xs truncate flex items-center justify-center border-b" title={d}>
              {d.slice(0, 6)}...
            </div>
          ))}
        </div>
        
        {docIds.map(rowDoc => (
          <div key={rowDoc} className="flex">
            <div className="w-20 text-xs truncate pr-2 flex items-center justify-end border-r" title={rowDoc}>
              {rowDoc.slice(0, 6)}...
            </div>
            {docIds.map(colDoc => {
              const sim = matrix[rowDoc][colDoc];
              const isFlagged = report?.doc_pairs?.some((p: { a: string, b: string }) => (p.a === rowDoc && p.b === colDoc) || (p.b === rowDoc && p.a === colDoc));
              const percentage = Math.round(sim * 100);
              
              // Color scale: white (0%) to red (100%)
              const opacity = sim;
              const color = `rgba(220, 38, 38, ${opacity})`; // Tailwind red-600

              const content = (
                <div 
                  className={`w-12 h-12 border border-gray-100 relative group flex items-center justify-center cursor-pointer hover:border-gray-900 transition-colors ${isFlagged ? 'ring-2 ring-red-500' : ''}`}
                  style={{ backgroundColor: color }}
                  onMouseEnter={() => setHoveredCell(`${rowDoc}-${colDoc}`)}
                  onMouseLeave={() => setHoveredCell(null)}
                  title={`${rowDoc} & ${colDoc}: ${percentage}%`}
                >
                  {(hoveredCell === `${rowDoc}-${colDoc}` || sim > 0.5) && (
                    <span className={`text-[10px] font-bold ${sim > 0.5 ? 'text-white' : 'text-gray-800'}`}>
                      {percentage}%
                    </span>
                  )}
                </div>
              );

              if (isFlagged && rowDoc !== colDoc) {
                return (
                  <Link key={colDoc} href="#pair-details" onClick={(e) => {
                     e.preventDefault();
                     router.push(`/cohorts/${cohortId || 'unknown'}/collusion`);
                  }}>
                    {content}
                  </Link>
                );
              }
              return <div key={colDoc}>{content}</div>;
            })}
          </div>
        ))}
      </div>
    </div>
  );
}
