'use client';
import { Button } from '../atoms/Button';

interface ItemCardProps {
  item: {
    id: number;
    name: string;
    description?: string;
    image_url?: string;
    unit_price: number | string;
    unit_type: string;
    tax_rate?: number | string;
    discount_rate?: number | string;
    quantity?: number | string;
  };
  onAddToCart: () => void;
}

export const ItemCard = ({ item, onAddToCart }: ItemCardProps) => {
  const price = typeof item.unit_price === 'number' ? item.unit_price : parseFloat(item.unit_price || '0');
  const quantity = typeof item.quantity === 'number' ? item.quantity : parseFloat(item.quantity || '0');
  
  return (
    <div className="bg-white rounded-lg shadow-sm border overflow-hidden flex flex-col">
      <div className="relative w-full h-40 bg-gray-100">
        {item.image_url ? (
          <img
            src={item.image_url}
            alt={item.name}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-400">
            No Image
          </div>
        )}
      </div>
      <div className="p-3 flex-1 flex flex-col">
        <h3 className="font-medium text-sm truncate">{item.name}</h3>
        {item.description && (
          <p className="text-xs text-gray-500 mt-1 line-clamp-2">{item.description}</p>
        )}
        <div className="mt-auto pt-2">
          <p className="text-lg font-bold text-blue-600">${price.toFixed(2)}</p>
          <p className="text-xs text-gray-400">per {item.unit_type}</p>
          {item.quantity !== undefined && (
            <p className="text-xs text-green-600 mt-1">{quantity.toFixed(2)} in stock</p>
          )}
        </div>
        <Button
          size="sm"
          className="w-full mt-2"
          onClick={onAddToCart}
        >
          Add to Cart
        </Button>
      </div>
    </div>
  );
};
