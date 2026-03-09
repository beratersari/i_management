'use client';
import { useState, useMemo } from 'react';
import { useGetStockByCategoryQuery } from '@/lib/redux/features/stockApi';
import { useGetCategoriesQuery } from '@/lib/redux/features/categoryApi';
import { ItemCard } from '../atoms/ItemCard';
import { Select } from '../atoms/Select';

interface ItemListProps {
  onAddToCart: (itemId: number) => void;
}

export const ItemList = ({ onAddToCart }: ItemListProps) => {
  const [selectedCategory, setSelectedCategory] = useState<number | undefined>(undefined);
  const { data: stockByCategory, isLoading: stockLoading, error: stockError } = useGetStockByCategoryQuery();
  const { data: categories, isLoading: categoriesLoading } = useGetCategoriesQuery();

  // Flatten stock items from all categories and filter by selected category
  const items = useMemo(() => {
    if (!stockByCategory) return [];
    
    if (selectedCategory) {
      const category = stockByCategory.find((cat: any) => cat.category_id === selectedCategory);
      return category?.items || [];
    }
    
    return stockByCategory.flatMap((cat: any) => cat.items);
  }, [stockByCategory, selectedCategory]);

  const categoryOptions = [
    { label: 'All Categories', value: '' },
    ...(categories?.map((cat: any) => ({ label: cat.name, value: String(cat.id) })) || []),
  ];

  const handleCategoryChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    setSelectedCategory(value ? parseInt(value) : undefined);
  };

  if (stockLoading || categoriesLoading) {
    return <div className="flex items-center justify-center h-full">Loading items...</div>;
  }

  if (stockError) {
    return <div className="text-red-500 p-4">Error loading items</div>;
  }

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b bg-white sticky top-0 z-10">
        <Select
          options={categoryOptions}
          value={selectedCategory?.toString() || ''}
          onChange={handleCategoryChange}
          className="w-full max-w-xs"
        />
      </div>
      <div className="flex-1 overflow-y-auto p-4">
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
          {items.map((item: any) => (
            <ItemCard
              key={item.item_id}
              item={{
                id: item.item_id,
                name: item.item_name,
                unit_price: item.unit_price,
                unit_type: item.unit_type,
                quantity: item.quantity,
              }}
              onAddToCart={() => onAddToCart(item.item_id)}
            />
          ))}
        </div>
        {items.length === 0 && (
          <div className="text-center text-gray-500 py-8">No items in stock</div>
        )}
      </div>
    </div>
  );
};
