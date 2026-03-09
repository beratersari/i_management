'use client';
import { useState, useEffect, useCallback } from 'react';
import { DashboardTemplate } from '@/components/templates/DashboardTemplate';
import { ItemList } from '@/components/organisms/ItemList';
import { CartSummary } from '@/components/organisms/CartSummary';
import { useCreateCartMutation, useAddCartItemMutation, useUpdateCartItemMutation, useGetCartQuery } from '@/lib/redux/features/cartApi';

export default function DashboardPage() {
  const [cartId, setCartId] = useState<number | null>(null);
  const [createCart] = useCreateCartMutation();
  const [addCartItem] = useAddCartItemMutation();
  const [updateCartItem] = useUpdateCartItemMutation();

  const { data: cartData } = useGetCartQuery(cartId!, {
    skip: !cartId,
  });

  const handleAddToCart = useCallback(async (itemId: number) => {
    let currentCartId = cartId;

    // Create cart if none exists
    if (!currentCartId) {
      try {
        const result = await createCart({}).unwrap();
        currentCartId = result.id;
        setCartId(currentCartId);
      } catch (err) {
        console.error('Failed to create cart', err);
        return;
      }
    }

    // Add item to cart
    try {
      await addCartItem({ cartId: currentCartId, item_id: itemId, quantity: 1 }).unwrap();
    } catch (err: any) {
      // If item already exists, update quantity
      if (err.status === 409) {
        const existingItem = cartData?.items?.find((item: any) => item.item_id === itemId);
        if (existingItem) {
          await updateCartItem({
            cartId: currentCartId,
            cartItemId: existingItem.id,
            quantity: parseFloat(existingItem.quantity) + 1,
          }).unwrap();
        }
      } else {
        console.error('Failed to add item to cart', err);
      }
    }
  }, [cartId, cartData, createCart, addCartItem, updateCartItem]);

  const handleCartCreated = (newCartId: number) => {
    setCartId(newCartId || null);
  };

  return (
    <DashboardTemplate>
      <div className="flex h-[calc(100vh-120px)] gap-4">
        {/* Left Half - Cart Summary */}
        <div className="w-1/3 min-w-[300px] bg-white rounded-lg shadow-sm border overflow-hidden">
          <CartSummary cartId={cartId} onCartCreated={handleCartCreated} />
        </div>

        {/* Right Half - Items Display */}
        <div className="flex-1 bg-white rounded-lg shadow-sm border overflow-hidden">
          <ItemList onAddToCart={handleAddToCart} />
        </div>
      </div>
    </DashboardTemplate>
  );
}
