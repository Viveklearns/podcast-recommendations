'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

type NavigationStyle = 'pills' | 'underline' | 'segmented' | 'minimal';

interface NavigationProps {
  style?: NavigationStyle;
}

export default function Navigation({ style = 'pills' }: NavigationProps) {
  const pathname = usePathname();

  const isThemeView = pathname === '/';
  const isGuestView = pathname === '/guest-recommendations';

  if (style === 'pills') {
    return <PillsNavigation isThemeView={isThemeView} isGuestView={isGuestView} />;
  } else if (style === 'underline') {
    return <UnderlineNavigation isThemeView={isThemeView} isGuestView={isGuestView} />;
  } else if (style === 'segmented') {
    return <SegmentedNavigation isThemeView={isThemeView} isGuestView={isGuestView} />;
  } else {
    return <MinimalNavigation isThemeView={isThemeView} isGuestView={isGuestView} />;
  }
}

// Option 1: Pills Navigation (Modern, rounded buttons)
function PillsNavigation({ isThemeView, isGuestView }: { isThemeView: boolean; isGuestView: boolean }) {
  return (
    <div className="flex items-start justify-between w-full">
      {/* Logo - Far Left */}
      <Link href="/" className="flex items-center gap-3">
        <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center">
          <span className="text-black font-bold text-2xl">📚</span>
        </div>
        <span className="font-bold text-3xl text-white">PodBooks</span>
      </Link>

      {/* Navigation Pills - Center */}
      <div className="flex items-center gap-3 bg-black/50 backdrop-blur-md border border-white/10 rounded-full px-2 py-2 absolute left-1/2 transform -translate-x-1/2">
        <Link
          href="/"
          className={`px-6 py-2.5 rounded-full font-medium transition-all duration-200 ${
            isThemeView
              ? 'bg-white text-black shadow-lg'
              : 'text-gray-300 hover:text-white hover:bg-white/10'
          }`}
        >
          Books by Theme
        </Link>
        <Link
          href="/guest-recommendations"
          className={`px-6 py-2.5 rounded-full font-medium transition-all duration-200 ${
            isGuestView
              ? 'bg-white text-black shadow-lg'
              : 'text-gray-300 hover:text-white hover:bg-white/10'
          }`}
        >
          Books by Guest
        </Link>
      </div>
    </div>
  );
}

// Option 2: Underline Navigation (Clean, minimal)
function UnderlineNavigation({ isThemeView, isGuestView }: { isThemeView: boolean; isGuestView: boolean }) {
  return (
    <nav className="flex items-center gap-8 border-b border-white/10 pb-1">
      <Link
        href="/"
        className={`px-4 py-2 font-medium transition-all duration-200 relative ${
          isThemeView
            ? 'text-white'
            : 'text-gray-400 hover:text-white'
        }`}
      >
        Books by Theme
        {isThemeView && (
          <div className="absolute bottom-[-5px] left-0 right-0 h-0.5 bg-gradient-to-r from-purple-500 to-blue-500" />
        )}
      </Link>
      <Link
        href="/guest-recommendations"
        className={`px-4 py-2 font-medium transition-all duration-200 relative ${
          isGuestView
            ? 'text-white'
            : 'text-gray-400 hover:text-white'
        }`}
      >
        Books by Guest
        {isGuestView && (
          <div className="absolute bottom-[-5px] left-0 right-0 h-0.5 bg-gradient-to-r from-purple-500 to-blue-500" />
        )}
      </Link>
    </nav>
  );
}

// Option 3: Segmented Control (iOS-style)
function SegmentedNavigation({ isThemeView, isGuestView }: { isThemeView: boolean; isGuestView: boolean }) {
  return (
    <nav className="inline-flex items-center bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-1">
      <Link
        href="/"
        className={`px-8 py-2.5 rounded-md font-medium transition-all duration-200 ${
          isThemeView
            ? 'bg-white text-black shadow-md'
            : 'text-gray-300 hover:text-white'
        }`}
      >
        By Theme
      </Link>
      <Link
        href="/guest-recommendations"
        className={`px-8 py-2.5 rounded-md font-medium transition-all duration-200 ${
          isGuestView
            ? 'bg-white text-black shadow-md'
            : 'text-gray-300 hover:text-white'
        }`}
      >
        By Guest
      </Link>
    </nav>
  );
}

// Option 4: Minimal Navigation (Simple text)
function MinimalNavigation({ isThemeView, isGuestView }: { isThemeView: boolean; isGuestView: boolean }) {
  return (
    <nav className="flex items-center gap-6">
      <Link
        href="/"
        className={`text-lg font-medium transition-all duration-200 ${
          isThemeView
            ? 'text-white'
            : 'text-gray-400 hover:text-gray-200'
        }`}
      >
        Books by Theme
      </Link>
      <div className="w-px h-6 bg-white/20" />
      <Link
        href="/guest-recommendations"
        className={`text-lg font-medium transition-all duration-200 ${
          isGuestView
            ? 'text-white'
            : 'text-gray-400 hover:text-gray-200'
        }`}
      >
        Books by Guest
      </Link>
    </nav>
  );
}
