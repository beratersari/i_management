import React, { useState } from 'react';
import { StyleSheet, View, FlatList, TouchableOpacity, ScrollView, Alert } from 'react-native';
import { useRouter, Stack } from 'expo-router';
import { ThemedView } from '@/components/themed-view';
import { ThemedText } from '@/components/themed-text';
import { useGetItemsQuery, useGetCategoriesQuery, useGetMeQuery, useDeleteItemMutation } from '@/services/api';
import { useThemeColor } from '@/hooks/use-theme-color';
import { Button } from '@/components/atoms/Button';
import { Ionicons } from '@expo/vector-icons';

export default function ItemsListScreen() {
  const router = useRouter();
  const backgroundColor = useThemeColor({}, 'background');
  const cardBackground = useThemeColor({ light: '#fff', dark: '#333' }, 'background');
  const activeTabColor = useThemeColor({}, 'tint');
  const inactiveTabColor = useThemeColor({ light: '#eee', dark: '#444' }, 'tabIconDefault');
  
  const [selectedCategory, setSelectedCategory] = useState<number | null>(null);

  const { data: user } = useGetMeQuery({});
  const { data: categories } = useGetCategoriesQuery({});
  const { data: items, isLoading } = useGetItemsQuery(selectedCategory);
  const [deleteItem] = useDeleteItemMutation();

  const canManage = user?.role === 'admin' || user?.role === 'market_owner';

  const handleDelete = (id: number) => {
    Alert.alert(
      "Delete Item",
      "Are you sure you want to delete this item? This cannot be undone.",
      [
        { text: "Cancel", style: "cancel" },
        { 
          text: "Delete", 
          style: "destructive", 
          onPress: async () => {
            try {
              await deleteItem(id).unwrap();
            } catch (error) {
              Alert.alert("Error", "Failed to delete item");
            }
          }
        }
      ]
    );
  };

  const renderCategoryTab = (category: { id: number | null, name: string }) => {
    const isActive = selectedCategory === category.id;
    return (
      <TouchableOpacity
        key={category.id ?? 'all'}
        onPress={() => setSelectedCategory(category.id)}
        style={[
          styles.categoryTab,
          { backgroundColor: isActive ? activeTabColor : inactiveTabColor }
        ]}
      >
        <ThemedText style={{ color: isActive ? '#fff' : undefined }}>
          {category.name}
        </ThemedText>
      </TouchableOpacity>
    );
  };

  const renderItem = ({ item }: { item: any }) => (
    <View style={[styles.card, { backgroundColor: cardBackground }]}>
      <View style={styles.cardContent}>
        <ThemedText type="defaultSemiBold">{item.name}</ThemedText>
        <ThemedText>Price: ${item.unit_price} / {item.unit_type}</ThemedText>
        {item.sku && <ThemedText style={styles.sku}>SKU: {item.sku}</ThemedText>}
      </View>
      
      {canManage && (
        <View style={styles.cardActions}>
          <TouchableOpacity 
            onPress={() => router.push(`/items/${item.id}`)}
            style={styles.iconButton}
          >
            <Ionicons name="pencil" size={20} color="#0a7ea4" />
          </TouchableOpacity>
          
          <TouchableOpacity 
            onPress={() => handleDelete(item.id)}
            style={styles.iconButton}
          >
            <Ionicons name="trash" size={20} color="#d32f2f" />
          </TouchableOpacity>
        </View>
      )}
    </View>
  );

  return (
    <ThemedView style={[styles.container, { backgroundColor }]}>
      <Stack.Screen options={{ headerShown: false }} />
      <View style={styles.header}>
        <ThemedText type="title">Items</ThemedText>
        {canManage && (
          <Button 
            title="Add Item" 
            onPress={() => router.push('/items/add')} 
          />
        )}
      </View>

      <View style={styles.categoriesContainer}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.categoriesContent}>
          {renderCategoryTab({ id: null, name: 'All' })}
          {categories?.map((cat: any) => renderCategoryTab(cat))}
        </ScrollView>
      </View>
      
      {isLoading ? (
        <ThemedText>Loading...</ThemedText>
      ) : (
        <FlatList
          data={items}
          renderItem={renderItem}
          keyExtractor={(item) => item.id.toString()}
          contentContainerStyle={styles.listContent}
          ListEmptyComponent={<ThemedText>No items found.</ThemedText>}
        />
      )}
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
    paddingTop: 60,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  categoriesContainer: {
    marginBottom: 16,
    height: 40,
  },
  categoriesContent: {
    gap: 8,
    paddingRight: 16,
  },
  categoryTab: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    marginRight: 8,
    justifyContent: 'center',
  },
  listContent: {
    gap: 12,
    paddingBottom: 20,
  },
  card: {
    padding: 16,
    borderRadius: 12,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  cardContent: {
    flex: 1,
  },
  sku: {
    fontSize: 12,
    opacity: 0.6,
    marginTop: 4,
  },
  cardActions: {
    flexDirection: 'row',
    gap: 12,
  },
  iconButton: {
    padding: 8,
  }
});
