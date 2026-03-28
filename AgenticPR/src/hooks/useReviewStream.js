/**
 * useReviewStream — SSE-based realtime review status updates.
 *
 * Connects to the SSE endpoint for a specific job and provides
 * live stage-by-stage progress updates. Falls back gracefully
 * when SSE is not available.
 *
 * Usage:
 *   const { status, stage, isLive, error } = useReviewStream(jobId);
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { API_BASE } from '../config';


/** All possible job statuses from the backend */
export const JOB_STATUSES = {
  QUEUED: 'queued',
  PROCESSING: 'processing',
  FETCHING: 'fetching',
  ANALYZING: 'analyzing',
  REVIEWING: 'reviewing',
  PUBLISHING: 'publishing',
  COMPLETED: 'completed',
  FAILED: 'failed',
  SUPERSEDED: 'superseded',
  CANCELED: 'canceled',
};

/** Check if a status is terminal (no more updates expected) */
export const isTerminalStatus = (status) =>
  ['completed', 'failed', 'superseded', 'canceled'].includes(status);

/** Check if a status is active (review in progress) */
export const isActiveStatus = (status) =>
  ['queued', 'processing', 'fetching', 'analyzing', 'reviewing', 'publishing'].includes(status);


/**
 * Human-friendly status labels and icons for the UI.
 */
export const STATUS_CONFIG = {
  queued:      { label: 'Review queued',               icon: '⏳',  color: 'text-yellow-400', bg: 'bg-yellow-900/30' },
  processing:  { label: 'Processing...',               icon: '⚙️',  color: 'text-blue-400',   bg: 'bg-blue-900/30' },
  fetching:    { label: 'Cloning repository...',       icon: '📥',  color: 'text-blue-400',   bg: 'bg-blue-900/30' },
  analyzing:   { label: 'Running static analysis...', icon: '🔍',  color: 'text-purple-400', bg: 'bg-purple-900/30' },
  reviewing:   { label: 'AI review in progress...',   icon: '🤖',  color: 'text-cyan-400',   bg: 'bg-cyan-900/30' },
  publishing:  { label: 'Publishing to GitHub...',    icon: '📤',  color: 'text-green-400',  bg: 'bg-green-900/30' },
  completed:   { label: 'Review complete',             icon: '✅',  color: 'text-green-400',  bg: 'bg-green-900/30' },
  failed:      { label: 'Review failed',               icon: '❌',  color: 'text-red-400',    bg: 'bg-red-900/30' },
  superseded:  { label: 'Superseded by newer commit',  icon: '🔄',  color: 'text-gray-400',   bg: 'bg-gray-900/30' },
  canceled:    { label: 'Review canceled',             icon: '🚫',  color: 'text-gray-400',   bg: 'bg-gray-900/30' },
};


/**
 * Hook that connects to SSE for realtime review updates.
 * Automatically invalidates TanStack Query caches when review completes.
 */
export function useReviewStream(jobId) {
  const [status, setStatus] = useState(null);
  const [stage, setStage] = useState(null);
  const [isLive, setIsLive] = useState(false);
  const [error, setError] = useState(null);
  const [events, setEvents] = useState([]);
  const eventSourceRef = useRef(null);
  const queryClient = useQueryClient();

  const connect = useCallback(() => {
    if (!jobId) return;
    
    // Don't connect if we already know it's terminal
    if (status && isTerminalStatus(status)) return;
    
    try {
      const url = `${API_BASE}/api/reviews/${jobId}/events`;
      const source = new EventSource(url);
      eventSourceRef.current = source;
      
      source.onopen = () => {
        setIsLive(true);
        setError(null);
      };
      
      source.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          setStatus(data.status);
          setStage(data.current_stage || data.stage);
          setEvents(prev => [...prev.slice(-20), data]); // Keep last 20 events
          
          // Invalidate relevant caches on terminal states
          if (isTerminalStatus(data.status)) {
            queryClient.invalidateQueries({ queryKey: ['jobs'] });
            queryClient.invalidateQueries({ queryKey: ['review-data'] });
            queryClient.invalidateQueries({ queryKey: ['job', jobId] });
            
            // Close the connection
            source.close();
            setIsLive(false);
          }
        } catch (e) {
          // Ignore parse errors (heartbeats, etc.)
        }
      };
      
      source.onerror = (e) => {
        setIsLive(false);
        setError('SSE connection lost');
        source.close();
        
        // Retry after 5 seconds if not terminal
        if (!isTerminalStatus(status)) {
          setTimeout(connect, 5000);
        }
      };
    } catch (e) {
      setError('SSE not supported');
    }
  }, [jobId, status, queryClient]);

  useEffect(() => {
    connect();
    
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        setIsLive(false);
      }
    };
  }, [jobId]); // Only reconnect when jobId changes

  return {
    status,
    stage,
    isLive,
    error,
    events,
    statusConfig: status ? STATUS_CONFIG[status] : null,
  };
}


/**
 * Hook to fetch queue status (for admin/monitoring views).
 */
export function useQueueStatus() {
  const [data, setData] = useState(null);
  
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/queue/status`);
        if (res.ok) {
          setData(await res.json());
        }
      } catch (e) {
        // Silent fail — monitoring is optional
      }
    };
    
    fetchStatus();
    const interval = setInterval(fetchStatus, 10000); // Every 10s
    return () => clearInterval(interval);
  }, []);
  
  return data;
}


export default useReviewStream;
