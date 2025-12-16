#!/usr/bin/env python3
"""
View and compare processing metrics across phases

Shows quality metrics, costs, and performance for Phase 1, 2, 3
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal
from app.services.metrics_service import MetricsService
from app.models.processing_metrics import ProcessingMetrics


def print_section(title):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def view_phase_summary(phase: str):
    """View summary for a specific phase"""
    db = SessionLocal()

    try:
        summary = MetricsService.get_phase_summary(db, phase)

        print_section(f"{phase.upper()} SUMMARY")

        if summary.get('total_episodes', 0) == 0:
            print(f"❌ No episodes processed in {phase} yet")
            print(f"\nTo process an episode in {phase}:")
            print(f"  python scripts/process_all_pending.py --limit 1")
            return

        print(f"📊 Episodes Processed: {summary['total_episodes']}")
        print(f"\n💰 Cost Metrics:")
        print(f"  Total cost: ${summary['total_cost_usd']:.2f}")
        print(f"  Avg cost per episode: ${summary['avg_cost_per_episode']:.4f}")

        print(f"\n⏱️  Performance Metrics:")
        print(f"  Avg processing time: {summary['avg_processing_time_seconds']:.1f} seconds ({summary['avg_processing_time_seconds']/60:.1f} minutes)")

        print(f"\n📚 Recommendation Metrics:")
        print(f"  Total recommendations: {summary['total_recommendations']}")
        print(f"  Avg per episode: {summary['avg_recommendations_per_episode']:.1f}")

        print(f"\n✅ Quality Metrics:")
        print(f"  Complete transcripts: {summary['complete_transcripts']}/{summary['total_episodes']} ({summary['complete_transcript_rate']:.1f}%)")
        print(f"  Episodes with errors: {summary['episodes_with_errors']}/{summary['total_episodes']} ({summary['error_rate']:.1f}%)")

    finally:
        db.close()


def compare_phases(phase1: str, phase2: str):
    """Compare two phases"""
    db = SessionLocal()

    try:
        comparison = MetricsService.compare_phases(db, phase1, phase2)

        if 'error' in comparison:
            print(f"❌ {comparison['error']}")
            return

        print_section(f"COMPARISON: {phase1.upper()} vs {phase2.upper()}")

        # Cost comparison
        cost = comparison['cost_comparison']
        print(f"💰 Cost Comparison:")
        print(f"  {phase1}: ${cost['phase1_avg']:.4f} per episode")
        print(f"  {phase2}: ${cost['phase2_avg']:.4f} per episode")
        print(f"  Savings: ${cost['savings_per_episode']:.4f} per episode ({cost['savings_percentage']:.1f}%)")

        if cost['savings_percentage'] > 0:
            print(f"  ✅ {phase2} is {cost['savings_percentage']:.1f}% cheaper!")
        else:
            print(f"  ⚠️ {phase2} is {abs(cost['savings_percentage']):.1f}% more expensive")

        # Performance comparison
        perf = comparison['performance_comparison']
        print(f"\n⏱️  Performance Comparison:")
        print(f"  {phase1}: {perf['phase1_avg_time']:.1f} seconds ({perf['phase1_avg_time']/60:.1f} min)")
        print(f"  {phase2}: {perf['phase2_avg_time']:.1f} seconds ({perf['phase2_avg_time']/60:.1f} min)")
        print(f"  Difference: {perf['time_difference_seconds']:.1f} seconds")

        if perf['time_difference_seconds'] > 0:
            print(f"  ✅ {phase2} is {perf['time_difference_seconds']:.1f} seconds faster!")
        else:
            print(f"  ⚠️ {phase2} is {abs(perf['time_difference_seconds']):.1f} seconds slower")

        # Quality comparison
        quality = comparison['quality_comparison']
        print(f"\n📚 Quality Comparison:")
        print(f"  {phase1}: {quality['phase1_avg_recs']:.1f} recommendations per episode")
        print(f"  {phase2}: {quality['phase2_avg_recs']:.1f} recommendations per episode")
        print(f"  Difference: {quality['recommendation_difference']:+.1f} ({quality['difference_percentage']:+.1f}%)")

        if quality['difference_percentage'] >= -10:
            print(f"  ✅ Quality maintained (within 10%)")
        else:
            print(f"  ⚠️ Quality decreased by {abs(quality['difference_percentage']):.1f}%")

    finally:
        db.close()


def list_all_metrics():
    """List all processing metrics"""
    db = SessionLocal()

    try:
        print_section("ALL PROCESSING METRICS")

        metrics = db.query(ProcessingMetrics).order_by(
            ProcessingMetrics.processing_date.desc()
        ).limit(20).all()

        if not metrics:
            print("No metrics found yet. Process some episodes first!")
            return

        print(f"{'Phase':<12} {'Episode ID':<38} {'Cost':<10} {'Recs':<6} {'Time (sec)':<12} {'Date'}")
        print("-" * 105)

        for m in metrics:
            phase = m.phase
            episode_id = m.episode_id[:35] + "..."
            cost = f"${m.estimated_cost:.4f}" if m.estimated_cost else "N/A"
            recs = str(m.unique_recommendations or 0)
            proc_time = f"{m.processing_time_seconds:.1f}s" if m.processing_time_seconds else "N/A"
            date = m.processing_date.strftime("%Y-%m-%d %H:%M") if m.processing_date else "N/A"

            print(f"{phase:<12} {episode_id:<38} {cost:<10} {recs:<6} {proc_time:<12} {date}")

        print("\n" + "-" * 100)
        print(f"Total metrics: {len(metrics)}")

    finally:
        db.close()


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='View and compare processing metrics across phases'
    )
    parser.add_argument(
        '--phase',
        type=str,
        choices=['phase_1', 'phase_2', 'phase_3'],
        help='View summary for specific phase'
    )
    parser.add_argument(
        '--compare',
        type=str,
        nargs=2,
        metavar=('PHASE1', 'PHASE2'),
        help='Compare two phases (e.g., phase_1 phase_2)'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all processing metrics'
    )

    args = parser.parse_args()

    if args.list:
        list_all_metrics()
    elif args.compare:
        compare_phases(args.compare[0], args.compare[1])
    elif args.phase:
        view_phase_summary(args.phase)
    else:
        # Default: show all phases
        for phase in ['phase_1', 'phase_2', 'phase_3']:
            view_phase_summary(phase)
            print()


if __name__ == "__main__":
    main()
