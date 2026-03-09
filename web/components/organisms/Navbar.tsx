'use client';
import Link from 'next/link';
import { useAppSelector, useAppDispatch } from '@/lib/redux/hooks';
import { logout } from '@/lib/redux/slices/authSlice';
import { useRouter } from 'next/navigation';
import { Button } from '../atoms/Button';

export const Navbar = () => {
  const { isAuthenticated, user } = useAppSelector((state) => state.auth);
  const dispatch = useAppDispatch();
  const router = useRouter();

  const handleLogout = () => {
    dispatch(logout());
    router.push('/login');
  };

  return (
    <nav className="flex items-center justify-between p-4 bg-white shadow-sm">
      <div className="flex items-center gap-6">
        <Link href="/dashboard" className="text-xl font-bold text-blue-600">
          Market Manager
        </Link>
        {isAuthenticated && (
          <div className="flex gap-4">
            <Link href="/dashboard" className="hover:text-blue-600">Dashboard</Link>
            <Link href="/stock" className="hover:text-blue-600">Stock</Link>
            <Link href="/settings" className="hover:text-blue-600">Settings</Link>
          </div>
        )}
      </div>
      <div className="flex items-center gap-4">
        {isAuthenticated ? (
          <>
            <span className="text-sm text-gray-600">
              {user?.full_name} ({user?.role})
            </span>
            <Button variant="outline" size="sm" onClick={handleLogout}>
              Logout
            </Button>
          </>
        ) : (
          <Link href="/login">
            <Button size="sm">Login</Button>
          </Link>
        )}
      </div>
    </nav>
  );
};
