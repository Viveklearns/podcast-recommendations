'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

interface RecommendationData {
  id: string;
  type: string;
  title: string;
  recommendedBy: string;
  episodeId: string;
  episodeTitle?: string;
  podcastName?: string;
  podcastId?: string;
  youtubeUrl?: string;
  recommendationContext?: string;
  quoteFromEpisode?: string;
  confidenceScore?: number;
  timestampSeconds?: number;
  metadata?: any;
  // Book-specific fields
  author?: string;
  amazonUrl?: string;
  isbn?: string;
  coverImageUrl?: string;
}

export default function DataPage() {
  const [recommendations, setRecommendations] = useState<RecommendationData[]>([]);
  const [episodes, setEpisodes] = useState<any[]>([]);
  const [podcasts, setPodcasts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState('book');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    async function fetchAllData() {
      try {
        // Fetch all data in parallel
        const [recsRes, epsRes, podsRes] = await Promise.all([
          fetch('http://localhost:8000/api/recommendations?limit=5000'),
          fetch('http://localhost:8000/api/episodes?limit=500'),
          fetch('http://localhost:8000/api/podcasts')
        ]);

        const recsData = await recsRes.json();
        const epsData = await epsRes.json();
        const podsData = await podsRes.json();

        setRecommendations(recsData);
        setEpisodes(epsData);
        setPodcasts(podsData);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching data:', error);
        setLoading(false);
      }
    }

    fetchAllData();
  }, []);

  // Enrich recommendations with episode and podcast data
  const enrichedData = recommendations.map(rec => {
    const episode = episodes.find(ep => ep.id === rec.episodeId);
    const podcast = episode ? podcasts.find(p => p.id === episode.podcastId) : null;

    return {
      ...rec,
      episodeTitle: episode?.title,
      podcastName: podcast?.name,
      podcastId: podcast?.id,
      youtubeUrl: episode?.youtubeUrl,
      guestNames: episode?.guestNames?.join(', ') || 'N/A'
    };
  });

  // Filter data
  const filteredData = enrichedData.filter(rec => {
    const matchesType = filterType === 'all' || rec.type === filterType;
    const matchesSearch = searchTerm === '' ||
      rec.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      rec.recommendedBy?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      rec.podcastName?.toLowerCase().includes(searchTerm.toLowerCase());

    return matchesType && matchesSearch;
  });

  // Get unique types
  const types = ['all', ...Array.from(new Set(recommendations.map(r => r.type)))];

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-2xl">Loading data...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-full mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-4xl font-bold text-gray-900">Recommendations Data</h1>
            <Link href="/" className="text-teal-600 hover:text-teal-700">
              ← Back to Home
            </Link>
          </div>
          <p className="text-gray-600">
            Complete dataset: {recommendations.length} recommendations from {podcasts.length} podcasts
          </p>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Search */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Search
              </label>
              <input
                type="text"
                placeholder="Search by title, person, or podcast..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent"
              />
            </div>

            {/* Type Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Filter by Type
              </label>
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent"
              >
                {types.map(type => (
                  <option key={type} value={type}>
                    {type === 'all' ? 'All Types' : type}
                    {type !== 'all' && ` (${recommendations.filter(r => r.type === type).length})`}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="mt-4 text-sm text-gray-600">
            Showing {filteredData.length} of {recommendations.length} recommendations
          </div>
        </div>

        {/* Data Table */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Cover
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Title
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Author
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Recommended By
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Guest(s)
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Podcast
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Episode
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Context
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Quote
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Confidence
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Metadata
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Links
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredData.map((rec) => {
                  return (
                  <tr key={rec.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-teal-100 text-teal-800">
                        {rec.type}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      {rec.coverImageUrl && rec.type === 'book' ? (
                        <img
                          src={rec.coverImageUrl}
                          alt={rec.title}
                          className="w-16 h-24 object-cover rounded shadow-sm"
                          onError={(e) => {
                            e.currentTarget.style.display = 'none';
                          }}
                        />
                      ) : (
                        <div className="w-16 h-24 bg-gray-100 rounded flex items-center justify-center text-gray-400 text-xs">
                          {rec.type === 'book' ? 'No cover' : '-'}
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-gray-900 max-w-xs">
                        {rec.title}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-600 max-w-xs">
                        {rec.author || (rec.type === 'book' ? 'No author data' : '-')}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{rec.recommendedBy}</div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-900 max-w-xs">
                        {rec.guestNames || 'N/A'}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{rec.podcastName}</div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-500 max-w-md truncate" title={rec.episodeTitle}>
                        {rec.episodeTitle}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-500 max-w-md">
                        {rec.recommendationContext && rec.recommendationContext.length > 100 ? (
                          <details>
                            <summary className="cursor-pointer text-teal-600 hover:text-teal-700">
                              {rec.recommendationContext.substring(0, 100)}... (click to expand)
                            </summary>
                            <div className="mt-2 p-3 bg-gray-50 rounded border-l-4 border-blue-500">
                              {rec.recommendationContext}
                            </div>
                          </details>
                        ) : (
                          <div>{rec.recommendationContext || 'No context'}</div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-500 max-w-md">
                        {rec.quoteFromEpisode && rec.quoteFromEpisode.length > 100 ? (
                          <details>
                            <summary className="cursor-pointer text-teal-600 hover:text-teal-700 italic">
                              {rec.quoteFromEpisode.substring(0, 100)}... (click to expand)
                            </summary>
                            <div className="mt-2 p-3 bg-gray-50 rounded italic border-l-4 border-teal-500">
                              {rec.quoteFromEpisode}
                            </div>
                          </details>
                        ) : (
                          <div className="italic">{rec.quoteFromEpisode || 'No quote'}</div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {rec.confidenceScore ? `${(rec.confidenceScore * 100).toFixed(0)}%` : 'N/A'}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-xs text-gray-500 max-w-xs">
                        {rec.metadata && Object.keys(rec.metadata).length > 0 ? (
                          <details>
                            <summary className="cursor-pointer text-teal-600 hover:text-teal-700">
                              View ({Object.keys(rec.metadata).length} fields)
                            </summary>
                            <pre className="mt-2 p-2 bg-gray-100 rounded text-xs overflow-auto max-h-40">
                              {JSON.stringify(rec.metadata, null, 2)}
                            </pre>
                          </details>
                        ) : (
                          'None'
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <div className="flex flex-col gap-1">
                        {rec.amazonUrl && (
                          <a
                            href={rec.amazonUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-orange-600 hover:text-orange-700 font-medium"
                          >
                            Amazon →
                          </a>
                        )}
                        {rec.youtubeUrl && (
                          <a
                            href={rec.youtubeUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-red-600 hover:text-red-700"
                          >
                            YouTube →
                          </a>
                        )}
                        <Link
                          href={`/recommendations/${rec.id}`}
                          className="text-teal-600 hover:text-teal-700"
                        >
                          Details →
                        </Link>
                      </div>
                    </td>
                  </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Export Button */}
        <div className="mt-6 flex justify-end">
          <button
            onClick={() => {
              const csvContent = [
                ['Type', 'Title', 'Author', 'Recommended By', 'Guest(s)', 'Podcast', 'Episode', 'Context', 'Quote', 'Confidence', 'Amazon URL', 'YouTube URL'].join(','),
                ...filteredData.map(rec => [
                  rec.type,
                  `"${rec.title?.replace(/"/g, '""')}"`,
                  `"${rec.author?.replace(/"/g, '""') || ''}"`,
                  `"${rec.recommendedBy?.replace(/"/g, '""')}"`,
                  `"${rec.guestNames?.replace(/"/g, '""')}"`,
                  `"${rec.podcastName?.replace(/"/g, '""')}"`,
                  `"${rec.episodeTitle?.replace(/"/g, '""')}"`,
                  `"${rec.recommendationContext?.replace(/"/g, '""')}"`,
                  `"${rec.quoteFromEpisode?.replace(/"/g, '""')}"`,
                  rec.confidenceScore || '',
                  rec.amazonUrl || '',
                  rec.youtubeUrl || ''
                ].join(','))
              ].join('\n');

              const blob = new Blob([csvContent], { type: 'text/csv' });
              const url = window.URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = 'recommendations-data.csv';
              a.click();
            }}
            className="bg-teal-600 text-white px-6 py-3 rounded-lg hover:bg-teal-700 font-semibold"
          >
            Export to CSV ({filteredData.length} rows)
          </button>
        </div>
      </div>
    </div>
  );
}
