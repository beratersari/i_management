import React, { useState, useEffect } from 'react';
import { StyleSheet, View, ScrollView, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { useForm, Controller } from 'react-hook-form';
import { ThemedView } from '@/components/themed-view';
import { ThemedText } from '@/components/themed-text';
import { FormField } from '@/components/molecules/FormField';
import { Button } from '@/components/atoms/Button';
import { useRegisterUserMutation, useGetMeQuery } from '@/services/api';
import { useThemeColor } from '@/hooks/use-theme-color';

export default function RegisterUserScreen() {
  const router = useRouter();
  const backgroundColor = useThemeColor({}, 'background');
  const [registerUser, { isLoading }] = useRegisterUserMutation();
  const { data: user } = useGetMeQuery({});
  const [error, setError] = useState<string | undefined>();
  
  const isAdmin = user?.role === 'admin';
  const isMarketOwner = user?.role === 'market_owner';

  const { control, handleSubmit, setValue, watch, formState: { errors } } = useForm({
    defaultValues: {
      username: '',
      email: '',
      password: '',
      full_name: '',
      role: 'admin',
    }
  });

  useEffect(() => {
    if (user) {
      if (user.role === 'market_owner') {
        setValue('role', 'employee');
      } else if (user.role === 'admin') {
        // Keep default or set to admin, but user might have changed it.
        // Actually for admin, we default to admin, but they can change it.
        // We only enforce employee for market_owner.
      }
    }
  }, [user, setValue]);

  const selectedRole = watch('role');

  const onSubmit = async (data: any) => {
    try {
      setError(undefined);
      await registerUser(data).unwrap();
      Alert.alert('Success', 'User created successfully', [
        { text: 'OK', onPress: () => router.back() }
      ]);
    } catch (err: any) {
      console.error('Registration failed:', err);
      setError(err?.data?.detail || 'Failed to create user');
    }
  };

  return (
    <ThemedView style={[styles.container, { backgroundColor }]}>
      <ScrollView contentContainerStyle={styles.content}>
        <ThemedText type="title" style={styles.title}>Create New User</ThemedText>
        
        <Controller
          control={control}
          rules={{ 
            required: 'Username is required',
            minLength: { value: 3, message: 'Username must be at least 3 characters' },
            pattern: {
              value: /^[a-zA-Z0-9_]+$/,
              message: 'Username can only contain letters, numbers, and underscores'
            }
          }}
          render={({ field: { onChange, value } }) => (
            <FormField
              label="Username"
              value={value}
              onChangeText={onChange}
              placeholder="username"
              autoCapitalize="none"
              error={errors.username?.message}
            />
          )}
          name="username"
        />
        
        <Controller
          control={control}
          rules={{ 
            required: 'Email is required',
            pattern: {
              value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
              message: 'Invalid email address'
            }
          }}
          render={({ field: { onChange, value } }) => (
            <FormField
              label="Email"
              value={value}
              onChangeText={onChange}
              placeholder="email@example.com"
              keyboardType="email-address"
              autoCapitalize="none"
              error={errors.email?.message}
            />
          )}
          name="email"
        />
        
        <Controller
          control={control}
          render={({ field: { onChange, value } }) => (
            <FormField
              label="Full Name (Optional)"
              value={value}
              onChangeText={onChange}
              placeholder="John Doe"
              error={errors.full_name?.message}
            />
          )}
          name="full_name"
        />
        
        <Controller
          control={control}
          rules={{ 
            required: 'Password is required',
            minLength: { value: 8, message: 'Password must be at least 8 characters' },
            pattern: {
              value: /^(?=.*[A-Z])(?=.*\d)/,
              message: 'Password must contain at least one uppercase letter and one number'
            }
          }}
          render={({ field: { onChange, value } }) => (
            <FormField
              label="Password"
              value={value}
              onChangeText={onChange}
              placeholder="Strong password"
              secureTextEntry
              error={errors.password?.message}
            />
          )}
          name="password"
        />
        
        <View style={styles.roleContainer}>
          <ThemedText type="defaultSemiBold" style={styles.label}>Role</ThemedText>
          <View style={styles.roleButtons}>
            {isAdmin && (
              <>
                <Button 
                  title="Admin" 
                  variant={selectedRole === 'admin' ? 'primary' : 'secondary'}
                  onPress={() => setValue('role', 'admin')}
                  style={styles.roleButton}
                />
                <Button 
                  title="Owner" 
                  variant={selectedRole === 'market_owner' ? 'primary' : 'secondary'}
                  onPress={() => setValue('role', 'market_owner')}
                  style={styles.roleButton}
                />
                <Button 
                  title="Employee" 
                  variant={selectedRole === 'employee' ? 'primary' : 'secondary'}
                  onPress={() => setValue('role', 'employee')}
                  style={styles.roleButton}
                />
              </>
            )}
            {isMarketOwner && (
              <Button 
                title="Employee" 
                variant="primary"
                onPress={() => {}} 
                disabled={true}
                style={styles.roleButton}
              />
            )}
          </View>
        </View>

        {error && <ThemedText style={styles.errorText}>{error}</ThemedText>}

        <View style={styles.actions}>
          <Button
            title="Create User"
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
  roleContainer: {
    marginBottom: 16,
  },
  label: {
    marginBottom: 8,
  },
  roleButtons: {
    flexDirection: 'row',
    gap: 12,
  },
  roleButton: {
    flex: 1,
  },
  errorText: {
    color: '#d32f2f',
    marginBottom: 16,
    textAlign: 'center',
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
