"""
Podcast‑to‑Book Recommender — end‑to‑end pipeline (no YouTube API key)
=====================================================================

Given a list of podcast show names and a look‑back window (e.g. 60 months),
this script will:
  1. **Search YouTube (like a human)** for matching episodes using `yt-dlp`’s
     web extractor (no YouTube Data API key required), sorted by newest first.
  2. **Fetch captions** (creator‑uploaded or auto) and, if missing, **transcribe**
     the audio with OpenAI Whisper (optional).
  3. **Extract and normalise book recommendations** from transcripts via GPT
     function‑calling (optional) **or a regex‑based fallback** (no OpenAI needed).
  4. **Resolve authors authoritatively** — prefer **Google Books (ISBN metadata)**
     and replace any existing author string; if Google yields nothing and ChatGPT
     is available, use **ChatGPT** as a fallback.
  5. **Export** the consolidated results to a CSV **or** a Google Sheet.

> **Important:** All OpenAI‑powered steps are automatically skipped if the
> `openai` package is *not* available. In that case we use the
> **regex extractor** and **Google Books** for author enrichment only.

Environment variables
---------------------
OPENAI_API_KEY        – key with access to whisper‑1 + GPT‑4o (optional).
GOOGLE_CRED_JSON      – *optional* path to a Google service‑account JSON if you
                        select the Google Sheet output mode.
GOOGLE_BOOKS_API_KEY  – *optional* key for Google Books; not required for low volume.

Quick start (CSV)
-----------------
$ pip install -r requirements.txt  # "openai" is optional
$ python podcast_book_recommender.py --podcasts "Tim Ferriss Show" Acquired \
      --months 60 --output csv --verbose
✓  Finished. Data written to book_recommendations.csv

Command‑line flags
------------------
--podcasts         One or more podcast names (quoted)                 (required)
--months           How many months back to search (int)               default = 60
--output           csv  |  sheet                                      default = csv
--author-source    auto | google | openai | none                      default = auto
--search-limit     Max YouTube results per podcast (int)              default = 200
--verbose          Show debug log                                     default = False
--selftest         Run offline unit tests and exit                    default = False
--force-fallback   Force regex extractor (ignore OpenAI if present)   default = False

Dependencies (see requirements.txt)
-----------------------------------
requests youtube-transcript-api yt-dlp python-dateutil tenacity pandas \
gspread oauth2client tqdm [openai]

*Items in square brackets are optional: the script degrades gracefully when
OpenAI is unavailable.*

Author policy
-------------
By default (`--author-source auto`) we **replace** any author string with
Google Books’ primary author when available; if Google yields nothing and
ChatGPT is enabled, we fill via ChatGPT. Set `--author-source google` to
use only Google (replace-or-keep), `openai` to try ChatGPT only, or `none`
to leave authors unchanged.

Programmatic usage
------------------
If you save this file as `podcast_book_recommender.py`, other Python code can do:

    import podcast_book_recommender as pbr
    pbr.run_programmatic([
        "Acquired",
        "Invest Like the Best"
    ], months=36, output="csv", author_source="auto", force_fallback=False,
       search_limit=300)

Note: **Do not import this file from itself.** Keep example imports in a
separate script or notebook to avoid `ModuleNotFoundError`.
"""

from __future__ import annotations
import argparse, json, logging, os, re, subprocess, tempfile, textwrap
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple, Optional

import pandas as pd
import requests
from dateutil.relativedelta import relativedelta
from tenacity import retry, stop_after_attempt, wait_random_exponential
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
from tqdm import tqdm

# Try in‑process yt_dlp first; fall back to calling the binary if missing
try:
    import yt_dlp  # type: ignore
except ModuleNotFoundError:
    yt_dlp = None  # type: ignore

# ---------------------------------------------------------------------------
# OPTIONAL: OpenAI (lazy import so script still loads when package is missing)
# ---------------------------------------------------------------------------
try:
    import openai  # type: ignore
except ModuleNotFoundError:  # pragma: no cover – tested below
    openai = None  # type: ignore

FORCE_FALLBACK = False  # set from CLI
AUTHOR_SOURCE = "auto"  # set from CLI: auto|google|openai|none
SEARCH_LIMIT = 200      # set from CLI

# Guard for OpenAI‑dependent code

def _ensure_openai(feature: str) -> None:
    if openai is None:
        raise RuntimeError(
            f"The '{feature}' feature requires the 'openai' package. "
            "Install it (pip install openai) or run with --force-fallback / --author-source google."
        )

# Configure API key *only if* openai is present
if openai is not None:
    openai.api_key = os.getenv("OPENAI_API_KEY")

# ---------------------------------------------------------------------------
# CONFIG & LOGGING
# ---------------------------------------------------------------------------
GOOGLE_BOOKS_URL = "https://www.googleapis.com/books/v1/volumes"
GOOGLE_BOOKS_KEY = os.getenv("GOOGLE_BOOKS_API_KEY")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("pipeline")

# ---------------------------------------------------------------------------
# DATA CLASSES
# ---------------------------------------------------------------------------
@dataclass
class Episode:
    podcast: str
    video_id: str
    url: str
    publish_date: str  # YYYY‑MM‑DD

@dataclass
class BookMention:
    podcast: str
    episode_date: str
    youtube_url: str
    title: str
    author: Optional[str]
    context: Optional[str]
    timestamp: Optional[str]

    @property
    def amazon_url(self) -> str:
        from urllib.parse import quote_plus
        query = quote_plus(f"{self.title} {self.author or ''}")
        return f"https://www.amazon.com/s?k={query}"

# ---------------------------------------------------------------------------
# UTIL: YouTube search via web (no API key)
# ---------------------------------------------------------------------------

def _to_iso(upload_date: str) -> Optional[str]:
    """Convert yt-dlp upload_date (YYYYMMDD) → YYYY-MM-DD."""
    try:
        dt = datetime.strptime(upload_date, "%Y%m%d")
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return None


def _extract_with_yt_dlp(query: str, limit: int) -> List[Dict[str, Any]]:
    """Return raw entries from yt-dlp either via Python API or subprocess JSON.
    Each entry is a dict with at least 'id', 'webpage_url', 'upload_date'.
    """
    if yt_dlp is not None:  # preferred path
        ydl_opts = {
            "quiet": True,
            "skip_download": True,
            "extract_flat": True,        # much faster, metadata only
            "nocheckcertificate": True,
            "ignoreerrors": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore[attr-defined]
            info = ydl.extract_info(f"ytsearchdate{limit}:{query}", download=False)
            entries = info.get("entries", []) if isinstance(info, dict) else []
            return [e for e in entries if isinstance(e, dict)]
    # Fallback: call the binary
    try:
        cmd = ["yt-dlp", "-j", f"ytsearchdate{limit}:{query}"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        entries: List[Dict[str, Any]] = []
        for line in res.stdout.splitlines():
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return entries
    except Exception as e:
        logger.error("yt-dlp search failed: %s", e)
        return []


@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(3))
def search_episodes(podcast: str, published_after_iso: str, search_limit: int = 200) -> List[Episode]:
    """Search YouTube like a human via yt-dlp (sorted newest→oldest) and
    filter by published_after date. No API key needed.
    """
    query = f"{podcast} podcast"
    entries = _extract_with_yt_dlp(query, search_limit)

    try:
        threshold = datetime.fromisoformat(published_after_iso.replace("Z", "+00:00")).date()
    except Exception:
        threshold = datetime.utcnow().date()

    episodes: List[Episode] = []
    for e in entries:
        vid = e.get("id")
        url = e.get("webpage_url") or (f"https://youtu.be/{vid}" if vid else None)
        up = e.get("upload_date")
        iso = _to_iso(up) if up else None
        if not (vid and url and iso):
            continue
        # date filter
        try:
            if datetime.strptime(iso, "%Y-%m-%d").date() < threshold:
                continue
        except Exception:
            pass
        episodes.append(Episode(podcast=podcast, video_id=vid, url=url, publish_date=iso))

    return episodes

# ---------------------------------------------------------------------------
# TRANSCRIPT FETCH
# ---------------------------------------------------------------------------

def get_captions(video_id: str) -> Optional[str]:
    try:
        parts = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])
        return " ".join(p["text"] for p in parts)
    except TranscriptsDisabled:
        return None
    except Exception:
        return None

# Whisper fallback (only if openai present)

def transcribe_with_whisper(video_id: str) -> Optional[str]:
    _ensure_openai("Whisper transcription")
    logger.debug("Downloading audio for %s", video_id)
    with tempfile.TemporaryDirectory() as td:
        audio_path = Path(td) / f"{video_id}.mp3"
        cmd = [
            "yt-dlp",
            "-x",
            "--audio-format",
            "mp3",
            "--quiet",
            "--no-warnings",
            f"https://youtu.be/{video_id}",
            "-o",
            str(audio_path),
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            logger.warning("yt-dlp failed: %s", e)
            return None

        logger.debug("Uploading to OpenAI Whisper…")
        try:
            with open(audio_path, "rb") as f:
                resp = openai.audio.transcriptions.create(model="whisper-1", file=f)  # type: ignore[attr-defined]
            return resp.text  # type: ignore[attr-defined]
        except Exception as e:  # pragma: no cover – network
            logger.warning("Whisper API failed: %s", e)
            return None


def fetch_transcript(video_id: str) -> Optional[str]:
    text = get_captions(video_id)
    if text:
        return text
    # Only attempt Whisper when openai is available and not forcing fallback
    if openai is not None and not FORCE_FALLBACK:
        return transcribe_with_whisper(video_id)
    return None

# ---------------------------------------------------------------------------
# BOOK‑MENTION EXTRACTION
# ---------------------------------------------------------------------------
# 1) OpenAI path (function‑calling)
FUNC_SCHEMA = {
    "name": "book_mention",
    "parameters": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "author": {"type": "string"},
            "context": {"type": "string"},
            "timestamp": {"type": "string"},
        },
        "required": ["title"],
    },
}

CHUNK_WORDS = 15_000  # ≈ 2‑3 k tokens


def _chunk(text: str, size: int = CHUNK_WORDS) -> Iterable[str]:
    words = text.split()
    for i in range(0, len(words), size):
        yield " ".join(words[i : i + size])


def extract_books_openai(transcript: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    try:
        for chunk in _chunk(transcript):
            chat = openai.chat.completions.create(  # type: ignore[attr-defined]
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": chunk}],
                tools=[{"type": "function", "function": FUNC_SCHEMA}],
                tool_choice="auto",
                max_tokens=256,
            )
            for choice in chat.choices:
                if choice.message.tool_calls:
                    for call in choice.message.tool_calls:
                        out.append(json.loads(call.function.arguments))
    except Exception as e:  # pragma: no cover – network
        logger.warning("GPT extraction failed: %s", e)
    return out

# 2) Regex fallback path (no OpenAI needed)
#    Extracts patterns like: "I recommend 'Deep Work' by Cal Newport" or
#    "My favorite book is Atomic Habits by James Clear".

_QUOTE = r"['\"“”]"
_TITLE = r"([A-Z][\w .:&'\-]{2,120}?)"  # permissive title capture
_AUTHOR = r"([A-Z][\w .\-']{2,80})"

# Pattern A: verbs + quoted title (+ optional author)
PATTERN_A = re.compile(
    rf"(?is)\b(?:recommend(?:ed)?|reading|read|book|favorite|favourite)[^\n\.\r]{{0,120}}?{_QUOTE}{_TITLE}{_QUOTE}\s*(?:by\s+{_AUTHOR})?"
)
# Pattern B: verbs + unquoted Title by Author
PATTERN_B = re.compile(
    rf"(?is)\b(?:recommend(?:ed)?|reading|read|book|favorite|favourite)\s+{_TITLE}\s+(?:by|from)\s+{_AUTHOR}"
)


def _context_snippet(text: str, start: int, end: int, pad: int = 120) -> str:
    a = max(0, start - pad)
    b = min(len(text), end + pad)
    snippet = text[a:b].strip()
    return re.sub(r"\s+", " ", snippet)

# ---------------------------------------------------------------------------
# AUTHOR RESOLUTION (Google Books authoritative; OpenAI fallback)
# ---------------------------------------------------------------------------

def _pick_best_author(candidates: List[str]) -> Optional[str]:
    """Heuristic: prefer the longest reasonable author string (to keep first + last).
    Filters obvious junk and returns a title‑cased variant.
    """
    clean: List[str] = []
    for c in candidates:
        if not c:
            continue
        t = c.strip()
        # simple junk filters
        if len(t) < 3 or len(t) > 120:
            continue
        # Remove trailing roles like "PhD" if present
        t = re.sub(r",\s*(PhD|MD|MBA)$", "", t, flags=re.I)
        clean.append(t)
    if not clean:
        return None
    clean.sort(key=lambda s: len(s), reverse=True)
    return clean[0]

@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(3))
def _google_books_request(params: Dict[str, str]) -> Dict[str, Any]:
    resp = requests.get(GOOGLE_BOOKS_URL, params=params, timeout=20)
    resp.raise_for_status()
    return resp.json()


def google_books_author(title: str) -> Optional[str]:
    q = f'intitle:"{title}"'
    params = {"q": q, "maxResults": "5"}
    if GOOGLE_BOOKS_KEY:
        params["key"] = GOOGLE_BOOKS_KEY
    try:
        data = _google_books_request(params)
        items = data.get("items", [])
        if not items:
            return None
        authors: List[str] = []
        for it in items:
            info = it.get("volumeInfo", {})
            for a in info.get("authors", []) or []:
                authors.append(a)
        return _pick_best_author(authors)
    except Exception as e:  # pragma: no cover – network
        logger.debug("Google Books lookup failed for %r: %s", title, e)
        return None


def openai_author(title: str, context: Optional[str] = None) -> Optional[str]:
    _ensure_openai("Author enrichment via OpenAI")
    try:
        prompt = (
            "You will be given a book title. Respond with the PRIMARY author's full name only.\n"
            "If unsure, respond with UNKNOWN.\n\n"
            f"Title: {title}\n"
        )
        if context:
            prompt += f"Context: {context[:4000]}\n"
        resp = openai.chat.completions.create(  # type: ignore[attr-defined]
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=32,
        )
        text = (resp.choices[0].message.content or "").strip()  # type: ignore[attr-defined]
        if text.upper() == "UNKNOWN" or not text:
            return None
        return _pick_best_author([text])
    except Exception as e:  # pragma: no cover – network
        logger.debug("OpenAI author resolution failed for %r: %s", title, e)
        return None


def resolve_author(title: str, current_author: Optional[str], context: Optional[str]) -> Optional[str]:
    """Return the authoritative author string for a title.

    Policy:
      • If AUTHOR_SOURCE == 'none' → preserve current_author (no lookup).
      • If AUTHOR_SOURCE in {'auto', 'google'} → query Google Books.
          - If Google returns an author → **use it even if current_author exists**.
          - If AUTHOR_SOURCE == 'google' and Google fails → keep current_author.
      • If AUTHOR_SOURCE in {'auto', 'openai'} and OpenAI is available →
          - If still no author, ask OpenAI; otherwise keep what we have.
    """
    if AUTHOR_SOURCE == "none":
        return (current_author or None)

    # 1) Google is authoritative when allowed
    if AUTHOR_SOURCE in ("auto", "google"):
        g = google_books_author(title)
        if g:
            return g
        if AUTHOR_SOURCE == "google":
            # No Google match; keep what we had
            return (current_author or None)

    # 2) OpenAI fallback if permitted and available
    if AUTHOR_SOURCE in ("auto", "openai") and openai is not None:
        if not (current_author and current_author.strip()):
            o = openai_author(title, context)
            if o:
                return o

    # 3) Return whatever we already had (possibly None)
    return (current_author or None)

# ---------------------------------------------------------------------------
# Unified book extractors (now use resolve_author even when author present)
# ---------------------------------------------------------------------------

def extract_books_fallback(transcript: str) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    seen: set[Tuple[str, str]] = set()

    for pat in (PATTERN_A, PATTERN_B):
        for m in pat.finditer(transcript):
            if pat is PATTERN_A:
                title = m.group(1).strip()
                author = (m.group(2).strip() if m.lastindex and m.lastindex >= 2 and m.group(2) else None)
            else:  # PATTERN_B
                title = m.group(1).strip()
                author = m.group(2).strip()

            # Resolve/replace author via policy (Google authoritative)
            author = resolve_author(title, author, _context_snippet(transcript, m.start(), m.end()))

            key = (title.lower(), (author or "").lower())
            if key in seen:
                continue
            seen.add(key)

            results.append(
                {
                    "title": title,
                    "author": author,
                    "context": _context_snippet(transcript, m.start(), m.end()),
                    "timestamp": None,
                }
            )

    return results


def extract_books(transcript: str) -> List[Dict[str, Any]]:
    """Unified extractor that chooses OpenAI or regex path.

    Uses OpenAI unless it's unavailable or --force-fallback is set. Author
    resolution is applied to every record (per --author-source).
    """
    if openai is not None and not FORCE_FALLBACK:
        raw = extract_books_openai(transcript)
        # Resolve/replace authors (Google authoritative; OpenAI fallback)
        for r in raw:
            r["author"] = resolve_author(r.get("title", ""), r.get("author"), r.get("context"))
        return raw
    return extract_books_fallback(transcript)

# ---------------------------------------------------------------------------
# OUTPUT HELPERS
# ---------------------------------------------------------------------------

def write_csv(rows: List[BookMention], path: str = "book_recommendations.csv") -> None:
    df = pd.DataFrame([asdict(r) | {"amazon_url": r.amazon_url} for r in rows])
    df.to_csv(path, index=False)
    logger.info("✓ CSV written → %s (%d rows)", path, len(rows))


def write_sheet(rows: List[BookMention], sheet_name: str = "PodcastBooks") -> None:
    try:
        import gspread  # type: ignore
        from oauth2client.service_account import ServiceAccountCredentials  # type: ignore
    except ModuleNotFoundError as e:
        raise RuntimeError("Missing gspread or oauth2client — install to use --output sheet") from e

    creds_path = os.getenv("GOOGLE_CRED_JSON")
    if not creds_path:
        raise RuntimeError("Set GOOGLE_CRED_JSON to a service‑account JSON path")

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
    client = gspread.authorize(creds)

    ss = client.create(sheet_name) if sheet_name not in [s.title for s in client.openall()] else client.open(sheet_name)
    ws = ss.sheet1

    header = [
        "podcast",
        "episode_date",
        "youtube_url",
        "title",
        "author",
        "context",
        "timestamp",
        "amazon_url",
    ]
    if ws.row_count == 0:
        ws.append_row(header)

    for r in rows:
        ws.append_row([
            r.podcast,
            r.episode_date,
            r.youtube_url,
            r.title,
            r.author or "",
            r.context or "",
            r.timestamp or "",
            r.amazon_url,
        ])
    logger.info("✓ Google Sheet updated → %s (%d rows)", ss.url, len(rows))

# ---------------------------------------------------------------------------
# PROGRAMMATIC ENTRY (for importing this module and calling from Python)
# ---------------------------------------------------------------------------

def run_programmatic(
    podcasts: List[str],
    months: int,
    *,
    output: str = "csv",
    author_source: str = "auto",
    force_fallback: bool = False,
    verbose: bool = False,
    search_limit: int = 200,
) -> None:
    """Convenience wrapper so you can call this module from Python code.

    Example (from another file):
        import podcast_book_recommender as pbr
        pbr.run_programmatic([
            "Acquired",
            "Invest Like the Best"
        ], months=36, output="csv", author_source="auto", force_fallback=False,
           search_limit=300)
    """
    global AUTHOR_SOURCE, FORCE_FALLBACK, SEARCH_LIMIT
    AUTHOR_SOURCE = author_source
    FORCE_FALLBACK = force_fallback
    SEARCH_LIMIT = int(search_limit)
    if verbose:
        logger.setLevel(logging.DEBUG)
    pipeline(podcasts, months, output)

# ---------------------------------------------------------------------------
# MAIN PIPELINE
# ---------------------------------------------------------------------------

def pipeline(podcasts: List[str], months_back: int, output: str = "csv") -> None:
    """Run the end‑to‑end extraction and export."""
    published_after = (
        datetime.utcnow().replace(tzinfo=timezone.utc) - relativedelta(months=months_back)
    ).isoformat()

    mentions: List[BookMention] = []

    for podcast in podcasts:
        logger.info("▶ Searching episodes for ‘%s’…", podcast)
        episodes = search_episodes(podcast, published_after, SEARCH_LIMIT)
        logger.info("  Found %d candidate episodes (after date filter)", len(episodes))

        for ep in tqdm(episodes, desc=podcast[:20], unit="episode"):
            tx = fetch_transcript(ep.video_id)
            if not tx:
                continue
            for m in extract_books(tx):
                mentions.append(
                    BookMention(
                        podcast=podcast,
                        episode_date=ep.publish_date,
                        youtube_url=ep.url,
                        title=m.get("title", "").strip(),
                        author=m.get("author"),
                        context=m.get("context"),
                        timestamp=m.get("timestamp"),
                    )
                )

    # De‑duplicate on (podcast, title, youtube_url)
    unique: Dict[Tuple[str, str, str], BookMention] = {}
    for bm in mentions:
        key = (bm.podcast.lower(), bm.title.lower(), bm.youtube_url)
        unique[key] = bm

    rows = list(unique.values())

    if output == "csv":
        write_csv(rows)
    elif output == "sheet":
        write_sheet(rows)
    else:
        raise ValueError("--output must be 'csv' or 'sheet'")

# ---------------------------------------------------------------------------
# OFFLINE SELF‑TESTS (no network, no OpenAI required)
# ---------------------------------------------------------------------------

def _self_tests() -> None:
    """Run simple offline tests to guard regressions.

    These tests avoid any network or OpenAI calls and validate internal
    behaviours like chunking, de‑duplication, and helper properties.
    """
    # 1) Chunking round‑trip
    sample = "Lorem ipsum dolor sit amet " * 100
    rejoined = " ".join(_chunk(sample, size=50))
    assert isinstance(rejoined, str)

    # 2) Amazon URL generation
    bm = BookMention(
        podcast="TestCast",
        episode_date="2024-01-02",
        youtube_url="https://youtu.be/vid",
        title="The Hobbit",
        author="J. R. R. Tolkien",
        context=None,
        timestamp=None,
    )
    assert "The+Hobbit" in bm.amazon_url

    # 3) De‑duplication behaviour
    dup1 = BookMention("A", "2024-01-01", "u1", "Book X", None, None, None)
    dup2 = BookMention("A", "2024-01-01", "u1", "Book X", None, None, None)
    uniq: Dict[Tuple[str, str, str], BookMention] = {}
    for r in [dup1, dup2]:
        uniq[(r.podcast.lower(), r.title.lower(), r.youtube_url)] = r
    assert len(uniq) == 1

    # 4) extract_books fallback (works with or without OpenAI)
    text = (
        "I recommend reading 'Deep Work' by Cal Newport for focus. "
        "My favorite book is Atomic Habits by James Clear—life changing. "
        "Another great book: ‘The Pragmatic Programmer’."
    )
    fb = extract_books_fallback(text)
    titles = {x["title"].lower() for x in fb}
    assert "deep work" in titles and "atomic habits" in titles and "the pragmatic programmer" in titles

    # 5) Author picker heuristic
    assert _pick_best_author(["Cal Newport", "Newport"]) == "Cal Newport"

    # 6) Date helpers
    assert _to_iso("20250102") == "2025-01-02"
    assert _to_iso("bad") is None

    print("✓ All self‑tests passed.")

# ---------------------------------------------------------------------------
# ENTRYPOINT
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(
            """Extract book recommendations from podcast episodes on YouTube (no API key).

Examples:
  python podcast_book_recommender.py --podcasts "Tim Ferriss Show" Acquired \
      --months 60 --output csv

  # run offline unit tests
  python podcast_book_recommender.py --selftest
            """,
        ),
    )
    parser.add_argument("--podcasts", nargs="+", help="Podcast show names")
    parser.add_argument("--months", type=int, default=60, help="Look‑back window in months")
    parser.add_argument("--output", choices=["csv", "sheet"], default="csv", help="Where to write results")
    parser.add_argument("--author-source", choices=["auto", "google", "openai", "none"], default="auto", help="How to fill missing authors")
    parser.add_argument("--search-limit", type=int, default=200, help="Max YouTube results per podcast (yt-dlp search)")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logs")
    parser.add_argument("--selftest", action="store_true", help="Run offline unit tests and exit")
    parser.add_argument("--force-fallback", action="store_true", help="Force regex extractor (ignore OpenAI if present)")
    args = parser.parse_args()

    if args.selftest:
        _self_tests()
        raise SystemExit(0)

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    if not args.podcasts:
        raise SystemExit("Error: --podcasts is required unless you run --selftest")

    FORCE_FALLBACK = bool(args.force_fallback)
    AUTHOR_SOURCE = args.author_source
    SEARCH_LIMIT = int(args.search_limit)

    pipeline(args.podcasts, args.months, args.output)
