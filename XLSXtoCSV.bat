@echo off

REM Ativar o ambiente virtual
call venv\Scripts\activate.bat

REM Definir o caminho para o seu aplicativo Streamlit
set APP_PATH=XLSXtoCSV\app.py

REM Executar o aplicativo Streamlit no navegador
streamlit run %APP_PATH% --browser.serverAddress 0.0.0.0 --server.port 8501

REM Desativar o ambiente virtual
deactivate
