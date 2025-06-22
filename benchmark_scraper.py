"""Performance comparison script for Washington County scraper"""

import time
import asyncio
from typing import Dict, Any
from sqlalchemy.orm import Session
from models.Jail import Jail
from scrapes.washington_so_ar import scrape_washington_so_ar_standard
from scrapes.washington_so_ar_optimized import scrape_washington_so_ar_optimized
from loguru import logger


def benchmark_scraper(
    session: Session, jail: Jail, scraper_func, scraper_name: str
) -> Dict[str, Any]:
    """
    Benchmark a scraper function and return performance metrics.

    Args:
        session: Database session
        jail: Jail object
        scraper_func: Scraper function to benchmark
        scraper_name: Name of the scraper for logging

    Returns:
        Dict containing performance metrics
    """
    logger.info(f"Benchmarking {scraper_name}...")

    start_time = time.time()
    try:
        scraper_func(
            session, jail, log_level="WARNING"
        )  # Reduce logging for cleaner output
        end_time = time.time()

        total_time = end_time - start_time
        logger.success(f"{scraper_name} completed in {total_time:.2f} seconds")

        return {
            "name": scraper_name,
            "success": True,
            "total_time": total_time,
            "error": None,
        }
    except Exception as e:
        end_time = time.time()
        total_time = end_time - start_time
        logger.error(f"{scraper_name} failed after {total_time:.2f} seconds: {e}")

        return {
            "name": scraper_name,
            "success": False,
            "total_time": total_time,
            "error": str(e),
        }


def compare_scrapers(session: Session, jail: Jail) -> None:
    """
    Compare the performance of standard vs optimized scrapers.

    Args:
        session: Database session
        jail: Jail object
    """
    logger.info("Starting scraper performance comparison...")
    logger.info("=" * 60)

    results = []

    # Test standard scraper
    standard_result = benchmark_scraper(
        session, jail, scrape_washington_so_ar_standard, "Standard Scraper"
    )
    results.append(standard_result)

    # Test optimized scraper with async
    optimized_result = benchmark_scraper(
        session,
        jail,
        lambda s, j, l: scrape_washington_so_ar_optimized(
            s, j, l, use_async=True, max_concurrent=10
        ),
        "Optimized Scraper (Async)",
    )
    results.append(optimized_result)

    # Test optimized scraper with threading
    threaded_result = benchmark_scraper(
        session,
        jail,
        lambda s, j, l: scrape_washington_so_ar_optimized(
            s, j, l, use_async=False, max_concurrent=5
        ),
        "Optimized Scraper (Threading)",
    )
    results.append(threaded_result)

    # Display results
    logger.info("=" * 60)
    logger.info("PERFORMANCE COMPARISON RESULTS")
    logger.info("=" * 60)

    successful_results = [r for r in results if r["success"]]

    if len(successful_results) > 1:
        fastest = min(successful_results, key=lambda x: x["total_time"])
        slowest = max(successful_results, key=lambda x: x["total_time"])

        for result in results:
            status = "✓" if result["success"] else "✗"
            time_str = f"{result['total_time']:.2f}s"

            if result["success"] and result == fastest:
                speedup = slowest["total_time"] / result["total_time"]
                logger.info(
                    f"{status} {result['name']}: {time_str} (FASTEST - {speedup:.1f}x speedup)"
                )
            elif result["success"]:
                speedup = result["total_time"] / fastest["total_time"]
                logger.info(
                    f"{status} {result['name']}: {time_str} ({speedup:.1f}x slower)"
                )
            else:
                logger.info(f"{status} {result['name']}: FAILED ({result['error']})")
    else:
        for result in results:
            status = "✓" if result["success"] else "✗"
            time_str = f"{result['total_time']:.2f}s" if result["success"] else "FAILED"
            logger.info(f"{status} {result['name']}: {time_str}")

    logger.info("=" * 60)


if __name__ == "__main__":
    # This script should be run with proper database setup
    logger.warning("This is a standalone performance comparison script.")
    logger.warning("Make sure to run it with proper database session and jail object.")
