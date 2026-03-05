import React, { useState } from 'react';
import { useRouter } from 'expo-router';
import { useDispatch } from 'react-redux';
import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';
import { LoginTemplate } from '@/components/templates/LoginTemplate';
import { useLoginMutation } from '@/services/api';
import { setCredentials } from '@/store/slices/authSlice';

export default function LoginScreen() {
  const router = useRouter();
  const dispatch = useDispatch();
  const [login, { isLoading }] = useLoginMutation();
  const [error, setError] = useState<string | undefined>();

  const handleLogin = async (data: any) => {
    try {
      setError(undefined);
      const result = await login(data).unwrap();

      if (!result?.access_token || !result?.refresh_token) {
        throw new Error('Missing tokens in response');
      }

      // Save tokens to SecureStore (fallback for web)
      if (Platform.OS === 'web') {
        localStorage.setItem('token', result.access_token);
        localStorage.setItem('refreshToken', result.refresh_token);
      } else {
        await SecureStore.setItemAsync('token', result.access_token);
        await SecureStore.setItemAsync('refreshToken', result.refresh_token);
      }

      dispatch(
        setCredentials({
          user: null, // We'll fetch the user profile later or update the backend to return it
          token: result.access_token,
          refreshToken: result.refresh_token,
        })
      );
      router.replace('/(tabs)');
    } catch (err: any) {
      console.error('Login failed:', err);
      const errorMessage = err?.data?.detail || err?.message || 'Login failed. Please check your credentials.';
      setError(errorMessage);
    }
  };

  return <LoginTemplate onSubmit={handleLogin} isLoading={isLoading} error={error} />;
}
