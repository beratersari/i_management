import React from 'react';
import { StyleSheet, View, ScrollView } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { ThemedView } from '@/components/themed-view';
import { ThemedText } from '@/components/themed-text';
import { useGetUserQuery, useGetMeQuery } from '@/services/api';
import { useThemeColor } from '@/hooks/use-theme-color';
import { Button } from '@/components/atoms/Button';

export default function UserDetailsScreen() {
  const { id } = useLocalSearchParams();
  const router = useRouter();
  const backgroundColor = useThemeColor({}, 'background');
  
  const { data: user, isLoading, error } = useGetUserQuery(id);
  const { data: currentUser } = useGetMeQuery({});

  if (isLoading) {
    return (
      <ThemedView style={[styles.container, { backgroundColor, justifyContent: 'center', alignItems: 'center' }]}>
        <ThemedText>Loading user details...</ThemedText>
      </ThemedView>
    );
  }

  if (error || !user) {
    return (
      <ThemedView style={[styles.container, { backgroundColor, justifyContent: 'center', alignItems: 'center' }]}>
        <ThemedText>User not found or access denied.</ThemedText>
        <Button title="Go Back" onPress={() => router.back()} style={styles.backButton} />
      </ThemedView>
    );
  }

  return (
    <ThemedView style={[styles.container, { backgroundColor }]}>
      <ScrollView contentContainerStyle={styles.content}>
        <ThemedText type="title" style={styles.title}>{user.full_name}</ThemedText>
        
        <View style={styles.section}>
          <ThemedText type="subtitle" style={styles.sectionTitle}>Profile Information</ThemedText>
          
          <DetailRow label="Username" value={user.username} />
          <DetailRow label="Email" value={user.email} />
          <DetailRow label="Role" value={user.role} />
          <DetailRow label="Status" value={user.is_active ? 'Active' : 'Inactive'} />
        </View>

        <Button 
          title="Back to List" 
          variant="secondary" 
          onPress={() => router.back()} 
          style={styles.backButton}
        />
      </ScrollView>
    </ThemedView>
  );
}

function DetailRow({ label, value }: { label: string, value: string | boolean }) {
  return (
    <View style={styles.row}>
      <ThemedText style={styles.label}>{label}</ThemedText>
      <ThemedText style={styles.value}>{value}</ThemedText>
    </View>
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
  section: {
    marginBottom: 24,
    backgroundColor: 'rgba(0,0,0,0.05)',
    padding: 16,
    borderRadius: 12,
  },
  sectionTitle: {
    marginBottom: 16,
  },
  row: {
    marginBottom: 12,
  },
  label: {
    fontSize: 12,
    opacity: 0.6,
    textTransform: 'uppercase',
    marginBottom: 4,
  },
  value: {
    fontSize: 16,
  },
  backButton: {
    marginTop: 12,
  }
});
