# --- PALETA DE CORES PRINCIPAL ---
PRIMARY_COLOR = "#0068C9"  # Azul primário para gráficos e elementos principais
SECONDARY_COLOR = "#83C9FF"  # Azul claro para acentos e dados reais
POSITIVE_COLOR = "#29B09D"  # Verde para indicadores positivos (ex: No Prazo)
NEGATIVE_COLOR = "#FF8787"  # Vermelho/Rosa para indicadores negativos (ex: Atrasado)
COLOR_SEQUENCE = [
    "#0068C9",
    "#83C9FF",
    "#29B09D",
    "#FF8787",
    "#F7D96D",
]  # Sequência para gráficos com múltiplas categorias
SEQUENTIAL_COLOR_SCALE = "Blues"  # Escala de cores para gradientes (ex: mapas de calor)


# --- CONFIGURAÇÃO DE CSS ---
# CSS padronizado para todas as páginas
CSS = """
    <style>
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 0rem;
            padding-left: 2.5rem;
            padding-right: 2.5rem;
        }
        #MainMenu, footer { visibility: hidden; }
        
        div[data-testid="stSlider"] .st-d3 {
            background-color: %(primary_color)s;
        }

        div[data-testid="stMetric"] { padding-top: 0.1rem; padding-bottom: 0rem; }
        .chart-title { font-size: 16px; font-weight: 600; text-align: center; margin-bottom: 0rem; }
    </style>
""" % {
    "primary_color": PRIMARY_COLOR
}
