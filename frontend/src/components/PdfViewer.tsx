'use client';

import { useState } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

export function PdfViewer({ url, onDownload }: { url: string, onDownload: () => void }) {
  const [numPages, setNumPages] = useState<number>();
  const [pageNumber, setPageNumber] = useState<number>(1);
  const [scale, setScale] = useState<number>(1.0);

  function onDocumentLoadSuccess({ numPages }: { numPages: number }): void {
    setNumPages(numPages);
  }

  return (
    <div className="flex flex-col items-center bg-gray-100 p-4 rounded border mt-4">
      <div className="flex justify-between items-center w-full max-w-2xl mb-4 bg-white p-2 rounded shadow-sm border">
        <div className="flex gap-2">
          <button 
            disabled={pageNumber <= 1} 
            onClick={() => setPageNumber(p => p - 1)}
            className="px-2 py-1 bg-gray-200 rounded disabled:opacity-50 text-sm"
          >
            Prev
          </button>
          <span className="text-sm py-1">
            Page {pageNumber} of {numPages || '--'}
          </span>
          <button 
            disabled={numPages === undefined || pageNumber >= numPages} 
            onClick={() => setPageNumber(p => p + 1)}
            className="px-2 py-1 bg-gray-200 rounded disabled:opacity-50 text-sm"
          >
            Next
          </button>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setScale(s => Math.max(0.5, s - 0.25))} className="px-2 py-1 bg-gray-200 rounded text-sm">Zoom Out</button>
          <span className="text-sm py-1">{Math.round(scale * 100)}%</span>
          <button onClick={() => setScale(s => Math.min(3, s + 0.25))} className="px-2 py-1 bg-gray-200 rounded text-sm">Zoom In</button>
        </div>
        <button onClick={onDownload} className="px-3 py-1 bg-blue-600 text-white rounded text-sm">Download</button>
      </div>

      <div className="overflow-auto border shadow-lg max-h-[800px] max-w-full">
        <Document
          file={url}
          onLoadSuccess={onDocumentLoadSuccess}
          loading={<div className="p-10">Loading PDF...</div>}
          error={<div className="p-10 text-red-500">Failed to load PDF. It may not be available yet.</div>}
        >
          <Page pageNumber={pageNumber} scale={scale} renderTextLayer={false} renderAnnotationLayer={false} />
        </Document>
      </div>
    </div>
  );
}
