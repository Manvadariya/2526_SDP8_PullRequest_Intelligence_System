/**
 * Centralized API configuration.
 * Uses VITE_API_URL env var if set, otherwise defaults to localhost:8000.
 */
export const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
