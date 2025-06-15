import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Home } from './pages/Home/Home';
import PerformanceTimeline from './pages/PerformanceTimeline';

const Nav: React.FC = () => (
  <nav style={{ padding: '1rem', background: '#222' }}>
    <Link to="/" style={{ color: '#fff', marginRight: '1rem' }}>
      Home
    </Link>
    <Link to="/timeline" style={{ color: '#fff' }}>
      Timeline
    </Link>
  </nav>
);

function App() {
  return (
    <Router>
      <Nav />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/timeline" element={<PerformanceTimeline />} />
      </Routes>
    </Router>
  );
}

export default App;
