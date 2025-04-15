import pandas as pd
from collections import defaultdict
from .categorizer import categorize_post
from .confidenceScore_logger import log_confidence_summary

# --- Group posts by weekly (or custom) period and categorize them ---
def group_posts_by_period(posts, period='W'):
    """
    Groups posts by a time period (default = week), categorizes them,
    and returns a nested dictionary of post counts per category per period.

    Args:
        posts (list of dict): List of posts with 'text' and 'timestamp'
        period (str): Pandas period string (e.g. 'W' = weekly)

    Returns:
        dict: {period: {category: count}}
    """
    # Convert post list into a DataFrame
    df = pd.DataFrame(posts)

    # Parse timestamps and extract the start date of each time period
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['period'] = df['timestamp'].dt.to_period(period).apply(lambda p: p.start_time.strftime('%Y-%m-%d'))

    # Apply semantic categorization function to each post
    df[['category', 'confidence']] = df['text'].apply(
        lambda text: pd.Series(categorize_post(text))
    )

    # Log confidence scores to CSV (optional analytics/reporting)
    log_confidence_summary(df)

    # Count number of posts per (period, category)
    period_counts = defaultdict(lambda: defaultdict(int))
    for _, row in df.iterrows():
        period = str(row['period'])
        category = row['category'][0] if isinstance(row['category'], list) else row['category']
        period_counts[period][category] += 1

    return period_counts

# --- Analyze trends and summarize top categories ---
def summarize_trends(period_counts):
    """
    Summarizes the categorized post counts into:
    - Weekly top categories
    - Overall top category
    - Raw weekly counts

    Args:
        period_counts (dict): Output from group_posts_by_period()

    Returns:
        dict: Summary object for frontend visualization
    """
    records = []
    # Flatten period/category/count structure into a list of dicts
    for period, cats in period_counts.items():
        for cat, count in cats.items():
            records.append({"period": period, "category": cat, "count": count})
    df = pd.DataFrame(records)

    # Get the top category for each week
    top_per_week = (
        df.sort_values("count", ascending=False)
          .groupby("period")
          .first()
          .reset_index()
    )

    # Get the top overall category across all weeks
    overall = df.groupby("category")["count"].sum().reset_index()
    top_overall = overall.sort_values("count", ascending=False).iloc[0].to_dict()

    return {
        "weekly_counts": period_counts,                        # Raw counts for plotting
        "top_category_per_week": top_per_week.to_dict(orient="records"),
        "top_overall_category": top_overall
    }
