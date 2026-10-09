'use client';

import { useParams, useRouter } from 'next/navigation';
import { useQuery, useMutation } from '@tanstack/react-query';
import { getRubric, deleteRubric } from '@/lib/api';
import Link from 'next/link';
import { useMemo, useState } from 'react';
import { Trash2 } from 'lucide-react';

export default function RubricDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const [isDeleting, setIsDeleting] = useState(false);

  const { data: rubric, isLoading, error } = useQuery({
    queryKey: ['rubric', id],
    queryFn: () => getRubric(id),
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteRubric(id),
    onSuccess: () => {
      router.push('/');
    },
    onError: (err: Error) => {
      alert(`Failed to delete rubric: ${err.message}`);
      setIsDeleting(false);
    }
  });

  const handleDelete = () => {
    if (confirm(`Are you sure you want to delete the rubric "${rubric?.title}"?`)) {
      setIsDeleting(true);
      deleteMutation.mutate();
    }
  };

  const svgGraph = useMemo(() => {
    if (!rubric || !rubric.criteria) return null;
    const nodes = rubric.criteria.map(c => c.id);
    const edges = rubric.criteria.flatMap(c => (c.depends_on || []).map(dep => ({ from: dep, to: c.id })));
    
    // Very simple layout: nodes in a circle
    const cx = 150, cy = 150, r = 100;
    const positions = new Map<string, { x: number, y: number }>();
    nodes.forEach((n, i) => {
      const angle = (i / nodes.length) * 2 * Math.PI - Math.PI / 2;
      positions.set(n, { x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle) });
    });

    return (
      <svg width="300" height="300" className="border rounded bg-gray-50">
        {/* Edges */}
        {edges.map((e, i) => {
          const from = positions.get(e.from);
          const to = positions.get(e.to);
          if (!from || !to) return null;
          return (
            <line key={`e-${i}`} x1={from.x} y1={from.y} x2={to.x} y2={to.y} stroke="#9ca3af" strokeWidth="2" markerEnd="url(#arrow)" />
          );
        })}
        {/* Nodes */}
        {nodes.map(n => {
          const pos = positions.get(n);
          if (!pos) return null;
          return (
            <g key={`n-${n}`}>
              <circle cx={pos.x} cy={pos.y} r="20" fill="#3b82f6" />
              <text x={pos.x} y={pos.y} textAnchor="middle" dy=".3em" fill="white" fontSize="12" fontWeight="bold">{n}</text>
            </g>
          );
        })}
        <defs>
          <marker id="arrow" viewBox="0 0 10 10" refX="25" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#9ca3af" />
          </marker>
        </defs>
      </svg>
    );
  }, [rubric]);

  if (isLoading) return <div className="p-6">Loading...</div>;
  if (error) return <div className="p-6 text-red-600">Failed to load rubric</div>;
  if (!rubric) return <div className="p-6">Rubric not found</div>;

  return (
    <div className="max-w-4xl mx-auto p-6 bg-white shadow rounded border">
      <Link href="/" className="text-blue-600 hover:underline mb-4 inline-block">&larr; Back to Dashboard</Link>
      <div className="flex items-center justify-between mb-6 pb-4 border-b">
        <h1 className="text-3xl font-bold">{rubric.title}</h1>
        <button
          onClick={handleDelete}
          disabled={isDeleting}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium text-rose-600 bg-rose-50 hover:bg-rose-100 transition-colors disabled:opacity-50"
        >
          <Trash2 className="w-3.5 h-3.5" />
          <span>{isDeleting ? "Deleting..." : "Delete Rubric"}</span>
        </button>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div>
          <h2 className="text-xl font-semibold mb-4">Criteria</h2>
          <div className="space-y-4">
            {rubric.criteria?.map(c => (
              <div key={c.id} className="border p-4 rounded bg-gray-50">
                <div className="flex justify-between items-start mb-2">
                  <span className="font-bold text-lg">{c.id}</span>
                  <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">Weight: {c.weight}</span>
                </div>
                <p className="text-sm text-gray-700 mb-2">{c.description}</p>
                {c.depends_on && c.depends_on.length > 0 && (
                  <p className="text-xs text-gray-500">Depends on: {c.depends_on.join(', ')}</p>
                )}
              </div>
            ))}
          </div>
        </div>
        <div>
          <h2 className="text-xl font-semibold mb-4">Dependency Graph</h2>
          {svgGraph}
        </div>
      </div>
    </div>
  );
}
