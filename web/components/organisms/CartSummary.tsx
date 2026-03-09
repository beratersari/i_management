'use client';
import { useGetCartQuery, useAddCartItemMutation, useUpdateCartItemMutation, useClearCartMutation, useCreateCartMutation, useCompleteCartMutation, useDeleteCartMutation } from '@/lib/redux/features/cartApi';
import { Button } from '../atoms/Button';
import { useState } from 'react';

interface CartSummaryProps {
  cartId: number | null;
  onCartCreated: (cartId: number) => void;
}

export const CartSummary = ({ cartId, onCartCreated }: CartSummaryProps) => {
  const [createCart] = useCreateCartMutation();
  const [addCartItem] = useAddCartItemMutation();
  const [updateCartItem] = useUpdateCartItemMutation();
  const [clearCart] = useClearCartMutation();
  const [completeCart] = useCompleteCartMutation();
  const [deleteCart] = useDeleteCartMutation();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  
  const { data: cartData, isLoading } = useGetCartQuery(cartId!, {
    skip: !cartId,
  });

  const showError = (message: string) => {
    setErrorMessage(message);
    // Auto-clear error after 5 seconds
    setTimeout(() => setErrorMessage(null), 5000);
  };

  const handleCreateCart = async () => {
    try {
      const result = await createCart({}).unwrap();
      onCartCreated(result.id);
    } catch (err) {
      console.error('Failed to create cart', err);
    }
  };

  const handleUpdateQuantity = async (cartItemId: number, newQuantity: number) => {
    if (!cartId) return;
    try {
      await updateCartItem({ cartId, cartItemId, quantity: newQuantity }).unwrap();
    } catch (err: any) {
      console.error('Failed to update quantity', err);
      const errorMsg = err.data?.detail || 'Failed to update quantity';
      showError(errorMsg);
    }
  };

  const handleRemoveItem = async (cartItemId: number) => {
    if (!cartId) return;
    try {
      await updateCartItem({ cartId, cartItemId, quantity: 0 }).unwrap();
    } catch (err) {
      console.error('Failed to remove item', err);
    }
  };

  const handleClearCart = async () => {
    if (!cartId) return;
    if (confirm('Are you sure you want to clear all items from the cart?')) {
      try {
        await clearCart(cartId).unwrap();
      } catch (err) {
        console.error('Failed to clear cart', err);
      }
    }
  };

  const handleCompleteCart = async () => {
    if (!cartId) return;
    if (confirm('Are you sure you want to complete this order?')) {
      try {
        await completeCart(cartId).unwrap();
        onCartCreated(0); // Reset to trigger new cart creation
      } catch (err) {
        console.error('Failed to complete cart', err);
      }
    }
  };

  const handleDeleteCart = async () => {
    if (!cartId) return;
    if (confirm('Are you sure you want to delete this cart?')) {
      try {
        await deleteCart(cartId).unwrap();
        onCartCreated(0);
      } catch (err) {
        console.error('Failed to delete cart', err);
      }
    }
  };

  const addItemToCart = async (itemId: number) => {
    if (!cartId) {
      try {
        const result = await createCart({}).unwrap();
        onCartCreated(result.id);
        await addCartItem({ cartId: result.id, item_id: itemId, quantity: 1 }).unwrap();
      } catch (err) {
        console.error('Failed to create cart and add item', err);
      }
    } else {
      try {
        await addCartItem({ cartId, item_id: itemId, quantity: 1 }).unwrap();
      } catch (err: any) {
        // Item might already exist, try to find it and update quantity
        const existingItem = cartData?.items?.find((item: any) => item.item_id === itemId);
        if (existingItem) {
          try {
            await updateCartItem({ 
              cartId, 
              cartItemId: existingItem.id, 
              quantity: parseFloat(existingItem.quantity) + 1 
            }).unwrap();
          } catch (updateErr: any) {
            const errorMsg = updateErr.data?.detail || 'Failed to increase quantity';
            showError(errorMsg);
          }
        } else {
          console.error('Failed to add item to cart', err);
        }
      }
    }
  };

  // Expose addItemToCart function
  if (typeof window !== 'undefined') {
    (window as any).addToCart = addItemToCart;
  }

  if (!cartId) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-4">
        <p className="text-gray-500 mb-4">No active cart</p>
        <Button onClick={handleCreateCart}>Create New Cart</Button>
      </div>
    );
  }

  if (isLoading) {
    return <div className="flex items-center justify-center h-full">Loading cart...</div>;
  }

  const { cart, items, totals } = cartData || { cart: null, items: [], totals: null };

  return (
    <div className="h-full flex flex-col">
      {/* Error Message */}
      {errorMessage && (
        <div className="p-3 mx-4 mt-4 text-sm text-red-600 bg-red-100 rounded border border-red-200">
          {errorMessage}
        </div>
      )}

      <div className="p-4 border-b bg-white">
        <div className="flex justify-between items-center">
          <h2 className="text-lg font-semibold">Cart #{cart?.id}</h2>
          <span className={`px-2 py-1 text-xs rounded-full ${
            cart?.status === 'completed' ? 'bg-green-100 text-green-800' :
            cart?.status === 'deleted' ? 'bg-red-100 text-red-800' :
            'bg-blue-100 text-blue-800'
          }`}>
            {cart?.status}
          </span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {items?.length === 0 ? (
          <p className="text-gray-500 text-center py-4">Cart is empty</p>
        ) : (
          <div className="space-y-3">
            {items?.map((item: any) => (
              <div key={item.id} className="bg-gray-50 p-3 rounded-lg">
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="font-medium">{item.name}</h4>
                    <p className="text-sm text-gray-500">
                      ${parseFloat(item.unit_price).toFixed(2)} × {parseFloat(item.quantity).toFixed(2)}
                    </p>
                  </div>
                  <p className="font-bold">${parseFloat(item.line_total).toFixed(2)}</p>
                </div>
                <div className="flex items-center gap-2 mt-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleUpdateQuantity(item.id, parseFloat(item.quantity) - 1)}
                    disabled={parseFloat(item.quantity) <= 1}
                  >
                    -
                  </Button>
                  <span className="px-3">{parseFloat(item.quantity).toFixed(2)}</span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleUpdateQuantity(item.id, parseFloat(item.quantity) + 1)}
                  >
                    +
                  </Button>
                  <Button
                    variant="danger"
                    size="sm"
                    onClick={() => handleRemoveItem(item.id)}
                    className="ml-auto"
                  >
                    Remove
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {totals && (
        <div className="p-4 border-t bg-white">
          <div className="space-y-1 text-sm">
            <div className="flex justify-between">
              <span>Subtotal:</span>
              <span>${parseFloat(totals.subtotal).toFixed(2)}</span>
            </div>
            <div className="flex justify-between text-green-600">
              <span>Discount:</span>
              <span>-${parseFloat(totals.discount_total).toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span>Tax:</span>
              <span>${parseFloat(totals.tax_total).toFixed(2)}</span>
            </div>
            <div className="flex justify-between font-bold text-lg pt-2 border-t">
              <span>Total:</span>
              <span>${parseFloat(totals.total).toFixed(2)}</span>
            </div>
          </div>

          <div className="flex gap-2 mt-4">
            <Button
              variant="danger"
              size="sm"
              onClick={handleClearCart}
              disabled={items?.length === 0}
            >
              Clear
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={handleDeleteCart}
            >
              Delete Cart
            </Button>
            <Button
              size="sm"
              className="flex-1"
              onClick={handleCompleteCart}
              disabled={items?.length === 0}
            >
              Complete Order
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};
