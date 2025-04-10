import pandas as pd
from collections import defaultdict
from .categorizer import categorize_post
from .confidenceScore_logger import log_confidence_summary

def group_posts_by_period(posts, period='W'):
    df = pd.DataFrame(posts)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['period'] = df['timestamp'].dt.to_period(period).apply(lambda p: p.start_time.strftime('%Y-%m-%d'))

    # Categorize once, extract category and confidence
    df[['category', 'confidence']] = df['text'].apply(
        lambda text: pd.Series(categorize_post(text))
    )
    log_confidence_summary(df)

    # Count per category per period
    period_counts = defaultdict(lambda: defaultdict(int))
    for _, row in df.iterrows():
        period = str(row['period'])
        category = row['category'][0] if isinstance(row['category'], list) else row['category']
        period_counts[period][category] += 1
    return period_counts

def summarize_trends(period_counts):
    records = []
    for period, cats in period_counts.items():
        for cat, count in cats.items():
            records.append({"period": period, "category": cat, "count": count})
    df = pd.DataFrame(records)

    top_per_week = (
        df.sort_values("count", ascending=False)
          .groupby("period")
          .first()
          .reset_index()
    )

    overall = df.groupby("category")["count"].sum().reset_index()
    top_overall = overall.sort_values("count", ascending=False).iloc[0].to_dict()

    return {
        "weekly_counts": period_counts,
        "top_category_per_week": top_per_week.to_dict(orient="records"),
        "top_overall_category": top_overall
    }
