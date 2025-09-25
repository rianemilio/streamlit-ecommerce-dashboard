import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from prophet import Prophet
from style_config import CSS, PRIMARY_COLOR, SECONDARY_COLOR

# --- CONFIGURAÇÃO DA PÁGINA E CSS ---
st.set_page_config(page_title="Previsão de Vendas", layout="wide")
st.title("Previsão de Receita Futura")
st.markdown(CSS, unsafe_allow_html=True)


# --- CARREGAMENTO DOS DADOS ---
@st.cache_data
def load_forecast_data():
    data_path = "data/"
    try:
        cols_orders = ["order_id", "order_purchase_timestamp"]
        cols_items = ["order_id", "price"]

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
    except Exception as e:
        st.error(f"Erro ao ler os arquivos Parquet. Detalhe: {e}")
        st.stop()
    df = orders.merge(items, on="order_id")
    df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"])
    return df


# --- LÓGICA PRINCIPAL ---
df_forecast = load_forecast_data()
df_prophet = df_forecast[["order_purchase_timestamp", "price"]].copy()
df_prophet = (
    df_prophet.set_index("order_purchase_timestamp").resample("D").sum().reset_index()
)
df_prophet.rename(
    columns={"order_purchase_timestamp": "ds", "price": "y"}, inplace=True
)

# --- FILTROS NA BARRA LATERAL ---
st.sidebar.header("Parâmetros")
prediction_period = st.sidebar.slider(
    "Horizonte de Previsão (Meses):",
    min_value=1,
    max_value=12,
    value=3,
    key="prediction_period",
)
st.markdown(
    "Use o controle na barra lateral para definir quantos meses no futuro você deseja prever a receita."
)

if st.button("Gerar Previsão"):
    with st.spinner("Treinando o modelo e gerando a previsão..."):
        # --- TREINAMENTO E PREVISÃO ---
        model = Prophet(
            yearly_seasonality=True, weekly_seasonality=True, daily_seasonality=False
        )
        model.fit(df_prophet)
        future = model.make_future_dataframe(periods=prediction_period * 30)
        forecast = model.predict(future)

        # --- VISUALIZAÇÃO DOS RESULTADOS ---
        st.markdown("---")
        st.markdown(
            '<p class="chart-title">Previsão de Receita vs. Dados Históricos</p>',
            unsafe_allow_html=True,
        )

        df_plot = df_prophet.copy()
        outlier_threshold = 100000
        max_value_without_outlier = df_plot[df_plot["y"] < outlier_threshold]["y"].max()
        has_outliers = (df_plot["y"] > outlier_threshold).any()
        if has_outliers:
            df_plot.loc[df_plot["y"] > outlier_threshold, "y"] = (
                max_value_without_outlier
            )
            st.info(
                "ℹ️ Um ou mais picos de vendas foram limitados visualmente para melhor clareza do gráfico."
            )

        fig1 = go.Figure()
        fig1.add_trace(
            go.Scatter(
                x=df_plot["ds"],
                y=df_plot["y"],
                mode="lines",
                name="Dados Reais",
                line=dict(color=SECONDARY_COLOR, width=2),
            )
        )
        fig1.add_trace(
            go.Scatter(
                x=forecast["ds"],
                y=forecast["yhat"],
                mode="lines",
                name="Previsão",
                line=dict(color=PRIMARY_COLOR, width=3, dash="dot"),
            )
        )
        fig1.add_trace(
            go.Scatter(
                x=forecast["ds"],
                y=forecast["yhat_upper"],
                mode="lines",
                line=dict(width=0),
                hoverinfo="skip",
                showlegend=False,
            )
        )
        fig1.add_trace(
            go.Scatter(
                x=forecast["ds"],
                y=forecast["yhat_lower"],
                mode="lines",
                line=dict(width=0),
                fillcolor="rgba(0, 104, 201, 0.2)",
                fill="tonexty",
                hoverinfo="skip",
                showlegend=False,
                name="Intervalo de Confiança",
            )
        )

        last_history_date = df_prophet["ds"].max()
        last_forecast_date = forecast["ds"].max()
        fig1.add_vrect(
            x0=last_history_date,
            x1=last_forecast_date,
            fillcolor="#E0E0E0",
            opacity=0.3,
            line_width=0,
            annotation_text="Previsão",
            annotation_position="top left",
        )

        fig1.update_layout(
            yaxis_title="Receita (R$)",
            xaxis_title="Data",
            margin=dict(l=20, r=20, t=20, b=20),
            legend=dict(orientation="h", yanchor="top", y=1.1, xanchor="center", x=0.5),
        )
        st.plotly_chart(fig1, use_container_width=True)

        # --- VISUALIZAÇÃO DOS COMPONENTES ---
        st.markdown("---")
        st.markdown(
            '<p class="chart-title">Componentes da Previsão</p>', unsafe_allow_html=True
        )
        st.write(
            "Estes gráficos mostram a tendência geral e as sazonalidades que o modelo aprendeu a partir dos dados."
        )

        fig_trend = px.line(
            forecast,
            x="ds",
            y="trend",
            title="Tendência Geral",
            color_discrete_sequence=[PRIMARY_COLOR],
        )
        fig_trend.add_vrect(
            x0=last_history_date,
            x1=last_forecast_date,
            fillcolor="#E0E0E0",
            opacity=0.3,
            line_width=0,
        )
        fig_trend.update_layout(
            yaxis_title="Valor da Tendência",
            xaxis_title="Data",
            margin=dict(t=50, b=20),
        )
        st.plotly_chart(fig_trend, use_container_width=True)

        fig_yearly = px.line(
            forecast,
            x="ds",
            y="yearly",
            title="Sazonalidade Anual",
            color_discrete_sequence=[PRIMARY_COLOR],
        )
        fig_yearly.add_vrect(
            x0=last_history_date,
            x1=last_forecast_date,
            fillcolor="#E0E0E0",
            opacity=0.3,
            line_width=0,
        )
        fig_yearly.update_layout(
            yaxis_title="Impacto Sazonal", xaxis_title="Data", margin=dict(t=50, b=20)
        )
        st.plotly_chart(fig_yearly, use_container_width=True)

        weekly_data = pd.DataFrame(
            {"day_name": forecast["ds"].dt.day_name(), "value": forecast["weekly"]}
        )
        weekly_component = weekly_data.groupby("day_name")["value"].mean().reset_index()
        day_order_en = [
            "Sunday",
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
        ]
        day_name_translation = {
            "Sunday": "Domingo",
            "Monday": "Segunda-feira",
            "Tuesday": "Terça-feira",
            "Wednesday": "Quarta-feira",
            "Thursday": "Quinta-feira",
            "Friday": "Sexta-feira",
            "Saturday": "Sábado",
        }
        weekly_component["day_name"] = pd.Categorical(
            weekly_component["day_name"], categories=day_order_en, ordered=True
        )
        weekly_component = weekly_component.sort_values("day_name")
        weekly_component["day_name"] = weekly_component["day_name"].map(
            day_name_translation
        )
        fig_weekly = px.line(
            weekly_component,
            x="day_name",
            y="value",
            title="Sazonalidade Semanal",
            markers=True,
            color_discrete_sequence=[PRIMARY_COLOR],
        )
        fig_weekly.update_layout(
            yaxis_title="Impacto Sazonal",
            xaxis_title="Dia da Semana",
            margin=dict(t=50, b=20),
        )
        st.plotly_chart(fig_weekly, use_container_width=True)
else:
    st.info("Clique no botão 'Gerar Previsão' para iniciar a análise.")
