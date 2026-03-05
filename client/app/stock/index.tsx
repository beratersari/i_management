import React from 'react';
import { StyleSheet, View, FlatList, TouchableOpacity, Alert } from 'react-native';
import { useRouter, Stack } from 'expo-router';
import { ThemedView } from '@/components/themed-view';
import { ThemedText } from '@/components/themed-text';
import { useGetStockQuery, useGetMeQuery, useDeleteStockMutation } from '@/services/api';
import { useThemeColor } from '@/hooks/use-theme-color';
import { Button } from '@/components/atoms/Button';
import { Ionicons } from '@expo/vector-icons';

export default function StockListScreen() {
  const router = useRouter();
  const backgroundColor = useThemeColor({}, 'background');
  const cardBackground = useThemeColor({ light: '#fff', dark: '#333' }, 'background');
  
  const { data: user } = useGetMeQuery({});
  const { data: stock, isLoading } = useGetStockQuery({});
  const [deleteStock] = useDeleteStockMutation();

  const canManage = user?.role === 'admin' || user?.role === 'market_owner';

  const handleDelete = (id: number) => {
    Alert.alert(
      "Delete Stock Item",
      "Are you sure you want to remove this item from stock?",
      [
        { text: "Cancel", style: "cancel" },
        { 
          text: "Delete", 
          style: "destructive", 
          onPress: async () => {
            try {
              await deleteStock(id).unwrap();
            } catch (error) {
              Alert.alert("Error", "Failed to delete stock item");
            }
          }
        }
      ]
    );
  };

  const renderItem = ({ item }: { item: any }) => (
    <View style={[styles.card, { backgroundColor: cardBackground }]}>
      <View style={styles.cardContent}>
        <ThemedText type="defaultSemiBold">{item.item_name}</ThemedText>
        <ThemedText>Quantity: {item.quantity}</ThemedText>
        <ThemedText style={styles.sku}>SKU: {item.sku}</ThemedText>
      </View>
      <View style={styles.cardActions}>
        <TouchableOpacity 
          onPress={() => router.push(`/stock/${item.item_id}`)}
          style={styles.iconButton}
        >
          <Ionicons name="pencil" size={20} color="#0a7ea4" />
        </TouchableOpacity>
        
        {canManage && (
          <TouchableOpacity 
            onPress={() => handleDelete(item.item_id)}
            style={styles.iconButton}
          >
            <Ionicons name="trash" size={20} color="#d32f2f" />
          </TouchableOpacity>
        )}
      </View>
    </View>
  );

  return (
    <ThemedView style={[styles.container, { backgroundColor }]}>
      <Stack.Screen options={{ headerShown: false }} />
      <View style={styles.header}>
        <ThemedText type="title">Stock Management</ThemedText>
        {canManage && (
          <Button 
            title="Add Item" 
            onPress={() => router.push('/stock/add')} 
            // size="small" // Button doesn't support size prop yet, will fix or remove
          />
        )}
      </View>
      
      {isLoading ? (
        <ThemedText>Loading...</ThemedText>
      ) : (
        <FlatList
          data={stock}
          renderItem={renderItem}
          keyExtractor={(item) => item.id.toString()}
          contentContainerStyle={styles.listContent}
          ListEmptyComponent={<ThemedText>No stock items found.</ThemedText>}
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
