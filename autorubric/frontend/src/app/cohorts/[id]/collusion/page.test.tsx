import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { describe, it, expect, vi } from 'vitest';
import CollusionPage from './page';
import { useQuery } from '@tanstack/react-query';

// Mock the next/navigation and useQuery
vi.mock('next/navigation', () => ({
  useParams: () => ({ id: 'c1' }),
}));

vi.mock('@tanstack/react-query', () => ({
  useQuery: vi.fn(),
}));

describe('CollusionPage XSS Test', () => {
  it('renders malicious proposition text as literal string, not HTML', () => {
    // Provide a mocked report with malicious text
    (useQuery as any).mockReturnValue({
      data: {
        cohort_id: 'c1',
        doc_pairs: [
          {
            a: 'doc1',
            b: 'doc2',
            similarity: 0.99,
            matching_props: ['<script>alert(1)</script>::<script>alert(2)</script>']
          }
        ]
      },
      isLoading: false,
      error: null
    });

    render(<CollusionPage />);

    // Search for the literal text
    const maliciousText1 = screen.getByText('<script>alert(1)</script>');
    const maliciousText2 = screen.getByText('<script>alert(2)</script>');

    expect(maliciousText1).toBeInTheDocument();
    expect(maliciousText2).toBeInTheDocument();
    
    // Check that it wasn't rendered as a script tag
    // If it was rendered as HTML, getByText would not find the tag text since it's hidden inside the DOM node.
    // Additionally, we can check that there are no script elements added
    const scripts = document.querySelectorAll('script');
    expect(scripts.length).toBe(0);
  });
});
