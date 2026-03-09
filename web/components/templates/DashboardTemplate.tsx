'use client';
import { Navbar } from '../organisms/Navbar';
import { useGetMeQuery } from '@/lib/redux/features/authApi';
import { useAppDispatch, useAppSelector } from '@/lib/redux/hooks';
import { setCredentials, logout } from '@/lib/redux/slices/authSlice';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export const DashboardTemplate = ({ children }: { children: React.ReactNode }) => {
  const { token, isAuthenticated, user } = useAppSelector((state) => state.auth);
  const { data: userData, error, isLoading } = useGetMeQuery(undefined, {
    skip: !token,
  });
  const dispatch = useAppDispatch();
  const router = useRouter();

  useEffect(() => {
    if (!token && !isLoading) {
      router.push('/login');
    }
  }, [token, isLoading, router]);

  useEffect(() => {
    if (userData) {
      dispatch(setCredentials({ user: userData, access_token: token! }));
    } else if (error) {
      dispatch(logout());
      router.push('/login');
    }
  }, [userData, error, dispatch, token, router]);

  if (isLoading || (!user && token)) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <main className="p-8">
        {children}
      </main>
    </div>
  );
};
