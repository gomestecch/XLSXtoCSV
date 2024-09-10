import streamlit as st
import pandas as pd
import re
import os

st.title("Processador de Arquivos de Cobrança")

# Função para processar o DataFrame
def processar_dataframe(df):
    # Cria uma lista com novas letras para os nomes das colunas
    novas_colunas = [chr(97 + i) for i in range(len(df.columns))]
    df.columns = novas_colunas

    # Padrão de número de telefone (com ou sem o dígito 9)
    padrao_telefone = r'\d{2}\s\d{8}|\d{2}\s\d{9}'

    # Encontra os índices das linhas onde a coluna 'e' corresponde ao padrão
    indices_correspondentes = df[df['e'].astype(str).str.match(padrao_telefone)].index

    # Cria uma lista com os índices das linhas correspondentes e as linhas seguintes
    linhas_manter = []
    for idx in indices_correspondentes:
        linhas_manter.extend([idx, idx + 1])

    # Filtra o DataFrame para manter apenas as linhas selecionadas
    df_filtrado = df.iloc[linhas_manter].copy()  

    # Remove linhas duplicadas (caso a última linha correspondente seja a última do DataFrame)
    df_filtrado = df_filtrado.drop_duplicates()

    # Mantém apenas as colunas 'a', 'b' e 'e'
    df_filtrado = df_filtrado[['a', 'b', 'e']]

    # Renomeia as colunas ANTES das demais operações
    df_filtrado = df_filtrado.rename(columns={'a': 'contrato', 'b': 'nome', 'e': 'fullNumber'})

    # Reinicia os índices do DataFrame filtrado
    df_filtrado = df_filtrado.reset_index(drop=True)

    # Itera sobre as linhas e substitui o valor de 'contrato' na linha anterior se 'nome' e 'fullNumber' forem NaN na linha atual
    for i in range(1, len(df_filtrado)):
        if pd.isna(df_filtrado.loc[i, 'nome']) and pd.isna(df_filtrado.loc[i, 'fullNumber']):
            df_filtrado.loc[i - 1, 'contrato'] = df_filtrado.loc[i, 'contrato']

    # Remove as linhas onde 'nome' e 'fullNumber' são NaN
    df_filtrado = df_filtrado.dropna(subset=['nome', 'fullNumber'])

    # Remove espaços em branco da coluna 'fullNumber'
    df_filtrado['fullNumber'] = df_filtrado['fullNumber'].astype(str).str.replace(' ', '', regex=False)

    # Insere '9' na terceira posição se o comprimento não for 11
    df_filtrado['fullNumber'] = df_filtrado['fullNumber'].apply(lambda x: x[:2] + '9' + x[2:] if len(x) != 11 else x)

    # Adiciona '55' no início de cada valor na coluna 'fullNumber'
    df_filtrado['fullNumber'] = '55' + df_filtrado['fullNumber']

    # Remove linhas duplicadas com base na coluna 'fullNumber', mantendo a primeira ocorrência
    df_filtrado = df_filtrado.loc[~df_filtrado['fullNumber'].duplicated(keep='first')]

    # Remove linhas onde o quinto dígito de 'fullNumber' não é '9'
    df_filtrado = df_filtrado[df_filtrado['fullNumber'].astype(str).str[4] == '9']
    return df_filtrado

# Função para adicionar colunas extras
def adicionar_colunas_extras(df):
    adicionar_colunas = st.radio("Deseja adicionar mais colunas?", ("Não", "Sim"))
    
    if adicionar_colunas == "Sim":
        num_colunas = st.number_input("Quantas colunas deseja adicionar?", min_value=1, step=1, format='%d')
        for i in range(int(num_colunas)):
            nome_coluna = st.text_input(f"Nome da coluna {i+1}:")
            conteudo_coluna = st.text_input(f"Conteúdo único para a coluna {i+1}:")
            if nome_coluna and conteudo_coluna:
                # Preenche todas as linhas da nova coluna com o mesmo valor
                df[nome_coluna] = conteudo_coluna
    return df

# Upload do arquivo
arquivo_carregado = st.file_uploader("Escolha um arquivo XLSX", type="xlsx")

if arquivo_carregado is not None:
    try:
        df = pd.read_excel(arquivo_carregado, engine='openpyxl', header=None)
        df_filtrado = processar_dataframe(df)
        
        # Exibe o DataFrame filtrado antes de adicionar colunas extras
        st.subheader("DataFrame processado:")
        st.write(df_filtrado.head(20).to_markdown(index=False, numalign="left", stralign="left"))

        # Adiciona colunas extras
        df_filtrado = adicionar_colunas_extras(df_filtrado)

        # Exibe o DataFrame após a adição de colunas extras
        st.subheader("DataFrame com colunas adicionais:")
        st.write(df_filtrado.head(20).to_markdown(index=False, numalign="left", stralign="left"))

        # Download do arquivo CSV
        csv = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download arquivo CSV",
            data=csv,
            file_name="output.csv",
            mime="text/csv",
        )

    except ValueError as e:
        st.error(str(e))
