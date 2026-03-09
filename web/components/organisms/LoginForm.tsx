'use client';
import { useState } from 'react';
import { FormField } from '../molecules/FormField';
import { Button } from '../atoms/Button';
import { useLoginMutation, useGetMeQuery } from '@/lib/redux/features/authApi';
import { useAppDispatch } from '@/lib/redux/hooks';
import { setCredentials } from '@/lib/redux/slices/authSlice';
import { useRouter } from 'next/navigation';

export const LoginForm = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [login, { isLoading }] = useLoginMutation();
  const dispatch = useAppDispatch();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      const result = await login({ username, password }).unwrap();
      // After login, we need to fetch user info. The login result only has tokens.
      // But we can set the token first.
      dispatch(setCredentials({ user: null, access_token: result.access_token }));
      
      // The token is now in state, so the next call to getMe will use it.
      // However, we might want to handle this more robustly.
      // For now, let's redirect to dashboard which will handle user fetching.
      router.push('/dashboard');
    } catch (err: any) {
      setError(err.data?.detail || 'Login failed');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 w-full max-w-md p-6 bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-bold text-center">Login</h2>
      {error && <div className="p-2 text-sm text-red-600 bg-red-100 rounded">{error}</div>}
      <FormField
        type="text"
        label="Username or Email"
        name="username"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        placeholder="Enter your username or email"
      />
      <FormField
        type="password"
        label="Password"
        name="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Enter your password"
      />
      <Button type="submit" className="w-full" disabled={isLoading}>
        {isLoading ? 'Logging in...' : 'Login'}
      </Button>
    </form>
  );
};
