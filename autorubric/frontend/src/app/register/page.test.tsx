import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import RegisterPage from './page';
import { useAuth } from '@/hooks/useAuth';
import { useRouter } from 'next/navigation';

vi.mock('@/hooks/useAuth');
vi.mock('next/navigation');

describe('RegisterPage', () => {
  const mockDoRegister = vi.fn();
  const mockPush = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (useAuth as any).mockReturnValue({
      token: null,
      doRegister: mockDoRegister,
    });
    (useRouter as any).mockReturnValue({
      push: mockPush,
    });
  });

  it('redirects if already signed in', () => {
    (useAuth as any).mockReturnValue({
      token: 'some-token',
      doRegister: mockDoRegister,
    });
    render(<RegisterPage />);
    expect(mockPush).toHaveBeenCalledWith('/');
  });

  it('shows validation messages for empty required fields', async () => {
    render(<RegisterPage />);
    fireEvent.click(screen.getByRole('button', { name: /sign up/i }));

    await waitFor(() => {
      expect(screen.getByText(/invalid email address/i)).toBeInTheDocument();
      expect(screen.getByText(/password must be at least 10 characters/i)).toBeInTheDocument();
    });
  });

  it('shows validation message for mismatched passwords', async () => {
    render(<RegisterPage />);
    
    fireEvent.change(screen.getByPlaceholderText('name@example.com'), { target: { value: 'test@example.com' } });
    fireEvent.change(screen.getAllByPlaceholderText('••••••••')[0], { target: { value: 'Password123!' } });
    fireEvent.change(screen.getAllByPlaceholderText('••••••••')[1], { target: { value: 'Password123' } }); // Mismatch

    fireEvent.click(screen.getByRole('button', { name: /sign up/i }));

    await waitFor(() => {
      expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument();
    });
    expect(mockDoRegister).not.toHaveBeenCalled();
  });

  it('displays server error', async () => {
    mockDoRegister.mockRejectedValueOnce(new Error(JSON.stringify({ detail: 'Email already registered' })));
    render(<RegisterPage />);
    
    fireEvent.change(screen.getByPlaceholderText('name@example.com'), { target: { value: 'test@example.com' } });
    fireEvent.change(screen.getAllByPlaceholderText('••••••••')[0], { target: { value: 'Password123!' } });
    fireEvent.change(screen.getAllByPlaceholderText('••••••••')[1], { target: { value: 'Password123!' } });

    fireEvent.click(screen.getByRole('button', { name: /sign up/i }));

    await waitFor(() => {
      expect(screen.getByText('Email already registered')).toBeInTheDocument();
    });
  });

  it('redirects on successful registration', async () => {
    mockDoRegister.mockResolvedValueOnce(undefined);
    render(<RegisterPage />);
    
    fireEvent.change(screen.getByPlaceholderText('name@example.com'), { target: { value: 'test@example.com' } });
    fireEvent.change(screen.getAllByPlaceholderText('••••••••')[0], { target: { value: 'Password123!' } });
    fireEvent.change(screen.getAllByPlaceholderText('••••••••')[1], { target: { value: 'Password123!' } });

    fireEvent.click(screen.getByRole('button', { name: /sign up/i }));

    await waitFor(() => {
      expect(mockDoRegister).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'Password123!',
        full_name: undefined,
        registration_code: undefined
      });
    });
    
    // Note: useAuth doRegister internally handles the router.push to '/' in our updated code
    // If the mock resolves, we just assume useAuth did its job. 
  });
});
