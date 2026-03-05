import React from 'react';
import { StyleSheet, View, FlatList, TouchableOpacity } from 'react-native';
import { useRouter } from 'expo-router';
import { ThemedView } from '@/components/themed-view';
import { ThemedText } from '@/components/themed-text';
import { useGetUsersQuery, useGetMeQuery } from '@/services/api';
import { useThemeColor } from '@/hooks/use-theme-color';

export default function UsersListScreen() {
  const router = useRouter();
  const backgroundColor = useThemeColor({}, 'background');
  const cardBackground = useThemeColor({ light: '#fff', dark: '#333' }, 'background');
  
  const { data: user } = useGetMeQuery({});
  const { data: users, isLoading } = useGetUsersQuery({});

  const renderItem = ({ item }: { item: any }) => (
    <TouchableOpacity 
      style={[styles.card, { backgroundColor: cardBackground }]}
      onPress={() => router.push(`/users/${item.id}`)}
    >
      <View style={styles.cardHeader}>
        <ThemedText type="defaultSemiBold">{item.full_name}</ThemedText>
        <ThemedText style={styles.roleBadge}>{item.role}</ThemedText>
      </View>
      <ThemedText style={styles.email}>{item.email}</ThemedText>
      <ThemedText style={styles.username}>@{item.username}</ThemedText>
    </TouchableOpacity>
  );

  return (
    <ThemedView style={[styles.container, { backgroundColor }]}>
      <ThemedText type="title" style={styles.title}>
        {user?.role === 'admin' ? 'All Users' : 'Employees'}
      </ThemedText>
      
      {isLoading ? (
        <ThemedText>Loading...</ThemedText>
      ) : (
        <FlatList
          data={users}
          renderItem={renderItem}
          keyExtractor={(item) => item.id.toString()}
          contentContainerStyle={styles.listContent}
          ListEmptyComponent={<ThemedText>No users found.</ThemedText>}
        />
      )}
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
    paddingTop: 60,
  },
  title: {
    marginBottom: 16,
  },
  listContent: {
    gap: 12,
    paddingBottom: 20,
  },
  card: {
    padding: 16,
    borderRadius: 12,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  roleBadge: {
    fontSize: 12,
    opacity: 0.6,
    textTransform: 'uppercase',
  },
  email: {
    opacity: 0.8,
    marginBottom: 2,
  },
  username: {
    fontSize: 12,
    opacity: 0.5,
  }
});
