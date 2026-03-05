import React from 'react';
import { TextInput, StyleSheet, TextInputProps } from 'react-native';
import { useThemeColor } from '@/hooks/use-theme-color';

export type InputProps = TextInputProps & {
  lightColor?: string;
  darkColor?: string;
};

export function Input({ style, lightColor, darkColor, ...rest }: InputProps) {
  const color = useThemeColor({ light: lightColor, dark: darkColor }, 'text');
  const borderColor = useThemeColor({ light: '#ccc', dark: '#555' }, 'icon');

  return (
    <TextInput
      style={[{ color, borderColor }, styles.input, style]}
      placeholderTextColor="#888"
      {...rest}
    />
  );
}

const styles = StyleSheet.create({
  input: {
    height: 48,
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 12,
    fontSize: 16,
    width: '100%',
  },
});
