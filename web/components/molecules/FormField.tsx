import { Input } from '../atoms/Input';
import { Select } from '../atoms/Select';

interface FormFieldProps {
  type: 'text' | 'password' | 'email' | 'select' | 'number';
  label: string;
  name: string;
  value: string | number;
  onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => void;
  error?: string;
  options?: { label: string; value: string }[];
  placeholder?: string;
}

export const FormField = ({ type, label, name, value, onChange, error, options, placeholder }: FormFieldProps) => {
  if (type === 'select' && options) {
    return (
      <Select
        label={label}
        name={name}
        value={value}
        onChange={onChange}
        error={error}
        options={options}
      />
    );
  }

  return (
    <Input
      type={type}
      label={label}
      name={name}
      value={value}
      onChange={onChange}
      error={error}
      placeholder={placeholder}
    />
  );
};
