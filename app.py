import streamlit as st

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Análise de E-commerce",
    page_icon="🛍️",
    layout="wide"
)

# --- PÁGINA INICIAL ---
st.title("🛍️ Análise de Performance de E-commerce")
st.markdown("---")

st.markdown(
    """
    ### Bem-vindo ao Dashboard de Análise do Olist!

    Este projeto interativo foi desenvolvido para analisar dados públicos de um grande e-commerce brasileiro, 
    o Olist. O objetivo é extrair insights valiosos sobre vendas, logística e comportamento do consumidor.

    **O que você encontrará aqui?**
    - **Página de Vendas:** Uma visão geral da performance de vendas, incluindo KPIs, receita por categoria, 
      métodos de pagamento e distribuição geográfica das vendas.
    - **Página de Logística:** Uma análise detalhada da eficiência das entregas, incluindo prazos, 
      atrasos e performance por região.
    - **Página de Previsão:** Uma projeção da receita futura baseada em modelos de séries temporais.

    **Como navegar?**
    - Use o menu na barra lateral à esquerda para explorar as diferentes páginas de análise.
    - Em cada página, você encontrará filtros interativos para explorar os dados em detalhes.

    **Tecnologias Utilizadas:**
    - **Linguagem:** Python
    - **Bibliotecas:** Streamlit, Pandas, Plotly
    - **Dados:** Olist E-commerce Dataset (disponível no Kaggle)

    Este dashboard foi criado como um projeto de portfólio para demonstrar habilidades em análise de dados, 
    visualização interativa e desenvolvimento de aplicações web com Python.
    """
)

st.sidebar.success("Selecione uma página de análise acima.")
