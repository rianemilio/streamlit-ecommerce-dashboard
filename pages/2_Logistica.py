import streamlit as st
import pandas as pd
import plotly.express as px
import os
from style_config import CSS, PRIMARY_COLOR, POSITIVE_COLOR, NEGATIVE_COLOR

# --- CONFIGURAÇÃO DA PÁGINA E CSS ---
st.set_page_config(page_title="Análise de Logística", layout="wide")
st.title("Visão Geral da Logística")
st.markdown(CSS, unsafe_allow_html=True)


# --- CARREGAMENTO DOS DADOS ---
@st.cache_data
def load_data():
    data_path = "data/"
    try:
        cols_orders = [
            "order_id",
            "customer_id",
            "order_purchase_timestamp",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ]
        cols_items = ["order_id", "price"]
        cols_customers = ["customer_id", "customer_unique_id", "customer_state"]

        orders = pd.read_parquet(
            os.path.join(data_path, "olist_orders_dataset.parquet"),
            columns=cols_orders,
            engine="fastparquet",
        )
        items = pd.read_parquet(
            os.path.join(data_path, "olist_order_items_dataset.parquet"),
            columns=cols_items,
            engine="fastparquet",
        )
        customers = pd.read_parquet(
            os.path.join(data_path, "olist_customers_dataset.parquet"),
            columns=cols_customers,
            engine="fastparquet",
        )

    except Exception as e:
        st.error(f"Erro ao ler os arquivos Parquet. Detalhe: {e}")
        st.stop()

    df = orders.merge(customers, on="customer_id").merge(items, on="order_id")
    for col in [
        "order_purchase_timestamp",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    df.dropna(
        subset=[
            "order_purchase_timestamp",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ],
        inplace=True,
    )
    df["customer_state"] = df["customer_state"].astype("category")
    return df


# --- PROCESSAMENTO DOS DADOS DE LOGÍSTICA ---
def process_logistics_data(df):
    df["delivery_time"] = (
        df["order_delivered_customer_date"] - df["order_purchase_timestamp"]
    ).dt.days
    df["estimated_time"] = (
        df["order_estimated_delivery_date"] - df["order_purchase_timestamp"]
    ).dt.days
    df["delivery_delay"] = (
        df["order_delivered_customer_date"] - df["order_estimated_delivery_date"]
    ).dt.days
    df = df[df["delivery_time"] >= 0]
    df["delivery_status"] = (
        df["delivery_delay"]
        .apply(lambda x: "Atrasado" if x > 0 else "No Prazo")
        .astype("category")
    )
    return df


# --- LÓGICA PRINCIPAL ---
df_logistics = load_data()
df_processed = process_logistics_data(df_logistics)

# --- FILTROS NA BARRA LATERAL ---
st.sidebar.header("Filtros")
min_date_log, max_date_log = (
    df_processed["order_purchase_timestamp"].min().date(),
    df_processed["order_purchase_timestamp"].max().date(),
)
start_date_log, end_date_log = st.sidebar.date_input(
    "Período:",
    value=(min_date_log, max_date_log),
    min_value=min_date_log,
    max_value=max_date_log,
    key="logistics_date_range",
)
states_log = sorted(df_processed["customer_state"].cat.categories)
selected_states_log = st.sidebar.multiselect(
    "Estado:", options=states_log, default=states_log, key="logistics_states"
)
start_date_log = pd.to_datetime(start_date_log)
end_date_log = pd.to_datetime(end_date_log) + pd.Timedelta(days=1)
query = "customer_state in @selected_states_log and order_purchase_timestamp >= @start_date_log and order_purchase_timestamp < @end_date_log"
df_filtered_log = df_processed.query(query)

# --- LAYOUT DO DASHBOARD ---
if not df_filtered_log.empty:
    avg_delivery_time = df_filtered_log["delivery_time"].mean()
    avg_estimated_time = df_filtered_log["estimated_time"].mean()
    delay_percentage = (
        (df_filtered_log["delivery_status"] == "Atrasado").sum()
        / len(df_filtered_log)
        * 100
    )

    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric(label="Tempo Médio Entrega", value=f"{avg_delivery_time:.1f} Dias")
    kpi2.metric(label="Tempo Médio Estimado", value=f"{avg_estimated_time:.1f} Dias")
    kpi3.metric(label="% de Atrasos", value=f"{delay_percentage:.1f}%")

    st.markdown("---")

    col1, col2 = st.columns([2, 3])
    with col1:
        st.markdown(
            '<p class="chart-title">Performance de Entrega</p>', unsafe_allow_html=True
        )
        status_count = df_filtered_log["delivery_status"].value_counts()
        pull_values = [
            0.1 if label == "Atrasado" else 0 for label in status_count.index
        ]
        fig_pie = px.pie(
            status_count,
            values=status_count.values,
            names=status_count.index,
            hole=0.5,
            color=status_count.index,
            color_discrete_map={"No Prazo": POSITIVE_COLOR, "Atrasado": NEGATIVE_COLOR},
            height=225,
        )
        fig_pie.update_traces(
            textinfo="percent", pull=pull_values, insidetextfont=dict(size=14)
        )
        fig_pie.update_layout(
            showlegend=True,
            margin=dict(l=20, r=20, t=20, b=20),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5,
                title="",
            ),
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        st.markdown(
            '<p class="chart-title">Tempo Médio de Entrega (Mensal)</p>',
            unsafe_allow_html=True,
        )
        monthly_delivery_time = (
            df_filtered_log.set_index("order_purchase_timestamp")
            .resample("ME")["delivery_time"]
            .mean()
            .reset_index()
        )
        fig_line = px.line(
            monthly_delivery_time,
            x="order_purchase_timestamp",
            y="delivery_time",
            color_discrete_sequence=[PRIMARY_COLOR],
            height=225,
        )
        fig_line.update_layout(
            margin=dict(l=10, r=10, t=20, b=20), yaxis_title="Dias", xaxis_title=None
        )
        st.plotly_chart(fig_line, use_container_width=True)

    state_performance = (
        df_filtered_log.groupby("customer_state", observed=False)
        .agg(
            avg_delivery_time=("delivery_time", "mean"),
            delay_percentage=(
                "delivery_status",
                lambda x: (x == "Atrasado").sum() / len(x) * 100,
            ),
        )
        .reset_index()
    )

    col3, col4 = st.columns(2)
    with col3:
        st.markdown(
            '<p class="chart-title">Top 10 Estados (Maior Tempo)</p>',
            unsafe_allow_html=True,
        )
        top_slowest_states = state_performance.nlargest(10, "avg_delivery_time")
        fig_bar_time = px.bar(
            top_slowest_states.sort_values(by="avg_delivery_time"),
            x="avg_delivery_time",
            y="customer_state",
            orientation="h",
            text_auto=".1f",
            color_discrete_sequence=[PRIMARY_COLOR],
            height=225,
        )
        fig_bar_time.update_layout(
            margin=dict(l=10, r=10, t=20, b=20), xaxis_title="Dias", yaxis_title=None
        )
        st.plotly_chart(fig_bar_time, use_container_width=True)

    with col4:
        st.markdown(
            '<p class="chart-title">Top 10 Estados (Maior % Atraso)</p>',
            unsafe_allow_html=True,
        )
        top_delayed_states = state_performance.nlargest(10, "delay_percentage")
        fig_bar_delay = px.bar(
            top_delayed_states.sort_values(by="delay_percentage"),
            x="delay_percentage",
            y="customer_state",
            orientation="h",
            text_auto=".1f",
            color_discrete_sequence=[NEGATIVE_COLOR],
            height=225,
        )
        fig_bar_delay.update_layout(
            margin=dict(l=10, r=10, t=20, b=20), xaxis_title="%", yaxis_title=None
        )
        st.plotly_chart(fig_bar_delay, use_container_width=True)
else:
    st.warning("Não há dados de logística para os filtros selecionados.")
