import { api } from '../api';

export const itemApi = api.injectEndpoints({
  endpoints: (builder) => ({
    getItems: builder.query<any[], number | undefined | void>({
      query: (categoryId?: number) => ({
        url: '/items',
        params: categoryId ? { category_id: categoryId } : undefined,
      }),
      providesTags: ['Item'],
    }),
    getItem: builder.query<any, number>({
      query: (id) => `/items/${id}`,
      providesTags: (result, error, id) => [{ type: 'Item', id }],
    }),
    createItem: builder.mutation({
      query: (data) => ({
        url: '/items',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['Item'],
    }),
    updateItem: builder.mutation({
      query: ({ id, ...data }) => ({
        url: `/items/${id}`,
        method: 'PATCH',
        body: data,
      }),
      invalidatesTags: (result, error, { id }) => [{ type: 'Item', id }, 'Item'],
    }),
    deleteItem: builder.mutation({
      query: (id) => ({
        url: `/items/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['Item'],
    }),
  }),
});

export const { useGetItemsQuery, useGetItemQuery, useCreateItemMutation, useUpdateItemMutation, useDeleteItemMutation } = itemApi;
