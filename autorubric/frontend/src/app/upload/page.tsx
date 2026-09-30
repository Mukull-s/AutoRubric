'use client';

import { useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation } from '@tanstack/react-query';
import { getRubrics, submitSingle, submitBatch } from '@/lib/api';

const MAX_SIZE = 10 * 1024 * 1024; // 10MB

export default function UploadPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [files, setFiles] = useState<File[]>([]);
  const [rubricId, setRubricId] = useState('');
  const [cohortName, setCohortName] = useState('');
  const [error, setError] = useState<string | null>(null);

  const { data: rubrics, isLoading: isLoadingRubrics } = useQuery({ queryKey: ['rubrics'], queryFn: getRubrics });

  const singleMutation = useMutation({
    mutationFn: submitSingle,
    onSuccess: (data) => router.push(`/jobs/${data.job_id}`),
    onError: (err: any) => setError(err.message || 'Failed to submit')
  });

  const batchMutation = useMutation({
    mutationFn: submitBatch,
    onSuccess: (data) => router.push(`/cohorts/${data.cohort_id}`),
    onError: (err: any) => setError(err.message || 'Failed to submit batch')
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setError(null);
    if (!e.target.files) return;
    const newFiles = Array.from(e.target.files);
    
    // Validations
    for (const f of newFiles) {
      if (f.type !== 'application/pdf') {
        setError('Only PDF files are allowed');
        return;
      }
      if (f.size > MAX_SIZE) {
        setError(`File ${f.name} is too large. Max size is 10MB.`);
        return;
      }
    }

    setFiles([...files, ...newFiles]);
  };

  const removeFile = (idx: number) => {
    const newF = [...files];
    newF.splice(idx, 1);
    setFiles(newF);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (files.length === 0) {
      setError('Please select at least one PDF file');
      return;
    }
    if (!rubricId) {
      setError('Please select a rubric');
      return;
    }

    if (files.length === 1) {
      const fd = new FormData();
      fd.append('file', files[0]);
      fd.append('rubric_id', rubricId);
      singleMutation.mutate(fd);
    } else {
      const fd = new FormData();
      files.forEach(f => fd.append('files', f));
      fd.append('rubric_id', rubricId);
      if (cohortName) fd.append('cohort_name', cohortName);
      batchMutation.mutate(fd);
    }
  };

  const isSubmitting = singleMutation.isPending || batchMutation.isPending;

  return (
    <div className="max-w-2xl mx-auto p-6 bg-white shadow rounded border">
      <h1 className="text-2xl font-bold mb-6">Upload Submissions</h1>
      {error && <div className="mb-4 p-3 bg-red-100 text-red-700 rounded">{error}</div>}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-sm font-medium mb-1">Select Rubric</label>
          <select 
            className="w-full border p-2 rounded bg-white" 
            value={rubricId} 
            onChange={e => setRubricId(e.target.value)}
            disabled={isLoadingRubrics}
          >
            <option value="">-- Select Rubric --</option>
            {rubrics?.map(r => (
              <option key={r.id} value={r.id}>{r.title}</option>
            ))}
          </select>
        </div>

        {files.length > 1 && (
          <div>
            <label className="block text-sm font-medium mb-1">Cohort Name (Optional)</label>
            <input 
              type="text" 
              className="w-full border p-2 rounded" 
              value={cohortName} 
              onChange={e => setCohortName(e.target.value)} 
              placeholder="e.g. Fall 2026 Biology"
            />
          </div>
        )}

        <div>
          <label className="block text-sm font-medium mb-1">PDF Files</label>
          <div 
            className="border-2 border-dashed p-8 text-center rounded bg-gray-50 cursor-pointer hover:bg-gray-100"
            onClick={() => fileInputRef.current?.click()}
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              const dt = new DataTransfer();
              Array.from(e.dataTransfer.files).forEach(f => dt.items.add(f));
              if (fileInputRef.current) {
                fileInputRef.current.files = dt.files;
                handleFileChange({ target: { files: dt.files } } as any);
              }
            }}
          >
            <p className="text-gray-500">Click to select or drag and drop PDFs here</p>
            <p className="text-xs text-gray-400 mt-1">Maximum 10MB per file</p>
          </div>
          <input 
            type="file" 
            multiple 
            accept="application/pdf" 
            className="hidden" 
            ref={fileInputRef}
            onChange={handleFileChange}
          />
        </div>

        {files.length > 0 && (
          <ul className="space-y-2">
            {files.map((f, i) => (
              <li key={i} className="flex justify-between items-center p-3 border rounded bg-gray-50">
                <span className="truncate flex-1 text-sm">{f.name}</span>
                <span className="text-xs text-gray-500 mr-4">{(f.size / 1024 / 1024).toFixed(2)} MB</span>
                <button type="button" onClick={() => removeFile(i)} className="text-red-500 text-sm hover:underline">Remove</button>
              </li>
            ))}
          </ul>
        )}

        <button type="submit" disabled={isSubmitting} className="w-full bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 disabled:opacity-50">
          {isSubmitting ? 'Uploading...' : 'Upload and Grade'}
        </button>
      </form>
    </div>
  );
}
