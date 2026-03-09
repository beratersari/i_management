'use client';
import React, { useState } from 'react';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { Button } from '../atoms/Button';
import { useUpdateCategoryMutation } from '@/lib/redux/features/categoryApi';

interface Category {
  id: number;
  name: string;
  description?: string;
  sort_order: number;
}

interface SortableCategoryListProps {
  categories: Category[];
  onEdit: (category: Category) => void;
}

// Sortable Category Item Component
function SortableCategoryItem({ category, onEdit }: { category: Category; onEdit: (category: Category) => void }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: category.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="p-3 border rounded-lg flex justify-between items-center hover:bg-gray-50 bg-white cursor-grab active:cursor-grabbing"
      {...attributes}
      {...listeners}
    >
      <div className="flex items-center gap-3">
        <span className="text-gray-400">⋮⋮</span>
        <div>
          <h3 className="font-medium">{category.name}</h3>
          {category.description && (
            <p className="text-sm text-gray-500">{category.description}</p>
          )}
        </div>
      </div>
      <Button
        size="sm"
        variant="outline"
        onClick={(e: React.MouseEvent) => {
          e.stopPropagation();
          onEdit(category);
        }}
      >
        Edit
      </Button>
    </div>
  );
}

export const SortableCategoryList = ({ categories, onEdit }: SortableCategoryListProps) => {
  const [items, setItems] = useState<Category[]>(categories);
  const [updateCategory] = useUpdateCategoryMutation();

  // Update local state when props change
  React.useEffect(() => {
    setItems(categories);
  }, [categories]);

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      setItems((items) => {
        const oldIndex = items.findIndex((item) => item.id === active.id);
        const newIndex = items.findIndex((item) => item.id === over.id);
        const newItems = arrayMove(items, oldIndex, newIndex);
        
        // Update sort_order for affected items
        newItems.forEach((item, index) => {
          if (item.sort_order !== index) {
            updateCategory({ id: item.id, sort_order: index });
          }
        });
        
        return newItems;
      });
    }
  };

  if (items.length === 0) {
    return (
      <div className="text-center text-gray-500 py-4">
        No categories found. Create one to get started.
      </div>
    );
  }

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragEnd={handleDragEnd}
    >
      <SortableContext items={items.map((c) => c.id)} strategy={verticalListSortingStrategy}>
        <div className="space-y-2">
          {items.map((category) => (
            <SortableCategoryItem
              key={category.id}
              category={category}
              onEdit={onEdit}
            />
          ))}
        </div>
      </SortableContext>
    </DndContext>
  );
};
