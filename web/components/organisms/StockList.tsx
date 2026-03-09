'use client';
import { useState } from 'react';
import { useGetStockByCategoryQuery, useUpdateStockMutation, useRemoveFromStockMutation } from '@/lib/redux/features/stockApi';
import { Button } from '../atoms/Button';
import { Input } from '../atoms/Input';

interface StockListProps {
  onEditItem: (item: any) => void;
}

export const StockList = ({ onEditItem }: StockListProps) => {
  const { data: stockByCategory, isLoading, error, refetch } = useGetStockByCategoryQuery();
  const [updateStock] = useUpdateStockMutation();
  const [removeFromStock] = useRemoveFromStockMutation();
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editQuantity, setEditQuantity] = useState<string>('');
  const [updateError, setUpdateError] = useState<string | null>(null);
  const [expandedCategories, setExpandedCategories] = useState<Set<number>>(new Set());

  const toggleCategory = (categoryId: number) => {
    const newExpanded = new Set(expandedCategories);
    if (newExpanded.has(categoryId)) {
      newExpanded.delete(categoryId);
    } else {
      newExpanded.add(categoryId);
    }
    setExpandedCategories(newExpanded);
  };

  const handleStartEdit = (item: any) => {
    setEditingId(item.item_id);
    setEditQuantity(String(item.quantity));
    setUpdateError(null);
  };

  const handleSaveEdit = async (itemId: number) => {
    setUpdateError(null);
    try {
      await updateStock({ itemId, quantity: parseFloat(editQuantity) || 0 }).unwrap();
      setEditingId(null);
      setEditQuantity('');
    } catch (err: any) {
      const errorMsg = err.data?.detail || 'Failed to update stock quantity';
      setUpdateError(errorMsg);
    }
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setEditQuantity('');
    setUpdateError(null);
  };

  const handleRemove = async (itemId: number, itemName: string) => {
    if (confirm(`Are you sure you want to remove "${itemName}" from stock?`)) {
      try {
        await removeFromStock(itemId).unwrap();
      } catch (err) {
        console.error('Failed to remove from stock', err);
      }
    }
  };

  if (isLoading) {
    return <div className="flex items-center justify-center h-full">Loading stock...</div>;
  }

  if (error) {
    return <div className="text-red-500 p-4">Error loading stock</div>;
  }

  // Expand all categories by default on first load
  if (stockByCategory && expandedCategories.size === 0) {
    const allCategoryIds = new Set(stockByCategory.map((cat: any) => cat.category_id));
    setExpandedCategories(allCategoryIds);
  }

  return (
    <div className="h-full overflow-y-auto">
      {updateError && (
        <div className="p-4 mb-4 text-sm text-red-600 bg-red-100 rounded">
          {updateError}
        </div>
      )}
      
      {stockByCategory?.length === 0 ? (
        <div className="text-center text-gray-500 py-8">No items in stock</div>
      ) : (
        <div className="space-y-4">
          {stockByCategory?.map((category: any) => (
            <div key={category.category_id} className="border rounded-lg overflow-hidden">
              <button
                className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 transition-colors"
                onClick={() => toggleCategory(category.category_id)}
              >
                <span className="font-semibold text-lg">{category.category_name}</span>
                <span className="text-gray-500">
                  {expandedCategories.has(category.category_id) ? '▼' : '▶'} {category.items.length} items
                </span>
              </button>
              
              {expandedCategories.has(category.category_id) && (
                <div className="divide-y">
                  {category.items.map((item: any) => (
                    <div key={item.item_id} className="p-4 hover:bg-gray-50">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <h4 className="font-medium">{item.item_name}</h4>
                          <div className="text-sm text-gray-500 flex gap-4">
                            <span>SKU: {item.sku || 'N/A'}</span>
                            <span>Unit: {item.unit_type}</span>
                            <span>Price: ${item.unit_price.toFixed(2)}</span>
                          </div>
                        </div>
                        
                        <div className="flex items-center gap-4">
                          {editingId === item.item_id ? (
                            <div className="flex items-center gap-2">
                              <Input
                                type="number"
                                step="0.001"
                                value={editQuantity}
                                onChange={(e) => setEditQuantity(e.target.value)}
                                className="w-24"
                              />
                              <Button size="sm" onClick={() => handleSaveEdit(item.item_id)}>
                                Save
                              </Button>
                              <Button size="sm" variant="outline" onClick={handleCancelEdit}>
                                Cancel
                              </Button>
                            </div>
                          ) : (
                            <>
                              <div className="text-right">
                                <span className="text-lg font-bold text-blue-600">
                                  {item.quantity.toFixed(2)}
                                </span>
                                <span className="text-sm text-gray-500 ml-1">in stock</span>
                              </div>
                              <Button size="sm" variant="outline" onClick={() => handleStartEdit(item)}>
                                Update
                              </Button>
                              <Button size="sm" variant="outline" onClick={() => onEditItem(item)}>
                                Edit Item
                              </Button>
                              <Button size="sm" variant="danger" onClick={() => handleRemove(item.item_id, item.item_name)}>
                                Remove
                              </Button>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
