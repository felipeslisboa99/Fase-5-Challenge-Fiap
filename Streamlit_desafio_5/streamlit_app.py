import streamlit as st
import gspread
from google.oauth2 import service_account

st.title("🔐 Teste de Autenticação com Google Sheets")

try:
    # Usa as credenciais do secrets.toml
    creds = service_account.Credentials.from_service_account_info(st.secrets["service_account"])
    client = gspread.authorize(creds)

    # Tente abrir a planilha pelo nome
    sheet = client.open("Modelo_Candidato_Simplificado")
    st.success("✅ Conexão com Google Sheets bem-sucedida!")
    st.info(f"Primeira aba encontrada: {sheet.worksheets()[0].title}")

except Exception as e:
    st.error("❌ Erro ao conectar com Google Sheets:")
    st.exception(e)
