import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { AppBar, Toolbar, Typography, Box } from '@mui/material';
import { Home } from './pages/Home/Home';
import PerformanceTimeline from './pages/PerformanceTimeline';
import { ColorModeToggle } from './components/ColorModeToggle/ColorModeToggle';

function App() {
  return (
    <Router>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div">
            SmartWalletFX
          </Typography>
          <Box sx={{ flexGrow: 1, ml: 2 }}>
            <Link to="/" style={{ color: 'inherit', textDecoration: 'none', marginRight: '1rem' }}>
              Home
            </Link>
            <Link to="/timeline" style={{ color: 'inherit', textDecoration: 'none' }}>
              Timeline
            </Link>
          </Box>
          <ColorModeToggle />
        </Toolbar>
      </AppBar>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/timeline" element={<PerformanceTimeline />} />
      </Routes>
    </Router>
  );
}

export default App;
