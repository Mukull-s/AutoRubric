'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { login } from '@/lib/api';

let memoryToken: string | null = null;

export function useAuth() {
  const [token, setToken] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    if (!memoryToken) {
      memoryToken = sessionStorage.getItem('token');
    }
    setToken(memoryToken);
  }, []);

  const doLogin = async (data: any) => {
    try {
      const res = await login(data);
      memoryToken = res.access_token;
      sessionStorage.setItem('token', res.access_token);
      localStorage.setItem('token', res.access_token); // required for API client, though we should really pass it or use memory token. Let's sync memoryToken to localStorage for simplicity with the API client.
      setToken(res.access_token);
      router.push('/');
    } catch (e) {
      console.error('Login failed', e);
      throw e;
    }
  };

  const doLogout = () => {
    memoryToken = null;
    sessionStorage.removeItem('token');
    localStorage.removeItem('token');
    setToken(null);
    router.push('/login');
  };

  return { token, doLogin, doLogout };
}
