import React from 'react';
import { StyleSheet, View, ScrollView } from 'react-native';
import { ThemedView } from '@/components/themed-view';
import { ThemedText } from '@/components/themed-text';
import { useGetMeQuery, useGetUsersQuery, useGetItemsQuery, useGetCategoriesQuery, useGetStockQuery, useGetDailyAccountsQuery } from '@/services/api';
import { Button } from '@/components/atoms/Button';
import { useRouter } from 'expo-router';
import { useThemeColor } from '@/hooks/use-theme-color';

export default function Dashboard() {
  const router = useRouter();
  const { data: user, isLoading: isUserLoading } = useGetMeQuery({});
  const backgroundColor = useThemeColor({}, 'background');
  
  const isAdmin = user?.role === 'admin';
  const isOwner = user?.role === 'market_owner';

  const { data: users, isLoading: isUsersLoading } = useGetUsersQuery({}, { skip: !isAdmin });
  const { data: items, isLoading: isItemsLoading } = useGetItemsQuery({}, { skip: !isAdmin });
  const { data: categories, isLoading: isCategoriesLoading } = useGetCategoriesQuery({}, { skip: !isAdmin });
  
  const { data: stock, isLoading: isStockLoading } = useGetStockQuery({}, { skip: !isOwner });
  const { data: dailyAccounts, isLoading: isDailyAccountsLoading } = useGetDailyAccountsQuery({}, { skip: !isOwner && !isAdmin });

  if (isUserLoading) {
    return (
      <ThemedView style={[styles.container, { backgroundColor, justifyContent: 'center', alignItems: 'center' }]}>
        <ThemedText>Loading profile...</ThemedText>
      </ThemedView>
    );
  }

  return (
    <ScrollView style={[styles.container, { backgroundColor }]} contentContainerStyle={styles.content}>
      <ThemedText type="title" style={styles.title}>Dashboard</ThemedText>
      <ThemedText type="subtitle" style={styles.subtitle}>Welcome, {user?.full_name}</ThemedText>
      <ThemedText style={styles.role}>Role: {user?.role?.replace('_', ' ')}</ThemedText>
      
      <Button 
        title="View My Profile" 
        variant="secondary"
        onPress={() => user?.id && router.push(`/users/${user.id}`)} 
        style={styles.profileButton}
      />

      {isAdmin && (
        <View style={styles.section}>
          <ThemedText type="subtitle">Admin Overview</ThemedText>
          <View style={styles.statsContainer}>
            <StatCard label="Users" value={users?.length} loading={isUsersLoading} />
            <StatCard label="Items" value={items?.length} loading={isItemsLoading} />
            <StatCard label="Categories" value={categories?.length} loading={isCategoriesLoading} />
          </View>
          
          <View style={styles.actionsContainer}>
            <Button 
              title="Manage Users" 
              onPress={() => router.push('/users')} 
              style={styles.actionButton}
            />
            <Button 
              title="Manage Items" 
              onPress={() => router.push('/items')} 
              style={styles.actionButton}
            />
            <Button 
              title="Manage Stock" 
              onPress={() => router.push('/stock')} 
              style={styles.actionButton}
            />
            <Button 
              title="Create New User" 
              variant="secondary"
              onPress={() => router.push('/register-user')} 
              style={styles.actionButton}
            />
          </View>
        </View>
      )}

      {isOwner && (
        <View style={styles.section}>
          <ThemedText type="subtitle">Market Overview</ThemedText>
          <View style={styles.statsContainer}>
            <StatCard label="Stock Items" value={stock?.length} loading={isStockLoading} />
            <StatCard label="Daily Accounts" value={dailyAccounts?.length} loading={isDailyAccountsLoading} />
          </View>
          
          <View style={styles.actionsContainer}>
            <Button 
              title="Manage Employees" 
              onPress={() => router.push('/users')} 
              style={styles.actionButton}
            />
            <Button 
              title="Manage Items" 
              onPress={() => router.push('/items')} 
              style={styles.actionButton}
            />
            <Button 
              title="Manage Stock" 
              onPress={() => router.push('/stock')} 
              style={styles.actionButton}
            />
            <Button 
              title="Create New Employee" 
              variant="secondary"
              onPress={() => router.push('/register-user')} 
              style={styles.actionButton}
            />
          </View>
        </View>
      )}
    </ScrollView>
  );
}

function StatCard({ label, value, loading }: { label: string, value?: number, loading: boolean }) {
  const cardBackground = useThemeColor({ light: '#fff', dark: '#333' }, 'background');
  
  return (
    <View style={[styles.card, { backgroundColor: cardBackground }]}>
      <ThemedText style={styles.cardLabel}>{label}</ThemedText>
      <ThemedText type="title" style={styles.cardValue}>
        {loading ? '...' : value ?? 0}
      </ThemedText>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    padding: 16,
    paddingTop: 60,
  },
  title: {
    marginBottom: 8,
  },
  subtitle: {
    marginBottom: 4,
    opacity: 0.8,
  },
  role: {
    marginBottom: 16,
    opacity: 0.6,
    textTransform: 'capitalize',
  },
  profileButton: {
    marginBottom: 24,
  },
  section: {
    marginBottom: 24,
  },
  statsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginTop: 12,
  },
  card: {
    width: '48%',
    padding: 16,
    borderRadius: 12,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  cardLabel: {
    fontSize: 14,
    opacity: 0.7,
  },
  cardValue: {
    fontSize: 24,
    marginTop: 8,
  },
  actionsContainer: {
    marginTop: 16,
    gap: 12,
  },
  actionButton: {
    // marginBottom: 8,
  }
});
