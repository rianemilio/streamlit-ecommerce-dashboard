import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
from prophet import Prophet
from prophet.plot import plot_plotly, plot_components_plotly

# --- CSS ---
st.set_page_config(page_title="Previsão de Vendas", layout="wide")
st.title("Previsão de Receita Futura")
st.markdown("""
    <style>
        .block-container {
            padding-top: 2rem !important; padding-bottom: 0rem;
            padding-left: 2.5rem; padding-right: 2.5rem;
        }
        div[data-testid="stMetric"] { padding-top: 0.1rem; padding-bottom: 0rem; }
        .chart-title { font-size: 16px; font-weight: 600; text-align: center; margin-bottom: 0rem; }
    </style>
""", unsafe_allow_html=True)

# --- CARREGAMENTO DE DADOS ---
@st.cache_data
def load_forecast_data():
    data_path = 'data/'
    try:
        cols_orders = ['order_id', 'order_purchase_timestamp']
        cols_items = ['order_id', 'price']
        
        orders = pd.read_parquet(os.path.join(data_path, 'olist_orders_dataset.parquet'), columns=cols_orders, engine='fastparquet')
        items = pd.read_parquet(os.path.join(data_path, 'olist_order_items_dataset.parquet'), columns=cols_items, engine='fastparquet')

    except Exception as e:
        st.error(f"Erro ao ler os arquivos Parquet. Detalhe: {e}")
        st.stop()

    df = orders.merge(items, on='order_id')
    df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'])
    return df

# --- LÓGICA PRINCIPAL ---
df_forecast = load_forecast_data()

# --- PREPARAÇÃO DOS DADOS ---
df_prophet = df_forecast[['order_purchase_timestamp', 'price']].copy()
df_prophet = df_prophet.set_index('order_purchase_timestamp').resample('D').sum().reset_index()
df_prophet.rename(columns={'order_purchase_timestamp': 'ds', 'price': 'y'}, inplace=True)

# --- FILTROS NA BARRA LATERAL ---
st.sidebar.header("Parâmetros da Previsão")
prediction_period = st.sidebar.slider("Horizonte de Previsão (Meses):", min_value=1, max_value=12, value=3, key="prediction_period")

# --- LAYOUT DO DASHBOARD ---
st.markdown("Use o controle na barra lateral para definir quantos meses no futuro você deseja prever a receita.")

if st.button("Gerar Previsão"):
    with st.spinner("Treinando o modelo e gerando a previsão... Por favor, aguarde."):
        model = Prophet(yearly_seasonality=True, weekly_seasonality=True, daily_seasonality=False)
        model.fit(df_prophet)
        
        future = model.make_future_dataframe(periods=prediction_period * 30)
        forecast = model.predict(future)

        st.markdown("---")
        st.markdown('<p class="chart-title">Previsão de Receita vs. Dados Históricos</p>', unsafe_allow_html=True)
        
        fig1 = plot_plotly(model, forecast)
        last_history_date = df_prophet['ds'].max()
        last_forecast_date = forecast['ds'].max()
        fig1.add_vrect(x0=last_history_date, x1=last_forecast_date, fillcolor="#E0E0E0", opacity=0.3, line_width=0, annotation_text="Previsão", annotation_position="top left", annotation_font_size=14)
        
        fig1.data[0].name = 'Previsão'
        fig1.data[1].name = 'Intervalo de Confiança'
        fig1.data[2].name = 'Dados Reais'
        
        fig1.update_layout(yaxis_title="Receita (R$)", xaxis_title="Data", margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="h", yanchor="top", y=1.1, xanchor="center", x=0.5))
        st.plotly_chart(fig1, use_container_width=True)

        st.markdown("---")
        st.markdown('<p class="chart-title">Componentes da Previsão</p>', unsafe_allow_html=True)
        st.write("Estes gráficos mostram a tendência geral e as sazonalidades (padrões anuais e semanais) que o modelo aprendeu a partir dos dados.")
        
        fig2 = plot_components_plotly(model, forecast)
        st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("Clique no botão 'Gerar Previsão' para iniciar a análise.")
