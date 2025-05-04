import streamlit as st
import pandas as pd
import gspread
import difflib
from google.oauth2 import service_account
from gspread_dataframe import set_with_dataframe
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

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

# --- Conversão ordinal de níveis ---
ordem_idioma = {"nenhum": 0, "básico": 1, "intermediário": 2, "avançado": 3, "fluente": 4}

def idioma_score(candidato_nivel, vaga_nivel):
    c = ordem_idioma.get(candidato_nivel.lower(), 0)
    v = ordem_idioma.get(vaga_nivel.lower(), 0)
    return 1 if c >= v else 0

# --- Cálculo de similaridade TF-IDF para habilidades ---
def similaridade_habilidades(candidato_skills, vaga_skills):
    corpus = [candidato_skills, vaga_skills]
    vectorizer = TfidfVectorizer().fit_transform(corpus)
    sim = cosine_similarity(vectorizer[0:1], vectorizer[1:2])
    return sim[0][0]

def calcular_score(candidato, vaga):
    score = 0
    peso_total = 0

    if isinstance(candidato["Título da vaga desejada"], str) and isinstance(vaga["Vaga"], str):
        ratio = difflib.SequenceMatcher(None, candidato["Título da vaga desejada"].lower(), vaga["Vaga"].lower()).ratio()
        score += ratio * 3
        peso_total += 3

    if isinstance(candidato["Tipo da vaga desejada"], str) and isinstance(vaga["Tipo"], str):
        if candidato["Tipo da vaga desejada"].lower() == vaga["Tipo"].lower():
            score += 1
        peso_total += 1

    if isinstance(candidato["Área de interesse"], str) and isinstance(vaga["Area"], str):
        if candidato["Área de interesse"].lower() in vaga["Area"].lower():
            score += 1
        peso_total += 1

    score += idioma_score(candidato["Nível de inglês"], vaga["Level de Ingles"])
    peso_total += 1
    score += idioma_score(candidato["Nível de espanhol"], vaga["Level de Espanhol"])
    peso_total += 1

    if candidato["Possui equipamento próprio? (Sim/Não)"].lower() == "sim" and "não" not in vaga["Precisa de Equipamento"].lower():
        score += 1
    peso_total += 1

    if candidato["Disponível para viagens? (Sim/Não)"].lower() == vaga["Precisa Viajar"].lower():
        score += 1
    peso_total += 1

    candidato_skills = ", ".join(candidato["Competências técnicas"]).lower() if isinstance(candidato["Competências técnicas"], list) else ""
    vaga_skills = str(vaga["Habilidades"]).lower()
    sim_hab = similaridade_habilidades(candidato_skills, vaga_skills)
    score += sim_hab * 4
    peso_total += 4

    return round((score / peso_total) * 100, 2) if peso_total else 0

# Interface Streamlit
st.title("🤖 Match Inteligente de Vagas com IA")
vagas_df = carregar_vagas()
titulos_disponiveis = sorted(vagas_df["Vaga"].dropna().unique())
areas_disponiveis = sorted(vagas_df["Area"].dropna().unique())
todas_habilidades = vagas_df["Habilidades"].dropna().str.cat(sep=", ").lower().split(",")
habilidades_unicas = sorted(set(h.strip().capitalize() for h in todas_habilidades if h.strip() != ""))

with st.form("formulario_candidato"):
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

    st.success("Dados salvos no Google Sheets com sucesso!")

    st.info("🔄 Calculando compatibilidade...")
    vagas_df["ia_score"] = vagas_df.apply(lambda row: calcular_score(candidato, row), axis=1)
    top_vagas = vagas_df.sort_values(by="ia_score", ascending=False).head(5)

    st.subheader("🏆 Top 5 Vagas Compatíveis")
    for _, vaga in top_vagas.iterrows():
        st.markdown(f"### {vaga['Vaga']}")
        st.markdown(f"**Tipo:** {vaga['Tipo']}")
        st.markdown(f"**Área:** {vaga['Area']}")
        st.markdown(f"**Cliente:** {vaga['Empresa']}")
        st.markdown(f"**Score IA:** {vaga['ia_score']}%")
        st.markdown(f"**Requisitos:** {vaga['Habilidades']}")
        st.markdown(f"**Descrição:** {vaga['Descricao']}")
        st.markdown(f"**Salário oferecido:** {vaga['Salario']}")
        st.markdown("---")
