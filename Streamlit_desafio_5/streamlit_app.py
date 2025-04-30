import streamlit as st
import pandas as pd
import difflib

st.set_page_config(page_title="Match de Vagas", page_icon="💼", layout="centered")

# ---------- CONFIG ---------- #
CAMINHO_VAGAS = "Streamlit_desafio_5/Vagas.xlsx"

# ---------- FUNÇÕES AUXILIARES ---------- #
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

def calcular_score(candidato, vaga):
    score = 0
    peso_total = 0

    # Título da vaga
    if isinstance(candidato["Título da vaga desejada"], str) and isinstance(vaga["Vaga"], str):
        ratio = difflib.SequenceMatcher(None, candidato["Título da vaga desejada"].lower(), vaga["Vaga"].lower()).ratio()
        score += ratio * 2
        peso_total += 2

    # Tipo (Júnior, Pleno, Sênior)
    if isinstance(candidato["Tipo da vaga desejada"], str) and isinstance(vaga["Tipo"], str):
        if candidato["Tipo da vaga desejada"].lower() == vaga["Tipo"].lower():
            score += 1
        peso_total += 1

    # Área
    if isinstance(candidato["Área de interesse"], str) and isinstance(vaga["Area"], str):
        if candidato["Área de interesse"].lower() in vaga["Area"].lower():
            score += 1
        peso_total += 1

    # Inglês
    if isinstance(candidato["Nível de inglês"], str) and isinstance(vaga["Level de Ingles"], str):
        if candidato["Nível de inglês"].lower() in vaga["Level de Ingles"].lower():
            score += 1
        peso_total += 1

    # Espanhol
    if isinstance(candidato["Nível de espanhol"], str) and isinstance(vaga["Level de Espanhol"], str):
        if candidato["Nível de espanhol"].lower() in vaga["Level de Espanhol"].lower():
            score += 1
        peso_total += 1

    # Equipamento
    if isinstance(candidato["Possui equipamento próprio? (Sim/Não)"], str) and isinstance(vaga["Precisa de Equipamento"], str):
        if candidato["Possui equipamento próprio? (Sim/Não)"].lower() == "sim" and "não" not in vaga["Precisa de Equipamento"].lower():
            score += 1
        peso_total += 1

    # Viagens
    if isinstance(candidato["Disponível para viagens? (Sim/Não)"], str) and isinstance(vaga["Precisa Viajar"], str):
        if candidato["Disponível para viagens? (Sim/Não)"].lower() == vaga["Precisa Viajar"].lower():
            score += 1
        peso_total += 1

    # Competências técnicas
    candidato_skills = set(str(candidato["Competências técnicas"]).lower().split(",")) if isinstance(candidato["Competências técnicas"], str) else set()
    vaga_skills = set(str(vaga["Habilidades"]).lower().split(",")) if isinstance(vaga["Habilidades"], str) else set()
    intersecao = candidato_skills.intersection(vaga_skills)
    if vaga_skills:
        score += len(intersecao) / len(vaga_skills) * 3
        peso_total += 3

    # Outros idiomas
    if isinstance(candidato["Outros idiomas"], str) and isinstance(vaga["Outros idiomas"], str):
        if candidato["Outros idiomas"].lower() in vaga["Outros idiomas"].lower():
            score += 1
        peso_total += 1

    # Descrição da vaga
    if isinstance(vaga["Descricao"], str) and isinstance(candidato["Competências técnicas"], str):
        ratio_desc = difflib.SequenceMatcher(None, candidato["Competências técnicas"].lower(), vaga["Descricao"].lower()).ratio()
        score += ratio_desc * 2
        peso_total += 2

    return round((score / peso_total) * 100, 2) if peso_total else 0

# ---------- INTERFACE STREAMLIT ---------- #
vagas_df = carregar_vagas()
titulos_disponiveis = sorted(vagas_df["Vaga"].dropna().unique())

st.title("🔍 Plataforma de Match de Vagas")
st.markdown("Preencha abaixo e veja quais vagas combinam com você!")

with st.form("formulario_candidato"):
    st.subheader("📄 Dados do Candidato")
    titulo = st.selectbox("Título da vaga desejada", titulos_disponiveis)
    tipo = st.selectbox("Tipo da vaga desejada", ["Júnior", "Pleno", "Sênior"])
    area = st.text_input("Área de interesse")
    ingles = st.selectbox("Nível de inglês", ["Nenhum", "Básico", "Intermediário", "Avançado", "Fluente"])
    espanhol = st.selectbox("Nível de espanhol", ["Nenhum", "Básico", "Intermediário", "Avançado", "Fluente"])
    outros_idiomas = st.text_input("Outros idiomas")
    tecnicas = st.text_area("Competências técnicas (separadas por vírgula)")
    comportamentais = st.text_area("Competências comportamentais")
    viagens = st.selectbox("Disponível para viagens?", ["Sim", "Não"])
    equipamento = st.selectbox("Possui equipamento próprio?", ["Sim", "Não"])
    salario = st.text_input("Expectativa salarial")

    enviado = st.form_submit_button("🔎 Encontrar Vagas")

if enviado:
    candidato = {
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

    st.info("🔄 Processando suas informações...")
    vagas_df["ia_score"] = vagas_df.apply(lambda row: calcular_score(candidato, row), axis=1)
    top_vagas = vagas_df.sort_values(by="ia_score", ascending=False).head(5)

    st.success("✅ Veja abaixo suas vagas com maior compatibilidade!")
    st.subheader("🏆 Top 5 Vagas Compatíveis")

    for i, vaga in top_vagas.iterrows():
        st.markdown(f"### {vaga['Vaga']}")
        st.markdown(f"**Tipo:** {vaga['Tipo']}")
        st.markdown(f"**Área:** {vaga['Area']}")
        st.markdown(f"**Cliente:** {vaga['Empresa']}")
        st.markdown(f"**Score de compatibilidade:** {vaga['ia_score']}%")
        st.markdown(f"**Requisitos:** {vaga['Habilidades']}")
        st.markdown(f"**Descrição:** {vaga['Descricao']}")
        st.markdown(f"**Salário oferecido:** {vaga['Salario']}")
        st.markdown("---")
