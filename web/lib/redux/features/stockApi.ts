import { api } from '../api';

export const stockApi = api.injectEndpoints({
  endpoints: (builder) => ({
    getStock: builder.query<any[], void>({
      query: () => '/stock',
      providesTags: ['Stock'],
    }),
    getStockByCategory: builder.query<any[], void>({
      query: () => '/stock/by-category',
      providesTags: ['Stock'],
    }),
    getStockEntry: builder.query<any, number>({
      query: (itemId) => `/stock/${itemId}`,
      providesTags: (result, error, itemId) => [{ type: 'Stock', id: itemId }],
    }),
    addToStock: builder.mutation({
      query: (data) => ({
        url: '/stock',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['Stock'],
    }),
    updateStock: builder.mutation({
      query: ({ itemId, quantity }) => ({
        url: `/stock/${itemId}`,
        method: 'PATCH',
        body: { quantity },
      }),
      invalidatesTags: (result, error, { itemId }) => [{ type: 'Stock', id: itemId }, 'Stock'],
    }),
    removeFromStock: builder.mutation({
      query: (itemId) => ({
        url: `/stock/${itemId}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['Stock'],
    }),
  }),
});

export const {
  useGetStockQuery,
  useGetStockByCategoryQuery,
  useGetStockEntryQuery,
  useAddToStockMutation,
  useUpdateStockMutation,
  useRemoveFromStockMutation,
} = stockApi;
