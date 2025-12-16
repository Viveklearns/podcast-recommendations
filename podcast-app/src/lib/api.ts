/**
 * API Client for Backend Communication
 *
 * This module provides functions to communicate with the FastAPI backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Generic fetch wrapper with error handling
 */
async function apiFetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`Failed to fetch ${endpoint}:`, error);
    throw error;
  }
}

/**
 * Fetch all recommendations with optional filters
 */
export async function getRecommendations(params?: {
  type?: string;
  podcast_id?: string;
  limit?: number;
  offset?: number;
}) {
  const searchParams = new URLSearchParams();
  if (params?.type) searchParams.append('type', params.type);
  if (params?.podcast_id) searchParams.append('podcast_id', params.podcast_id);
  if (params?.limit) searchParams.append('limit', params.limit.toString());
  if (params?.offset) searchParams.append('offset', params.offset.toString());

  const queryString = searchParams.toString();
  const endpoint = `/api/recommendations${queryString ? `?${queryString}` : ''}`;

  return apiFetch<any[]>(endpoint);
}

/**
 * Fetch a single recommendation by ID
 */
export async function getRecommendationById(id: string) {
  return apiFetch<any>(`/api/recommendations/${id}`);
}

/**
 * Fetch all podcasts
 */
export async function getPodcasts() {
  return apiFetch<any[]>('/api/podcasts');
}

/**
 * Fetch a single podcast by ID
 */
export async function getPodcastById(id: string) {
  return apiFetch<any>(`/api/podcasts/${id}`);
}

/**
 * Fetch all episodes with optional podcast filter
 */
export async function getEpisodes(params?: {
  podcast_id?: string;
  limit?: number;
  offset?: number;
}) {
  const searchParams = new URLSearchParams();
  if (params?.podcast_id) searchParams.append('podcast_id', params.podcast_id);
  if (params?.limit) searchParams.append('limit', params.limit.toString());
  if (params?.offset) searchParams.append('offset', params.offset.toString());

  const queryString = searchParams.toString();
  const endpoint = `/api/episodes${queryString ? `?${queryString}` : ''}`;

  return apiFetch<any[]>(endpoint);
}

/**
 * Search recommendations
 */
export async function searchRecommendations(query: string) {
  const searchParams = new URLSearchParams({ q: query });
  return apiFetch<any[]>(`/api/search?${searchParams.toString()}`);
}

/**
 * Get statistics
 */
export async function getStats() {
  return apiFetch<{
    total_podcasts: number;
    total_episodes: number;
    total_recommendations: number;
    recommendations_by_type: Record<string, number>;
  }>('/api/stats');
}

/**
 * Check if backend API is available
 */
export async function checkApiHealth(): Promise<boolean> {
  try {
    await fetch(`${API_BASE_URL}/api/stats`);
    return true;
  } catch {
    return false;
  }
}
