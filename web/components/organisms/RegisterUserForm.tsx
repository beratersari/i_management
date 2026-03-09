'use client';
import { useState } from 'react';
import { FormField } from '../molecules/FormField';
import { Button } from '../atoms/Button';
import { useRegisterUserMutation } from '@/lib/redux/features/userApi';
import { useAppSelector } from '@/lib/redux/hooks';

interface ValidationError {
  type: string;
  loc: string[];
  msg: string;
  input: any;
  ctx?: Record<string, any>;
}

function formatValidationErrors(errors: ValidationError[]): string {
  return errors.map(err => {
    const field = err.loc.join('.');
    return `${field}: ${err.msg}`;
  }).join('\n');
}

export const RegisterUserForm = ({ onSuccess }: { onSuccess?: () => void }) => {
  const { user } = useAppSelector((state) => state.auth);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    full_name: '',
    password: '',
    role: 'employee',
  });
  const [errors, setErrors] = useState<string[]>([]);
  const [register, { isLoading }] = useRegisterUserMutation();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors([]);
    try {
      await register(formData).unwrap();
      setFormData({
        username: '',
        email: '',
        full_name: '',
        password: '',
        role: 'employee',
      });
      if (onSuccess) onSuccess();
    } catch (err: any) {
      if (err.data?.detail && Array.isArray(err.data.detail)) {
        setErrors(err.data.detail.map((e: ValidationError) => `${e.loc.join('.')}: ${e.msg}`));
      } else if (err.data?.detail && typeof err.data.detail === 'string') {
        setErrors([err.data.detail]);
      } else {
        setErrors(['Registration failed']);
      }
    }
  };

  const roleOptions = [
    { label: 'Employee', value: 'employee' },
  ];

  if (user?.role === 'admin') {
    roleOptions.push(
      { label: 'Admin', value: 'admin' },
      { label: 'Market Owner', value: 'market_owner' }
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 w-full p-6 bg-white rounded-lg shadow-sm border">
      <h3 className="text-xl font-semibold">Register New User</h3>
      {errors.length > 0 && (
        <div className="p-2 text-sm text-red-600 bg-red-100 rounded">
          {errors.map((error, index) => (
            <div key={index}>{error}</div>
          ))}
        </div>
      )}
      <FormField
        type="text"
        label="Username"
        name="username"
        value={formData.username}
        onChange={handleChange}
        placeholder="Username"
      />
      <FormField
        type="email"
        label="Email"
        name="email"
        value={formData.email}
        onChange={handleChange}
        placeholder="email@example.com"
      />
      <FormField
        type="text"
        label="Full Name"
        name="full_name"
        value={formData.full_name}
        onChange={handleChange}
        placeholder="Full Name"
      />
      <FormField
        type="password"
        label="Password"
        name="password"
        value={formData.password}
        onChange={handleChange}
        placeholder="********"
      />
      <FormField
        type="select"
        label="Role"
        name="role"
        value={formData.role}
        onChange={handleChange}
        options={roleOptions}
      />
      <Button type="submit" className="w-full" disabled={isLoading}>
        {isLoading ? 'Registering...' : 'Register User'}
      </Button>
    </form>
  );
};
