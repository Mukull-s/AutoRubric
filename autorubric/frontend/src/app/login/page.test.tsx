import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import LoginPage from './page';
import { QueryProvider } from '@/components/QueryProvider';

const mockPush = vi.fn();
vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
  usePathname: () => '/login',
}));

describe('LoginPage', () => {
  it('allows user to login', async () => {
    render(
      <QueryProvider>
        <LoginPage />
      </QueryProvider>
    );

    fireEvent.change(screen.getByLabelText(/Username/i), { target: { value: 'user' } });
    fireEvent.change(screen.getByLabelText(/Password/i), { target: { value: 'pass' } });
    fireEvent.click(screen.getByRole('button', { name: /Sign In/i }));

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/');
    });
  });
});
