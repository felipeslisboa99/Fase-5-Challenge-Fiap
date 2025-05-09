import streamlit as st
import pandas as pd
import gspread
import difflib
from google.oauth2 import service_account
from gspread_dataframe import set_with_dataframe

# Configurações
CAMINHO_VAGAS = "Streamlit_desafio_5/Vagas.xlsx"
NOME_PLANILHA_GOOGLE = "Modelo_Candidato_Simplificado"
ABA_PLANILHA = "Dados"

# Função para salvar no Google Sheets
def salvar_em_google_sheets(novo_df):
    creds = service_account.Credentials.from_service_account_info(
        st.secrets["service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    )
    client = gspread.authorize(creds)

    try:
        spreadsheet = client.open(NOME_PLANILHA_GOOGLE)
    except Exception as e:
        st.error(f"Erro ao abrir planilha: {e}")
        return

    try:
        sheet = spreadsheet.worksheet(ABA_PLANILHA)
    except gspread.exceptions.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(title=ABA_PLANILHA, rows="1000", cols="20")

    try:
        existing = pd.DataFrame(sheet.get_all_records())
    except:
        existing = pd.DataFrame()

    df_final = pd.concat([existing, novo_df], ignore_index=True)
    sheet.clear()
    set_with_dataframe(sheet, df_final)

# Carregar vagas
@st.cache_data
def carregar_vagas():
    vagas = pd.read_excel(CAMINHO_VAGAS)
    vagas.rename(columns={
        "Título da vaga": "Vaga",
        "Tipo": "Tipo",
        "Área": "Area",
        "Habilidades": "Habilidades",
        "Nível de inglês": "Level de Ingles",
        "Nível de espanhol": "Level de Espanhol",
        "Outros idiomas": "Outros idiomas",
        "Disponível para viagens": "Precisa Viajar",
        "Possui equipamento próprio": "Precisa de Equipamento",
        "Empresa": "Empresa",
        "Descrição da vaga": "Descricao",
        "Salário pago": "Salario"
    }, inplace=True)
    return vagas

# Calcular score

def calcular_score(candidato, vaga):
    score = 0
    peso_total = 0

    # Título da vaga
    if isinstance(candidato["Título da vaga desejada"], str) and isinstance(vaga["Vaga"], str):
        ratio = difflib.SequenceMatcher(None, candidato["Título da vaga desejada"].lower(), vaga["Vaga"].lower()).ratio()
        score += ratio * 2
        peso_total += 2

    # Tipo
    if candidato["Tipo da vaga desejada"].lower() == vaga["Tipo"].lower():
        score += 1
    peso_total += 1

    # Área
    if candidato["Área de interesse"].lower() in vaga["Area"].lower():
        score += 1
    peso_total += 1

    # Idiomas
    if candidato["Nível de inglês"].lower() in vaga["Level de Ingles"].lower():
        score += 1
    peso_total += 1

    if candidato["Nível de espanhol"].lower() in vaga["Level de Espanhol"].lower():
        score += 1
    peso_total += 1

    outros_idiomas_vaga = vaga["Outros idiomas"].lower() if isinstance(vaga["Outros idiomas"], str) else ""
    outros_idiomas_candidato = candidato["Outros idiomas"].lower() if isinstance(candidato["Outros idiomas"], str) else ""
    if outros_idiomas_candidato and outros_idiomas_candidato in outros_idiomas_vaga:
        score += 1
    peso_total += 1

    # Equipamentos
    if candidato["Possui equipamento próprio? (Sim/Não)"].lower() == "sim" and "não" not in vaga["Precisa de Equipamento"].lower():
        score += 0.5
    peso_total += 0.5

    # Viagens
    if candidato["Disponível para viagens? (Sim/Não)"].lower() == vaga["Precisa Viajar"].lower():
        score += 0.5
    peso_total += 0.5

    # Habilidades
    candidato_skills = set(h.lower() for h in candidato["Competências técnicas"]) if isinstance(candidato["Competências técnicas"], list) else set()
    vaga_skills = set(str(vaga["Habilidades"]).lower().split(",")) if isinstance(vaga["Habilidades"], str) else set()
    vaga_skills = set(h.strip() for h in vaga_skills)
    intersecao = candidato_skills.intersection(vaga_skills)
    if vaga_skills:
        score += len(intersecao) / len(vaga_skills) * 4
        peso_total += 4

    return round((score / peso_total) * 100, 2) if peso_total else 0

# Interface
st.title("🔍 Plataforma de Match de Vagas")
st.markdown("Preencha abaixo e veja quais vagas combinam com você!")

vagas_df = carregar_vagas()
titulos_disponiveis = sorted(vagas_df["Vaga"].dropna().unique())
areas_disponiveis = sorted(vagas_df["Area"].dropna().unique())
todas_habilidades = vagas_df["Habilidades"].dropna().str.cat(sep=", ").lower().split(",")
habilidades_unicas = sorted(set(h.strip().capitalize() for h in todas_habilidades if h.strip() != ""))

with st.form("formulario_candidato"):
    st.subheader("📄 Dados do Candidato")
    nome = st.text_input("Nome completo")
    cpf = st.text_input("CPF")
    cidade = st.text_input("Cidade onde mora")
    titulo = st.selectbox("Título da vaga desejada", titulos_disponiveis)
    tipo = st.selectbox("Tipo da vaga desejada", ["Júnior", "Pleno", "Sênior"])
    area = st.selectbox("Área de interesse", areas_disponiveis)
    ingles = st.selectbox("Nível de inglês", ["Nenhum", "Básico", "Intermediário", "Avançado", "Fluente"])
    espanhol = st.selectbox("Nível de espanhol", ["Nenhum", "Básico", "Intermediário", "Avançado", "Fluente"])
    outros_idiomas = st.text_input("Outros idiomas")
    tecnicas = st.multiselect("Competências técnicas", habilidades_unicas)
    comportamentais = st.text_area("Competências comportamentais")
    viagens = st.selectbox("Disponível para viagens?", ["Sim", "Não"])
    equipamento = st.selectbox("Possui equipamento próprio?", ["Sim", "Não"])
    salario = st.text_input("Expectativa salarial")
    enviado = st.form_submit_button("🔎 Encontrar Vagas")

if enviado:
    candidato = {
        "Nome completo": nome,
        "CPF": cpf,
        "Cidade": cidade,
        "Título da vaga desejada": titulo,
        "Tipo da vaga desejada": tipo,
        "Área de interesse": area,
        "Nível de inglês": ingles,
        "Nível de espanhol": espanhol,
        "Outros idiomas": outros_idiomas,
        "Competências técnicas": tecnicas,
        "Competências comportamentais": comportamentais,
        "Disponível para viagens? (Sim/Não)": viagens,
        "Possui equipamento próprio? (Sim/Não)": equipamento,
        "Expectativa salarial": salario
    }

    novo_candidato_df = pd.DataFrame([candidato])
    novo_candidato_df["Competências técnicas"] = [", ".join(tecnicas)]
    salvar_em_google_sheets(novo_candidato_df)

    st.success("📝 Dados salvos no Google Sheets com sucesso!")

    st.info("🔄 Processando suas informações...")
    vagas_df["ia_score"] = vagas_df.apply(lambda row: calcular_score(candidato, row), axis=1)
    top_vagas = vagas_df.sort_values(by="ia_score", ascending=False).head(5)

    st.success("✅ Veja abaixo suas vagas com maior compatibilidade!")
    st.subheader("🏆 Top 5 Vagas Compatíveis")

    for _, vaga in top_vagas.iterrows():
        st.markdown(f"### {vaga['Vaga']}")
        st.markdown(f"**Tipo:** {vaga['Tipo']}")
        st.markdown(f"**Área:** {vaga['Area']}")
        st.markdown(f"**Cliente:** {vaga['Empresa']}")
        st.markdown(f"**Score de compatibilidade:** {vaga['ia_score']}%")
        st.markdown(f"**Requisitos:** {vaga['Habilidades']}")
        st.markdown(f"**Descrição:** {vaga['Descricao']}")
        st.markdown(f"**Salário oferecido:** {vaga['Salario']}")
        st.markdown("---")
