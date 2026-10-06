'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { login, register, getMe } from '@/lib/api';

let memoryToken: string | null = null;
let cachedUser: any = null;

export function useAuth() {
  const [token, setToken] = useState<string | null>(() => {
    if (typeof window !== 'undefined') {
      return sessionStorage.getItem('token') || localStorage.getItem('token') || memoryToken;
    }
    return null;
  });
  const [user, setUser] = useState<any>(cachedUser);
  const router = useRouter();

  useEffect(() => {
    if (!memoryToken && typeof window !== 'undefined') {
      memoryToken = sessionStorage.getItem('token') || localStorage.getItem('token');
    }
    if (memoryToken) {
      setToken(memoryToken);
    }
  }, []);

  const fetchUser = async () => {
    try {
      const u = await getMe();
      cachedUser = u;
      setUser(u);
    } catch (e) {
      console.error('Failed to fetch user', e);
      doLogout();
    }
  };

  useEffect(() => {
    if (token && !user) {
      fetchUser();
    }
  }, [token, user]);

  const doLogin = async (data: Record<string, unknown>) => {
    try {
      const res = await login(data);
      memoryToken = res.access_token;
      sessionStorage.setItem('token', res.access_token);
      localStorage.setItem('token', res.access_token);
      setToken(res.access_token);
      cachedUser = res.user;
      setUser(res.user);
      router.push('/');
    } catch (e) {
      console.error('Login failed', e);
      throw e;
    }
  };

  const doRegister = async (data: Record<string, unknown>) => {
    try {
      const res = await register(data);
      memoryToken = res.access_token;
      sessionStorage.setItem('token', res.access_token);
      localStorage.setItem('token', res.access_token);
      setToken(res.access_token);
      cachedUser = res.user;
      setUser(res.user);
      router.push('/');
    } catch (e) {
      console.error('Registration failed', e);
      throw e;
    }
  };

  const doLogout = () => {
    memoryToken = null;
    cachedUser = null;
    if (typeof window !== 'undefined') {
      sessionStorage.removeItem('token');
      localStorage.removeItem('token');
    }
    setToken(null);
    setUser(null);
    router.push('/login');
  };

  return { token, user, doLogin, doRegister, doLogout };
}
