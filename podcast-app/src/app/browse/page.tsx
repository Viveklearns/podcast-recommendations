'use client';

import { useState, useEffect } from "react";
import RecommendationCard from "@/components/RecommendationCard";
import { useApi } from "@/hooks/useApi";
import { getRecommendations, getPodcasts } from "@/lib/api";
import { Recommendation } from "@/types";

type FilterType = 'all' | 'book' | 'movie' | 'tv_show' | 'app' | 'podcast' | 'product' | 'other';

export default function BrowsePage() {
  const [activeFilter, setActiveFilter] = useState<FilterType>('all');
  const [selectedPodcast, setSelectedPodcast] = useState<string>('all');

  // Fetch recommendations from API (fetch all with high limit)
  const { data: allRecommendations, loading, error, refetch } = useApi(() => getRecommendations({ limit: 500 }));
  const { data: podcasts } = useApi(getPodcasts);

  // Filter recommendations based on user selection
  const filteredRecommendations = (allRecommendations || []).filter((rec: any) => {
    // Filter by type
    if (activeFilter !== 'all' && rec.type !== activeFilter) {
      return false;
    }
    // Filter by podcast - we'll skip this for now since it requires episode lookup
    return true;
  });

  // Group recommendations by type for "All" view
  const bookRecs = (allRecommendations || []).filter((r: any) => r.type === 'book');
  const movieRecs = (allRecommendations || []).filter((r: any) => r.type === 'movie');
  const tvShowRecs = (allRecommendations || []).filter((r: any) => r.type === 'tv_show');
  const productRecs = (allRecommendations || []).filter((r: any) => r.type === 'product');
  const otherRecs = (allRecommendations || []).filter((r: any) =>
    !['book', 'movie', 'tv_show', 'product'].includes(r.type)
  );

  const filterButtons: { label: string; value: FilterType; emoji: string }[] = [
    { label: 'All', value: 'all', emoji: '🌟' },
    { label: 'Books', value: 'book', emoji: '📚' },
    { label: 'Movies', value: 'movie', emoji: '🎬' },
    { label: 'TV Shows', value: 'tv_show', emoji: '📺' },
    { label: 'Apps', value: 'app', emoji: '📱' },
    { label: 'Podcasts', value: 'podcast', emoji: '🎙️' },
    { label: 'Products', value: 'product', emoji: '🛍️' },
    { label: 'Other', value: 'other', emoji: '✨' },
  ];

  // Count recommendations by type
  const getCountForType = (type: FilterType) => {
    if (type === 'all') return allRecommendations?.length || 0;
    return (allRecommendations || []).filter((r: any) => r.type === type).length;
  };

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-teal-600 mb-4"></div>
          <p className="text-gray-600 text-lg">Loading real recommendations from Lenny's Podcast...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white rounded-lg border border-red-200 p-8 max-w-md">
          <div className="text-6xl mb-4 text-center">⚠️</div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2 text-center">
            Failed to load recommendations
          </h3>
          <p className="text-gray-600 mb-6 text-center">
            Make sure the backend API is running on http://localhost:8000
          </p>
          <button
            onClick={() => refetch()}
            className="w-full px-6 py-3 bg-teal-600 text-white rounded-lg font-semibold hover:bg-teal-700 transition-colors"
          >
            Retry
          </button>
          <p className="text-sm text-gray-500 mt-4 text-center">
            Error: {error.message}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-gray-900 mb-2">
                Browse Recommendations
              </h1>
              <p className="text-gray-600">
                Explore {filteredRecommendations.length} real recommendations from Lenny's Podcast
              </p>
            </div>
            <div className="bg-teal-50 border border-teal-200 rounded-lg px-4 py-2">
              <p className="text-sm text-teal-700 font-semibold">
                ✨ Live Data from API
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col lg:flex-row gap-8">
          {/* Sidebar Filters */}
          <aside className="lg:w-64 flex-shrink-0">
            <div className="bg-white rounded-lg border border-gray-200 p-6 sticky top-20">
              <h3 className="font-semibold text-gray-900 mb-4">Filter by Type</h3>
              <div className="space-y-2">
                {filterButtons.map((filter) => (
                  <button
                    key={filter.value}
                    onClick={() => setActiveFilter(filter.value)}
                    className={`w-full text-left px-4 py-2 rounded-lg transition-colors flex items-center space-x-2 ${
                      activeFilter === filter.value
                        ? 'bg-teal-100 text-teal-700 font-semibold'
                        : 'hover:bg-gray-100 text-gray-700'
                    }`}
                  >
                    <span>{filter.emoji}</span>
                    <span>{filter.label}</span>
                    <span className="ml-auto text-xs text-gray-500">
                      {getCountForType(filter.value)}
                    </span>
                  </button>
                ))}
              </div>

              <hr className="my-6" />

              <h3 className="font-semibold text-gray-900 mb-4">Source</h3>
              <div className="bg-teal-50 border border-teal-200 rounded-lg p-4">
                <p className="text-sm text-teal-700 mb-1 font-semibold">
                  Lenny's Podcast
                </p>
                <p className="text-xs text-teal-600">
                  AI-extracted from {podcasts?.length || 1} podcast with {allRecommendations?.length || 0} recommendations
                </p>
              </div>
            </div>
          </aside>

          {/* Main Content */}
          <main className="flex-1">
            {/* Category Tabs (Mobile) */}
            <div className="lg:hidden mb-6 overflow-x-auto">
              <div className="flex space-x-2 pb-2">
                {filterButtons.map((filter) => (
                  <button
                    key={filter.value}
                    onClick={() => setActiveFilter(filter.value)}
                    className={`px-4 py-2 rounded-lg whitespace-nowrap transition-colors flex items-center space-x-1 ${
                      activeFilter === filter.value
                        ? 'bg-teal-600 text-white font-semibold'
                        : 'bg-white border border-gray-200 text-gray-700'
                    }`}
                  >
                    <span>{filter.emoji}</span>
                    <span>{filter.label}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Sort Options */}
            <div className="flex items-center justify-between mb-6">
              <div>
                <span className="text-sm text-gray-600">
                  Showing <strong>{filteredRecommendations.length}</strong> recommendations
                </span>
              </div>
              <button
                onClick={() => refetch()}
                className="px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50 transition-colors"
              >
                🔄 Refresh
              </button>
            </div>

            {/* Recommendations Display */}
            {filteredRecommendations.length > 0 ? (
              activeFilter === 'all' ? (
                // Categorized view for "All" filter
                <div className="space-y-12">
                  {/* Books Section */}
                  {bookRecs.length > 0 && (
                    <section>
                      <h3 className="text-2xl font-bold text-gray-900 mb-4">
                        Books ({bookRecs.length})
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {bookRecs.map((rec: any) => (
                          <RecommendationCard key={rec.id} recommendation={rec} />
                        ))}
                      </div>
                    </section>
                  )}

                  {/* Movies Section */}
                  {movieRecs.length > 0 && (
                    <section>
                      <h3 className="text-2xl font-bold text-gray-900 mb-4">
                        Movies ({movieRecs.length})
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {movieRecs.map((rec: any) => (
                          <RecommendationCard key={rec.id} recommendation={rec} />
                        ))}
                      </div>
                    </section>
                  )}

                  {/* TV Shows Section */}
                  {tvShowRecs.length > 0 && (
                    <section>
                      <h3 className="text-2xl font-bold text-gray-900 mb-4">
                        TV Shows ({tvShowRecs.length})
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {tvShowRecs.map((rec: any) => (
                          <RecommendationCard key={rec.id} recommendation={rec} />
                        ))}
                      </div>
                    </section>
                  )}

                  {/* Products Section */}
                  {productRecs.length > 0 && (
                    <section>
                      <h3 className="text-2xl font-bold text-gray-900 mb-4">
                        Products ({productRecs.length})
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {productRecs.map((rec: any) => (
                          <RecommendationCard key={rec.id} recommendation={rec} />
                        ))}
                      </div>
                    </section>
                  )}
                </div>
              ) : (
                // Simple grid for specific filter
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {filteredRecommendations.map((rec: any) => (
                    <RecommendationCard key={rec.id} recommendation={rec} />
                  ))}
                </div>
              )
            ) : (
              <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
                <div className="text-6xl mb-4">🔍</div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  No recommendations found
                </h3>
                <p className="text-gray-600 mb-6">
                  Try adjusting your filters to see more results
                </p>
                <button
                  onClick={() => {
                    setActiveFilter('all');
                    setSelectedPodcast('all');
                  }}
                  className="px-6 py-3 bg-teal-600 text-white rounded-lg font-semibold hover:bg-teal-700 transition-colors"
                >
                  Clear Filters
                </button>
              </div>
            )}
          </main>
        </div>
      </div>
    </div>
  );
}
