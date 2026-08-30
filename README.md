# Vidas Marinhas — aplicativo educacional em Streamlit

Aplicativo web educacional inspirado no cartaz do projeto **Desenvolvimento Web na Prática: Construindo a Plataforma Vidas Marinhas**. A interface organiza conteúdos sobre ecossistemas, fauna, flora e ciclos biogeoquímicos do oceano, além de oferecer um quiz e um formulário para dúvidas.

## Funcionalidades

A aplicação possui navegação lateral entre oito áreas: Início, Sobre, Ecossistemas, Fauna & Flora, Ciclos do oceano, Quiz rápido, Contato e Gestão de dúvidas. O formulário funciona imediatamente em modo demonstração, salvando os registros em `data/duvidas.jsonl`. Quando o arquivo privado `firebase.json` é colocado na raiz do projeto, o envio passa a usar o Google Cloud Firestore. A tela de gestão permite consultar, editar e excluir registros, atendendo ao requisito de operações CRUD do projeto.

## Execução e publicação

Para testar localmente:

```bash
cd vidas_marinhas_streamlit
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Para seguir o caminho das diretrizes no celular, crie um repositório no GitHub, envie os arquivos do projeto sem `firebase.json`, acesse o [Streamlit Community Cloud](https://streamlit.io/cloud), faça login com Google, crie uma aplicação em branco, selecione o repositório e indique `app.py` como arquivo principal. O código será publicado diretamente a partir do GitHub.

O navegador abrirá em `http://localhost:8501`.

## Configuração do Firebase/Firestore

Siga o fluxo mostrado nas diretrizes: crie um projeto no [Firebase Console](https://console.firebase.google.com), ative o Cloud Firestore e gere uma chave privada de conta de serviço. Renomeie o arquivo baixado para `firebase.json` e coloque-o na raiz do projeto. O `.gitignore` já impede que essa chave seja enviada ao GitHub.

A aplicação usa a biblioteca `google-cloud-firestore` e grava os registros na coleção `duvidas`. Em produção, configure as regras de segurança e mantenha a chave privada somente nos Secrets ou no ambiente protegido da implantação. Não publique `firebase.json` em repositórios públicos.

No Streamlit Community Cloud, a alternativa mais segura é armazenar o conteúdo da credencial nos Secrets e adaptar `firestore_client()` para ler essa configuração, em vez de enviar o arquivo privado ao repositório.

## Estrutura

```text
vidas_marinhas_streamlit/
├── app.py
├── requirements.txt
├── README.md
├── RELATORIO_VIDAS_MARINHAS.md
├── RELATORIO_VIDAS_MARINHAS.pdf
├── ROTEIRO_VIDEO.md
├── .gitignore
├── REQUISITOS_PDF.md
├── .streamlit/config.toml
├── assets/
│   ├── cartaz_referencia.jpg
│   ├── recife_vida_marinha.jpg
│   ├── tartaruga_noaa.jpg
│   └── tartaruga_recife.jpg
└── data/
    └── duvidas.jsonl  # criado após o primeiro envio local
```

## Imagens

O cartaz enviado pelo usuário foi mantido como referência local. As imagens de apoio foram coletadas de páginas públicas de organizações e projetos relacionados à educação marinha, incluindo a NOAA Fisheries e o Aquarium of the Pacific. Verifique as condições de uso e atribuição antes de publicar o aplicativo fora de um contexto educacional.

## Próximas melhorias

Como extensão, o projeto pode receber autenticação de usuários, painel administrativo para leitura das dúvidas, filtros por faixa etária, atividades arrasta-e-solta e uma camada de acessibilidade com audiodescrição dos conteúdos visuais.
