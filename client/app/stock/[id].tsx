import React, { useEffect, useState } from 'react';
import { StyleSheet, View, ScrollView } from 'react-native';
import { useLocalSearchParams, useRouter, Stack } from 'expo-router';
import { useForm, Controller } from 'react-hook-form';
import { ThemedView } from '@/components/themed-view';
import { ThemedText } from '@/components/themed-text';
import { FormField } from '@/components/molecules/FormField';
import { Button } from '@/components/atoms/Button';
import { useUpdateStockMutation, useGetStockQuery } from '@/services/api';
import { useThemeColor } from '@/hooks/use-theme-color';

export default function EditStockScreen() {
  const { id } = useLocalSearchParams();
  const router = useRouter();
  const backgroundColor = useThemeColor({}, 'background');
  
  const [updateStock, { isLoading: isUpdating }] = useUpdateStockMutation();
  const { data: stockItems, isLoading: isFetching } = useGetStockQuery({});
  
  const [error, setError] = useState<string | undefined>();
  
  const stockItem = stockItems?.find((item: any) => item.item_id.toString() === id);

  const { control, handleSubmit, setValue, formState: { errors } } = useForm({
    defaultValues: {
      quantity: '',
    }
  });

  useEffect(() => {
    if (stockItem) {
      setValue('quantity', stockItem.quantity.toString());
    }
  }, [stockItem, setValue]);

  const onSubmit = async (data: any) => {
    try {
      setError(undefined);
      await updateStock({
        id: parseInt(id as string),
        quantity: parseFloat(data.quantity),
      }).unwrap();
      router.back();
    } catch (err: any) {
      console.error('Update stock failed:', err);
      setError(err?.data?.detail || 'Failed to update stock');
    }
  };

  if (isFetching) {
    return (
      <ThemedView style={[styles.container, { backgroundColor, justifyContent: 'center', alignItems: 'center' }]}>
        <ThemedText>Loading...</ThemedText>
      </ThemedView>
    );
  }

  if (!stockItem) {
    return (
      <ThemedView style={[styles.container, { backgroundColor, justifyContent: 'center', alignItems: 'center' }]}>
        <ThemedText>Stock item not found.</ThemedText>
        <Button title="Go Back" onPress={() => router.back()} style={styles.backButton} />
      </ThemedView>
    );
  }

  return (
    <ThemedView style={[styles.container, { backgroundColor }]}>
      <Stack.Screen options={{ title: 'Update Stock' }} />
      <ScrollView contentContainerStyle={styles.content}>
        <ThemedText type="title" style={styles.title}>Update Stock</ThemedText>
        
        <View style={styles.infoContainer}>
          <ThemedText type="subtitle">{stockItem.item_name}</ThemedText>
          <ThemedText style={styles.sku}>SKU: {stockItem.sku}</ThemedText>
        </View>
        
        <Controller
          control={control}
          rules={{ 
            required: 'Quantity is required',
            min: { value: 0, message: 'Quantity must be positive' }
          }}
          render={({ field: { onChange, value } }) => (
            <FormField
              label="Quantity"
              value={value}
              onChangeText={onChange}
              placeholder="0"
              keyboardType="numeric"
              error={errors.quantity?.message}
            />
          )}
          name="quantity"
        />
        
        {error && <ThemedText style={styles.errorText}>{error}</ThemedText>}

        <View style={styles.actions}>
          <Button
            title="Update Quantity"
            onPress={handleSubmit(onSubmit)}
            loading={isUpdating}
            disabled={isUpdating}
            style={styles.submitButton}
          />
          
          <Button
            title="Cancel"
            variant="secondary"
            onPress={() => router.back()}
            disabled={isUpdating}
            style={styles.cancelButton}
          />
        </View>
      </ScrollView>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    padding: 24,
    paddingTop: 60,
  },
  title: {
    marginBottom: 24,
    textAlign: 'center',
  },
  infoContainer: {
    marginBottom: 24,
    alignItems: 'center',
  },
  sku: {
    opacity: 0.6,
    marginTop: 4,
  },
  errorText: {
    color: '#d32f2f',
    marginTop: 4,
    fontSize: 12,
  },
  actions: {
    marginTop: 24,
    gap: 12,
  },
  submitButton: {
    marginTop: 8,
  },
  cancelButton: {
    marginTop: 12,
  },
  backButton: {
    marginTop: 16,
  }
});
