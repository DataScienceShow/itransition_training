import pandas as pd
import plotly.express as px
from pipeline import *

def build_dashboard(dataset):
    users, books, orders = load_data(dataset)

    users = clean_users(users)
    books = clean_books(books)
    orders = clean_orders(orders)

    daily_rev = compute_daily_revenue(orders)
    top5 = top_5_days(daily_rev)

    unique_users = compute_unique_users(users)
    unique_sets, books = compute_author_sets(books)
    top_author = most_popular_author(orders, books)
    best_user = best_customer(users, orders)

    # format date
    top5['date'] = pd.to_datetime(top5['date']).dt.strftime('%Y-%m-%d')

    # chart
    fig = px.line(daily_rev, x='date', y='daily_revenue', title="Daily Revenue")

    html = f"""
    <html>
    <head>
        <title>{dataset} Dashboard</title>
        <style>
            body {{ font-family: Arial; margin: 40px; background:#f9f9f9; }}
            h1 {{ color:#333; }}
            .card {{ padding:15px; margin:10px; background:white; border-radius:8px; box-shadow:0 2px 5px rgba(0,0,0,0.1); }}
        </style>
    </head>
    <body>

        <h1>{dataset} Dashboard</h1>

        <div class="card">
            <h2>Metrics</h2>
            <p><b>Unique Users:</b> {unique_users}</p>
            <p><b>Unique Author Sets:</b> {unique_sets}</p>
            <p><b>Top Author:</b> {top_author}</p>
            <p><b>Best Customer:</b> {best_user}</p>
        </div>

        <div class="card">
            <h2>Top 5 Days</h2>
            {top5.to_html(index=False)}
        </div>

        <div class="card">
            <h2>Daily Revenue</h2>
            {fig.to_html(full_html=False)}
        </div>

    </body>
    </html>
    """

    with open(f"{dataset.lower()}_dashboard.html", "w", encoding="utf-8") as f:
        f.write(html)


if __name__ == "__main__":
    for ds in ["DATA1", "DATA2", "DATA3"]:
        build_dashboard(ds)