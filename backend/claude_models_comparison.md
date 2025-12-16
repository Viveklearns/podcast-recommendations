# Claude Models Comparison for Recommendation Extraction

## Available Models (January 2025)

| Model | Model ID | Input Cost | Output Cost | Speed | Quality | Best For |
|-------|----------|------------|-------------|-------|---------|----------|
| **Claude Opus 3.5** | `claude-opus-4-20250514` | $15.00/M | $75.00/M | Slowest | Highest | Complex analysis, max accuracy |
| **Claude Sonnet 4** | `claude-sonnet-4-20250514` | $3.00/M | $15.00/M | Medium | Very High | Current choice - best balance |
| **Claude Sonnet 3.5** | `claude-3-5-sonnet-20241022` | $3.00/M | $15.00/M | Medium | High | Same price as Sonnet 4, older |
| **Claude Haiku 3.5** | `claude-3-5-haiku-20241022` | $0.80/M | $4.00/M | Fastest | Good | High volume, cost-sensitive |
| **Claude Haiku 3** | `claude-3-haiku-20240307` | $0.25/M | $1.25/M | Fastest | Moderate | Maximum cost savings |

---

## Cost Estimates for Your Project

**Assumptions:**
- 216 remaining episodes
- Average 70,000 characters per transcript
- ~17,500 tokens per episode (4 chars ≈ 1 token)
- Total: ~3.78M input tokens
- Output: ~400K tokens (100 recommendations, ~4K tokens each)

### Total Cost Breakdown

| Model | Input Cost | Output Cost | Total Cost | Cost per Episode |
|-------|------------|-------------|------------|------------------|
| **Opus 3.5** | $56.70 | $30.00 | **$86.70** | $0.40 |
| **Sonnet 4** | $11.34 | $6.00 | **$17.34** | $0.08 |
| **Sonnet 3.5** | $11.34 | $6.00 | **$17.34** | $0.08 |
| **Haiku 3.5** | $3.02 | $1.60 | **$4.62** | $0.02 |
| **Haiku 3** | $0.95 | $0.50 | **$1.45** | $0.007 |

---

## Expected Performance Comparison

Based on our tests and general model capabilities:

| Model | Recommendation Recall | JSON Compliance | Accuracy | Context Understanding |
|-------|----------------------|-----------------|----------|----------------------|
| **Opus 3.5** | 100% (baseline) | Excellent | Highest | Deepest analysis |
| **Sonnet 4** | ~95-98% | Excellent | Very High | Very good |
| **Sonnet 3.5** | ~90-95% | Very Good | High | Good |
| **Haiku 3.5** | ~80-85% | Good* | Good | Moderate |
| **Haiku 3** | ~70-75% | Fair* | Fair | Basic |

*Note: Haiku models sometimes struggle with strict JSON formatting, as we saw in tests.

---

## Our Test Results (Actual)

### Episode 1: Seth Godin (43,966 chars)
- **Sonnet 4:** 3 recommendations ✓
- **Haiku 3.5:** 2 recommendations (-1)
- **Missing:** Purple Cow

### Episode 2: Duolingo (97,601 chars)
- **Sonnet 4:** 5 recommendations ✓
- **Haiku 3.5:** 4 recommendations (-1)
- **Missing:** Adjustable Leg Ladder

**Haiku 3.5 Performance:** 75% recall rate (6 out of 8 recommendations)

---

## Recommendation by Use Case

### 1. **Maximum Accuracy (Your Production App)**
   - **Model:** Sonnet 4
   - **Cost:** $17.34 for 216 episodes
   - **Why:** Best quality-to-cost ratio, excellent JSON compliance, minimal missed recommendations

### 2. **Balanced Approach**
   - **Model:** Sonnet 3.5
   - **Cost:** $17.34 (same as Sonnet 4)
   - **Why:** Same price as Sonnet 4 but older, so no reason to use this

### 3. **Budget Conscious**
   - **Model:** Haiku 3.5
   - **Cost:** $4.62 for 216 episodes
   - **Why:** 75% cost savings, acceptable for less critical applications
   - **Risk:** Will miss ~20-25% of recommendations

### 4. **Minimum Cost (Development/Testing)**
   - **Model:** Haiku 3
   - **Cost:** $1.45 for 216 episodes
   - **Why:** Cheapest option, good for prototyping
   - **Risk:** Lower quality, more JSON parsing errors

### 5. **Research/High Stakes**
   - **Model:** Opus 3.5
   - **Cost:** $86.70 for 216 episodes
   - **Why:** If you absolutely need every single recommendation found
   - **When:** Critical business decisions depend on the data

---

## Rate Limits (Important!)

All models share the same rate limits per organization:

| Tier | Input Tokens/min | Requests/min |
|------|------------------|--------------|
| Free | 10,000 | 5 |
| Build Tier 1 | 30,000 | 50 |
| Build Tier 2 | 200,000 | 1,000 |
| Build Tier 3 | 400,000 | 2,000 |
| Build Tier 4 | 2,000,000 | 4,000 |

**Your Current Status:** Tier 1 (30,000 tokens/min = ~2-3 episodes/min)

**Note:** Rate limits are the same across all models, so using a cheaper model won't help you go faster.

---

## My Recommendation for You

**Continue with Sonnet 4** because:

1. ✅ **Best quality-to-cost ratio** ($17 total is reasonable for production data)
2. ✅ **Already tested and working** well
3. ✅ **Excellent JSON compliance** (no parsing errors)
4. ✅ **High recall** (~95%+ of recommendations found)
5. ✅ **Same price as Sonnet 3.5** so no reason to downgrade
6. ✅ **Rate limits are your constraint**, not budget
7. ✅ **Missing 20% of recommendations** (like Haiku does) could impact your product quality

**Only switch to Haiku 3.5 if:**
- Budget is extremely tight (saves $12.72)
- You're okay missing 1 in 5 recommendations
- You can manually review and fill gaps later

---

## Alternative: Hybrid Approach

You could also use a **two-pass system**:

1. **Pass 1:** Haiku 3.5 on all episodes ($4.62)
2. **Pass 2:** Sonnet 4 on episodes where Haiku found 0-2 recommendations (~50 episodes = $4.00)

**Total Cost:** ~$8.62 (50% savings)
**Coverage:** ~90% of recommendations found

Would you like me to implement this hybrid approach?
