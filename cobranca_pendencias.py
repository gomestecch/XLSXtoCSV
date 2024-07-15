import pandas as pd
import re

# Lê o arquivo Excel em um DataFrame
input_file = '02parcelasnaocontemplados.xlsx'  

# Verifica se a extensão do arquivo é .xlsx
if not input_file.endswith('.xlsx'):
    raise ValueError("Formato de arquivo não suportado. Use apenas arquivos .xlsx.")

df = pd.read_excel(input_file, engine='openpyxl', header=None)  # Lê sem cabeçalho

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

# Salva o DataFrame filtrado em um arquivo CSV com o separador correto
output_file = os.path.splitext(input_file)[0] + '.csv'
filtered_df.to_csv(output_file, sep=',', index=False)  # Usa vírgula como separador

# Mostra o DataFrame filtrado
print(filtered_df.head(20).to_markdown(index=False, numalign="left", stralign="left"))
