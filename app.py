from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).parent
ASSETS = APP_DIR / "assets"
DATA_DIR = APP_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
QUESTIONS_FILE = DATA_DIR / "duvidas.jsonl"

st.set_page_config(
    page_title="Vidas Marinhas | Aprender para proteger",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');
    :root { --deep:#062b3a; --teal:#0f8b8d; --aqua:#22c7c9; --sand:#f5f0e6; --ink:#17313b; }
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; color: var(--ink); }
    .stApp { background: linear-gradient(180deg, #f7fbfa 0%, #eef7f6 100%); }
    [data-testid="stSidebar"] { background: var(--deep); }
    [data-testid="stSidebar"] * { color: #eaf8f6 !important; }
    h1, h2, h3 { font-family: 'Playfair Display', serif; color: var(--deep); }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color:#fff !important; }
    .hero { padding: 2.4rem 2.8rem; border-radius: 26px; background: linear-gradient(118deg, rgba(6,43,58,.95), rgba(15,139,141,.84)), url('https://images.unsplash.com/photo-1544551763-46a013bb70d5?auto=format&fit=crop&w=1600&q=85') center/cover; color:white; margin-bottom:1.5rem; box-shadow:0 18px 45px rgba(6,43,58,.16); }
    .hero h1 { color:white; font-size: clamp(2.3rem, 5vw, 4.6rem); margin:0; line-height:1.02; }
    .hero p { font-size:1.15rem; max-width:660px; color:#e3fbf8; margin-top:1rem; }
    .eyebrow { text-transform:uppercase; letter-spacing:.16em; font-size:.78rem; font-weight:700; color:#8ef3e9; }
    .pill { display:inline-block; background:#d8faf3; color:#086a6a; border-radius:999px; padding:.35rem .7rem; font-size:.8rem; font-weight:700; margin:.15rem .2rem .15rem 0; }
    .card { background:rgba(255,255,255,.9); border:1px solid #d9ece9; padding:1.2rem 1.3rem; border-radius:18px; height:100%; box-shadow:0 8px 26px rgba(6,43,58,.06); }
    .card h3 { margin-top:0; font-size:1.35rem; }
    .metric { border-left:5px solid var(--aqua); padding:.8rem 1rem; background:white; border-radius:12px; box-shadow:0 7px 20px rgba(6,43,58,.06); }
    .metric strong { display:block; font-size:1.9rem; color:var(--teal); }
    .source { color:#638087; font-size:.78rem; }
    .quote { border-left:5px solid var(--aqua); background:#e8f8f5; padding:1rem 1.2rem; border-radius:0 14px 14px 0; font-style:italic; }
    .footer { margin-top:3rem; padding:1.3rem 0; color:#638087; border-top:1px solid #cfe3e0; font-size:.85rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


def image_path(name: str) -> str:
    """Localiza a imagem na pasta assets ou, como fallback, na raiz do GitHub."""
    asset_file = ASSETS / name
    root_file = APP_DIR / name
    return str(asset_file if asset_file.exists() else root_file)


def save_question(name: str, email: str, question: str) -> None:
    record = {"data": datetime.now().isoformat(timespec="seconds"), "nome": name, "email": email, "duvida": question}
    with QUESTIONS_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")


@st.cache_resource(show_spinner=False)
def firestore_client():
    """Cria um cliente Firestore a partir do firebase.json privado, se existir."""
    credentials_file = APP_DIR / "firebase.json"
    if not credentials_file.exists():
        return None
    try:
        from google.cloud import firestore
        from google.oauth2 import service_account
        credentials = service_account.Credentials.from_service_account_file(str(credentials_file))
        return firestore.Client(project=credentials.project_id, credentials=credentials)
    except Exception:
        return None


def send_to_firebase(record: dict) -> bool:
    client = firestore_client()
    if client is None:
        return False
    try:
        client.collection("duvidas").add(record)
        return True
    except Exception:
        return False


def load_questions() -> list[dict]:
    """Consulta dúvidas do Firestore ou do arquivo local de demonstração."""
    client = firestore_client()
    if client is not None:
        try:
            return [{"id": doc.id, **doc.to_dict()} for doc in client.collection("duvidas").stream()]
        except Exception:
            pass
    if not QUESTIONS_FILE.exists():
        return []
    records = []
    for line in QUESTIONS_FILE.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return [{"id": str(index), **record} for index, record in enumerate(records)]


def update_question(question_id: str, updated: dict) -> bool:
    client = firestore_client()
    if client is not None:
        try:
            client.collection("duvidas").document(question_id).update(updated)
            return True
        except Exception:
            return False
    records = load_questions()
    for record in records:
        if record["id"] == question_id:
            record.update(updated)
    QUESTIONS_FILE.write_text("\n".join(json.dumps({k: v for k, v in r.items() if k != "id"}, ensure_ascii=False) for r in records) + ("\n" if records else ""), encoding="utf-8")
    return True


def delete_question(question_id: str) -> bool:
    client = firestore_client()
    if client is not None:
        try:
            client.collection("duvidas").document(question_id).delete()
            return True
        except Exception:
            return False
    records = [r for r in load_questions() if r["id"] != question_id]
    QUESTIONS_FILE.write_text("\n".join(json.dumps({k: v for k, v in r.items() if k != "id"}, ensure_ascii=False) for r in records) + ("\n" if records else ""), encoding="utf-8")
    return True


with st.sidebar:
    st.markdown("# Vidas Marinhas")
    st.caption("Aprender para proteger")
    page = st.radio(
        "Navegação",
        ["Início", "Sobre", "Ecossistemas", "Fauna & Flora", "Ciclos do oceano", "Quiz rápido", "Contato", "Gestão de dúvidas"],
        label_visibility="collapsed",
    )
    st.divider()
    st.markdown("**Público-alvo**")
    st.caption("Estudantes, professores e pessoas interessadas na conservação dos oceanos.")
    st.markdown("**Projeto educacional**")
    st.caption("Desenvolvimento Web na Prática · Python · Streamlit · Firestore")

if page == "Início":
    st.markdown("<div class='hero'><div class='eyebrow'>Plataforma de educação oceânica</div><h1>O oceano começa aqui.</h1><p>Explore ecossistemas, conheça espécies e entenda as conexões que mantêm a vida marinha em equilíbrio.</p><span class='pill'>Conteúdo científico</span><span class='pill'>Aprendizagem ativa</span><span class='pill'>Conservação</span></div>", unsafe_allow_html=True)
    st.markdown("## Uma jornada azul em três passos")
    cols = st.columns(3)
    for col, title, text in zip(cols, ["01 · Explorar", "02 · Conectar", "03 · Agir"], ["Navegue por ambientes costeiros, recifes, manguezais e mar aberto.", "Relacione espécies, ciclos biogeoquímicos e serviços ecossistêmicos.", "Transforme conhecimento em atitudes para proteger o oceano." ]):
        with col:
            st.markdown(f"<div class='card'><h3>{title}</h3><p>{text}</p></div>", unsafe_allow_html=True)
    st.write("")
    left, right = st.columns([1.1, 1])
    with left:
        st.image(image_path("tartaruga_noaa.jpg"), width="stretch", caption="Tartaruga-de-pente em seu ambiente marinho — NOAA Fisheries")
    with right:
        st.markdown("### Por que o oceano importa?")
        st.write("O oceano abriga uma enorme diversidade de formas de vida e participa da regulação do clima, da produção de oxigênio e do sustento de comunidades humanas. Nesta plataforma, o conteúdo foi organizado para transformar curiosidade em compreensão.")
        st.markdown("<div class='quote'>Quando entendemos as conexões do oceano, cada escolha cotidiana passa a fazer parte da conservação.</div>", unsafe_allow_html=True)
    st.write("")
    m1, m2, m3, m4 = st.columns(4)
    for col, value, label in [(m1, "3", "trilhas de aprendizagem"), (m2, "6", "ecossistemas em destaque"), (m3, "8", "espécies para conhecer"), (m4, "1", "quiz para revisar")]:
        with col:
            st.markdown(f"<div class='metric'><strong>{value}</strong>{label}</div>", unsafe_allow_html=True)

elif page == "Sobre":
    st.markdown("<div class='eyebrow'>Sobre o projeto</div><h1>Conhecer para proteger</h1>", unsafe_allow_html=True)
    st.write("Vidas Marinhas é uma plataforma educativa criada para aproximar ciência, tecnologia e conservação dos oceanos.")
    about_left, about_right = st.columns([1, 1])
    with about_left:
        st.markdown("<div class='card'><h3>Objetivo</h3><p>Organizar conteúdos introdutórios sobre ambientes, espécies e ciclos marinhos em uma experiência acessível e interativa.</p><h3>Para quem?</h3><p>Estudantes, professores, profissionais da área ambiental e qualquer pessoa interessada em aprender sobre o oceano.</p></div>", unsafe_allow_html=True)
    with about_right:
        st.image(image_path("tartaruga_recife.jpg"), width="stretch", caption="Vida marinha e conservação")
    st.write("")
    st.info("Este projeto aplica menus, textos, imagens, formulários, animações, estilos e integração com banco de dados usando Python e Streamlit.")

elif page == "Ecossistemas":
    st.markdown("<div class='eyebrow'>Trilha 01</div><h1>Ecossistemas marinhos</h1>", unsafe_allow_html=True)
    st.write("Cada ambiente apresenta condições próprias de luz, salinidade, temperatura e movimento da água. Essas condições determinam quais espécies conseguem viver ali e quais relações ecológicas se formam.")
    ecosystems = {
        "Recifes de coral": ("Estruturas construídas por pequenos animais chamados corais, que oferecem abrigo e alimento para muitas espécies.", "Alta biodiversidade, águas rasas e quentes, relação entre corais e algas simbiontes."),
        "Manguezais": ("Áreas costeiras onde a água doce e a salgada se encontram, protegidas por árvores tolerantes ao sal.", "Berçário de peixes e crustáceos, retenção de sedimentos e proteção da costa."),
        "Mar aberto": ("A grande extensão oceânica além da plataforma continental, com ambientes que variam conforme a profundidade.", "Correntes marinhas, migração de grandes animais e zonas de pouca luz."),
        "Costões rochosos": ("Faixas entre o mar e a terra onde organismos precisam resistir às ondas e à variação da maré.", "Poças de maré, algas, moluscos e invertebrados adaptados à exposição ao ar."),
        "Pradarias marinhas": ("Áreas formadas por plantas com flores submersas, importantes para a captura de carbono e abrigo de juvenis.", "Águas rasas, sedimentos arenosos e alta produtividade ecológica."),
        "Mar profundo": ("Região escura e fria, sob alta pressão, onde a vida encontra energia por caminhos muito diferentes da fotossíntese.", "Quimiossíntese, fontes hidrotermais e espécies altamente especializadas."),
    }
    for row in range(0, len(ecosystems), 2):
        cols = st.columns(2)
        for col, (name, (description, traits)) in zip(cols, list(ecosystems.items())[row:row+2]):
            with col:
                st.markdown(f"<div class='card'><h3>{name}</h3><p>{description}</p><p><b>Características:</b> {traits}</p></div>", unsafe_allow_html=True)
        st.write("")

elif page == "Fauna & Flora":
    st.markdown("<div class='eyebrow'>Trilha 02</div><h1>Fauna & Flora</h1>", unsafe_allow_html=True)
    st.image(image_path("recife_vida_marinha.jpg"), width="stretch", caption="Comunidade de recife — Aquarium of the Pacific")
    st.write("A vida marinha está organizada em redes alimentares. Produtores, consumidores e decompositores trocam matéria e energia, conectando organismos muito diferentes.")
    species = pd.DataFrame([
        ["Tartaruga-verde", "Herbívora na fase adulta", "Pradarias marinhas", "Ajuda a manter a vegetação equilibrada"],
        ["Peixe-papagaio", "Herbívoro", "Recifes de coral", "Controla algas e contribui para a areia biogênica"],
        ["Mangue-vermelho", "Produtor", "Manguezais", "Protege a costa e retém carbono"],
        ["Baleia-jubarte", "Consumidora", "Mar aberto", "Transporta nutrientes entre diferentes camadas do oceano"],
        ["Fitoplâncton", "Produtor microscópico", "Superfície do oceano", "Base de muitas cadeias alimentares"],
        ["Coral construtor", "Animal colonial", "Recifes de coral", "Forma habitat para inúmeras espécies"],
    ], columns=["Espécie ou grupo", "Papel", "Ambiente", "Contribuição"])
    st.dataframe(species, width="stretch", hide_index=True)
    st.markdown("### A regra de ouro das redes alimentares")
    st.info("Alterações em uma população podem se espalhar pela rede inteira. Proteger habitats é tão importante quanto proteger espécies isoladas.")

elif page == "Ciclos do oceano":
    st.markdown("<div class='eyebrow'>Trilha 03</div><h1>Ciclos biogeoquímicos</h1>", unsafe_allow_html=True)
    st.write("Os ciclos biogeoquímicos descrevem o movimento de elementos essenciais entre atmosfera, água, sedimentos e seres vivos. Eles ajudam a explicar por que o oceano funciona como um sistema conectado.")
    cycles = {
        "Ciclo do carbono": "O carbono circula entre atmosfera, água, organismos e sedimentos. O fitoplâncton captura CO₂ durante a fotossíntese, enquanto a respiração e a decomposição devolvem carbono ao ambiente.",
        "Ciclo do nitrogênio": "Bactérias transformam compostos nitrogenados em formas que podem ser utilizadas por produtores. Esse ciclo sustenta proteínas, ácidos nucleicos e a produtividade dos ecossistemas.",
        "Ciclo do fósforo": "O fósforo chega ao oceano principalmente pelo desgaste de rochas e pelo transporte de sedimentos. Ele é importante para ATP, membranas celulares e material genético.",
        "Bomba biológica": "Parte do material orgânico produzido na superfície afunda e leva carbono para águas profundas. Esse processo conecta a superfície aos grandes reservatórios do oceano.",
    }
    for title, body in cycles.items():
        with st.expander(title, expanded=title == "Ciclo do carbono"):
            st.write(body)
    st.markdown("### Observe as conexões")
    chart = pd.DataFrame({"Processo": ["Fotossíntese", "Respiração", "Decomposição", "Transporte profundo"], "Conexão relativa": [92, 68, 54, 43]}).set_index("Processo")
    st.bar_chart(chart, color="#0f8b8d")
    st.caption("Gráfico didático para comparar a importância de processos no roteiro de aprendizagem; não representa uma medição global.")

elif page == "Quiz rápido":
    st.markdown("<div class='eyebrow'>Aprendizagem ativa</div><h1>Quiz rápido</h1>", unsafe_allow_html=True)
    st.write("Teste o que você aprendeu. Ao final, veja uma explicação para cada resposta.")
    questions = [
        ("Qual ambiente é conhecido como berçário de muitas espécies costeiras?", ["Mar profundo", "Manguezal", "Mar aberto", "Geleira"], "Manguezal"),
        ("Qual grupo está na base de muitas cadeias alimentares marinhas?", ["Fitoplâncton", "Tubarões", "Tartarugas adultas", "Caranguejos"], "Fitoplâncton"),
        ("O que a bomba biológica ajuda a transportar?", ["Luz", "Carbono para águas profundas", "Sal para a atmosfera", "Areia para os rios"], "Carbono para águas profundas"),
    ]
    answers = []
    for idx, (question, options, correct) in enumerate(questions):
        answer = st.radio(f"{idx+1}. {question}", options, key=f"q{idx}")
        answers.append((answer, correct))
    if st.button("Ver meu resultado", type="primary"):
        score = sum(answer == correct for answer, correct in answers)
        st.success(f"Você acertou {score} de {len(questions)} questões.")
        if score < len(questions):
            st.write("Revise as trilhas de ecossistemas e ciclos do oceano e tente novamente.")
        else:
            st.balloons()
            st.write("Excelente! Você conectou habitats, espécies e processos ecológicos.")

elif page == "Gestão de dúvidas":
    st.markdown("<div class='eyebrow'>Banco de dados</div><h1>Gestão de dúvidas</h1>", unsafe_allow_html=True)
    st.write("Consulte, edite e exclua registros enviados pelo formulário. Em produção, proteja esta área com autenticação do Streamlit Cloud ou de um proxy institucional.")
    questions = load_questions()
    if not questions:
        st.info("Ainda não há dúvidas cadastradas.")
    else:
        st.caption(f"{len(questions)} registro(s) encontrado(s) · {'Firestore' if firestore_client() else 'modo local'}")
        for record in questions:
            question_id = record["id"]
            with st.expander(f"{record.get('nome', 'Sem nome')} · {record.get('data', '')}"):
                new_question = st.text_area("Dúvida", record.get("duvida", ""), key=f"question_{question_id}")
                new_email = st.text_input("E-mail", record.get("email", ""), key=f"email_{question_id}")
                edit_col, delete_col = st.columns(2)
                with edit_col:
                    if st.button("Salvar edição", key=f"edit_{question_id}"):
                        if update_question(question_id, {"email": new_email, "duvida": new_question}):
                            st.success("Registro atualizado.")
                            st.rerun()
                with delete_col:
                    if st.button("Excluir registro", key=f"delete_{question_id}"):
                        if delete_question(question_id):
                            st.warning("Registro excluído.")
                            st.rerun()

elif page == "Contato":
    st.markdown("<div class='eyebrow'>Fale com o projeto</div><h1>Contato</h1>", unsafe_allow_html=True)
    st.write("Use o formulário para enviar perguntas, sugestões de conteúdo ou pedidos de aprofundamento.")
    with st.form("duvida_form", clear_on_submit=True):
        name = st.text_input("Nome")
        email = st.text_input("E-mail")
        question = st.text_area("Sua dúvida ou sugestão", height=150)
        submitted = st.form_submit_button("Enviar dúvida", type="primary")
    if submitted:
        if not name.strip() or not email.strip() or not question.strip():
            st.error("Preencha nome, e-mail e dúvida antes de enviar.")
        elif "@" not in email:
            st.error("Digite um e-mail válido.")
        else:
            record = {"data": datetime.now().isoformat(timespec="seconds"), "nome": name.strip(), "email": email.strip(), "duvida": question.strip()}
            firebase_sent = send_to_firebase(record)
            if not firebase_sent:
                save_question(name.strip(), email.strip(), question.strip())
            st.success("Dúvida enviada com sucesso. Obrigado por participar!")
            if not firebase_sent:
                st.caption("Modo demonstração: o registro foi salvo localmente. Adicione o arquivo privado firebase.json para usar o Firestore.")
            else:
                st.caption("Registro enviado ao Firestore em tempo real.")

st.markdown("<div class='footer'>Vidas Marinhas · Projeto educacional em Python e Streamlit · Conteúdo organizado para apoiar a aprendizagem e a conservação.</div>", unsafe_allow_html=True)
