/* eslint-disable prettier/prettier */
import React, { createContext, ReactNode, useMemo, useState } from 'react';
import { ThemeProvider as MuiThemeProvider, CssBaseline } from '@mui/material';
import { createAppTheme } from '../theme';

interface ColorModeContextValue {
  mode: 'light' | 'dark';
  toggleColorMode: () => void;
}

export const ColorModeContext = createContext<ColorModeContextValue>({
  mode: 'dark',
  // eslint-disable-next-line @typescript-eslint/no-empty-function
  toggleColorMode: () => {},
});

interface Props {
  children: ReactNode;
}

export const ThemeProvider: React.FC<Props> = ({ children }) => {
  const [mode, setMode] = useState<'light' | 'dark'>('dark');

  const colorMode = useMemo<ColorModeContextValue>(
    () => ({
      mode,
      toggleColorMode: () => setMode(prev => (prev === 'light' ? 'dark' : 'light')),
    }),
    [mode]
  );

  const theme = useMemo(() => createAppTheme(mode), [mode]);

  return (
    <ColorModeContext.Provider value={colorMode}>
      <MuiThemeProvider theme={theme}>
        <CssBaseline />
        {children}
      </MuiThemeProvider>
    </ColorModeContext.Provider>
  );
};
