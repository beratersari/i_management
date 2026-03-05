import React, { useEffect, useState } from 'react';
import { StyleSheet, View, ScrollView } from 'react-native';
import { useLocalSearchParams, useRouter, Stack } from 'expo-router';
import { useForm, Controller } from 'react-hook-form';
import { ThemedView } from '@/components/themed-view';
import { ThemedText } from '@/components/themed-text';
import { FormField } from '@/components/molecules/FormField';
import { Button } from '@/components/atoms/Button';
import { useUpdateItemMutation, useGetItemsQuery, useGetCategoriesQuery } from '@/services/api';
import { useThemeColor } from '@/hooks/use-theme-color';
import { Picker } from '@react-native-picker/picker';

export default function EditItemScreen() {
  const { id } = useLocalSearchParams();
  const router = useRouter();
  const backgroundColor = useThemeColor({}, 'background');
  
  const [updateItem, { isLoading: isUpdating }] = useUpdateItemMutation();
  const { data: items, isLoading: isFetching } = useGetItemsQuery(null);
  const { data: categories } = useGetCategoriesQuery({});
  
  const [error, setError] = useState<string | undefined>();
  
  const item = items?.find((i: any) => i.id.toString() === id);

  const { control, handleSubmit, setValue, formState: { errors } } = useForm({
    defaultValues: {
      name: '',
      category_id: '',
      unit_price: '',
      unit_type: '',
      sku: '',
      description: '',
      tax_rate: '',
      discount_rate: '',
    }
  });

  useEffect(() => {
    if (item) {
      setValue('name', item.name);
      setValue('category_id', item.category_id.toString());
      setValue('unit_price', item.unit_price.toString());
      setValue('unit_type', item.unit_type);
      setValue('sku', item.sku || '');
      setValue('description', item.description || '');
      setValue('tax_rate', item.tax_rate.toString());
      setValue('discount_rate', item.discount_rate.toString());
    }
  }, [item, setValue]);

  const onSubmit = async (data: any) => {
    try {
      setError(undefined);
      await updateItem({
        id: parseInt(id as string),
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
      console.error('Update item failed:', err);
      setError(err?.data?.detail || 'Failed to update item');
    }
  };

  if (isFetching) {
    return (
      <ThemedView style={[styles.container, { backgroundColor, justifyContent: 'center', alignItems: 'center' }]}>
        <ThemedText>Loading...</ThemedText>
      </ThemedView>
    );
  }

  if (!item) {
    return (
      <ThemedView style={[styles.container, { backgroundColor, justifyContent: 'center', alignItems: 'center' }]}>
        <ThemedText>Item not found.</ThemedText>
        <Button title="Go Back" onPress={() => router.back()} style={styles.backButton} />
      </ThemedView>
    );
  }

  return (
    <ThemedView style={[styles.container, { backgroundColor }]}>
      <Stack.Screen options={{ title: 'Edit Item' }} />
      <ScrollView contentContainerStyle={styles.content}>
        <ThemedText type="title" style={styles.title}>Edit Item</ThemedText>
        
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
            title="Update Item"
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
  },
  backButton: {
    marginTop: 16,
  }
});
