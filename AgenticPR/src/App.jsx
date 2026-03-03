import './index.css';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';

// Public pages
import Landing from './pages/Landing';
import Login from './pages/Login';
import Signup from './pages/Signup';
import AuthCallback from './pages/AuthCallback';

// App layout + protected pages
import AppLayout from './components/AppLayout';
import RepoLayout from './components/RepoLayout';
import Home from './pages/Home';
import Repositories from './pages/Repositories';
import PRVisualize from './pages/PRVisualize';
import Reports from './pages/Reports';
import Members from './pages/Members';
import Settings from './pages/Settings';
import ScanDetail from './pages/ScanDetail';
import Issues from './pages/Issues';
import Overview from './pages/Overview';
import PRDetail from './pages/PRDetail';
import History from './pages/History';
import Metrics from './pages/Metrics';

function App() {
  return (
    <AuthProvider>
      <Routes>
        {/* Public routes */}
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/auth/callback" element={<AuthCallback />} />
        <Route path="/auth/bitbucket/callback" element={<AuthCallback />} />

        {/* App routes — protected by auth + AppLayout */}
        <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
          {/* Global Dashboard */}
          <Route path="/home" element={<Home />} />
          <Route path="/repositories" element={<Repositories />} />
          <Route path="/reports" element={<Reports />} />
          
          {/* Nested Repository Layout */}
          <Route path="/repositories/:repoName" element={<RepoLayout />}>
             <Route index element={<Navigate to="overview" replace />} />
             <Route path="overview" element={<Overview />} />
             <Route path="issues" element={<Issues />} />
             <Route path="metrics" element={<Metrics />} />
             <Route path="reports" element={<Reports />} />
             <Route path="pull-requests" element={<History />} />
             <Route path="settings" element={<Settings />} />
          </Route>

          <Route path="/pr" element={<PRVisualize />} />
          <Route path="/members" element={<Members />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/scan" element={<ScanDetail />} />
          <Route path="/scan/:id" element={<ScanDetail />} />
          <Route path="/repositories/:repoName/pr/:prId" element={<PRDetail />} />
        </Route>

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}

export default App;
