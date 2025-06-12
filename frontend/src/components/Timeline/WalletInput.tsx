import React from 'react';
import { Autocomplete, TextField } from '@mui/material';

export interface WalletSelectorProps {
  address: string;
  options: string[];
  onChange: (addr: string) => void;
}

const ETH_ADDRESS_REGEX = /^0x[a-fA-F0-9]{40}$/;

export const WalletSelector: React.FC<WalletSelectorProps> = ({
  address,
  options,
  onChange,
}) => {
  const [input, setInput] = React.useState(address);

  const isValid = ETH_ADDRESS_REGEX.test(input);

  React.useEffect(() => {
    setInput(address);
  }, [address]);

  const handleSelect = (value: string | null) => {
    const val = value ?? '';
    setInput(val);
    if (ETH_ADDRESS_REGEX.test(val)) {
      onChange(val);
    }
  };

  return (
    <Autocomplete
      freeSolo
      options={options}
      value={address}
      inputValue={input}
      onInputChange={(_, value) => handleSelect(value)}
      onChange={(_, value) => handleSelect(value as string | null)}
      renderInput={(params) => (
        <TextField
          {...params}
          label="Wallet Address"
          error={!!input && !isValid}
          helperText={!!input && !isValid ? 'Invalid Ethereum address' : ''}
          size="small"
        />
      )}
      sx={{ mb: 2 }}
    />
  );
}; 