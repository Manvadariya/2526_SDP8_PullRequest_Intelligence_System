import React, { useEffect, useState, useRef } from 'react';
import { useNavigate, useSearchParams, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function AuthCallback() {
  const [searchParams] = useSearchParams();
  const { handleCallback, handleBitbucketCallback } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [error, setError] = useState(null);
  const hasRunRef = useRef(false);

  // Determine provider from the URL path
  const isBitbucket = location.pathname.includes('/bitbucket/');

  useEffect(() => {
    if (hasRunRef.current) return;
    hasRunRef.current = true;

    const code = searchParams.get('code');
    if (!code) {
      setError('No authorization code received');
      return;
    }

    const callbackFn = isBitbucket ? handleBitbucketCallback : handleCallback;

    callbackFn(code)
      .then(() => navigate('/home', { replace: true }))
      .catch((err) => setError(err.message));
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const providerLabel = isBitbucket ? 'Bitbucket' : 'GitHub';

  if (error) {
    return (
      <div className="min-h-screen bg-[#0d1117] flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-semibold text-red-400 mb-4">Authentication Failed</h2>
          <p className="text-gray-400 mb-6">{error}</p>
          <a href="/login" className="text-blue-400 hover:underline">Try again</a>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0d1117] flex items-center justify-center">
      <div className="text-center">
        <div className="w-8 h-8 border-2 border-blue-400 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-gray-400">Signing in with {providerLabel}...</p>
      </div>
    </div>
  );
}
