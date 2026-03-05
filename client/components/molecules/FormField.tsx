import React from 'react';
import { StyleSheet, View } from 'react-native';
import { ThemedText } from '@/components/themed-text';
import { Input, InputProps } from '@/components/atoms/Input';

type FormFieldProps = InputProps & {
  label: string;
  error?: string;
};

export function FormField({ label, error, style, ...rest }: FormFieldProps) {
  return (
    <View style={[styles.container, style]}>
      <ThemedText type="defaultSemiBold" style={styles.label}>
        {label}
      </ThemedText>
      <Input
        style={[error ? styles.inputError : undefined]}
        {...rest}
      />
      {error && <ThemedText style={styles.errorText}>{error}</ThemedText>}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    width: '100%',
    marginBottom: 16,
  },
  label: {
    marginBottom: 8,
  },
  inputError: {
    borderColor: '#d32f2f',
  },
  errorText: {
    color: '#d32f2f',
    fontSize: 12,
    marginTop: 4,
  },
});
