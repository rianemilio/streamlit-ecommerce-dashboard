import streamlit as st
import pandas as pd
import plotly.express as px
import os
from style_config import CSS, PRIMARY_COLOR, COLOR_SEQUENCE, SEQUENTIAL_COLOR_SCALE

# --- CONFIGURAÇÃO DA PÁGINA E CSS ---
st.set_page_config(page_title="Análise de Vendas", layout="wide")
st.title("Visão Geral de Vendas")
st.markdown(CSS, unsafe_allow_html=True)


# --- CARREGAMENTO DOS DADOS ---
@st.cache_data
def load_data():
    data_path = "data/"
    try:
        cols_orders = ["order_id", "customer_id", "order_purchase_timestamp"]
        cols_items = ["order_id", "product_id", "price"]
        cols_payments = ["order_id", "payment_type", "payment_value"]
        cols_customers = ["customer_id", "customer_unique_id", "customer_state"]
        cols_products = ["product_id", "product_category_name"]
        cols_translation = ["product_category_name", "product_category_name_english"]

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
        payments = pd.read_parquet(
            os.path.join(data_path, "olist_order_payments_dataset.parquet"),
            columns=cols_payments,
            engine="fastparquet",
        )
        customers = pd.read_parquet(
            os.path.join(data_path, "olist_customers_dataset.parquet"),
            columns=cols_customers,
            engine="fastparquet",
        )
        products = pd.read_parquet(
            os.path.join(data_path, "olist_products_dataset.parquet"),
            columns=cols_products,
            engine="fastparquet",
        )
        translation = pd.read_parquet(
            os.path.join(data_path, "product_category_name_translation.parquet"),
            columns=cols_translation,
            engine="fastparquet",
        )

    except Exception as e:
        st.error(f"Erro ao ler os arquivos Parquet. Detalhe: {e}")
        st.stop()

    df = (
        orders.merge(items, on="order_id")
        .merge(payments, on="order_id")
        .merge(customers, on="customer_id")
        .merge(products, on="product_id")
        .merge(translation, on="product_category_name", how="left")
    )

    df["order_purchase_timestamp"] = pd.to_datetime(
        df["order_purchase_timestamp"], errors="coerce"
    )
    df.dropna(subset=["order_purchase_timestamp"], inplace=True)
    df["customer_state"] = df["customer_state"].astype("category")
    df["payment_type"] = df["payment_type"].astype("category")
    df["product_category_name_english"] = (
        df["product_category_name_english"].fillna("unknown").astype("category")
    )
    df["price"] = df["price"].astype("float32")
    df["payment_value"] = df["payment_value"].astype("float32")

    return df


# --- LÓGICA PRINCIPAL E DICIONÁRIOS ---
df = load_data()
translation_df = pd.read_parquet(
    os.path.join("data", "product_category_name_translation.parquet"),
    engine="fastparquet",
)
category_translation_raw = pd.Series(
    translation_df.product_category_name.values,
    index=translation_df.product_category_name_english,
).to_dict()
category_translation = {
    en: pt.replace("_", " ").title() for en, pt in category_translation_raw.items()
}
category_translation["unknown"] = "Desconhecida"
payment_type_translation = {
    "credit_card": "Cartão de Crédito",
    "boleto": "Boleto",
    "voucher": "Voucher",
    "debit_card": "Cartão de Débito",
    "not_defined": "Não Definido",
}

# --- FILTROS NA BARRA LATERAL ---
st.sidebar.header("Filtros")
min_date = df["order_purchase_timestamp"].min().date()
max_date = df["order_purchase_timestamp"].max().date()
start_date, end_date = st.sidebar.date_input(
    "Período:", value=(min_date, max_date), min_value=min_date, max_value=max_date
)
start_date = pd.to_datetime(start_date)
end_date = pd.to_datetime(end_date) + pd.Timedelta(days=1)
states = sorted(df["customer_state"].cat.categories)
selected_states = st.sidebar.multiselect("Estado:", options=states, default=states)
categories_pt = sorted(
    [
        category_translation.get(cat, cat)
        for cat in df["product_category_name_english"].cat.categories
    ]
)
selected_categories_pt = st.sidebar.multiselect(
    "Categoria:", options=categories_pt, default=categories_pt
)

# --- FILTRAGEM DO DATAFRAME ---
category_translation_rev = {v: k for k, v in category_translation.items()}
selected_categories_en = [
    category_translation_rev.get(cat, cat) for cat in (selected_categories_pt or [])
]
query = "customer_state in @selected_states and product_category_name_english in @selected_categories_en and order_purchase_timestamp >= @start_date and order_purchase_timestamp < @end_date"
df_filtered = df.query(query)

# --- LAYOUT DO DASHBOARD ---
if not df_filtered.empty:
    total_revenue = df_filtered["price"].sum()
    total_orders = df_filtered["order_id"].nunique()
    average_ticket = total_revenue / total_orders if total_orders > 0 else 0
    unique_customers = df_filtered["customer_unique_id"].nunique()

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric(label="Receita Total", value=f"R$ {total_revenue:,.0f}")
    kpi2.metric(label="Pedidos Totais", value=f"{total_orders:,}")
    kpi3.metric(label="Ticket Médio", value=f"R$ {average_ticket:,.2f}")
    kpi4.metric(label="Clientes Únicos", value=f"{unique_customers:,}")

    st.markdown("---")

    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown(
            '<p class="chart-title">Tendência Mensal de Receita</p>',
            unsafe_allow_html=True,
        )
        monthly_revenue = (
            df_filtered.set_index("order_purchase_timestamp")
            .resample("ME")["price"]
            .sum()
            .reset_index()
        )
        fig_monthly = px.area(
            monthly_revenue,
            x="order_purchase_timestamp",
            y="price",
            color_discrete_sequence=[PRIMARY_COLOR],
            height=225,
        )
        fig_monthly.update_layout(
            margin=dict(l=10, r=10, t=20, b=20), yaxis_title=None, xaxis_title=None
        )
        st.plotly_chart(fig_monthly, use_container_width=True)

    with col2:
        st.markdown(
            '<p class="chart-title">Top 10 Categorias por Receita</p>',
            unsafe_allow_html=True,
        )
        revenue_by_category = (
            df_filtered.groupby("product_category_name_english", observed=False)[
                "price"
            ]
            .sum()
            .nlargest(10)
            .sort_values()
        )
        revenue_by_category.index = revenue_by_category.index.map(category_translation)
        fig_cat = px.bar(
            revenue_by_category,
            x="price",
            y=revenue_by_category.index,
            orientation="h",
            text_auto=".2s",
            color_discrete_sequence=[PRIMARY_COLOR],
            height=225,
        )
        fig_cat.update_layout(
            margin=dict(l=10, r=10, t=20, b=20), yaxis_title=None, xaxis_title=None
        )
        st.plotly_chart(fig_cat, use_container_width=True)

    col3, col4 = st.columns([2, 3])
    with col3:
        st.markdown(
            '<p class="chart-title">Métodos de Pagamento</p>', unsafe_allow_html=True
        )
        payment_distribution = df_filtered.groupby("payment_type", observed=False)[
            "payment_value"
        ].sum()
        payment_distribution.index = payment_distribution.index.map(
            payment_type_translation
        )
        fig_payment = px.pie(
            payment_distribution,
            names=payment_distribution.index,
            values="payment_value",
            hole=0.5,
            color_discrete_sequence=COLOR_SEQUENCE,
            height=225,
        )
        fig_payment.update_traces(textposition="inside", textinfo="percent")
        fig_payment.update_layout(
            margin=dict(l=20, r=20, t=20, b=20), legend_title_text=""
        )
        st.plotly_chart(fig_payment, use_container_width=True)

    with col4:
        st.markdown(
            '<p class="chart-title">Top 10 Estados por Receita</p>',
            unsafe_allow_html=True,
        )
        revenue_by_state = (
            df_filtered.groupby("customer_state", observed=False)["price"]
            .sum()
            .nlargest(10)
            .sort_values(ascending=False)
        )
        fig_state = px.bar(
            revenue_by_state,
            x=revenue_by_state.index,
            y="price",
            text_auto=".2s",
            color="price",
            color_continuous_scale=SEQUENTIAL_COLOR_SCALE,
            height=225,
        )
        fig_state.update_layout(
            margin=dict(l=10, r=10, t=20, b=20), yaxis_title=None, xaxis_title=None
        )
        st.plotly_chart(fig_state, use_container_width=True)
else:
    st.warning("Não há dados para os filtros selecionados.")
