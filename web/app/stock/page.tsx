'use client';
import { useState, useMemo } from 'react';
import { DashboardTemplate } from '@/components/templates/DashboardTemplate';
import { StockList } from '@/components/organisms/StockList';
import { AddToStockModal } from '@/components/organisms/AddToStockModal';
import { ItemFormModal } from '@/components/organisms/ItemFormModal';
import { CategoryFormModal } from '@/components/organisms/CategoryFormModal';
import { SortableCategoryList } from '@/components/organisms/SortableCategoryList';
import { Button } from '@/components/atoms/Button';
import { useGetCategoriesQuery } from '@/lib/redux/features/categoryApi';
import { useGetItemsQuery } from '@/lib/redux/features/itemApi';
import { useGetStockQuery } from '@/lib/redux/features/stockApi';
import { useDeleteItemMutation } from '@/lib/redux/features/itemApi';
import { useAppSelector } from '@/lib/redux/hooks';

export default function StockPage() {
  const { user } = useAppSelector((state) => state.auth);
  const { data: categories } = useGetCategoriesQuery();
  const { data: items } = useGetItemsQuery(undefined);
  const { data: stock } = useGetStockQuery();
  const [deleteItem] = useDeleteItemMutation();
  
  const [showAddToStock, setShowAddToStock] = useState(false);
  const [showCreateItem, setShowCreateItem] = useState(false);
  const [showCreateCategory, setShowCreateCategory] = useState(false);
  const [editingItem, setEditingItem] = useState<any>(null);
  const [editingCategory, setEditingCategory] = useState<any>(null);
  const [showCategoryList, setShowCategoryList] = useState(false);

  const canManageStock = user?.role === 'admin' || user?.role === 'market_owner';

  // Determine if there are items available to add to stock (items not already in stock)
  const itemsNotInStock = useMemo(() => {
    if (!items || !stock) return [];
    const stockItemIds = new Set(stock.map((s: any) => s.item_id));
    return items.filter((item: any) => !stockItemIds.has(item.id));
  }, [items, stock]);

  const canAddToStock = itemsNotInStock.length > 0;

  const handleEditItem = (item: any) => {
    // The item from stock list has different structure
    setEditingItem({
      item_id: item.item_id,
      name: item.item_name,
      category_id: item.category_id,
      ...item,
    });
  };

  const handleDeleteItem = async (itemId: number) => {
    if (confirm('Are you sure you want to delete this item?')) {
      try {
        await deleteItem(itemId).unwrap();
      } catch (err) {
        console.error('Failed to delete item', err);
      }
    }
  };

  return (
    <DashboardTemplate>
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold">Stock Management</h1>
            <p className="text-gray-500">View and manage item stock levels</p>
          </div>
          {canManageStock && (
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setShowCategoryList(!showCategoryList)}>
                {showCategoryList ? 'Hide Categories' : 'Manage Categories'}
              </Button>
              <Button variant="outline" onClick={() => setShowCreateItem(true)}>
                New Item
              </Button>
              {canAddToStock && (
                <Button onClick={() => setShowAddToStock(true)}>
                  Add to Stock
                </Button>
              )}
            </div>
          )}
        </div>

        {/* Category List with Drag and Drop */}
        {showCategoryList && (
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold">Categories</h2>
              <Button size="sm" onClick={() => setShowCreateCategory(true)}>
                New Category
              </Button>
            </div>
            <SortableCategoryList 
              categories={categories || []} 
              onEdit={setEditingCategory} 
            />
          </div>
        )}

        {/* Stock List */}
        <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
          <StockList onEditItem={handleEditItem} />
        </div>
      </div>

      {/* Modals */}
      {showAddToStock && (
        <AddToStockModal onClose={() => setShowAddToStock(false)} />
      )}
      {showCreateItem && (
        <ItemFormModal onClose={() => setShowCreateItem(false)} />
      )}
      {editingItem && (
        <ItemFormModal item={editingItem} onClose={() => setEditingItem(null)} />
      )}
      {showCreateCategory && (
        <CategoryFormModal onClose={() => setShowCreateCategory(false)} />
      )}
      {editingCategory && (
        <CategoryFormModal category={editingCategory} onClose={() => setEditingCategory(null)} />
      )}
    </DashboardTemplate>
  );
}
