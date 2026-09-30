'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useMutation } from '@tanstack/react-query';
import { createRubric } from '@/lib/api';
import { Criterion } from '@/lib/api/schemas';
import { Plus, Trash2 } from 'lucide-react';

export default function NewRubricPage() {
  const router = useRouter();
  const [title, setTitle] = useState('');
  const [criteria, setCriteria] = useState<Criterion[]>([]);
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: createRubric,
    onSuccess: () => {
      router.push('/');
    },
    onError: (err: Error) => {
      setError(err.message || 'Failed to create rubric');
    }
  });

  const hasCycle = (crit: Criterion[]) => {
    const adj = new Map<string, string[]>();
    crit.forEach(c => adj.set(c.id, c.depends_on || []));
    
    const visited = new Set<string>();
    const recStack = new Set<string>();

    const dfs = (node: string): boolean => {
      if (!visited.has(node)) {
        visited.add(node);
        recStack.add(node);
        
        for (const neighbor of adj.get(node) || []) {
          if (!visited.has(neighbor) && dfs(neighbor)) return true;
          else if (recStack.has(neighbor)) return true;
        }
      }
      recStack.delete(node);
      return false;
    };

    for (const node of adj.keys()) {
      if (dfs(node)) return true;
    }
    return false;
  };

  const validate = () => {
    setError(null);
    if (!title) return 'Title is required';
    if (criteria.length === 0) return 'At least one criterion is required';
    
    const ids = new Set<string>();
    for (const c of criteria) {
      if (!c.id) return 'Criterion ID cannot be empty';
      if (ids.has(c.id)) return `Duplicate ID: ${c.id}`;
      ids.add(c.id);
      if (c.weight <= 0) return `Weight must be positive for ${c.id}`;
    }

    for (const c of criteria) {
      for (const dep of (c.depends_on || [])) {
        if (!ids.has(dep)) return `Dependency ${dep} for ${c.id} does not exist`;
      }
    }

    if (hasCycle(criteria)) {
      return 'Cycle detected in dependencies';
    }

    return null;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const valError = validate();
    if (valError) {
      setError(valError);
      return;
    }
    mutation.mutate({ title, criteria });
  };

  const addCriterion = () => {
    setCriteria([...criteria, { id: '', description: '', weight: 1, depends_on: [] }]);
  };

  const removeCriterion = (index: number) => {
    const newC = [...criteria];
    newC.splice(index, 1);
    setCriteria(newC);
  };

  const updateCriterion = (index: number, field: keyof Criterion, value: Criterion[keyof Criterion]) => {
    const newC = [...criteria];
    newC[index] = { ...newC[index], [field]: value };
    setCriteria(newC);
  };

  return (
    <div className="max-w-3xl mx-auto p-6 bg-white shadow rounded border">
      <h1 className="text-2xl font-bold mb-6">Create New Rubric</h1>
      {error && <div className="mb-4 p-3 bg-red-100 text-red-700 rounded">{error}</div>}
      
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-sm font-medium mb-1">Title</label>
          <input 
            type="text" 
            className="w-full border p-2 rounded" 
            value={title} 
            onChange={e => setTitle(e.target.value)} 
          />
        </div>

        <div>
          <div className="flex justify-between items-center mb-2">
            <label className="block text-sm font-medium">Criteria</label>
            <button type="button" onClick={addCriterion} className="flex items-center text-sm text-blue-600 hover:underline">
              <Plus size={16} className="mr-1" /> Add
            </button>
          </div>
          
          <div className="space-y-4">
            {criteria.map((c, i) => (
              <div key={i} className="border p-4 rounded bg-gray-50 flex flex-col gap-3 relative">
                <button type="button" onClick={() => removeCriterion(i)} className="absolute top-4 right-4 text-gray-500 hover:text-red-600">
                  <Trash2 size={18} />
                </button>
                <div className="grid grid-cols-2 gap-4 mr-8">
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">ID</label>
                    <input type="text" className="w-full border p-1 rounded" value={c.id} onChange={e => updateCriterion(i, 'id', e.target.value)} />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">Weight</label>
                    <input type="number" step="0.1" className="w-full border p-1 rounded" value={c.weight} onChange={e => updateCriterion(i, 'weight', parseFloat(e.target.value))} />
                  </div>
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Description</label>
                  <textarea className="w-full border p-1 rounded h-16" value={c.description} onChange={e => updateCriterion(i, 'description', e.target.value)}></textarea>
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Depends On (comma separated IDs)</label>
                  <input type="text" className="w-full border p-1 rounded" value={c.depends_on.join(', ')} onChange={e => updateCriterion(i, 'depends_on', e.target.value.split(',').map(s => s.trim()).filter(Boolean))} />
                </div>
              </div>
            ))}
          </div>
        </div>

        <button type="submit" disabled={mutation.isPending} className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 disabled:opacity-50">
          {mutation.isPending ? 'Saving...' : 'Save Rubric'}
        </button>
      </form>
    </div>
  );
}
