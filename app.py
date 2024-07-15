import streamlit as st
import pandas as pd
import re
import os

st.title("Processador de Arquivos de Cobrança")

# Função para processar o DataFrame
def process_dataframe(df):
    # Cria uma lista com as novas letras para os nomes das colunas
    new_columns = [chr(97 + i) for i in range(len(df.columns))]
    df.columns = new_columns

    # Padrão de número de telefone (com ou sem o dígito 9)
    phone_pattern = r'\d{2}\s\d{8}|\d{2}\s\d{9}'

    # Encontra os índices das linhas onde a coluna 'e' corresponde ao padrão
    matching_indices = df[df['e'].astype(str).str.match(phone_pattern)].index

    # Cria uma lista com os índices das linhas correspondentes e as linhas seguintes
    rows_to_keep = []
    for idx in matching_indices:
        rows_to_keep.extend([idx, idx + 1])

    # Filtra o DataFrame para manter apenas as linhas selecionadas
    filtered_df = df.iloc[rows_to_keep].copy()  

    # Remove linhas duplicadas (caso a última linha correspondente seja a última do DataFrame)
    filtered_df = filtered_df.drop_duplicates()

    # Mantém apenas as colunas 'a', 'b' e 'e'
    filtered_df = filtered_df[['a', 'b', 'e']]

    # Renomeia as colunas ANTES das demais operações
    filtered_df = filtered_df.rename(columns={'a': 'contrato', 'b': 'nome', 'e': 'fullNumber'})

    # Reinicia os índices do DataFrame filtrado
    filtered_df = filtered_df.reset_index(drop=True)

    # Itera sobre as linhas e substitui o valor de 'contrato' na linha anterior se 'nome' e 'fullNumber' forem NaN na linha atual
    for i in range(1, len(filtered_df)):
        if pd.isna(filtered_df.loc[i, 'nome']) and pd.isna(filtered_df.loc[i, 'fullNumber']):
            filtered_df.loc[i - 1, 'contrato'] = filtered_df.loc[i, 'contrato']

    # Remove as linhas onde 'nome' e 'fullNumber' são NaN
    filtered_df = filtered_df.dropna(subset=['nome', 'fullNumber'])

    # Remove espaços em branco da coluna 'fullNumber'
    filtered_df['fullNumber'] = filtered_df['fullNumber'].astype(str).str.replace(' ', '', regex=False)

    # Insere '9' na terceira posição se o comprimento não for 11
    filtered_df['fullNumber'] = filtered_df['fullNumber'].apply(lambda x: x[:2] + '9' + x[2:] if len(x) != 11 else x)

    # Adiciona '55' no início de cada valor na coluna 'fullNumber'
    filtered_df['fullNumber'] = '55' + filtered_df['fullNumber']

    # Remove linhas duplicadas com base na coluna 'fullNumber', mantendo a primeira ocorrência
    filtered_df = filtered_df.loc[~filtered_df['fullNumber'].duplicated(keep='first')]

    # Remove linhas onde o quinto dígito de 'fullNumber' não é '9'
    filtered_df = filtered_df[filtered_df['fullNumber'].astype(str).str[4] == '9']
    return filtered_df

# Upload do arquivo
uploaded_file = st.file_uploader("Escolha um arquivo XLSX", type="xlsx")

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file, engine='openpyxl', header=None)
        filtered_df = process_dataframe(df)

        # Exibe o DataFrame filtrado
        st.subheader("DataFrame processado:")
        st.write(filtered_df.head(20).to_markdown(index=False, numalign="left", stralign="left"))

        # Download do arquivo CSV
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download arquivo CSV",
            data=csv,
            file_name="output.csv",
            mime="text/csv",
        )

    except ValueError as e:
        st.error(str(e))
