import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import { RootState } from '../store';
import { setCredentials, logout, updateToken } from '../store/slices/authSlice';
import * as SecureStore from 'expo-secure-store';
import { Mutex } from 'async-mutex';
import Constants from 'expo-constants';
import { Platform } from 'react-native';

// Create a mutex for handling concurrent refresh token requests
const mutex = new Mutex();

const getBaseUrl = () => {
  if (process.env.EXPO_PUBLIC_API_URL) {
    return process.env.EXPO_PUBLIC_API_URL;
  }

  const hostUri = Constants.expoConfig?.hostUri ?? (Constants as any).manifest?.hostUri;
  if (hostUri) {
    const host = hostUri.split(':')[0];
    return `http://${host}:8000/api/v1`;
  }

  if (Platform.OS === 'android') {
    return 'http://10.0.2.2:8000/api/v1';
  }

  return 'http://localhost:8000/api/v1';
};

const BASE_URL = getBaseUrl();
console.log(`[API] Base URL: ${BASE_URL}`);

const baseQuery = fetchBaseQuery({
  baseUrl: BASE_URL,
  prepareHeaders: (headers, { getState }) => {
    const token = (getState() as RootState).auth.token;
    if (token) {
      headers.set('authorization', `Bearer ${token}`);
    }
    return headers;
  },
});

const baseQueryWithReauth = async (args: any, api: any, extraOptions: any) => {
  // wait until the mutex is available without locking it
  await mutex.waitForUnlock();
  let result = await baseQuery(args, api, extraOptions);

  if (result.error && result.error.status === 401) {
    // checking whether the mutex is locked
    if (!mutex.isLocked()) {
      const release = await mutex.acquire();
      try {
        const refreshToken = (api.getState() as RootState).auth.refreshToken;
        
        if (refreshToken) {
          const refreshResult = await baseQuery(
            {
              url: '/auth/refresh',
              method: 'POST',
              body: { refresh_token: refreshToken },
            },
            api,
            extraOptions
          );

          if (refreshResult.data) {
            const { access_token } = refreshResult.data as any;
            
            // Store the new token
            api.dispatch(updateToken({ token: access_token }));
            await SecureStore.setItemAsync('token', access_token);
            
            // Retry the initial query
            result = await baseQuery(args, api, extraOptions);
          } else {
            api.dispatch(logout());
            await SecureStore.deleteItemAsync('token');
            await SecureStore.deleteItemAsync('refreshToken');
          }
        } else {
          api.dispatch(logout());
          await SecureStore.deleteItemAsync('token');
          await SecureStore.deleteItemAsync('refreshToken');
        }
      } finally {
        // release must be called once the mutex should be released again.
        release();
      }
    } else {
      // wait until the mutex is available without locking it
      await mutex.waitForUnlock();
      result = await baseQuery(args, api, extraOptions);
    }
  }
  return result;
};

export const api = createApi({
  reducerPath: 'api',
  baseQuery: baseQueryWithReauth,
  tagTypes: ['Stock', 'Items', 'Categories'],
  endpoints: (builder) => ({
    login: builder.mutation({
      query: (credentials) => {
        const formData = new FormData();
        formData.append('username', credentials.username);
        formData.append('password', credentials.password);
        return {
          url: '/auth/login',
          method: 'POST',
          body: formData,
        };
      },
    }),
    getMe: builder.query({
      query: () => '/auth/me',
    }),
    getUsers: builder.query({
      query: () => '/users',
    }),
    getUser: builder.query({
      query: (id) => `/users/${id}`,
    }),
    getItems: builder.query({
      query: (categoryId) => {
        if (categoryId) return `/items?category_id=${categoryId}`;
        return '/items';
      },
      providesTags: ['Items'],
    }),
    addItem: builder.mutation({
      query: (itemData) => ({
        url: '/items',
        method: 'POST',
        body: itemData,
      }),
      invalidatesTags: ['Items'],
    }),
    updateItem: builder.mutation({
      query: ({ id, ...data }) => ({
        url: `/items/${id}`,
        method: 'PATCH',
        body: data,
      }),
      invalidatesTags: ['Items'],
    }),
    deleteItem: builder.mutation({
      query: (id) => ({
        url: `/items/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['Items'],
    }),
    getCategories: builder.query({
      query: () => '/categories',
      providesTags: ['Categories'],
    }),
    getStock: builder.query({
      query: () => '/stock',
      providesTags: ['Stock'],
    }),
    addStock: builder.mutation({
      query: (stockData) => ({
        url: '/stock',
        method: 'POST',
        body: stockData,
      }),
      invalidatesTags: ['Stock'],
    }),
    updateStock: builder.mutation({
      query: ({ id, ...data }) => ({
        url: `/stock/${id}`,
        method: 'PATCH',
        body: data,
      }),
      invalidatesTags: ['Stock'],
    }),
    deleteStock: builder.mutation({
      query: (id) => ({
        url: `/stock/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['Stock'],
    }),
    getDailyAccounts: builder.query({
      query: () => '/daily-accounts',
    }),
    registerUser: builder.mutation({
      query: (userData) => ({
        url: '/users/register',
        method: 'POST',
        body: userData,
      }),
    }),
  }),
});

export const {
  useLoginMutation,
  useGetMeQuery,
  useGetUsersQuery,
  useGetUserQuery,
  useGetItemsQuery,
  useAddItemMutation,
  useUpdateItemMutation,
  useDeleteItemMutation,
  useGetCategoriesQuery,
  useGetStockQuery,
  useAddStockMutation,
  useUpdateStockMutation,
  useDeleteStockMutation,
  useGetDailyAccountsQuery,
  useRegisterUserMutation,
} = api;
