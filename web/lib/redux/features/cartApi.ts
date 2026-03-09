import { api } from '../api';

export const cartApi = api.injectEndpoints({
  endpoints: (builder) => ({
    createCart: builder.mutation({
      query: () => ({
        url: '/carts',
        method: 'POST',
        body: {},
      }),
      invalidatesTags: ['Cart'],
    }),
    getCart: builder.query({
      query: (cartId) => `/carts/${cartId}`,
      providesTags: (result, error, cartId) => [{ type: 'Cart', id: cartId }],
    }),
    addCartItem: builder.mutation({
      query: ({ cartId, item_id, quantity }) => ({
        url: `/carts/${cartId}/items`,
        method: 'POST',
        body: { item_id, quantity },
      }),
      invalidatesTags: (result, error, { cartId }) => [{ type: 'Cart', id: cartId }],
    }),
    updateCartItem: builder.mutation({
      query: ({ cartId, cartItemId, quantity }) => ({
        url: `/carts/${cartId}/items/${cartItemId}`,
        method: 'PATCH',
        body: { quantity },
      }),
      invalidatesTags: (result, error, { cartId }) => [{ type: 'Cart', id: cartId }],
    }),
    clearCart: builder.mutation({
      query: (cartId) => ({
        url: `/carts/${cartId}/items`,
        method: 'DELETE',
      }),
      invalidatesTags: (result, error, cartId) => [{ type: 'Cart', id: cartId }],
    }),
    completeCart: builder.mutation({
      query: (cartId) => ({
        url: `/carts/${cartId}/complete`,
        method: 'POST',
      }),
      invalidatesTags: ['Cart'],
    }),
    deleteCart: builder.mutation({
      query: (cartId) => ({
        url: `/carts/${cartId}/delete`,
        method: 'POST',
      }),
      invalidatesTags: ['Cart'],
    }),
  }),
});

export const {
  useCreateCartMutation,
  useGetCartQuery,
  useAddCartItemMutation,
  useUpdateCartItemMutation,
  useClearCartMutation,
  useCompleteCartMutation,
  useDeleteCartMutation,
} = cartApi;
