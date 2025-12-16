'use client';

import Link from "next/link";
import { useApi } from "@/hooks/useApi";
import { getPodcasts, getEpisodes, getRecommendations } from "@/lib/api";
import { useState, useEffect } from "react";

export default function PodcastsPage() {
  const { data: podcasts, loading, error } = useApi(getPodcasts);
  const { data: episodes } = useApi(getEpisodes);
  const { data: recommendations } = useApi(getRecommendations);

  // Count episodes and recommendations per podcast
  const getStatsForPodcast = (podcastId: string) => {
    const podcastEpisodes = (episodes || []).filter((ep: any) => ep.podcastId === podcastId);
    const podcastRecs = (recommendations || []).filter((rec: any) =>
      podcastEpisodes.some((ep: any) => ep.id === rec.episodeId)
    );
    return {
      episodeCount: podcastEpisodes.length,
      recCount: podcastRecs.length
    };
  };

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-teal-600 mb-4"></div>
          <p className="text-gray-600 text-lg">Loading podcasts...</p>
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
            Failed to load podcasts
          </h3>
          <p className="text-gray-600 mb-6 text-center">
            Make sure the backend API is running on http://localhost:8000
          </p>
          <p className="text-sm text-gray-500 text-center">
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
              <h1 className="text-4xl font-bold text-gray-900 mb-2">Podcasts</h1>
              <p className="text-gray-600">
                Browse recommendations from {podcasts?.length || 0} podcasts with real AI-extracted data
              </p>
            </div>
            <div className="bg-teal-50 border border-teal-200 rounded-lg px-4 py-2">
              <p className="text-sm text-teal-700 font-semibold">
                ✨ Live Data
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {podcasts && podcasts.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {podcasts.map((podcast: any) => {
              const stats = getStatsForPodcast(podcast.id);

              return (
                <Link key={podcast.id} href={`/podcasts/${podcast.id}`}>
                  <div className="bg-white rounded-lg border border-gray-200 overflow-hidden hover:shadow-lg transition-all duration-300 hover:scale-[1.02] cursor-pointer">
                    <div className="relative h-48 bg-gradient-to-br from-teal-100 to-teal-200">
                      <img
                        src={podcast.imageUrl || podcast.image_url || 'https://images.unsplash.com/photo-1478737270239-2f02b77fc618?w=400'}
                        alt={podcast.name}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          e.currentTarget.src = 'https://images.unsplash.com/photo-1478737270239-2f02b77fc618?w=400';
                        }}
                      />
                    </div>
                    <div className="p-6">
                      <h3 className="text-xl font-bold text-gray-900 mb-2">
                        {podcast.name}
                      </h3>
                      <p className="text-sm text-gray-600 mb-4">{podcast.category}</p>
                      <div className="flex items-center justify-between text-sm text-gray-500">
                        <span>{stats.episodeCount} episodes</span>
                        <span className="text-teal-600 font-semibold">
                          {stats.recCount} recommendations
                        </span>
                      </div>
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>
        ) : (
          <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
            <div className="text-6xl mb-4">🎙️</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              No podcasts found
            </h3>
            <p className="text-gray-600">
              Process some podcast episodes to see them here
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
