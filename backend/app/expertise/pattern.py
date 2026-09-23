"""Expert Pattern Extraction (spec section 11).

Retrieval returns individual episodes, but the recommendation should reflect the *common*
successful pattern across them, not just the single best match -- more robust, and
demonstrates multi-episode consensus (spec section 29).
"""
from __future__ import annotations

from collections import Counter
from functools import reduce

from app.expertise.matcher import ExperienceMatch


def _lcs(a: list[str], b: list[str]) -> list[str]:
    """Longest common subsequence of two action sequences (classic DP)."""
    n, m = len(a), len(b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    result: list[str] = []
    i, j = n, m
    while i > 0 and j > 0:
        if a[i - 1] == b[j - 1]:
            result.append(a[i - 1])
            i -= 1
            j -= 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            i -= 1
        else:
            j -= 1
    result.reverse()
    return result


def extract_expert_pattern(matches: list[ExperienceMatch]) -> dict | None:
    """Extracts the common successful action sequence from a set of similar episodes.
    Returns None if no successful episode is available (caller should fall back to
    "no reliable experience found", spec section 32)."""
    successful = [m for m in matches if m.episode.outcome.get("successful", False)]
    if not successful:
        return None

    sequences = [tuple(m.episode.action_sequence) for m in successful]

    if len(sequences) == 1:
        pattern = list(sequences[0])
        return {
            "pattern": pattern,
            "supporting_episode_count": 1,
            "method": "single_episode",
        }

    counts = Counter(sequences)
    most_common_seq, most_common_count = counts.most_common(1)[0]
    if most_common_count >= 2:
        return {
            "pattern": list(most_common_seq),
            "supporting_episode_count": most_common_count,
            "method": "exact_match_consensus",
        }

    # No two episodes agree exactly -- fall back to the longest common subsequence shared
    # across all of them (spec section 11's worked example).
    common = reduce(_lcs, [list(s) for s in sequences])
    if not common:
        # Sequences share nothing in common; use the single highest-similarity episode.
        best = max(successful, key=lambda m: m.similarity)
        return {
            "pattern": list(best.episode.action_sequence),
            "supporting_episode_count": 1,
            "method": "best_match_no_consensus",
        }

    return {
        "pattern": common,
        "supporting_episode_count": len(sequences),
        "method": "longest_common_subsequence",
    }
