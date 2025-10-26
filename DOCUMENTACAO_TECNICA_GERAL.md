# 📚 Documentação Técnica Geral - Projeto VidConv

**Sistema Integrado para Conversão e Gerenciamento de Vídeos**

---

## 📋 Índice

1. [Visão Geral](#-visão-geral)
2. [Arquitetura do Sistema](#-arquitetura-do-sistema)
3. [Módulos Principais](#-módulos-principais)
    - [Interface Gráfica (GUI)](#-interface-gráfica-gui)
    - [Módulo de Conversão de Vídeo](#-módulo-de-conversão-de-vídeo)
    - [Instalador e Gerenciador de Dependências](#-instalador-e-gerenciador-de-dependências)
    - [Serviço de Usuários (API Users)](#-serviço-de-usuários-api-users)
    - [Serviço de Notificações](#-serviço-de-notificações)
4. [Fluxos de Trabalho](#-fluxos-de-trabalho)
5. [Configuração e Deploy](#-configuração-e-deploy)

---

## 🏗️ Arquitetura do Sistema

O sistema VidConv é composto por uma aplicação de desktop principal e um conjunto de serviços de backend que podem ser implantados de forma independente. A arquitetura foi projetada para ser modular e escalável.

### Diagrama de Arquitetura

```
+----------------------------------------------------+
|               Aplicação Desktop (GUI)              |
|  (main_tkinter.py)                                 |
|                                                    |
| +------------------------------------------------+ |
| |  Módulo de Conversão de Vídeo (local)          | |
| |  (video_converter_module)                      | |
| +------------------------------------------------+ |
|                                                    |
| +------------------------------------------------+ |
| |  Downloader de Mídia (yt-dlp) (local)          | |
| +------------------------------------------------+ |
+-------------------------|--------------------------+
                          |
                          | (HTTP/REST API Calls)
                          v
+-------------------------|--------------------------+
|               Gateway de API (Futuro)              |
+-------------------------|--------------------------+
                          |
            +-------------+-------------+
            |                           |
            v                           v
+-------------------------+ +-------------------------+
|  Serviço de Usuários    | |  Serviço de Notificações  |
|  (user_service)         | |  (notification_service) |
|                         | |                         |
| +---------------------+ | | +---------------------+ |
| |   Banco de Dados    | | | |   Serviço de Email  | |
| |   (MySQL/MariaDB)   | | | |   (ex: GMail)       | |
| +---------------------+ | | +---------------------+ |
+-------------------------+ +-------------------------+

```

### Descrição dos Componentes

- **Aplicação Desktop (GUI):** O ponto de entrada para o usuário. É uma aplicação Python com interface gráfica em Tkinter que orquestra as chamadas para os módulos locais (conversão, download) e para os serviços de backend (autenticação, etc.).

- **Módulos Locais:**
  - **Módulo de Conversão de Vídeo:** Uma biblioteca Python que encapsula a lógica de linha de comando do FFmpeg para realizar as conversões de vídeo.
  - **Downloader de Mídia:** Utiliza a biblioteca `yt-dlp` para baixar conteúdo de vídeo e áudio da web.

- **Serviços de Backend:**
  - **Serviço de Usuários:** Uma API RESTful construída com FastAPI, responsável por todo o ciclo de vida do usuário, autenticação, autorização e gerenciamento de perfis. Ele possui seu próprio banco de dados.
  - **Serviço de Notificações:** Responsável por enviar comunicações aos usuários, como e-mails de confirmação de cadastro ou notificações sobre o status de uma conversão longa. (Atualmente integrado, mas pode ser um serviço separado).

- Gateway de API (Planejamento Futuro): Um ponto de entrada único para todas as requisições da API, simplificando a comunicação entre o cliente e os microsserviços, além de adicionar uma camada de segurança e orquestração.

---

## Módulos Principais

### 1. Interface Gráfica (GUI)

- **Arquivo Principal:** `gui/main_window_tkinter.py`
- **Framework:** Tkinter

**Descrição:**

A GUI é o coração da interação do usuário com o VidConv. Ela foi construída com a biblioteca padrão do Python, Tkinter, por sua simplicidade e por não exigir dependências externas pesadas. A interface é organizada em abas para separar as diferentes funcionalidades (Conversão, Download, etc.), proporcionando uma experiência de usuário clara e organizada.

**Componentes Chave:**

- **`MainWindow` (classe principal):** Orquestra toda a janela, inicializa os componentes, as abas e gerencia o estado geral da aplicação.
- **Abas (Notebook):** Cada aba corresponde a uma funcionalidade principal:
  - **Conversor:** Permite ao usuário selecionar arquivos de vídeo, escolher formatos de saída, definir a resolução e iniciar o processo de conversão.
  - **Download:** Oferece uma interface para colar URLs do YouTube, selecionar a qualidade desejada e baixar o conteúdo.
  - **Configurações:** Centraliza as configurações da aplicação, como a localização do FFmpeg e preferências do usuário.
- **Widgets de Interação:** Utiliza uma variedade de widgets do Tkinter (botões, caixas de texto, menus suspensos, barras de progresso) para capturar a entrada do usuário e exibir o status dos processos.
- **Gerenciamento de Threads:** Para evitar que a interface do usuário congele durante operações longas (como conversão ou download), a aplicação utiliza threads separadas para executar essas tarefas em segundo plano. A comunicação de volta para a thread principal da GUI (para atualizar barras de progresso, por exemplo) é feita de forma segura usando `queue` ou `after`.

**Fluxo de Interação Típico (Conversão):**

1. O usuário clica no botão "Selecionar Arquivos" para abrir um diálogo de seleção de arquivo.
2. Após selecionar um ou mais vídeos, a lista de arquivos é exibida na interface.
3. O usuário escolhe o formato de saída e a resolução desejada nos menus suspensos.
4. Ao clicar em "Converter", uma nova thread é iniciada para chamar o `video_converter_module`.
5. A barra de progresso na GUI é atualizada em tempo real para refletir o andamento da conversão.
6. Uma mensagem de sucesso ou erro é exibida ao final do processo.

### 2. Módulo de Conversão de Vídeo

- **Diretório:** `video_converter_module/`
- **Tecnologia Principal:** FFmpeg (via `subprocess`)

**Descrição:**

Este módulo é o cérebro por trás da funcionalidade de conversão de vídeo. Ele atua como uma camada de abstração sobre o FFmpeg, traduzindo as seleções do usuário na GUI em comandos de linha de comando específicos do FFmpeg. Ele foi projetado para ser robusto, lidar com diferentes cenários de conversão e fornecer feedback em tempo real sobre o progresso.

**Componentes Chave:**

- **`VideoConverter` (classe principal):** Contém a lógica para construir e executar os comandos do FFmpeg. Recebe como entrada a lista de arquivos, o formato de saída, a resolução e outras opções.
- **Construção de Comando:** Monta dinamicamente a string de comando do FFmpeg com base nas opções fornecidas. Isso inclui a seleção de codecs (`-c:v`, `-c:a`), o ajuste de resolução (`-vf scale=...`), o controle de bitrate (`-b:v`) e a definição do formato de saída.
- **Execução com `subprocess`:** O comando FFmpeg é executado em um processo separado usando o módulo `subprocess` do Python. Isso permite que a aplicação principal capture a saída (stdout e stderr) do FFmpeg em tempo real.
- **Parse da Saída do FFmpeg:** O módulo lê a saída do FFmpeg linha por linha para extrair informações cruciais, como a duração total do vídeo e o tempo atual do processamento. Esses dados são usados para calcular a porcentagem de progresso.
- **Callbacks de Progresso:** O módulo utiliza um sistema de *callbacks* para notificar a GUI sobre o progresso da conversão. A cada atualização de progresso extraída do FFmpeg, ele invoca uma função de callback (fornecida pela GUI), que por sua vez atualiza a barra de progresso na interface do usuário.

**Fluxo de Processamento Típico:**

1. A GUI instancia a classe `VideoConverter`, passando os caminhos dos arquivos de entrada, o diretório de saída e as opções de conversão.
2. O `VideoConverter` itera sobre cada arquivo de vídeo.
3. Para cada arquivo, ele primeiro usa o FFprobe (uma ferramenta do FFmpeg) para obter a duração total do vídeo.
4. Em seguida, constrói o comando FFmpeg completo para a conversão.
5. O processo FFmpeg é iniciado com `subprocess.Popen`, com os pipes de `stdout` e `stderr` configurados para serem lidos pelo Python.
6. O módulo entra em um loop, lendo a saída do FFmpeg em tempo real.
7. Expressões regulares são usadas para encontrar e extrair o timestamp do progresso (ex: `time=00:01:23.45`).
8. O progresso é calculado como `(tempo_atual / duração_total) * 100`.
9. A função de callback é chamada com o valor do progresso, atualizando a GUI.
10. Ao final do processo, o módulo notifica a GUI sobre a conclusão (sucesso ou falha).

### 3. Downloader de Mídia (yt-dlp)

- **Tecnologia Principal:** `yt-dlp` (biblioteca Python)

**Descrição:**

Integrado à aba "Download de Mídia", este módulo oferece aos usuários a capacidade de baixar vídeos e extrair áudio de uma vasta gama de plataformas online, com destaque para o YouTube. Ele utiliza a poderosa e versátil biblioteca `yt-dlp`, um fork do popular `youtube-dl`, conhecido por seu amplo suporte a sites e flexibilidade.

**Componentes Chave:**

- **Interface de Entrada:** Um campo de texto na GUI permite que o usuário cole a URL do vídeo desejado.
- **Seleção de Formato:** O módulo permite que o usuário escolha entre baixar o vídeo completo (com a melhor qualidade de áudio e vídeo combinadas) ou extrair apenas o áudio (geralmente no formato M4A ou MP3).
- **Wrapper do `yt-dlp`:** A lógica de download é encapsulada em uma função que configura e chama a biblioteca `yt-dlp`. As opções (`ydl_opts`) são cuidadosamente definidas para controlar o comportamento do download.
- **Opções de Configuração (`ydl_opts`):**
    - `format`: Usado para especificar a qualidade e o tipo de stream a ser baixado. Por exemplo, `'bestvideo+bestaudio/best'` tenta baixar as melhores faixas de vídeo e áudio separadamente e depois mesclá-las.
    - `outtmpl`: Define o template do nome do arquivo de saída, incluindo o diretório e a extensão.
    - `progress_hooks`: Um dos recursos mais importantes para a integração com a GUI. É uma lista de funções (callbacks) que o `yt-dlp` chama periodicamente durante o processo de download, passando um dicionário com o status atual (ex: bytes baixados, tamanho total, velocidade, etc.).
    - `ffmpeg_location`: Especifica o caminho para o executável do FFmpeg, que é essencial para o `yt-dlp` mesclar streams de vídeo e áudio ou para realizar a extração de áudio.
- **Gerenciamento de Thread:** Assim como a conversão, o processo de download é executado em uma thread separada para não congelar a interface principal. O progresso é comunicado de volta à thread principal de forma segura para atualizar os widgets da GUI.

**Fluxo de Download Típico:**

1. O usuário cola uma URL na aba de download e seleciona o formato desejado (vídeo ou áudio).
2. Ao clicar em "Baixar", a GUI inicia uma nova thread, chamando a função de download.
3. A função de download configura o dicionário `ydl_opts` com base nas escolhas do usuário.
4. O `progress_hook` é definido para uma função que recebe o status do download e o coloca em uma fila ou usa um mecanismo seguro para notificar a thread da GUI.
5. A instância do `yt_dlp.YoutubeDL` é criada com as opções configuradas e o método `download()` é chamado com a lista de URLs.
6. Durante o download, o `yt-dlp` invoca o `progress_hook`.
7. A função de hook calcula a porcentagem de progresso e atualiza a barra de progresso na GUI.
8. Se o FFmpeg for necessário para mesclar ou converter, o `yt-dlp` o chama automaticamente.
9. Ao final, a GUI é notificada da conclusão e exibe uma mensagem de sucesso ou erro.

### 4. Módulo Instalador

- **Diretório:** `installer/`
- **Tecnologia Principal:** Python (módulos `os`, `subprocess`, `requests`)

**Descrição:**

O módulo instalador é um componente crítico projetado para simplificar drasticamente a configuração inicial do VidConv. Sua principal responsabilidade é garantir que todas as dependências externas e componentes essenciais, como FFmpeg e drivers CUDA, estejam presentes e corretamente configurados no sistema do usuário antes da primeira execução da aplicação principal. Ele automatiza um processo que, de outra forma, seria manual, complexo e propenso a erros.

**Componentes Chave:**

- **`os_detector`:** Detecta o sistema operacional do usuário (Windows, macOS, Linux) para determinar os procedimentos de instalação corretos.
- **`gpu_detector`:** Verifica a presença de uma GPU NVIDIA e a compatibilidade com CUDA, uma informação vital para habilitar a aceleração de hardware na conversão de vídeo.
- **`ffmpeg_manager`:** Gerencia o download e a instalação do FFmpeg. Ele baixa a compilação apropriada para o sistema operacional do usuário de uma fonte confiável e a extrai para um local conhecido, adicionando-a ao PATH do sistema, se necessário.
- **`cuda_installer`:** Se uma GPU NVIDIA compatível for detectada, este componente guia o usuário ou tenta automatizar a instalação do NVIDIA CUDA Toolkit, que é um pré-requisito para a codificação/decodificação de vídeo acelerada por GPU (NVENC/NVDEC).
- **`python_manager`:** Verifica a versão do Python e pode, no futuro, gerenciar ambientes virtuais para isolar as dependências do projeto.
- **`downloader`:** Um utilitário robusto para baixar arquivos da internet, exibindo uma barra de progresso para fornecer feedback visual ao usuário durante o download de componentes grandes como o FFmpeg ou o CUDA Toolkit.

**Fluxo de Instalação Típico:**

1. O `main_installer.py` é executado como o ponto de entrada.
2. O `os_detector` identifica o sistema operacional.
3. O `gpu_detector` verifica o hardware gráfico.
4. O `ffmpeg_manager` verifica se o FFmpeg já existe e está acessível. Se não estiver, ele inicia o processo de download e instalação, usando o `downloader` para buscar o arquivo.
5. Com base na detecção da GPU, o `cuda_installer` verifica a instalação do CUDA. Se ausente, ele informa ao usuário sobre os benefícios da aceleração de hardware e fornece instruções ou links para a instalação.
6. O instalador verifica o arquivo `requirements.txt` e garante que todas as dependências Python sejam instaladas usando o `pip`.
7. Ao final do processo, uma mensagem indica que a instalação foi concluída com sucesso e que a aplicação principal pode ser iniciada.

### 5. API de Usuários (user_service)

- **Diretório:** `user_service/`
- **Tecnologia Principal:** FastAPI, SQLAlchemy, Pydantic, Alembic, MySQL/MariaDB

**Descrição:**

O `user_service` é um microsserviço de backend independente, construído com FastAPI, que serve como a autoridade central para tudo relacionado a usuários, autenticação e autorização. Ele foi projetado para ser escalável e seguro, seguindo as melhores práticas de desenvolvimento de APIs RESTful. A comunicação com a aplicação desktop (e futuras aplicações web/mobile) ocorrerá por meio de um Gateway de API (a ser implementado), que roteará as requisições para este serviço.

**Componentes Chave:**

- **API (FastAPI):** Define todos os endpoints da API RESTful. Utiliza a injeção de dependências do FastAPI para gerenciar sessões de banco de dados e serviços.
    - **Endpoints:** `/register`, `/login`, `/logout`, `/users/me`, etc.
- **Schemas (Pydantic):** Modelos de dados para validação de entrada e serialização de saída. Garantem que os dados que entram e saem da API estejam no formato correto (ex: `UserCreate`, `UserRead`, `Token`).
- **Models (SQLAlchemy):** Define a estrutura das tabelas do banco de dados (`users`, `credentials`) e seus relacionamentos. É a representação ORM (Object-Relational Mapping) dos dados.
- **Services:** Camada de lógica de negócios. Contém as funções que interagem com o banco de dados e executam as operações principais (ex: `create_user`, `authenticate_user`). Desacopla a lógica de negócios dos endpoints da API.
- **Database:** Contém a configuração da conexão com o banco de dados (MySQL/MariaDB) e a inicialização da sessão do SQLAlchemy.
- **Migrations (Alembic):** Ferramenta para gerenciamento de migrações de esquema de banco de dados. Permite que a estrutura do banco de dados evolua de forma controlada e versionada à medida que o modelo de dados muda.
- **Events (Pub/Sub):** (Futuro) Integração com um barramento de eventos (como RabbitMQ ou Google Cloud Pub/Sub) para publicar eventos importantes (ex: `user_created`, `password_changed`) que outros serviços (como o `notification_service`) podem consumir.

**Fluxo de Autenticação Típico:**

1. O usuário insere suas credenciais na aplicação cliente (GUI).
2. O cliente envia uma requisição POST para o endpoint `/login` da API com o email e a senha.
3. O endpoint da API recebe a requisição e usa o schema `LoginRequest` do Pydantic para validar os dados.
4. O endpoint chama o `auth_service` para autenticar o usuário.
5. O `auth_service` busca o usuário no banco de dados pelo email e verifica se a senha fornecida corresponde à hash armazenada.
6. Se a autenticação for bem-sucedida, o serviço gera um token de acesso JWT (JSON Web Token).
7. O token JWT é retornado ao cliente em uma resposta JSON.
8. O cliente armazena o token de forma segura e o inclui no cabeçalho `Authorization` de todas as requisições subsequentes para endpoints protegidos.
9. Para uma requisição a um endpoint protegido (ex: `/users/me`), um middleware ou dependência do FastAPI verifica a validade do token JWT antes de permitir o acesso ao recurso.

### 6. Serviço de Notificações (notification_service)

- **Diretório:** `notification_service/`
- **Tecnologia Principal:** Python, Pika (para RabbitMQ), SMTP (para e-mail)

**Descrição:**

O `notification_service` é outro microsserviço de backend, projetado para lidar com todas as comunicações assíncronas com os usuários. Sua principal função é ouvir eventos de outros serviços (como o `user_service`) e agir com base neles, por exemplo, enviando um e-mail de boas-vindas quando um novo usuário se registra. Essa arquitetura orientada a eventos promove o baixo acoplamento entre os serviços, aumentando a resiliência e a escalabilidade do sistema como um todo.

**Componentes Chave:**

- **Barramento de Eventos (Event Bus):** O serviço se conecta a um barramento de eventos (como RabbitMQ) para consumir mensagens. Ele se inscreve em tópicos ou filas específicas (ex: `user.created`).
- **`event_handlers`:** Contém a lógica para processar diferentes tipos de eventos. Por exemplo, o `handle_user_created_event` será acionado quando uma mensagem do tipo `user.created` for recebida.
- **`services` (Email Service):** Contém a lógica para se comunicar com um serviço de e-mail externo via SMTP. Ele é responsável por formatar e enviar os e-mails, utilizando templates para o corpo da mensagem.
- **`templates`:** Armazena os templates de e-mail (ex: em HTML ou texto simples) que serão preenchidos com dados específicos do usuário antes do envio.
- **`main`:** O ponto de entrada do serviço, que inicializa a conexão com o barramento de eventos e inicia o processo de escuta de mensagens.

**Fluxo de Notificação Típico (Novo Usuário):**

1. Um novo usuário se registra através da API no `user_service`.
2. Após criar o usuário no banco de dados, o `user_service` publica um evento `user.created` no barramento de eventos. A mensagem do evento contém informações sobre o novo usuário, como nome e e-mail.
3. O `notification_service`, que está constantemente escutando a fila de eventos de usuário, recebe a mensagem `user.created`.
4. O `event_handler` apropriado é acionado para processar o evento.
5. O handler extrai os dados do usuário da mensagem do evento.
6. Ele então chama o `EmailService`, passando o e-mail do destinatário, o assunto e o template de e-mail de boas-vindas.
7. O `EmailService` se conecta ao servidor SMTP, renderiza o template com o nome do usuário e envia o e-mail.
8. O evento é reconhecido (`ack`) no barramento de eventos, marcando-o como processado com sucesso.

## Fluxos de Trabalho (Workflows)

Esta seção descreve a sequência de interações entre os diferentes módulos para realizar as principais funcionalidades do sistema.

### 1. Fluxo de Conversão de Vídeo Local

**Objetivo:** Converter um arquivo de vídeo de um formato para outro na máquina local do usuário.

1.  **Seleção (GUI):** O usuário abre a aba "Conversor de Vídeo", clica em "Adicionar Arquivos" e seleciona um ou mais vídeos. Os arquivos aparecem na lista.
2.  **Configuração (GUI):** O usuário escolhe o formato de saída (ex: MP4), a resolução (ex: 1080p) e o diretório de destino.
3.  **Início (GUI):** O usuário clica no botão "Converter". A GUI desabilita os controles para evitar modificações durante o processo e exibe uma barra de progresso.
4.  **Delegação (GUI -> `video_converter_module`):** A GUI cria uma nova thread e instancia a classe `VideoConverter` do módulo de conversão, passando a lista de arquivos, as opções de conversão e uma função de *callback* para atualizar o progresso.
5.  **Execução (FFmpeg):** O `video_converter_module` constrói o comando FFmpeg apropriado e o executa em um subprocesso.
6.  **Feedback de Progresso (`video_converter_module` -> GUI):** O módulo captura a saída do FFmpeg, calcula o progresso e invoca o *callback* fornecido pela GUI.
7.  **Atualização da UI (GUI):** A função de *callback* atualiza a barra de progresso na interface do usuário em tempo real.
8.  **Conclusão (`video_converter_module` -> GUI):** Ao término da conversão, o módulo notifica a GUI.
9.  **Resultado (GUI):** A GUI exibe uma mensagem de sucesso ou erro e reabilita os controles.

### 2. Fluxo de Download de Mídia do YouTube

**Objetivo:** Baixar um vídeo do YouTube e salvá-lo localmente.

1.  **Entrada (GUI):** O usuário abre a aba "Download de Mídia", cola a URL de um vídeo do YouTube no campo de texto e seleciona o formato (ex: "Melhor Vídeo").
2.  **Início (GUI):** O usuário clica em "Baixar". A GUI exibe uma barra de progresso.
3.  **Delegação (GUI -> `yt-dlp` wrapper):** A GUI inicia uma nova thread, chamando a função que encapsula a lógica do `yt-dlp`.
4.  **Configuração (`yt-dlp`):** A função de wrapper configura as opções do `yt-dlp`, incluindo o `progress_hook` para capturar o progresso do download.
5.  **Execução (`yt-dlp`):** A biblioteca `yt-dlp` é chamada para iniciar o download.
6.  **Feedback de Progresso (`yt-dlp` -> GUI):** O `progress_hook` é acionado pelo `yt-dlp`, e a função de hook atualiza a barra de progresso na GUI.
7.  **Pós-processamento (FFmpeg):** Se necessário, o `yt-dlp` utiliza o FFmpeg automaticamente para mesclar os arquivos de áudio e vídeo.
8.  **Conclusão (`yt-dlp` -> GUI):** Ao final do download, a função de wrapper notifica a GUI.
9.  **Resultado (GUI):** A GUI exibe uma mensagem de conclusão.

## Configuração e Deploy

Esta seção aborda os passos necessários para configurar o ambiente de desenvolvimento e para implantar os serviços de backend em um ambiente de produção.

### 1. Ambiente de Desenvolvimento

**Pré-requisitos:**

- Python 3.8+
- Git
- (Opcional, mas recomendado) Um ambiente virtual Python (venv ou Conda)

**Passos para Configuração:**

1.  **Clonar o Repositório:**
    ```bash
    git clone <URL_DO_REPOSITORIO>
    cd vidconv
    ```

2.  **Executar o Instalador:**
    O primeiro passo é rodar o instalador para garantir que todas as dependências (Python e externas como FFmpeg) estejam configuradas.
    ```bash
    python installer/main_installer.py
    ```

3.  **Configurar os Serviços de Backend:**
    - Navegue até o diretório de cada serviço (`user_service`, `notification_service`).
    - Crie um arquivo `.env` a partir do `.env.example` e preencha as variáveis de ambiente, como as credenciais do banco de dados e do servidor de e-mail.
    - Instale as dependências Python de cada serviço:
      ```bash
      pip install -r requirements.txt
      ```

4.  **Banco de Dados (user_service):**
    - Certifique-se de ter uma instância do MySQL ou MariaDB em execução.
    - Execute as migrações do Alembic para criar as tabelas no banco de dados:
      ```bash
      alembic upgrade head
      ```

5.  **Executar os Serviços:**
    - Inicie cada serviço de backend em um terminal separado:
      ```bash
      # No diretório user_service
      uvicorn main:app --reload

      # No diretório notification_service
      python main.py
      ```

6.  **Executar a Aplicação Principal:**
    - Com os serviços de backend em execução, inicie a aplicação desktop:
      ```bash
      python main_tkinter.py
      ```

### 2. Deploy em Produção (Visão Geral)

O deploy dos serviços de backend (`user_service`, `notification_service`) em um ambiente de produção deve ser feito utilizando contêineres Docker para garantir consistência e isolamento.

**Componentes da Infraestrutura:**

- **Servidor/VM:** Uma máquina virtual em um provedor de nuvem (AWS, Google Cloud, Azure) ou um servidor on-premise.
- **Docker & Docker Compose:** Para orquestrar os contêineres dos serviços e suas dependências (como o banco de dados).
- **Banco de Dados Gerenciado:** Recomenda-se o uso de um serviço de banco de dados gerenciado (como Amazon RDS ou Google Cloud SQL) para maior confiabilidade e escalabilidade.
- **Gateway de API:** Um serviço como Nginx, Traefik ou um gateway de API gerenciado (Amazon API Gateway) deve ser colocado na frente dos serviços para lidar com roteamento, SSL e rate limiting.
- **Barramento de Eventos Gerenciado:** Um serviço como RabbitMQ (em contêiner ou gerenciado) ou Google Cloud Pub/Sub para a comunicação entre os microsserviços.

**Passos Gerais para o Deploy:**

1.  **Dockerizar os Serviços:** Criar um `Dockerfile` para cada serviço (`user_service`, `notification_service`).
2.  **Criar um `docker-compose.yml`:** Definir os serviços, redes, volumes e variáveis de ambiente para orquestrar a subida de toda a stack (API, notificador, banco de dados, barramento de eventos).
3.  **Configurar o Gateway de API:** Configurar o Nginx (ou similar) para rotear o tráfego externo para o contêiner do `user_service`.
4.  **CI/CD:** Implementar um pipeline de Integração Contínua e Deploy Contínuo (usando ferramentas como GitHub Actions) para automatizar os testes, a construção das imagens Docker e o deploy em produção a cada novo commit na branch principal.

---

### Propósito

O **VidConv** é uma solução de software completa projetada para oferecer uma experiência de usuário robusta e eficiente para a conversão de vídeos, download de conteúdo de plataformas como o YouTube e gerenciamento de mídia. O sistema foi arquitetado de forma modular para garantir escalabilidade, manutenibilidade e a fácil integração de novas funcionalidades.

### Principais Funcionalidades

- **Conversão de Vídeo:** Suporte para múltiplos formatos (MP4, MKV, AVI, etc.) com controle sobre resolução, bitrate e codecs, utilizando a potência do FFmpeg.
- **Download de Mídia:** Funcionalidade integrada para baixar vídeos e áudios do YouTube, com seleção de qualidade e formato.
- **Interface Gráfica Intuitiva:** Uma aplicação de desktop desenvolvida em Tkinter que centraliza todas as funcionalidades de forma amigável.
- **Gerenciamento de Dependências:** Um instalador automatizado que verifica e instala todas as dependências necessárias, como FFmpeg e CUDA, de acordo com o hardware do usuário.
- **Arquitetura de Microsserviços:** Módulos desacoplados para gerenciamento de usuários e notificações, permitindo escalabilidade e resiliência.

### Pilha de Tecnologia Principal

- **Backend (Desktop e Módulos):** Python 3.11+
- **Interface Gráfica:** Tkinter
- **Manipulação de Vídeo:** FFmpeg
- **Download de Mídia:** yt-dlp
- **API de Usuários:** FastAPI, SQLAlchemy, Pydantic
- **Banco de Dados (Usuários):** MySQL / MariaDB
- **Comunicação entre Serviços:** HTTP/REST, Mensageria (planejado)
- **Containerização:** Docker (para serviços de backend)

---