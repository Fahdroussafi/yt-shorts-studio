import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { RefreshCw } from 'lucide-react';
import { AppProvider, useApp } from './context/AppContext';
import Layout from './components/Layout';
import LoginPage from './pages/LoginPage';
import OverviewPage from './pages/OverviewPage';
import VaultPage from './pages/VaultPage';
import IdeasPage from './pages/IdeasPage';
import StudioPage from './pages/StudioPage';
import DispatcherPage from './pages/DispatcherPage';

function ProtectedRoute({ children }) {
  const { authToken, authChecking } = useApp();

  if (authChecking) {
    return (
      <div className="min-h-screen bg-[#09090e] flex items-center justify-center text-slate-400 font-sans">
        <div className="flex flex-col items-center gap-3">
          <RefreshCw className="w-8 h-8 animate-spin text-violet-500" />
          <p className="text-xs font-mono tracking-widest uppercase">Connecting to Studio Core...</p>
        </div>
      </div>
    );
  }

  if (!authToken) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

export default function App() {
  return (
    <AppProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
            <Route path="/" element={<Navigate to="/overview" replace />} />
            <Route path="/overview" element={<OverviewPage />} />
            <Route path="/vault" element={<VaultPage />} />
            <Route path="/ideas" element={<IdeasPage />} />
            <Route path="/studio" element={<StudioPage />} />
            <Route path="/dispatcher" element={<DispatcherPage />} />
            <Route path="*" element={<Navigate to="/overview" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AppProvider>
  );
}
