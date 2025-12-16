'use client';

import { notFound } from "next/navigation";
import { use } from "react";
import Link from "next/link";
import RecommendationCard from "@/components/RecommendationCard";
import { useApi } from "@/hooks/useApi";
import { getPodcastById, getEpisodes, getRecommendations } from "@/lib/api";

export default function PodcastDetailPage({ params }: { params: Promise<{ id: string }> }) {
  // Unwrap params Promise using React.use()
  const { id } = use(params);
  const { data: podcast, loading: podcastLoading } = useApi(() => getPodcastById(id));
  const { data: allEpisodes, loading: episodesLoading } = useApi(getEpisodes);
  const { data: allRecommendations, loading: recsLoading } = useApi(getRecommendations);

  const loading = podcastLoading || episodesLoading || recsLoading;

  // Filter episodes for this podcast
  const episodes = (allEpisodes || []).filter((ep: any) => ep.podcastId === id);

  // Filter recommendations for this podcast's episodes
  const episodeIds = episodes.map((ep: any) => ep.id);
  const recommendations = (allRecommendations || []).filter((rec: any) =>
    episodeIds.includes(rec.episodeId)
  );

  // Group recommendations by type
  const bookRecs = recommendations.filter((r: any) => r.type === 'book');
  const movieRecs = recommendations.filter((r: any) => r.type === 'movie');
  const tvShowRecs = recommendations.filter((r: any) => r.type === 'tv_show');
  const productRecs = recommendations.filter((r: any) => r.type === 'product');
  const otherRecs = recommendations.filter((r: any) =>
    !['book', 'movie', 'tv_show', 'product'].includes(r.type)
  );

  // Count recommendations by type
  const bookCount = bookRecs.length;
  const movieCount = movieRecs.length;

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-teal-600 mb-4"></div>
          <p className="text-gray-600 text-lg">Loading podcast details...</p>
        </div>
      </div>
    );
  }

  if (!podcast) {
    notFound();
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-br from-teal-600 to-teal-800 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="flex flex-col md:flex-row items-center md:items-start space-y-6 md:space-y-0 md:space-x-8">
            <img
              src={podcast.imageUrl || podcast.image_url || 'https://images.unsplash.com/photo-1478737270239-2f02b77fc618?w=400'}
              alt={podcast.name}
              className="w-48 h-48 rounded-lg object-cover shadow-2xl"
              onError={(e) => {
                e.currentTarget.src = 'https://images.unsplash.com/photo-1478737270239-2f02b77fc618?w=400';
              }}
            />
            <div className="flex-1 text-center md:text-left">
              <h1 className="text-4xl md:text-5xl font-bold mb-3">{podcast.name}</h1>
              <p className="text-xl text-teal-100 mb-2">{podcast.category}</p>
              <div className="bg-teal-700 bg-opacity-50 rounded-lg px-4 py-2 inline-block mb-6">
                <p className="text-sm text-teal-100">
                  ✨ AI-extracted recommendations from real podcast transcripts
                </p>
              </div>
              <div className="flex flex-wrap justify-center md:justify-start gap-6 text-sm">
                <div>
                  <div className="text-3xl font-bold">{episodes.length}</div>
                  <div className="text-teal-200">Episodes Processed</div>
                </div>
                <div>
                  <div className="text-3xl font-bold">{recommendations.length}</div>
                  <div className="text-teal-200">Recommendations</div>
                </div>
                <div>
                  <div className="text-3xl font-bold">{bookCount}</div>
                  <div className="text-teal-200">Books</div>
                </div>
                <div>
                  <div className="text-3xl font-bold">{movieCount}</div>
                  <div className="text-teal-200">Movies</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Recommendations by Category */}
        {recommendations.length > 0 ? (
          <div className="space-y-12 mb-12">
            {/* Books Section */}
            {bookRecs.length > 0 && (
              <section>
                <h2 className="text-3xl font-bold text-gray-900 mb-6">
                  Books ({bookRecs.length})
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  {bookRecs.map((rec: any) => (
                    <RecommendationCard key={rec.id} recommendation={rec} />
                  ))}
                </div>
              </section>
            )}

            {/* Movies Section */}
            {movieRecs.length > 0 && (
              <section>
                <h2 className="text-3xl font-bold text-gray-900 mb-6">
                  Movies ({movieRecs.length})
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  {movieRecs.map((rec: any) => (
                    <RecommendationCard key={rec.id} recommendation={rec} />
                  ))}
                </div>
              </section>
            )}

            {/* TV Shows Section */}
            {tvShowRecs.length > 0 && (
              <section>
                <h2 className="text-3xl font-bold text-gray-900 mb-6">
                  TV Shows ({tvShowRecs.length})
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  {tvShowRecs.map((rec: any) => (
                    <RecommendationCard key={rec.id} recommendation={rec} />
                  ))}
                </div>
              </section>
            )}

            {/* Products Section */}
            {productRecs.length > 0 && (
              <section>
                <h2 className="text-3xl font-bold text-gray-900 mb-6">
                  Products ({productRecs.length})
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  {productRecs.map((rec: any) => (
                    <RecommendationCard key={rec.id} recommendation={rec} />
                  ))}
                </div>
              </section>
            )}
          </div>
        ) : (
          <div className="bg-white rounded-lg border border-gray-200 p-12 text-center mb-12">
            <p className="text-gray-600">No recommendations yet for this podcast.</p>
          </div>
        )}

        {/* Episodes */}
        <section>
          <h2 className="text-3xl font-bold text-gray-900 mb-6">
            Recent Episodes ({episodes.length})
          </h2>
          <div className="space-y-4">
            {episodes.map((episode: any) => {
              const episodeRecs = recommendations.filter((rec: any) => rec.episodeId === episode.id);
              return (
                <div
                  key={episode.id}
                  className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow"
                >
                  <div className="flex flex-col md:flex-row md:items-center md:justify-between">
                    <div className="flex-1 mb-4 md:mb-0">
                      <h3 className="text-xl font-semibold text-gray-900 mb-2">
                        {episode.title}
                      </h3>
                      <p className="text-sm text-gray-600 mb-2 line-clamp-2">
                        {episode.description}
                      </p>
                      <div className="flex flex-wrap items-center gap-4 text-sm text-gray-500">
                        <span>
                          {new Date(episode.publishedDate || episode.published_date).toLocaleDateString("en-US", {
                            year: "numeric",
                            month: "long",
                            day: "numeric",
                          })}
                        </span>
                        {episode.guestNames && episode.guestNames.length > 0 && (
                          <span>with {episode.guestNames.join(", ")}</span>
                        )}
                        <span className="text-teal-600 font-semibold">
                          {episodeRecs.length} recommendations
                        </span>
                      </div>
                    </div>
                    {(episode.youtubeUrl || episode.youtube_url) && (
                      <a
                        href={episode.youtubeUrl || episode.youtube_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-6 py-3 bg-red-600 text-white rounded-lg font-semibold hover:bg-red-700 transition-colors flex items-center justify-center space-x-2"
                      >
                        <span>▶</span>
                        <span>Watch on YouTube</span>
                      </a>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      </div>
    </div>
  );
}
