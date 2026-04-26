import pandas as pd
import numpy as np
import yaml
import networkx as nx

# --------------------
# LOAD DATA
# --------------------
def load_data(dataset="DATA1"):
    base = f"data/data/{dataset}"

    users = pd.read_csv(f"{base}/users.csv")

    with open(f"{base}/books.yaml", 'r', encoding='utf-8') as f:
        books = pd.json_normalize(yaml.safe_load(f))

    orders = pd.read_parquet(f"{base}/orders.parquet")

    return users, books, orders


# --------------------
# CLEAN DATA
# --------------------
def clean_users(users):
    users = users.drop_duplicates(subset='id')
    users['id'] = pd.to_numeric(users['id'], errors='coerce')
    users['phone'] = users['phone'].str.replace(r'\D', '', regex=True)
    users['email'] = users['email'].str.strip().str.lower()
    users['name'] = users['name'].str.lower().str.strip()
    users['address'] = users['address'].str.lower().str.strip()
    return users.dropna(subset=['id'])


def clean_books(books):
    books.columns = books.columns.str.replace(':', '')
    books = books.drop_duplicates(subset='id')
    books['id'] = pd.to_numeric(books['id'], errors='coerce')
    books['year'] = pd.to_numeric(books['year'], errors='coerce')
    return books.dropna(subset=['id'])


def parse_price(x):
    if pd.isna(x):
        return np.nan
    x = str(x)
    if '€' in x:
        val = pd.to_numeric(x.replace('€', '').replace('¢', '').replace(',', '.'), errors='coerce')
        return val * 1.2
    return pd.to_numeric(x.replace('$', ''), errors='coerce')

def clean_orders(orders):
    orders = orders.drop_duplicates(subset='id')

    for col in ['id', 'user_id', 'book_id', 'quantity']:
        orders[col] = pd.to_numeric(orders[col], errors='coerce')

    orders['timestamp'] = orders['timestamp'].astype(str)
    orders['timestamp'] = (
        orders['timestamp']
        .str.replace(';', ':', regex=False)
        .str.replace('A.M.', 'AM', regex=False)
        .str.replace('P.M.', 'PM', regex=False)
    )

    # 🔥 FIX: force proper datetime dtype
    orders['timestamp'] = pd.to_datetime(
        orders['timestamp'],
        errors='coerce',
        dayfirst=True,
        utc=True
    )

    # 🔥 drop bad timestamps BEFORE using .dt
    orders = orders.dropna(subset=['id', 'user_id', 'book_id', 'timestamp'])

    # 🔥 ensure dtype again (this guarantees .dt works)
    orders['timestamp'] = pd.to_datetime(orders['timestamp'])

    orders['unit_price_usd'] = orders['unit_price'].apply(parse_price)
    orders['paid_price'] = orders['quantity'] * orders['unit_price_usd']

    orders['date'] = orders['timestamp'].dt.date

    return orders

# --------------------
# METRICS
# --------------------
def compute_daily_revenue(orders):
    return (
        orders.groupby('date', as_index=False)['paid_price']
        .sum()
        .rename(columns={'paid_price': 'daily_revenue'})
    )


def top_5_days(daily_revenue):
    return (
        daily_revenue
        .sort_values('daily_revenue', ascending=False)
        .head(5)
    )


def compute_unique_users(users):
    u = users.copy()

    G = nx.Graph()
    G.add_nodes_from(u.index)

    for col in ['email', 'phone', 'name', 'address']:
        for idxs in u.groupby(col).groups.values():
            idxs = list(idxs)
            for i in range(len(idxs) - 1):
                G.add_edge(idxs[i], idxs[i + 1])

    return nx.number_connected_components(G)


def compute_author_sets(books):
    def normalize(x):
        return tuple(sorted([a.strip().lower() for a in str(x).split(',')]))

    books['author_set'] = books['author'].apply(normalize)
    return books['author_set'].nunique(), books


def most_popular_author(orders, books):
    df = orders.merge(
        books[['id', 'author_set']],
        left_on='book_id',
        right_on='id',
        how='left'
    )

    return (
        df.groupby('author_set')['quantity']
        .sum()
        .sort_values(ascending=False)
        .index[0]
    )


def best_customer(users, orders):
    u = users.copy()

    G = nx.Graph()
    G.add_nodes_from(u.index)

    for col in ['email', 'phone', 'name', 'address']:
        for idxs in u.groupby(col).groups.values():
            idxs = list(idxs)
            for i in range(len(idxs) - 1):
                G.add_edge(idxs[i], idxs[i + 1])

    u['group_id'] = u.index.map({
        i: gid for gid, comp in enumerate(nx.connected_components(G)) for i in comp
    })

    top_group = (
        u.merge(
            orders.groupby('user_id')['paid_price'].sum(),
            left_on='id',
            right_index=True
        )
        .groupby('group_id')['paid_price']
        .sum()
        .idxmax()
    )

    return u[u['group_id'] == top_group]['id'].tolist()