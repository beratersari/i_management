'use client';
import { useState } from 'react';
import { useCreateCategoryMutation, useUpdateCategoryMutation, useDeleteCategoryMutation } from '@/lib/redux/features/categoryApi';
import { Button } from '../atoms/Button';
import { Input } from '../atoms/Input';

interface CategoryFormModalProps {
  category?: any;
  onClose: () => void;
}

interface ValidationError {
  type: string;
  loc: string[];
  msg: string;
}

export const CategoryFormModal = ({ category, onClose }: CategoryFormModalProps) => {
  const isEdit = !!category;
  const [createCategory, { isLoading: isCreating }] = useCreateCategoryMutation();
  const [updateCategory, { isLoading: isUpdating }] = useUpdateCategoryMutation();
  const [deleteCategory, { isLoading: isDeleting }] = useDeleteCategoryMutation();
  
  const [formData, setFormData] = useState({
    name: category?.name || '',
    description: category?.description || '',
    sort_order: String(category?.sort_order || '0'),
  });
  const [errors, setErrors] = useState<string[]>([]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors([]);

    const payload = {
      name: formData.name,
      description: formData.description || null,
      sort_order: parseInt(formData.sort_order) || 0,
    };

    try {
      if (isEdit) {
        await updateCategory({ id: category.id, ...payload }).unwrap();
      } else {
        await createCategory(payload).unwrap();
      }
      onClose();
    } catch (err: any) {
      if (err.data?.detail && Array.isArray(err.data.detail)) {
        setErrors(err.data.detail.map((e: ValidationError) => `${e.loc.join('.')}: ${e.msg}`));
      } else if (err.data?.detail && typeof err.data.detail === 'string') {
        setErrors([err.data.detail]);
      } else {
        setErrors([isEdit ? 'Failed to update category' : 'Failed to create category']);
      }
    }
  };

  const handleDelete = async () => {
    if (!isEdit) return;
    if (!confirm(`Are you sure you want to delete "${category.name}"? This action cannot be undone.`)) {
      return;
    }
    
    try {
      await deleteCategory(category.id).unwrap();
      onClose();
    } catch (err: any) {
      if (err.data?.detail && typeof err.data.detail === 'string') {
        setErrors([err.data.detail]);
      } else {
        setErrors(['Failed to delete category']);
      }
    }
  };

  const isLoading = isCreating || isUpdating || isDeleting;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white p-6 rounded-lg shadow-xl w-full max-w-md">
        <h3 className="text-xl font-semibold mb-4">
          {isEdit ? 'Edit Category' : 'Create New Category'}
        </h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          {errors.length > 0 && (
            <div className="p-2 text-sm text-red-600 bg-red-100 rounded">
              {errors.map((error, index) => (
                <div key={index}>{error}</div>
              ))}
            </div>
          )}
          
          <Input
            label="Name"
            name="name"
            value={formData.name}
            onChange={handleChange}
            placeholder="Category name"
          />
          
          <Input
            label="Description"
            name="description"
            value={formData.description}
            onChange={handleChange}
            placeholder="Category description"
          />
          
          <Input
            type="number"
            label="Sort Order"
            name="sort_order"
            value={formData.sort_order}
            onChange={handleChange}
          />
          
          <div className="flex justify-between gap-2 mt-6">
            {isEdit && (
              <Button variant="danger" onClick={handleDelete} type="button" disabled={isLoading}>
                Delete
              </Button>
            )}
            <div className="flex gap-2 ml-auto">
              <Button variant="outline" onClick={onClose} type="button">
                Cancel
              </Button>
              <Button type="submit" disabled={isLoading}>
                {isLoading ? 'Saving...' : (isEdit ? 'Update' : 'Create')}
              </Button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};
