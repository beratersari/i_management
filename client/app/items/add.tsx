import React, { useState } from 'react';
import { StyleSheet, View, ScrollView } from 'react-native';
import { useRouter, Stack } from 'expo-router';
import { useForm, Controller } from 'react-hook-form';
import { ThemedView } from '@/components/themed-view';
import { ThemedText } from '@/components/themed-text';
import { FormField } from '@/components/molecules/FormField';
import { Button } from '@/components/atoms/Button';
import { useAddItemMutation, useGetCategoriesQuery } from '@/services/api';
import { useThemeColor } from '@/hooks/use-theme-color';
import { Picker } from '@react-native-picker/picker';

export default function AddItemScreen() {
  const router = useRouter();
  const backgroundColor = useThemeColor({}, 'background');
  const [addItem, { isLoading }] = useAddItemMutation();
  const { data: categories } = useGetCategoriesQuery({});
  const [error, setError] = useState<string | undefined>();

  const { control, handleSubmit, formState: { errors } } = useForm({
    defaultValues: {
      name: '',
      category_id: '',
      unit_price: '',
      unit_type: 'each',
      sku: '',
      description: '',
      tax_rate: '0',
      discount_rate: '0',
    }
  });

  const onSubmit = async (data: any) => {
    try {
      setError(undefined);
      await addItem({
        name: data.name,
        category_id: parseInt(data.category_id),
        unit_price: parseFloat(data.unit_price),
        unit_type: data.unit_type,
        sku: data.sku || undefined,
        description: data.description || undefined,
        tax_rate: parseFloat(data.tax_rate),
        discount_rate: parseFloat(data.discount_rate),
      }).unwrap();
      router.back();
    } catch (err: any) {
      console.error('Add item failed:', err);
      setError(err?.data?.detail || 'Failed to add item');
    }
  };

  return (
    <ThemedView style={[styles.container, { backgroundColor }]}>
      <Stack.Screen options={{ title: 'Add Item' }} />
      <ScrollView contentContainerStyle={styles.content}>
        <ThemedText type="title" style={styles.title}>Add New Item</ThemedText>
        
        <Controller
          control={control}
          rules={{ required: 'Name is required' }}
          render={({ field: { onChange, value } }) => (
            <FormField
              label="Name"
              value={value}
              onChangeText={onChange}
              placeholder="Item Name"
              error={errors.name?.message}
            />
          )}
          name="name"
        />

        <View style={styles.fieldContainer}>
          <ThemedText style={styles.label}>Category</ThemedText>
          <Controller
            control={control}
            rules={{ required: 'Category is required' }}
            render={({ field: { onChange, value } }) => (
              <View style={styles.pickerContainer}>
                <Picker
                  selectedValue={value}
                  onValueChange={onChange}
                  style={styles.picker}
                >
                  <Picker.Item label="Select a category..." value="" />
                  {categories?.map((cat: any) => (
                    <Picker.Item key={cat.id} label={cat.name} value={cat.id.toString()} />
                  ))}
                </Picker>
              </View>
            )}
            name="category_id"
          />
          {errors.category_id && <ThemedText style={styles.errorText}>{errors.category_id.message}</ThemedText>}
        </View>

        <Controller
          control={control}
          rules={{ 
            required: 'Price is required',
            min: { value: 0, message: 'Price must be positive' }
          }}
          render={({ field: { onChange, value } }) => (
            <FormField
              label="Price"
              value={value}
              onChangeText={onChange}
              placeholder="0.00"
              keyboardType="numeric"
              error={errors.unit_price?.message}
            />
          )}
          name="unit_price"
        />

        <Controller
          control={control}
          rules={{ required: 'Unit Type is required' }}
          render={({ field: { onChange, value } }) => (
            <FormField
              label="Unit Type (e.g. kg, each)"
              value={value}
              onChangeText={onChange}
              placeholder="each"
              error={errors.unit_type?.message}
            />
          )}
          name="unit_type"
        />

        <Controller
          control={control}
          render={({ field: { onChange, value } }) => (
            <FormField
              label="SKU (Optional)"
              value={value}
              onChangeText={onChange}
              placeholder="SKU-123"
            />
          )}
          name="sku"
        />

        <Controller
          control={control}
          render={({ field: { onChange, value } }) => (
            <FormField
              label="Description (Optional)"
              value={value}
              onChangeText={onChange}
              placeholder="Description"
              multiline
            />
          )}
          name="description"
        />

        <View style={{ flexDirection: 'row', gap: 12 }}>
          <View style={{ flex: 1 }}>
            <Controller
              control={control}
              render={({ field: { onChange, value } }) => (
                <FormField
                  label="Tax Rate (%)"
                  value={value}
                  onChangeText={onChange}
                  placeholder="0"
                  keyboardType="numeric"
                />
              )}
              name="tax_rate"
            />
          </View>
          <View style={{ flex: 1 }}>
            <Controller
              control={control}
              render={({ field: { onChange, value } }) => (
                <FormField
                  label="Discount (%)"
                  value={value}
                  onChangeText={onChange}
                  placeholder="0"
                  keyboardType="numeric"
                />
              )}
              name="discount_rate"
            />
          </View>
        </View>
        
        {error && <ThemedText style={styles.errorText}>{error}</ThemedText>}

        <View style={styles.actions}>
          <Button
            title="Create Item"
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
