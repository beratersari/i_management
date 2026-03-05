import React, { useState } from 'react';
import { StyleSheet, View, ScrollView } from 'react-native';
import { useRouter, Stack } from 'expo-router';
import { useForm, Controller } from 'react-hook-form';
import { ThemedView } from '@/components/themed-view';
import { ThemedText } from '@/components/themed-text';
import { FormField } from '@/components/molecules/FormField';
import { Button } from '@/components/atoms/Button';
import { useAddStockMutation, useGetItemsQuery } from '@/services/api';
import { useThemeColor } from '@/hooks/use-theme-color';
import { Picker } from '@react-native-picker/picker';

export default function AddStockScreen() {
  const router = useRouter();
  const backgroundColor = useThemeColor({}, 'background');
  const [addStock, { isLoading }] = useAddStockMutation();
  const { data: items } = useGetItemsQuery(null);
  const [error, setError] = useState<string | undefined>();

  const { control, handleSubmit, formState: { errors } } = useForm({
    defaultValues: {
      item_id: '',
      quantity: '',
    }
  });

  const onSubmit = async (data: any) => {
    try {
      setError(undefined);
      await addStock({
        item_id: parseInt(data.item_id),
        quantity: parseFloat(data.quantity),
      }).unwrap();
      router.back();
    } catch (err: any) {
      console.error('Add stock failed:', err);
      setError(err?.data?.detail || 'Failed to add stock');
    }
  };

  return (
    <ThemedView style={[styles.container, { backgroundColor }]}>
      <Stack.Screen options={{ title: 'Add Stock' }} />
      <ScrollView contentContainerStyle={styles.content}>
        <ThemedText type="title" style={styles.title}>Add to Stock</ThemedText>
        
        <View style={styles.fieldContainer}>
          <ThemedText style={styles.label}>Item</ThemedText>
          <Controller
            control={control}
            rules={{ required: 'Item is required' }}
            render={({ field: { onChange, value } }) => (
              <View style={styles.pickerContainer}>
                <Picker
                  selectedValue={value}
                  onValueChange={onChange}
                  style={styles.picker}
                >
                  <Picker.Item label="Select an item..." value="" />
                  {items?.map((item: any) => (
                    <Picker.Item key={item.id} label={`${item.name} (${item.sku})`} value={item.id.toString()} />
                  ))}
                </Picker>
              </View>
            )}
            name="item_id"
          />
          {errors.item_id && <ThemedText style={styles.errorText}>{errors.item_id.message}</ThemedText>}
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
            title="Add to Stock"
            onPress={handleSubmit(onSubmit)}
            loading={isLoading}
            disabled={isLoading}
            style={styles.submitButton}
          />
          
          <Button
            title="Cancel"
            variant="secondary"
            onPress={() => router.back()}
            disabled={isLoading}
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
  fieldContainer: {
    marginBottom: 16,
  },
  label: {
    marginBottom: 8,
    fontSize: 16,
    fontWeight: '500',
  },
  pickerContainer: {
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    // backgroundColor: 'rgba(255,255,255,0.1)',
  },
  picker: {
    height: 50,
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
  }
});
