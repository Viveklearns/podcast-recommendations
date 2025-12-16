from typing import Dict, Optional
from datetime import datetime
import logging
from app.models.processing_metrics import ProcessingMetrics
from app.models.recommendation import Recommendation
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class MetricsService:
    """Service for tracking and storing processing metrics"""

    @staticmethod
    def save_processing_metrics(
        db: Session,
        episode_id: str,
        phase: str,
        transcript_metadata: Dict,
        claude_metadata: Dict,
        recommendations: list,
        ai_model: str,
        estimated_cost: float,
        processing_time: float,
        youtube_url: Optional[str] = None,
        had_errors: bool = False,
        error_message: Optional[str] = None
    ) -> ProcessingMetrics:
        """
        Save processing metrics to database

        Args:
            db: Database session
            episode_id: ID of episode processed
            phase: Processing phase ('phase_1', 'phase_2', 'phase_3')
            transcript_metadata: Metadata from transcript verification
            claude_metadata: Metadata from Claude processing
            recommendations: List of recommendations found
            ai_model: AI model used (e.g., 'claude-sonnet-4')
            estimated_cost: Estimated cost in USD
            processing_time: Time taken in seconds
            had_errors: Whether processing had errors
            error_message: Error message if any

        Returns:
            ProcessingMetrics object
        """

        # Count recommendation types
        books_count = sum(1 for r in recommendations if r.get('type') == 'book')
        movies_count = sum(1 for r in recommendations if r.get('type') in ['movie', 'tv_show'])
        products_count = sum(1 for r in recommendations if r.get('type') == 'product')

        # Calculate coverage
        coverage_verified = (
            transcript_metadata.get('character_count', 0) ==
            claude_metadata.get('total_characters_sent', 0)
        )

        metrics = ProcessingMetrics(
            episode_id=episode_id,
            phase=phase,
            processing_date=datetime.utcnow(),

            # Transcript metrics
            total_segments=transcript_metadata.get('total_segments'),
            character_count=transcript_metadata.get('character_count'),
            word_count=transcript_metadata.get('word_count'),
            start_time=transcript_metadata.get('start_time'),
            end_time=transcript_metadata.get('end_time'),
            duration_covered_seconds=transcript_metadata.get('duration_covered_seconds'),
            video_duration_seconds=transcript_metadata.get('video_duration_seconds'),
            coverage_percent=transcript_metadata.get('coverage_percent'),
            gaps_detected=transcript_metadata.get('gaps_detected'),
            is_complete=transcript_metadata.get('is_complete'),

            # Claude metrics
            total_chunks=claude_metadata.get('total_chunks'),
            total_characters_sent=claude_metadata.get('total_characters_sent'),
            first_chunk_position=claude_metadata.get('first_chunk', {}).get('position'),
            last_chunk_position=claude_metadata.get('last_chunk', {}).get('position'),
            coverage_verified=coverage_verified,

            # Recommendation metrics
            total_recommendations_found=claude_metadata.get('total_recommendations_found', 0),
            unique_recommendations=claude_metadata.get('unique_recommendations', 0),
            books_found=books_count,
            movies_found=movies_count,
            products_found=products_count,

            # Performance metrics
            ai_model_used=ai_model,
            estimated_cost=estimated_cost,
            processing_time_seconds=processing_time,

            # Error tracking
            had_errors=had_errors,
            error_message=error_message,

            # Video metadata
            youtube_url=youtube_url
        )

        db.add(metrics)
        db.commit()
        db.refresh(metrics)

        logger.info(f"Saved processing metrics for episode {episode_id} (phase: {phase})")

        return metrics

    @staticmethod
    def get_metrics_for_episode(db: Session, episode_id: str):
        """Get all processing metrics for an episode"""
        return db.query(ProcessingMetrics).filter(
            ProcessingMetrics.episode_id == episode_id
        ).order_by(ProcessingMetrics.processing_date.desc()).all()

    @staticmethod
    def get_metrics_by_phase(db: Session, phase: str):
        """Get all metrics for a specific phase"""
        return db.query(ProcessingMetrics).filter(
            ProcessingMetrics.phase == phase
        ).order_by(ProcessingMetrics.processing_date.desc()).all()

    @staticmethod
    def get_phase_summary(db: Session, phase: str) -> Dict:
        """Get summary statistics for a phase"""
        metrics = db.query(ProcessingMetrics).filter(
            ProcessingMetrics.phase == phase
        ).all()

        if not metrics:
            return {
                "phase": phase,
                "total_episodes": 0,
                "message": "No episodes processed in this phase yet"
            }

        total_episodes = len(metrics)
        total_cost = sum(m.estimated_cost or 0 for m in metrics)
        avg_processing_time = sum(m.processing_time_seconds or 0 for m in metrics) / total_episodes
        total_recommendations = sum(m.unique_recommendations or 0 for m in metrics)
        complete_transcripts = sum(1 for m in metrics if m.is_complete)
        episodes_with_errors = sum(1 for m in metrics if m.had_errors)

        return {
            "phase": phase,
            "total_episodes": total_episodes,
            "total_cost_usd": round(total_cost, 2),
            "avg_cost_per_episode": round(total_cost / total_episodes, 4),
            "avg_processing_time_seconds": round(avg_processing_time, 1),
            "total_recommendations": total_recommendations,
            "avg_recommendations_per_episode": round(total_recommendations / total_episodes, 1),
            "complete_transcripts": complete_transcripts,
            "complete_transcript_rate": round(complete_transcripts / total_episodes * 100, 1),
            "episodes_with_errors": episodes_with_errors,
            "error_rate": round(episodes_with_errors / total_episodes * 100, 1),
        }

    @staticmethod
    def compare_phases(db: Session, phase1: str, phase2: str) -> Dict:
        """Compare metrics between two phases"""
        summary1 = MetricsService.get_phase_summary(db, phase1)
        summary2 = MetricsService.get_phase_summary(db, phase2)

        if summary1['total_episodes'] == 0 or summary2['total_episodes'] == 0:
            return {
                "error": "Both phases need processed episodes for comparison"
            }

        cost_savings = summary1['avg_cost_per_episode'] - summary2['avg_cost_per_episode']
        cost_savings_pct = (cost_savings / summary1['avg_cost_per_episode']) * 100

        time_diff = summary1['avg_processing_time_seconds'] - summary2['avg_processing_time_seconds']

        rec_diff = summary2['avg_recommendations_per_episode'] - summary1['avg_recommendations_per_episode']
        rec_diff_pct = (rec_diff / summary1['avg_recommendations_per_episode']) * 100 if summary1['avg_recommendations_per_episode'] > 0 else 0

        return {
            "phase1": phase1,
            "phase2": phase2,
            "cost_comparison": {
                "phase1_avg": summary1['avg_cost_per_episode'],
                "phase2_avg": summary2['avg_cost_per_episode'],
                "savings_per_episode": round(cost_savings, 4),
                "savings_percentage": round(cost_savings_pct, 1),
            },
            "performance_comparison": {
                "phase1_avg_time": summary1['avg_processing_time_seconds'],
                "phase2_avg_time": summary2['avg_processing_time_seconds'],
                "time_difference_seconds": round(time_diff, 1),
            },
            "quality_comparison": {
                "phase1_avg_recs": summary1['avg_recommendations_per_episode'],
                "phase2_avg_recs": summary2['avg_recommendations_per_episode'],
                "recommendation_difference": round(rec_diff, 1),
                "difference_percentage": round(rec_diff_pct, 1),
            }
        }
