import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from './layouts/MainLayout';
import AdminLayout from './layouts/AdminLayout';
import Home from './pages/Home';
import VerifyNotice from './pages/VerifyNotice';
import HowItWorks from './pages/HowItWorks';
import About from './pages/About';
import AdminLogin from './pages/AdminLogin';
import AdminDashboard from './pages/AdminDashboard';

function App() {
  return (
    <Routes>
      {/* Public Pages with Main Layout */}
      <Route path="/" element={<MainLayout />}>
        <Route index element={<Home />} />
        <Route path="verify" element={<VerifyNotice />} />
        <Route path="how-it-works" element={<HowItWorks />} />
        <Route path="about" element={<About />} />
      </Route>

      {/* Admin Authentication (Standalone layout) */}
      <Route path="/admin/login" element={<AdminLogin />} />

      {/* Admin Portal with Protected/Dedicated Admin Layout */}
      <Route path="/admin" element={<AdminLayout />}>
        <Route index element={<Navigate to="/admin/dashboard" replace />} />
        <Route path="dashboard" element={<AdminDashboard />} />
      </Route>

      {/* Fallback 404 Route */}
      <Route
        path="*"
        element={
          <div className="min-h-screen flex flex-col items-center justify-center bg-midnight-950 text-white p-6 text-center">
            <h1 className="text-6xl font-black text-cyan-400 font-mono mb-2">404</h1>
            <h2 className="text-xl font-bold mb-4">Cryptographic Record Not Found</h2>
            <p className="text-sm text-slate-400 max-w-md mb-6">
              The requested verification route does not exist or has been moved.
            </p>
            <a
              href="/"
              className="px-6 py-2.5 rounded-lg bg-cyan-500 text-midnight-950 font-bold text-xs uppercase tracking-wider"
            >
              Return to Homepage
            </a>
          </div>
        }
      />
    </Routes>
  );
}

export default App;

