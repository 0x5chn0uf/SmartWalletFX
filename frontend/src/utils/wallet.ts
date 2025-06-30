export const isValidAddress = (value: string): boolean => {
  if (!value) return false;
  const regex = /^(0x[a-fA-F0-9]{40}|[a-z0-9-]+\.eth)$/;
  return regex.test(value.trim());
};
