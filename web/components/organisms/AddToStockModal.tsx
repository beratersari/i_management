'use client';
import { useState, useMemo } from 'react';
import { useGetItemsQuery } from '@/lib/redux/features/itemApi';
import { useGetStockQuery } from '@/lib/redux/features/stockApi';
import { useAddToStockMutation } from '@/lib/redux/features/stockApi';
import { Button } from '../atoms/Button';
import { Input } from '../atoms/Input';
import { Select } from '../atoms/Select';

interface AddToStockModalProps {
  onClose: () => void;
}

interface ValidationError {
  type: string;
  loc: string[];
  msg: string;
}

export const AddToStockModal = ({ onClose }: AddToStockModalProps) => {
  const { data: items, isLoading: itemsLoading } = useGetItemsQuery(undefined);
  const { data: stock } = useGetStockQuery();
  const [addToStock, { isLoading }] = useAddToStockMutation();
  
  const [formData, setFormData] = useState({
    item_id: '',
    quantity: '1',
  });
  const [errors, setErrors] = useState<string[]>([]);

  // Filter items that are NOT already in stock
  const itemsNotInStock = useMemo(() => {
    if (!items || !stock) return [];
    const stockItemIds = new Set(stock.map((s: any) => s.item_id));
    return items.filter((item: any) => !stockItemIds.has(item.id));
  }, [items, stock]);

  const itemOptions = [
    { label: 'Select an item', value: '' },
    ...(itemsNotInStock?.map((item: any) => ({ label: `${item.name} (ID: ${item.id})`, value: String(item.id) })) || []),
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors([]);

    if (!formData.item_id) {
      setErrors(['Please select an item']);
      return;
    }

    try {
      await addToStock({
        item_id: parseInt(formData.item_id),
        quantity: parseFloat(formData.quantity) || 0,
      }).unwrap();
      onClose();
    } catch (err: any) {
      if (err.data?.detail && Array.isArray(err.data.detail)) {
        setErrors(err.data.detail.map((e: ValidationError) => `${e.loc.join('.')}: ${e.msg}`));
      } else if (err.data?.detail && typeof err.data.detail === 'string') {
        setErrors([err.data.detail]);
      } else {
        setErrors(['Failed to add item to stock']);
      }
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white p-6 rounded-lg shadow-xl w-full max-w-md">
        <h3 className="text-xl font-semibold mb-4">Add Item to Stock</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          {errors.length > 0 && (
            <div className="p-2 text-sm text-red-600 bg-red-100 rounded">
              {errors.map((error, index) => (
                <div key={index}>{error}</div>
              ))}
            </div>
          )}
          
          {itemsLoading ? (
            <div>Loading items...</div>
          ) : (
            <Select
              label="Item"
              name="item_id"
              value={formData.item_id}
              onChange={(e) => setFormData({ ...formData, item_id: e.target.value })}
              options={itemOptions}
            />
          )}
          
          <Input
            type="number"
            step="0.001"
            label="Quantity"
            value={formData.quantity}
            onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
          />
          
          <div className="flex justify-end gap-2 mt-6">
            <Button variant="outline" onClick={onClose} type="button">
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? 'Adding...' : 'Add to Stock'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};