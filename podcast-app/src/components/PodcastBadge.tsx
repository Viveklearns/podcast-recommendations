import { Podcast } from "@/types";
import Link from "next/link";

interface PodcastBadgeProps {
  podcast: Podcast;
  showImage?: boolean;
}

export default function PodcastBadge({ podcast, showImage = true }: PodcastBadgeProps) {
  return (
    <Link
      href={`/podcasts/${podcast.id}`}
      className="inline-flex items-center space-x-2 bg-white border border-gray-200 rounded-lg px-3 py-2 hover:border-teal-400 hover:shadow-md transition-all"
    >
      {showImage && (
        <img
          src={podcast.imageUrl}
          alt={podcast.name}
          className="w-8 h-8 rounded object-cover"
        />
      )}
      <div>
        <p className="text-sm font-semibold text-gray-900">{podcast.name}</p>
        <p className="text-xs text-gray-500">{podcast.category}</p>
      </div>
    </Link>
  );
}
