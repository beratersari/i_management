'use client';
import { useState, useEffect } from 'react';
import { useCreateItemMutation, useUpdateItemMutation } from '@/lib/redux/features/itemApi';
import { useGetCategoriesQuery } from '@/lib/redux/features/categoryApi';
import { Button } from '../atoms/Button';
import { Input } from '../atoms/Input';
import { Select } from '../atoms/Select';

interface ItemFormModalProps {
  item?: any;
  onClose: () => void;
}

interface ValidationError {
  type: string;
  loc: string[];
  msg: string;
}

export const ItemFormModal = ({ item, onClose }: ItemFormModalProps) => {
  const isEdit = !!item;
  const [createItem, { isLoading: isCreating }] = useCreateItemMutation();
  const [updateItem, { isLoading: isUpdating }] = useUpdateItemMutation();
  const { data: categories } = useGetCategoriesQuery();
  
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    category_id: '',
    sku: '',
    barcode: '',
    image_url: '',
    unit_price: '0',
    unit_type: 'piece',
    tax_rate: '0',
    discount_rate: '0',
  });
  const [errors, setErrors] = useState<string[]>([]);

  useEffect(() => {
    if (item) {
      setFormData({
        name: item.name || '',
        description: item.description || '',
        category_id: String(item.category_id || ''),
        sku: item.sku || '',
        barcode: item.barcode || '',
        image_url: item.image_url || '',
        unit_price: String(item.unit_price || '0'),
        unit_type: item.unit_type || 'piece',
        tax_rate: String(item.tax_rate || '0'),
        discount_rate: String(item.discount_rate || '0'),
      });
    }
  }, [item]);

  const categoryOptions = [
    { label: 'Select a category', value: '' },
    ...(categories?.map((cat: any) => ({ label: cat.name, value: String(cat.id) })) || []),
  ];

  const unitTypeOptions = [
    { label: 'Piece', value: 'piece' },
    { label: 'Kilogram', value: 'kg' },
    { label: 'Gram', value: 'g' },
    { label: 'Liter', value: 'L' },
    { label: 'Milliliter', value: 'mL' },
  ];

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors([]);

    if (!formData.category_id) {
      setErrors(['Please select a category']);
      return;
    }

    const payload = {
      name: formData.name,
      description: formData.description || null,
      category_id: parseInt(formData.category_id),
      sku: formData.sku || null,
      barcode: formData.barcode || null,
      image_url: formData.image_url || null,
      unit_price: parseFloat(formData.unit_price) || 0,
      unit_type: formData.unit_type,
      tax_rate: parseFloat(formData.tax_rate) || 0,
      discount_rate: parseFloat(formData.discount_rate) || 0,
    };

    try {
      if (isEdit) {
        await updateItem({ id: item.item_id || item.id, ...payload }).unwrap();
      } else {
        await createItem(payload).unwrap();
      }
      onClose();
    } catch (err: any) {
      if (err.data?.detail && Array.isArray(err.data.detail)) {
        setErrors(err.data.detail.map((e: ValidationError) => `${e.loc.join('.')}: ${e.msg}`));
      } else if (err.data?.detail && typeof err.data.detail === 'string') {
        setErrors([err.data.detail]);
      } else {
        setErrors([isEdit ? 'Failed to update item' : 'Failed to create item']);
      }
    }
  };

  const isLoading = isCreating || isUpdating;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white p-6 rounded-lg shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <h3 className="text-xl font-semibold mb-4">{isEdit ? 'Edit Item' : 'Create New Item'}</h3>
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
            placeholder="Item name"
          />
          
          <Input
            label="Description"
            name="description"
            value={formData.description}
            onChange={handleChange}
            placeholder="Item description"
          />
          
          <Select
            label="Category"
            name="category_id"
            value={formData.category_id}
            onChange={handleChange}
            options={categoryOptions}
          />
          
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="SKU"
              name="sku"
              value={formData.sku}
              onChange={handleChange}
              placeholder="SKU"
            />
            <Input
              label="Barcode"
              name="barcode"
              value={formData.barcode}
              onChange={handleChange}
              placeholder="Barcode"
            />
          </div>
          
          <Input
            label="Image URL"
            name="image_url"
            value={formData.image_url}
            onChange={handleChange}
            placeholder="https://..."
          />
          
          <div className="grid grid-cols-2 gap-4">
            <Input
              type="number"
              step="0.01"
              label="Unit Price"
              name="unit_price"
              value={formData.unit_price}
              onChange={handleChange}
            />
            <Select
              label="Unit Type"
              name="unit_type"
              value={formData.unit_type}
              onChange={handleChange}
              options={unitTypeOptions}
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <Input
              type="number"
              step="0.01"
              label="Tax Rate (%)"
              name="tax_rate"
              value={formData.tax_rate}
              onChange={handleChange}
            />
            <Input
              type="number"
              step="0.01"
              label="Discount Rate (%)"
              name="discount_rate"
              value={formData.discount_rate}
              onChange={handleChange}
            />
          </div>
          
          <div className="flex justify-end gap-2 mt-6">
            <Button variant="outline" onClick={onClose} type="button">
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? 'Saving...' : (isEdit ? 'Update Item' : 'Create Item')}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};
