import Link from "next/link";
import { Recommendation } from "@/types";
import { getEpisodeById, getPodcastById } from "@/lib/mockData";

interface RecommendationCardProps {
  recommendation: Recommendation;
}

export default function RecommendationCard({ recommendation }: RecommendationCardProps) {
  const episode = getEpisodeById(recommendation.episodeId);
  const podcast = episode ? getPodcastById(episode.podcastId) : null;

  const getImageUrl = () => {
    if (recommendation.type === "book") {
      return recommendation.coverImageUrl;
    } else if (recommendation.type === "movie" || recommendation.type === "tv_show") {
      return recommendation.posterUrl;
    }
    return undefined;
  };

  const getTypeLabel = () => {
    switch (recommendation.type) {
      case "book":
        return "Book";
      case "movie":
        return "Movie";
      case "tv_show":
        return "TV Show";
      case "app":
        return "App";
      case "podcast":
        return "Podcast";
      case "product":
        return "Product";
      default:
        return "Other";
    }
  };

  const getTypeColor = () => {
    switch (recommendation.type) {
      case "book":
        return "bg-blue-100 text-teal-700";
      case "movie":
        return "bg-purple-100 text-purple-700";
      case "tv_show":
        return "bg-pink-100 text-pink-700";
      case "app":
        return "bg-green-100 text-green-700";
      default:
        return "bg-gray-100 text-gray-700";
    }
  };

  const getSubtitle = () => {
    if (recommendation.type === "book") {
      return recommendation.author;
    } else if (recommendation.type === "movie" || recommendation.type === "tv_show") {
      return recommendation.creatorDirector || `${recommendation.releaseYear}`;
    }
    return undefined;
  };

  return (
    <Link href={`/recommendations/${recommendation.id}`}>
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden hover:shadow-lg transition-all duration-300 hover:scale-[1.02] cursor-pointer group">
        {/* Image */}
        <div className="relative h-64 bg-gradient-to-br from-gray-100 to-gray-200 overflow-hidden">
          {getImageUrl() ? (
            <img
              src={getImageUrl()}
              alt={recommendation.title}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <span className="text-gray-400 text-4xl">📚</span>
            </div>
          )}
          {/* Type Badge */}
          <div className="absolute top-3 left-3">
            <span
              className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${getTypeColor()}`}
            >
              {getTypeLabel()}
            </span>
          </div>
          {/* Confidence Score */}
          {recommendation.confidenceScore >= 0.9 && (
            <div className="absolute top-3 right-3 bg-white/90 backdrop-blur-sm rounded-full px-2 py-1">
              <span className="text-xs font-semibold text-gray-700">
                ⭐ {(recommendation.confidenceScore * 100).toFixed(0)}%
              </span>
            </div>
          )}
        </div>

        {/* Content */}
        <div className="p-4">
          <h3 className="font-bold text-lg text-gray-900 mb-1 line-clamp-2 group-hover:text-teal-600 transition-colors">
            {recommendation.title}
          </h3>

          {getSubtitle() && (
            <p className="text-sm text-gray-600 mb-3">{getSubtitle()}</p>
          )}

          {/* Quote */}
          <p className="text-sm text-gray-700 line-clamp-2 mb-3 italic">
            &quot;{recommendation.quoteFromEpisode}&quot;
          </p>

          {/* Recommended By */}
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span className="font-medium">{recommendation.recommendedBy}</span>
            {podcast && (
              <span className="text-teal-600">{podcast.name}</span>
            )}
          </div>

          {/* Rating for books/movies */}
          {(recommendation.type === "book" && "goodreadsRating" in recommendation && recommendation.goodreadsRating) && (
            <div className="mt-2 flex items-center">
              <span className="text-yellow-500 text-sm mr-1">★</span>
              <span className="text-sm font-semibold text-gray-700">
                {recommendation.goodreadsRating.toFixed(2)}
              </span>
              <span className="text-xs text-gray-500 ml-1">Goodreads</span>
            </div>
          )}
          {((recommendation.type === "movie" || recommendation.type === "tv_show") && "rating" in recommendation && recommendation.rating) && (
            <div className="mt-2 flex items-center">
              <span className="text-yellow-500 text-sm mr-1">★</span>
              <span className="text-sm font-semibold text-gray-700">
                {recommendation.rating.toFixed(1)}
              </span>
              <span className="text-xs text-gray-500 ml-1">IMDB</span>
            </div>
          )}
        </div>
      </div>
    </Link>
  );
}
