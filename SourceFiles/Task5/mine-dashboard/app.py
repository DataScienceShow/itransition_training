import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from scipy import stats
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table
from reportlab.lib.styles import getSampleStyleSheet

st.set_page_config(layout="wide")

# -------------------------
# LOAD DATA
# -------------------------
@st.cache_data
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1OdOOq3IjXKoe8ppLVn2PxcCWz0MzKe57/export?format=csv&gid=1140580581"
    df = pd.read_csv(url)
    df["Date"] = pd.to_datetime(df["Date"])
    return df

df = load_data()
mines = df.columns[1:]
df["Total"] = df[mines].sum(axis=1)

# -------------------------
# SIDEBAR
# -------------------------
st.sidebar.title("Settings")

selected = st.sidebar.multiselect(
    "Select Mines",
    list(mines) + ["Total"],
    default=["Total"]
)

chart_type = st.sidebar.selectbox("Chart Type", ["line", "bar", "stacked"])
trend_degree = st.sidebar.selectbox("Trendline Degree", [1, 2, 3, 4])

# anomaly params
st.sidebar.header("Anomaly Detection")
iqr_mult = st.sidebar.slider("IQR Multiplier", 1.0, 3.0, 1.5)
z_thresh = st.sidebar.slider("Z-score Threshold", 1.0, 5.0, 3.0)
ma_window = st.sidebar.slider("Moving Avg Window", 2, 20, 5)
ma_pct = st.sidebar.slider("MA Distance %", 0.0, 1.0, 0.2)

# -------------------------
# ANOMALY FUNCTIONS
# -------------------------
def detect_iqr(series):
    q1, q3 = series.quantile(0.25), series.quantile(0.75)
    iqr = q3 - q1
    return (series < q1 - iqr_mult * iqr) | (series > q3 + iqr_mult * iqr)

def detect_z(series):
    return np.abs(stats.zscore(series, nan_policy='omit')) > z_thresh

def detect_ma(series):
    ma = series.rolling(ma_window).mean()
    return np.abs(series - ma) / (ma + 1e-9) > ma_pct

def detect_grubbs(series):
    return np.abs(stats.zscore(series, nan_policy='omit')) > 3

# -------------------------
# STATS
# -------------------------
st.title("Mining Dashboard")

stats_data = []
for col in selected:
    s = df[col]
    stats_data.append({
        "Mine": col,
        "Mean": round(s.mean(), 2),
        "Std Dev": round(s.std(), 2),
        "Median": round(s.median(), 2),
        "IQR": round(s.quantile(0.75) - s.quantile(0.25), 2)
    })

st.subheader("Statistics")
st.dataframe(pd.DataFrame(stats_data))

# -------------------------
# COMBINED CHART
# -------------------------
st.subheader("Combined Output")

if chart_type == "line":
    fig = px.line(df, x="Date", y=selected)
elif chart_type == "bar":
    fig = px.bar(df, x="Date", y=selected)
else:
    fig = px.area(df, x="Date", y=selected)

st.plotly_chart(fig, use_container_width=True)

# -------------------------
# PER MINE CHARTS
# -------------------------
all_anomalies = {}

for col in selected:
    st.subheader(col)

    temp = df.copy()
    temp["Anomaly"] = (
        detect_iqr(temp[col]) |
        detect_z(temp[col]) |
        detect_ma(temp[col]) |
        detect_grubbs(temp[col])
    )

    all_anomalies[col] = temp[temp["Anomaly"]]

    if chart_type == "line":
        fig = px.line(temp, x="Date", y=col)
    elif chart_type == "bar":
        fig = px.bar(temp, x="Date", y=col)
    else:
        fig = px.area(temp, x="Date", y=col)

    # anomalies
    fig.add_scatter(
        x=temp[temp["Anomaly"]]["Date"],
        y=temp[temp["Anomaly"]][col],
        mode="markers",
        marker=dict(color="red", size=10, symbol="x"),
        name="Anomalies"
    )

    # trendline
    x = np.arange(len(temp))
    y = temp[col].ffill()
    trend = np.poly1d(np.polyfit(x, y, trend_degree))(x)

    fig.add_scatter(
        x=temp["Date"],
        y=trend,
        name="Trend",
        line=dict(dash="dash")
    )

    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(temp[temp["Anomaly"]][["Date", col]])

# -------------------------
# PDF GENERATION
# -------------------------
def generate_pdf():
    doc = SimpleDocTemplate("report.pdf")
    styles = getSampleStyleSheet()
    content = []

    content.append(Paragraph("Mining Report", styles["Title"]))
    content.append(Spacer(1, 20))

    # stats table
    table_data = [["Mine", "Mean", "Std", "Median", "IQR"]]
    for row in stats_data:
        table_data.append(list(row.values()))
    content.append(Table(table_data))
    content.append(Spacer(1, 20))

    # per mine
    for col in selected:
        content.append(Paragraph(col, styles["Heading2"]))

        temp = df.copy()
        temp["Anomaly"] = (
            detect_iqr(temp[col]) |
            detect_z(temp[col]) |
            detect_ma(temp[col]) |
            detect_grubbs(temp[col])
        )

        # chart image
        if chart_type == "line":
            fig = px.line(temp, x="Date", y=col)
        elif chart_type == "bar":
            fig = px.bar(temp, x="Date", y=col)
        else:
            fig = px.area(temp, x="Date", y=col)
        fig.write_image(f"{col}.png")

        content.append(Image(f"{col}.png", width=500, height=250))
        content.append(Spacer(1, 10))

        anomalies = temp[temp["Anomaly"]]

        if not anomalies.empty:
            content.append(Paragraph("Anomalies", styles["Heading3"]))

            for _, row in anomalies.iterrows():
                val = row[col]
                mean = temp[col].mean()

                desc = "Spike" if val > mean else "Drop"

                content.append(Paragraph(
                    f"{desc} on {row['Date'].date()} → value {round(val,2)}",
                    styles["Normal"]
                ))

        content.append(Spacer(1, 20))

    doc.build(content)

# -------------------------
# BUTTON
# -------------------------
if st.button("Export Detailed PDF"):
    generate_pdf()
    with open("report.pdf", "rb") as f:
        st.download_button("Download PDF", f, "report.pdf")