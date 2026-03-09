'use client';
import { useState } from 'react';
import { FormField } from '../molecules/FormField';
import { Button } from '../atoms/Button';
import { useUpdateUserMutation } from '@/lib/redux/features/userApi';
import { useAppSelector } from '@/lib/redux/hooks';

interface EditUserModalProps {
  user: any;
  onClose: () => void;
}

interface ValidationError {
  type: string;
  loc: string[];
  msg: string;
  input: any;
  ctx?: Record<string, any>;
}

export const EditUserModal = ({ user: targetUser, onClose }: EditUserModalProps) => {
  const { user: currentUser } = useAppSelector((state) => state.auth);
  const [formData, setFormData] = useState({
    email: targetUser.email,
    full_name: targetUser.full_name,
    role: targetUser.role,
  });
  const [errors, setErrors] = useState<string[]>([]);
  const [update, { isLoading }] = useUpdateUserMutation();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors([]);
    try {
      await update({ id: targetUser.id, ...formData }).unwrap();
      onClose();
    } catch (err: any) {
      if (err.data?.detail && Array.isArray(err.data.detail)) {
        setErrors(err.data.detail.map((e: ValidationError) => `${e.loc.join('.')}: ${e.msg}`));
      } else if (err.data?.detail && typeof err.data.detail === 'string') {
        setErrors([err.data.detail]);
      } else {
        setErrors(['Update failed']);
      }
    }
  };

  const roleOptions = [
    { label: 'Employee', value: 'employee' },
    { label: 'Market Owner', value: 'market_owner' },
    { label: 'Admin', value: 'admin' },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white p-6 rounded-lg shadow-xl w-full max-w-md">
        <h3 className="text-xl font-semibold mb-4">Edit User: {targetUser.username}</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          {errors.length > 0 && (
            <div className="p-2 text-sm text-red-600 bg-red-100 rounded">
              {errors.map((error, index) => (
                <div key={index}>{error}</div>
              ))}
            </div>
          )}
          <FormField
            type="email"
            label="Email"
            name="email"
            value={formData.email}
            onChange={handleChange}
          />
          <FormField
            type="text"
            label="Full Name"
            name="full_name"
            value={formData.full_name}
            onChange={handleChange}
          />
          {currentUser?.role === 'admin' && (
            <FormField
              type="select"
              label="Role"
              name="role"
              value={formData.role}
              onChange={handleChange}
              options={roleOptions}
            />
          )}
          <div className="flex justify-end gap-2 mt-6">
            <Button variant="outline" onClick={onClose} type="button">
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? 'Saving...' : 'Save Changes'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};
