'use client';
import { DashboardTemplate } from '@/components/templates/DashboardTemplate';
import { useAppSelector } from '@/lib/redux/hooks';
import { RegisterUserForm } from '@/components/organisms/RegisterUserForm';
import { UserList } from '@/components/organisms/UserList';

export default function SettingsPage() {
  const { user } = useAppSelector((state) => state.auth);

  if (!user) return null;

  const canRegister = user.role === 'admin' || user.role === 'market_owner';

  return (
    <DashboardTemplate>
      <div className="space-y-8">
        <section className="bg-white p-6 rounded-lg shadow-sm">
          <h2 className="text-2xl font-bold mb-4">My Information</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-500">Username</p>
              <p className="font-medium">{user.username}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Email</p>
              <p className="font-medium">{user.email}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Full Name</p>
              <p className="font-medium">{user.full_name}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Role</p>
              <p className="font-medium capitalize">{user.role}</p>
            </div>
          </div>
        </section>

        {canRegister && (
          <section className="bg-white p-6 rounded-lg shadow-sm">
            <h2 className="text-2xl font-bold mb-4">User Management</h2>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              <div className="lg:col-span-1">
                <RegisterUserForm />
              </div>
              <div className="lg:col-span-2">
                <UserList />
              </div>
            </div>
          </section>
        )}
      </div>
    </DashboardTemplate>
  );
}
