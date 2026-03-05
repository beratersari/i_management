import React, { useState } from 'react';
import { View, StyleSheet } from 'react-native';
import { FormField } from '@/components/molecules/FormField';
import { Button } from '@/components/atoms/Button';
import { ThemedText } from '@/components/themed-text';

type LoginFormProps = {
  onSubmit: (data: any) => void;
  isLoading: boolean;
  error?: string;
};

export function LoginForm({ onSubmit, isLoading, error }: LoginFormProps) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = () => {
    onSubmit({ username, password });
  };

  return (
    <View style={styles.container}>
      <FormField
        label="Username"
        value={username}
        onChangeText={setUsername}
        placeholder="Enter your username"
        autoCapitalize="none"
      />
      <FormField
        label="Password"
        value={password}
        onChangeText={setPassword}
        placeholder="Enter your password"
        secureTextEntry
      />
      {error && (
        <ThemedText style={styles.errorText}>{error}</ThemedText>
      )}
      <Button
        title="Login"
        onPress={handleSubmit}
        loading={isLoading}
        disabled={isLoading || !username || !password}
        style={styles.button}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    width: '100%',
  },
  button: {
    marginTop: 16,
  },
  errorText: {
    color: '#d32f2f',
    marginBottom: 16,
    textAlign: 'center',
  },
});
