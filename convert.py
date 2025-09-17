import pandas as pd
import os

print("Iniciando a conversão de arquivos CSV para Parquet...")

# --- CONFIGURAÇÃO ---
data_path = 'data/'
files_to_convert = [
    'olist_customers_dataset.csv',
    'olist_orders_dataset.csv',
    'olist_order_items_dataset.csv',
    'olist_order_payments_dataset.csv',
    'olist_products_dataset.csv',
    'product_category_name_translation.csv'
]

# --- PROCESSO DE CONVERSÃO ---
for file in files_to_convert:
    csv_path = os.path.join(data_path, file)
    parquet_path = csv_path.replace('.csv', '.parquet')
    
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        df.to_parquet(parquet_path, engine='fastparquet')
        print(f"SUCESSO: Convertido '{file}' para formato Parquet.")
    else:
        print(f"AVISO: Arquivo '{file}' não encontrado. Pulando.")

print("\nConversão concluída! Agora você pode usar os arquivos .parquet no seu dashboard.")
