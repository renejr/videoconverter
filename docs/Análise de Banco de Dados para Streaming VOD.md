

# **Análise Arquitetural de uma Estratégia de Persistência Poliglota para uma Plataforma de Vídeo sob Demanda**

## **Seção 1: O Imperativo Estratégico para a Persistência Poliglota em Streaming de Mídia**

### **Introdução: Além do Monólito**

A arquitetura de sistemas de software complexos, como plataformas de vídeo sob demanda (VOD), evoluiu para além da abordagem de banco de dados monolítico, onde uma única tecnologia de banco de dados é forçada a atender a todas as necessidades da aplicação. Essa abordagem de "tamanho único" é um antipadrão reconhecido para aplicações modernas, pois inevitavelmente leva a compromissos em desempenho, escalabilidade ou produtividade do desenvolvedor.1 Em resposta a esse desafio, emergiu a persistência poliglota como uma estratégia arquitetural deliberada. Este padrão defende o uso estratégico de múltiplas tecnologias de banco de dados dentro de um único ecossistema de aplicação, alinhando a tecnologia aos requisitos específicos de negócios e dados.1 O princípio fundamental é que diferentes componentes de uma aplicação possuem necessidades de dados fundamentalmente distintas, e a seleção da ferramenta certa para cada trabalho leva a um sistema geral mais robusto e eficiente.

A decisão de adotar uma arquitetura de dados híbrida, como a proposta de usar MySQL e MongoDB, transcende a mera escolha técnica. Ela reflete uma maturidade na estrutura organizacional e no processo de desenvolvimento, especialmente em um contexto de microsserviços. O padrão "um banco de dados por serviço" é um pilar da arquitetura de microsserviços, promovendo baixo acoplamento e implantação independente.1 Portanto, a adoção de uma arquitetura poliglota é implicitamente uma decisão de estruturar o backend em serviços distintos e com limites bem definidos — por exemplo, um "Serviço de Autenticação" utilizando MySQL e um "Serviço de Catálogo" utilizando MongoDB. Isso exige que a equipe de desenvolvimento pense em termos de contextos delimitados e APIs, em vez de uma camada de dados monolítica e compartilhada, influenciando diretamente a estrutura da equipe e o fluxo de trabalho de desenvolvimento.

### **O Desafio do VOD: Uma Confluência de Necessidades de Dados Disparatadas**

Uma plataforma de VOD representa um caso de uso exemplar para a persistência poliglota, pois suas operações diárias geram uma confluência de requisitos de dados radicalmente diferentes e muitas vezes conflitantes. Um sistema de banco de dados único teria dificuldade em otimizar para todas essas demandas simultaneamente. As principais necessidades incluem:

* **Integridade Transacional:** Para domínios críticos como gerenciamento de assinaturas de usuários, processamento de pagamentos e faturamento, a consistência dos dados é inegociável. O sistema deve garantir que as transações financeiras sejam atômicas, consistentes, isoladas e duráveis (ACID) para evitar corrupção de dados e perda de receita.3  
* **Flexibilidade de Esquema:** O catálogo de mídia é um ativo dinâmico e em constante evolução. Novos tipos de conteúdo, atributos de metadados (por exemplo, prêmios, classificações da crítica, suporte a 4K/HDR) e requisitos de licenciamento regional podem surgir com frequência. Um esquema rígido pode dificultar a inovação e a adaptação rápida. A capacidade de lidar com dados semiestruturados de forma eficiente é crucial.5  
* **Taxa de Transferência de Escrita e Escalabilidade Extremas:** A plataforma deve ser capaz de lidar com milhões de interações de usuários concorrentes, como atualizações de histórico de exibição, "curtidas", classificações e comentários. Cada ação do usuário gera um ponto de dados, criando um fluxo massivo de eventos que exigem alta taxa de transferência de escrita e escalabilidade horizontal.7  
* **Leituras de Baixa Latência:** Para proporcionar uma experiência de usuário fluida e responsiva, o sistema deve servir dados como catálogos de vídeos, perfis de usuário e histórico de exibição com latência mínima. A navegação, a pesquisa e a recuperação de informações devem ser quase instantâneas.7

### **Precedente da Indústria: Aprendendo com os Gigantes**

A validade da abordagem de persistência poliglota é confirmada pelas arquiteturas de grandes players do setor de streaming. A Netflix, por exemplo, é um caso bem documentado de adoção de modelos de dados híbridos para alcançar escala massiva e resiliência. Eles utilizam diferentes bancos de dados para diferentes propósitos, como o Apache Cassandra (um banco de dados NoSQL) para o histórico de visualização do usuário, que lida com cargas pesadas de leitura e escrita em várias regiões geográficas.7 Essa prática da indústria valida a direção proposta como um padrão estabelecido para a construção de serviços de streaming em larga escala, demonstrando que a segmentação de dados por carga de trabalho é uma estratégia comprovada para o sucesso.

### **A Troca Fundamental: Especialização vs. Complexidade**

Apesar de seus benefícios significativos, a persistência poliglota introduz uma troca fundamental: o poder da especialização em troca de uma maior complexidade operacional.1 Utilizar tecnologias "best-of-breed" para cada tarefa pode otimizar o desempenho e a escalabilidade, mas também acarreta desafios significativos. A manutenção da consistência dos dados entre sistemas diferentes torna-se uma responsabilidade da camada de aplicação, exigindo padrões como Sagas ou arquiteturas orientadas a eventos.1 A sobrecarga de monitoramento, backup e recuperação aumenta, pois cada sistema de banco de dados tem suas próprias ferramentas e procedimentos. Além disso, a equipe de desenvolvimento precisa possuir ou adquirir um conjunto diversificado de habilidades para gerenciar e otimizar múltiplas tecnologias de banco de dados.

A intenção explícita de usar este projeto como uma oportunidade de aprendizado para o MongoDB é um fator de risco que deve ser gerenciado ativamente. Introduzir uma tecnologia nova e desconhecida em um caminho crítico do projeto adiciona "desconhecidos desconhecidos" relacionados ao ajuste de desempenho, práticas operacionais e modos de falha. Essa curva de aprendizado amplifica a sobrecarga operacional inerente à persistência poliglota.1 Portanto, a análise deve equilibrar o objetivo de aprendizado com a necessidade de construir um sistema robusto e sustentável. É imperativo mitigar esse risco através de prototipagem completa, testes de carga rigorosos e investimento em monitoramento robusto e procedimentos de backup desde o início do projeto.

## **Seção 2: Desconstruindo o Cenário de Dados do VOD: Uma Abordagem Orientada por Domínio**

### **Metodologia: Alinhando Modelos de Dados com Domínios de Negócio**

Para particionar os dados da aplicação de forma lógica e defensável, adotaremos uma abordagem estruturada baseada nos princípios do Design Orientado por Domínio (Domain-Driven Design). Em vez de começar com a modelagem de tabelas e coleções, primeiro identificaremos os domínios de negócio lógicos. Essa metodologia fornece uma justificativa clara para nossas escolhas de banco de dados, garantindo que a tecnologia sirva à função de negócio, e não o contrário. Identificamos três domínios principais em uma plataforma de VOD.

### **Domínio A: Identidade e Transações (O Sistema de Registro)**

* **Entidades:** Users (Usuários), Credentials (Credenciais, como senhas com hash e tokens de autenticação), Subscriptions (Assinaturas), Plans (Planos), Payments (Pagamentos), Invoices (Faturas).  
* **Características:** Esses dados são altamente estruturados, de missão crítica e possuem baixa tolerância à inconsistência. Eles exigem garantias estritas de ACID (Atomicidade, Consistência, Isolamento, Durabilidade).3 Os relacionamentos são bem definidos e aplicados, como um User que possui uma Subscription, que por sua vez tem muitos Payments. Este domínio funciona como o sistema de registro autoritativo para todas as informações de contas e financeiras.  
* **Padrões de Acesso:** A carga de escrita é intensa durante o registro de novos usuários e alterações de assinatura, mas a carga de leitura é predominante para verificações de autenticação e autorização em quase todas as interações do usuário com a plataforma. A integridade transacional é o requisito mais importante.9

### **Domínio B: Catálogo de Conteúdo e Metadados (O Sistema de Descoberta)**

* **Entidades:** Videos (Filmes, Séries, Episódios), Genres (Gêneros), Actors (Atores), Directors (Diretores), Thumbnails (Miniaturas), Video URLs (ponteiros para o armazenamento de objetos), Encoding Profiles (Perfis de codificação).  
* **Características:** Os dados neste domínio são semiestruturados e hierárquicos. Um vídeo tem um título e uma descrição, mas também uma lista de membros do elenco (que são objetos em si), múltiplos gêneros e, potencialmente, metadados diferentes para regiões distintas.3 O esquema provavelmente evoluirá à medida que novos recursos (por exemplo, legendas, faixas de áudio, conteúdo bônus) forem adicionados.  
* **Padrões de Acesso:** Este domínio é extremamente pesado em leituras. Os usuários estão constantemente navegando, filtrando e pesquisando o catálogo. As escritas ocorrem quando novo conteúdo é adicionado ou atualizado, o que é significativamente menos frequente do que as leituras. A otimização para recuperação rápida de dados é a principal prioridade.

### **Domínio C: Engajamento e Interação do Usuário (O Sistema de Engajamento)**

* **Entidades:** Watch History (Histórico de exibição), Playback Progress (Progresso de reprodução, por exemplo, "usuário X está em 45:32 do vídeo Y"), Likes (Curtidas), Ratings (Avaliações), Comments (Comentários), Watchlists (Listas de interesse).  
* **Características:** Esses dados representam um fluxo contínuo de eventos. Cada ação do usuário gera um ponto de dados. O volume é massivo e cresce linearmente com a atividade do usuário. A estrutura de dados por evento é relativamente simples, mas precisa ser armazenada e recuperada com extrema eficiência e baixa latência.3  
* **Padrões de Acesso:** Este domínio é extremamente pesado em escritas. O sistema precisa lidar com milhões de escritas concorrentes em potencial durante os horários de pico. As leituras também são frequentes (por exemplo, para exibir o histórico de exibição ou para a funcionalidade "continue assistindo"). A capacidade de escalar horizontalmente para absorver picos de escrita é o requisito técnico mais crítico.

A separação desses três domínios revela que eles possuem vetores de escalabilidade fundamentalmente diferentes, o que constitui o argumento mais forte para uma arquitetura poliglota. O Domínio A (Identidade) escala com o *número total de usuários registrados*, que é grande, mas cresce de forma relativamente previsível. O Domínio B (Catálogo) escala com o *tamanho da biblioteca de conteúdo*, que também cresce, mas não de forma explosiva. O Domínio C (Engajamento), no entanto, escala com o *número de usuários ativos concorrentes multiplicado pela sua taxa de interação*. Este é o vetor de escalabilidade mais volátil e explosivo. Um único programa de sucesso pode aumentar o tráfego de escrita em uma ordem de magnitude da noite para o dia. Um banco de dados único teria que ser provisionado para lidar com a carga de pico do Domínio C, o que seria ineficiente e caro. Ao separar os domínios, podemos escolher um banco de dados para o Domínio C (como o MongoDB) que é projetado especificamente para escalabilidade horizontal de escrita (sharding), enquanto usamos um banco de dados mais tradicional e econômico para o Domínio A.

É crucial entender que esses domínios não são isolados. Uma "interação" no Domínio C conecta um "usuário" do Domínio A com um "vídeo" do Domínio B. Em um banco de dados relacional monolítico, isso seria gerenciado por chaves estrangeiras, garantindo a integridade referencial no nível do banco de dados.3 Na arquitetura poliglota proposta, um user\_id na coleção de interações do MongoDB fará referência a um usuário na tabela de usuários do MySQL. O banco de dados não pode impor esse vínculo entre sistemas. Isso significa que a camada de aplicação se torna responsável por manter essa integridade. Por exemplo, quando um usuário é excluído (um evento raro), um processo deve ser acionado para lidar com seus dados de interação no MongoDB, possivelmente através de um mecanismo orientado a eventos. Essa transferência de responsabilidade da integridade do banco de dados para a aplicação é uma troca direta feita para obter escalabilidade e flexibilidade.

## **Seção 3: Aprofundamento Tecnológico: MySQL vs. MongoDB**

### **MySQL: A Base para Transações e Identidade**

Para o Domínio A (Identidade e Transações), o MySQL é uma escolha excelente e comprovada. Suas forças estão perfeitamente alinhadas com os requisitos deste domínio.

* **Conformidade ACID e Integridade de Dados:** As garantias ACID (Atomicidade, Consistência, Isolamento, Durabilidade) não são negociáveis para o gerenciamento de contas de usuário e transações financeiras. O motor transacional maduro do MySQL, como o InnoDB, garante que uma operação complexa, como a inscrição em um plano e o processamento de um pagamento, seja concluída com sucesso em sua totalidade ou falhe completamente, prevenindo estados de dados inconsistentes e corrupção.3  
* **Esquema Estruturado e Poder Relacional:** O esquema rígido do MySQL é uma característica fundamental, não uma limitação, para este domínio. Ele impõe a qualidade e a consistência dos dados, garantindo que todas as entradas de usuário e pagamento sigam um formato predefinido. Isso permite consultas poderosas e consistentes usando SQL JOINs para vincular de forma eficiente tabelas de usuários, assinaturas e pagamentos, o que é essencial para relatórios de negócios e lógica de aplicação complexa.3  
* **Segurança e Autenticação:** O MySQL oferece modelos robustos de gerenciamento de usuários, autenticação e privilégios. Isso é crítico para proteger dados sensíveis do usuário, como informações pessoais e de pagamento. Ele fornece controle granular sobre quem pode acessar e modificar quais dados, uma base essencial para a segurança da plataforma.9

### **MongoDB: O Motor para Escala e Flexibilidade**

Para os Domínios B (Catálogo de Conteúdo) e C (Engajamento do Usuário), o MongoDB oferece vantagens distintas que o tornam uma escolha estratégica.

* **O Modelo de Documento para Metadados Ricos:** O modelo de documento do MongoDB, semelhante a JSON (BSON), é um ajuste natural para os dados semiestruturados do catálogo de conteúdo. É possível incorporar matrizes de atores, objetos aninhados para a equipe de produção e diferentes URLs para várias qualidades de codificação, tudo dentro de um único documento de vídeo. Essa desnormalização pode simplificar a lógica da aplicação e otimizar o desempenho, pois todas as informações necessárias para exibir uma página de detalhes do vídeo podem ser recuperadas em uma única operação de leitura.5 O estudo de caso da Mediastream, uma empresa de tecnologia de mídia, demonstra o uso bem-sucedido do MongoDB para gerenciar metadados de conteúdo e catálogos em escala.18  
* **Escalabilidade Horizontal para Dados de Engajamento:** Esta é a característica principal do MongoDB para o Domínio C. O MongoDB foi projetado desde o início para escalabilidade horizontal através do sharding. Isso permite que uma coleção massiva (como watch\_history) seja distribuída por múltiplos servidores. À medida que a carga de escrita aumenta, novos servidores (shards) podem ser adicionados ao cluster para distribuir a carga, permitindo que o sistema escale de forma quase linear para lidar com picos de tráfego massivos sem degradação de desempenho.5  
* **Experiência do Desenvolvedor e Curva de Aprendizagem:** O modelo de documento do MongoDB frequentemente se mapeia de forma mais direta aos objetos nas linguagens de programação (como dicionários em Python ou objetos em JavaScript), o que pode acelerar o desenvolvimento.16 Embora o MongoDB ofereça o GridFS para armazenar arquivos grandes, é crucial notar que ele não deve ser usado para os próprios arquivos de vídeo. O GridFS é adequado para armazenar metadados ou arquivos de tamanho moderado que excedem o limite de 16 MB do BSON, mas o armazenamento de objetos dedicado é a solução correta para os ativos de mídia.19

### **Alternativa Crítica: O Poder Unificado do PostgreSQL com JSONB**

Uma análise completa deve considerar uma alternativa poderosa que desafia a necessidade de uma arquitetura poliglota: o PostgreSQL.

* **Um Único Motor, Dois Paradigmas:** O PostgreSQL é um banco de dados relacional de classe mundial com total conformidade ACID, tornando-o um substituto perfeito para o MySQL no Domínio A. No entanto, sua capacidade mais notável neste contexto é o suporte nativo a dados não estruturados.  
* **Suporte Nativo a JSON:** O PostgreSQL oferece o tipo de dados JSONB, que armazena dados JSON em um formato binário otimizado. Isso permite que ele lide com os dados semiestruturados dos Domínios B e C com eficiência surpreendente.23 O JSONB não apenas armazena os documentos, mas também permite a indexação de seus conteúdos através de índices GIN (Generalized Inverted Index), o que possibilita consultas de alto desempenho dentro dos documentos JSON.23  
* **A Troca entre Simplicidade e Especialização Revisitada:** Esta alternativa força uma reavaliação da troca fundamental. A abordagem híbrida MySQL/MongoDB oferece potencialmente o mais alto desempenho no pico absoluto de escala para o Domínio C, devido à maturidade e simplicidade do sharding nativo do MongoDB. No entanto, a abordagem unificada com PostgreSQL simplifica drasticamente a arquitetura. Ela reduz a sobrecarga operacional, elimina os desafios de consistência de dados entre bancos de dados e permite consultas poderosas que podem unir dados relacionais (como usuários) com dados JSON (como histórico de exibição) em uma única transação atômica.5 Para muitos projetos que não antecipam a escala da Netflix no futuro imediato, a simplicidade operacional e a integridade de dados de uma solução unificada com PostgreSQL podem ser uma vantagem decisiva.

A escolha não é simplesmente entre "SQL vs. NoSQL", mas sim uma avaliação de três vias: "Relacional Maduro (MySQL) \+ Documento Maduro (MongoDB)" vs. "Relacional Híbrido Avançado (PostgreSQL)". O PostgreSQL moderno não é mais apenas um banco de dados relacional; é um banco de dados multi-modelo. Isso significa que não é mais necessário aceitar a complexidade operacional de uma arquitetura poliglota para obter flexibilidade de esquema. Além disso, a evolução do MongoDB para incluir transações ACID multi-documento (desde a versão 4.0) 5 reduz o risco de seu uso, mas não altera seu propósito fundamental. A principal razão para escolher o MongoDB neste caso de uso de VOD permanece sua escalabilidade horizontal nativa para cargas de trabalho de escrita intensiva, não sua capacidade transacional.

## **Seção 4: Um Plano para a Arquitetura Híbrida**

Esta seção apresenta um plano concreto para implementar a arquitetura híbrida proposta, com esquemas de exemplo e uma estratégia para manter a consistência entre os bancos de dados.

### **Esquema MySQL Proposto (Domínio A)**

A seguir, um Data Definition Language (DDL) SQL para as tabelas transacionais centrais no MySQL. Este esquema foca na integridade referencial e na normalização para garantir a consistência dos dados.

SQL

\-- Tabela para armazenar informações do usuário  
CREATE TABLE users (  
    id INT AUTO\_INCREMENT PRIMARY KEY,  
    username VARCHAR(50) UNIQUE NOT NULL,  
    email VARCHAR(100) UNIQUE NOT NULL,  
    password\_hash VARCHAR(255) NOT NULL,  
    created\_at TIMESTAMP DEFAULT CURRENT\_TIMESTAMP,  
    updated\_at TIMESTAMP DEFAULT CURRENT\_TIMESTAMP ON UPDATE CURRENT\_TIMESTAMP  
);

\-- Tabela para os diferentes planos de assinatura oferecidos  
CREATE TABLE subscription\_plans (  
    id INT AUTO\_INCREMENT PRIMARY KEY,  
    name VARCHAR(100) NOT NULL,  
    price DECIMAL(10, 2) NOT NULL,  
    billing\_cycle ENUM('monthly', 'yearly') NOT NULL,  
    is\_active BOOLEAN DEFAULT TRUE  
);

\-- Tabela para rastrear as assinaturas ativas dos usuários  
CREATE TABLE subscriptions (  
    id INT AUTO\_INCREMENT PRIMARY KEY,  
    user\_id INT NOT NULL,  
    plan\_id INT NOT NULL,  
    status ENUM('active', 'canceled', 'expired') NOT NULL,  
    start\_date TIMESTAMP NOT NULL,  
    end\_date TIMESTAMP,  
    created\_at TIMESTAMP DEFAULT CURRENT\_TIMESTAMP,  
    FOREIGN KEY (user\_id) REFERENCES users(id) ON DELETE CASCADE,  
    FOREIGN KEY (plan\_id) REFERENCES subscription\_plans(id)  
);

\-- Tabela para registrar todos os pagamentos  
CREATE TABLE payments (  
    id INT AUTO\_INCREMENT PRIMARY KEY,  
    subscription\_id INT NOT NULL,  
    amount DECIMAL(10, 2) NOT NULL,  
    payment\_date TIMESTAMP DEFAULT CURRENT\_TIMESTAMP,  
    transaction\_id VARCHAR(255) UNIQUE NOT NULL,  
    status ENUM('completed', 'failed', 'pending') NOT NULL,  
    FOREIGN KEY (subscription\_id) REFERENCES subscriptions(id)  
);

### **Modelos de Documento MongoDB Propostos (Domínios B e C)**

A seguir, exemplos de estruturas de documentos JSON para as coleções no MongoDB. Esses modelos aproveitam a flexibilidade do MongoDB para armazenar dados ricos e hierárquicos.

#### **Coleção videos (Domínio B: Catálogo de Conteúdo)**

Este documento desnormaliza os dados para otimizar as leituras do catálogo.

JSON

{  
  "\_id": ObjectId("60d5ec49a3e3a4a8a0e3b2a1"),  
  "title": "Inception",  
  "description": "A thief who steals corporate secrets through the use of dream-sharing technology is given the inverse task of planting an idea into the mind of a C.E.O.",  
  "release\_year": 2010,  
  "duration\_minutes": 148,  
  "genres":,  
  "cast":,  
  "crew": {  
    "director": "Christopher Nolan",  
    "writer": "Christopher Nolan"  
  },  
  "assets": {  
    "thumbnail\_url": "https://example.com/thumbnails/inception.jpg",  
    "video\_files": \[  
      { "quality": "1080p", "url": "s3://bucket/inception\_1080p.mp4" },  
      { "quality": "720p", "url": "s3://bucket/inception\_720p.mp4" }  
    \]  
  },  
  "ratings": {  
    "imdb": 8.8,  
    "rotten\_tomatoes": "87%"  
  },  
  "last\_updated": ISODate("2023-10-27T10:00:00Z")  
}

#### **Coleção user\_interactions (Domínio C: Engajamento do Usuário)**

Este documento é projetado para ser leve e otimizado para escritas rápidas. Índices em user\_id, video\_id e timestamp seriam cruciais.

JSON

{  
  "\_id": ObjectId("60d5ed8da3e3a4a8a0e3b2a2"),  
  "user\_id": "12345", // Referência ao ID do usuário no MySQL  
  "video\_id": ObjectId("60d5ec49a3e3a4a8a0e3b2a1"), // Referência ao vídeo  
  "event\_type": "PLAYBACK\_PROGRESS",  
  "value": {  
    "timestamp\_seconds": 2732 // Onde o usuário parou no vídeo  
  },  
  "timestamp": ISODate("2023-10-27T12:34:56Z")  
}

{  
  "\_id": ObjectId("60d5ee1fa3e3a4a8a0e3b2a3"),  
  "user\_id": "12345",  
  "video\_id": ObjectId("60d5ec49a3e3a4a8a0e3b2a1"),  
  "event\_type": "LIKE",  
  "timestamp": ISODate("2023-10-27T13:00:00Z")  
}

### **Mantendo a Consistência Entre Bancos de Dados**

Como não há chaves estrangeiras entre o MySQL e o MongoDB, a consistência deve ser gerenciada na camada de aplicação, preferencialmente de forma assíncrona para manter o baixo acoplamento. Uma abordagem orientada a eventos usando um message broker como Apache Kafka ou RabbitMQ é ideal. Por exemplo, quando um novo usuário se inscreve no MySQL, o serviço de identidade publica um evento UserCreated. Um serviço de backend, que ouve esses eventos, pode então consumir essa mensagem e realizar ações necessárias em outros sistemas, como criar um perfil de usuário inicial no MongoDB, se necessário.29 Isso garante a consistência eventual sem criar dependências rígidas entre os serviços.

### **Tabela: Mapeamento de Domínio de Dados para Banco de Dados**

A tabela a seguir resume a arquitetura de dados proposta, fornecendo uma visão clara de "o que vai para onde e por quê".

| Domínio | Entidades Chave | Características dos Dados | Banco de Dados Recomendado | Justificativa |
| :---- | :---- | :---- | :---- | :---- |
| **Identidade e Transações** | Usuários, Assinaturas, Pagamentos | Estruturado, Relacional, Alto Valor, Requer ACID | **MySQL** | Integridade transacional, consistência de dados e segurança inigualáveis para dados financeiros e de identidade. |
| **Catálogo de Conteúdo** | Vídeos, Gêneros, Atores | Semi-estruturado, Hierárquico, Pesado em Leitura | **MongoDB** | O modelo de documento flexível permite metadados ricos e em evolução. A desnormalização otimiza a navegação rápida no catálogo. |
| **Engajamento do Usuário** | Histórico de Exibição, Curtidas, Progresso | Eventos de Alto Volume, Extremamente Pesado em Escrita | **MongoDB** | A escalabilidade horizontal comprovada via sharding é essencial para lidar com o fluxo de dados de interação do usuário sem degradação de desempenho. |

### **Tabela: Comparação de Abordagens Arquiteturais**

Esta tabela compara as três principais opções discutidas, permitindo uma decisão final informada com base nas prioridades específicas do projeto.

| Critério | Abordagem 1: MySQL \+ MongoDB (Híbrida) | Abordagem 2: PostgreSQL com JSONB (Unificada) | Abordagem 3: Apenas MongoDB (Hipotética) |
| :---- | :---- | :---- | :---- |
| **Desempenho (Escritas)** | Excelente (especializado) | Bom (pode se tornar um gargalo em escala extrema) | Excelente |
| **Desempenho (Leituras)** | Excelente (especializado) | Muito Bom (indexação poderosa) | Muito Bom |
| **Consistência de Dados** | Complexa (nível de aplicação, consistência eventual) | Excelente (transações ACID nativas em todos os dados) | Bom (ACID dentro do MongoDB, mas a integridade relacional é mais difícil) |
| **Simplicidade Arquitetural** | Baixa | Alta | Média |
| **Sobrecarga Operacional** | Alta (dois sistemas para gerenciar) | Baixa (um sistema para gerenciar) | Média (um sistema, mas requer conhecimento profundo) |
| **Velocidade de Desenvolvimento** | Média (troca de contexto) | Alta (padrão único de acesso a dados) | Alta (se a equipe conhece bem o MongoDB) |
| **Ideal Para...** | Plataformas de grande escala que priorizam o desempenho "best-of-breed" e estão dispostas a gerenciar a complexidade operacional. | Projetos que priorizam simplicidade, integridade de dados e desenvolvimento rápido, mas ainda precisam de bom desempenho e flexibilidade. | Projetos onde a grande maioria dos dados é orientada a documentos e a equipe possui profundo conhecimento em MongoDB. |

## **Seção 5: Integrando a Camada de Dados no Ecossistema VOD**

A escolha do banco de dados é central, mas é apenas uma parte de um ecossistema de dados maior, necessário para oferecer uma experiência de streaming de alta qualidade. A arquitetura do banco de dados atua como o "cérebro" do sistema, mas a percepção de velocidade e confiabilidade do usuário final é ditada pelo desempenho de todo o ecossistema.

### **A Regra de Ouro: Banco de Dados NÃO é para Arquivos**

É imperativo começar com uma regra fundamental: os arquivos de vídeo (MP4, WebM, etc.) NUNCA devem ser armazenados em um banco de dados, seja ele SQL ou NoSQL. O armazenamento e a entrega de grandes arquivos binários a partir de um banco de dados são extremamente ineficientes e não escalam. O local correto para esses ativos é um sistema de **Armazenamento de Objetos** distribuído, como Amazon S3, Google Cloud Storage ou uma solução auto-hospedada como o MinIO.7 A função do banco de dados é armazenar os *metadados* sobre o vídeo e um *ponteiro* (uma URL) para a localização do arquivo no armazenamento de objetos.

### **Acelerando a Entrega: CDN e Cache**

* **Rede de Distribuição de Conteúdo (CDN):** O uso de uma CDN (como Cloudflare, Amazon CloudFront ou Akamai) é inegociável para um serviço de streaming. Uma CDN armazena em cache cópias dos arquivos de vídeo em servidores de borda localizados geograficamente em todo o mundo. Quando um usuário solicita a reprodução de um vídeo, o conteúdo é entregue a partir do servidor de borda mais próximo dele, o que reduz drasticamente a latência e o tempo de buffer. Isso não apenas melhora a experiência do usuário, mas também descarrega a maior parte do tráfego de largura de banda dos servidores de origem, reduzindo custos e a carga na infraestrutura principal.7  
* **Camada de Cache (Redis/Memcached):** Para reduzir a carga nos bancos de dados primários e acelerar as respostas da API, uma camada de cache na memória, como Redis ou Memcached, é essencial. Dados frequentemente acessados, como informações de sessão do usuário, metadados de vídeos populares, ou os resultados de consultas comuns à API (por exemplo, a página inicial), podem ser armazenados no cache. Como o acesso à RAM é ordens de magnitude mais rápido do que o acesso ao disco, isso melhora significativamente a responsividade da interface do usuário.7

A percepção de "velocidade" de um usuário em uma plataforma de VOD é impulsionada principalmente por dois fatores: a rapidez com que a interface do usuário carrega (tempo de resposta da API) e a rapidez com que o vídeo começa a ser reproduzido sem interrupções (tempo de entrega do vídeo). A escolha do banco de dados afeta principalmente o primeiro fator. O segundo, e indiscutivelmente mais crítico, depende quase inteiramente do desempenho do armazenamento de objetos e da CDN.7 Um banco de dados lento pode fazer o site parecer lento, mas uma CDN mal configurada tornará o produto principal (assistir a vídeos) inutilizável.

### **Melhorando a Descoberta: A Necessidade de um Índice de Busca Dedicado**

Embora os bancos de dados modernos tenham capacidades de busca de texto, eles não são otimizados para a experiência de busca rica e interativa que os usuários esperam de um serviço de streaming. Funcionalidades como autocompletar, tolerância a erros de digitação, busca facetada (filtrar por gênero, ano, etc.) e classificação de resultados por relevância são complexas de implementar e lentas em bancos de dados de propósito geral.

Para isso, é altamente recomendável integrar um motor de busca dedicado, como **Elasticsearch** ou **Apache Solr**. Os metadados de vídeo da coleção do MongoDB seriam indexados no Elasticsearch. Quando um usuário realiza uma busca na aplicação, a consulta é enviada ao Elasticsearch, que é otimizado para esse tipo de consulta de texto e retorna os resultados relevantes com baixa latência.7 O front-end então usa os IDs dos vídeos retornados para buscar os metadados completos do MongoDB para exibição.

## **Seção 6: Preparando para o Futuro: Escalando para Capacidades Avançadas**

A arquitetura inicial proposta com MySQL e MongoDB é excelente para as funcionalidades principais de um serviço de VOD. No entanto, à medida que a plataforma amadurece, novos recursos exigirão tecnologias de dados ainda mais especializadas. Planejar essa evolução desde o início é uma marca de uma arquitetura robusta.

### **A Próxima Fronteira: Construindo um Motor de Recomendações**

Motores de recomendação sofisticados ("usuários que assistiram a X também assistiram a Y", "recomendações personalizadas para você") são um diferencial competitivo chave. Tentar construir isso com consultas complexas em um banco de dados relacional ou de documentos é ineficiente e não escala bem.

A ferramenta ideal para essa tarefa é um **Banco de Dados de Grafos** (por exemplo, Neo4j, Memgraph, NebulaGraph). Em um modelo de grafo, entidades como usuários, vídeos, gêneros e atores são representadas como *nós*, e suas interações (ASSISTIU, CURTIU, ATUOU\_EM) são representadas como *arestas* direcionadas e com propriedades. Essa estrutura de dados torna trivial a execução de consultas de travessia complexas para encontrar padrões e fazer recomendações em tempo real, consultas que seriam proibitivamente lentas e complexas em SQL ou MQL.33 Os dados dos bancos de dados MySQL e MongoDB seriam ingeridos no banco de dados de grafos para construir e atualizar continuamente o modelo de recomendação.

### **Obtendo Insights em Tempo Real: Análise e Monitoramento**

Para monitorar a saúde da plataforma, detectar fraudes, entender tendências de visualização em tempo real e otimizar a qualidade do serviço (QoS), é necessário coletar e analisar um grande volume de dados de eventos com carimbo de data/hora.

Para essa finalidade, **Bancos de Dados de Séries Temporais** (por exemplo, Amazon Timestream, InfluxDB) são a solução ideal. Eles são otimizados para a ingestão de alta velocidade e a consulta eficiente de dados indexados por tempo, como eventos de início/parada de reprodução, eventos de buffer, latências de API ou métricas de uso da CPU do servidor.39 Alternativamente, uma **Plataforma de Streaming de Dados** como o Apache Kafka pode ser usada para processar esses eventos em tempo real. Os eventos podem ser consumidos por múltiplos sistemas simultaneamente: armazenados no MongoDB para o histórico do usuário, enviados para um data warehouse para análise de negócios e processados por um banco de dados de séries temporais para monitoramento operacional.29

A arquitetura poliglota inicial evolui naturalmente para um tecido de dados mais complexo e multi-sistema à medida que a plataforma amadurece. Isso revela uma tendência importante: plataformas bem-sucedidas continuam a adotar armazenamentos de dados especializados para problemas especializados. A implicação é que a arquitetura de backend deve ser construída em torno de um modelo orientado a eventos e centrado em um barramento de mensagens (como o Kafka) desde o início. Isso facilita a "conexão" de novos sistemas de dados. Por exemplo, os mesmos eventos de interação do usuário que são escritos no MongoDB podem ser transmitidos do Kafka para um banco de dados de grafos para recomendações e para um banco de dados de séries temporais para análises, sem modificar a lógica principal da aplicação. Projetar essa "espinha dorsal de dados" desde o início é uma estratégia crítica para preparar a arquitetura para o futuro.

## **Seção 7: Conclusão e Recomendações Estratégicas**

### **Veredito Final sobre a Abordagem Híbrida**

A análise detalhada confirma que a arquitetura híbrida proposta, utilizando MySQL para dados transacionais e MongoDB para metadados de conteúdo e dados de engajamento, não é apenas viável, mas é uma abordagem sólida e alinhada com os padrões da indústria para a construção de uma plataforma de VOD escalável. A estratégia separa corretamente as preocupações com base nas características dos dados, utilizando cada tecnologia onde seus pontos fortes são mais proeminentes. Ela reconhece que diferentes partes do sistema têm diferentes requisitos de consistência, flexibilidade e escala.

### **O Dilema do PostgreSQL: Um Forte Concorrente**

Apesar da validade da abordagem híbrida, a alternativa de uma arquitetura unificada usando PostgreSQL com seu tipo de dados JSONB deve ser seriamente considerada. Esta abordagem oferece uma simplicidade arquitetural e operacional significativamente maior, eliminando a complexidade de gerenciar a consistência de dados entre dois sistemas distintos. Para projetos que não antecipam a escala massiva de um serviço global como a Netflix no futuro imediato, os benefícios da simplicidade, da integridade de dados unificada e da capacidade de realizar consultas complexas que unem dados relacionais e de documentos podem superar os ganhos de desempenho de uma solução especializada. A escolha final dependerá de um balanço entre a necessidade de desempenho em escala extrema e a preferência por simplicidade operacional e velocidade de desenvolvimento.

### **Princípios Chave para o Sucesso**

Para garantir o sucesso na implementação da arquitetura de dados da plataforma de VOD, as seguintes recomendações estratégicas devem ser seguidas:

1. **Adote a Persistência Poliglota:** A ideia central de usar a ferramenta certa para cada trabalho é validada. A separação de dados transacionais, de catálogo e de engajamento é uma base sólida.  
2. **Modele por Domínio:** Particione os dados com base na função de negócio (Identidade, Catálogo, Engajamento). Isso fornecerá uma justificativa clara para as escolhas tecnológicas e promoverá uma arquitetura de backend mais limpa.  
3. **Use Armazenamento de Objetos para Mídia:** Esta é uma regra inegociável. Arquivos de vídeo devem residir em um sistema como o S3, com o banco de dados armazenando apenas os metadados e ponteiros.  
4. **Priorize o Ecossistema de Dados:** Invista desde o primeiro dia em uma Rede de Distribuição de Conteúdo (CDN), uma camada de cache (Redis) e um motor de busca dedicado (Elasticsearch). O desempenho percebido pelo usuário depende de todo o ecossistema.  
5. **Projete para Consistência Eventual:** Planeje a manutenção da integridade dos dados entre os bancos de dados no nível da aplicação, preferencialmente usando uma arquitetura assíncrona e orientada a eventos.  
6. **Prototipe e Teste a Carga:** Dada a curva de aprendizado com o MongoDB e a complexidade da interação entre sistemas, valide as suposições de desempenho com protótipos realistas e testes de carga rigorosos antes de se comprometer com a produção.  
7. **Planeje a Especialização Futura:** Projete o backend de uma maneira que facilite a integração de futuros sistemas de dados, como Bancos de Dados de Grafos para recomendações e Bancos de Dados de Séries Temporais para análises. A adoção de um barramento de eventos central é a melhor estratégia para isso.

#### **Referências citadas**

1. Polyglot Persistence: A Strategic Approach to Modern Data ..., acessado em outubro 19, 2025, [https://medium.com/@rachoork/polyglot-persistence-a-strategic-approach-to-modern-data-architecture-e2a4f957f50b](https://medium.com/@rachoork/polyglot-persistence-a-strategic-approach-to-modern-data-architecture-e2a4f957f50b)  
2. Achieving Polyglot Persistence through Data Integration in the Cloud \- EDB, acessado em outubro 19, 2025, [https://www.enterprisedb.com/blog/achieving-polyglot-persistence-through-data-integration-cloud](https://www.enterprisedb.com/blog/achieving-polyglot-persistence-through-data-integration-cloud)  
3. How to Design a Database for Video Streaming Service ..., acessado em outubro 19, 2025, [https://www.geeksforgeeks.org/sql/how-to-design-a-database-for-video-streaming-service/](https://www.geeksforgeeks.org/sql/how-to-design-a-database-for-video-streaming-service/)  
4. mysql: For billing purpose, printing user ID on bill . \- Stack Overflow, acessado em outubro 19, 2025, [https://stackoverflow.com/questions/8725749/mysql-for-billing-purpose-printing-user-id-on-bill](https://stackoverflow.com/questions/8725749/mysql-for-billing-purpose-printing-user-id-on-bill)  
5. PostgreSQL vs. MongoDB: Differences, Strengths, and Use Cases ..., acessado em outubro 19, 2025, [https://estuary.dev/blog/postgresql-vs-mongodb/](https://estuary.dev/blog/postgresql-vs-mongodb/)  
6. MongoDB vs PostgreSQL: A Detailed Comparison Guide \- EDB, acessado em outubro 19, 2025, [https://www.enterprisedb.com/choosing-mongodb-postgresql-cloud-database-solutions-guide](https://www.enterprisedb.com/choosing-mongodb-postgresql-cloud-database-solutions-guide)  
7. Designing a Netflix-Like Streaming Service for System Design ..., acessado em outubro 19, 2025, [https://www.designgurus.io/answers/detail/designing-netflixlike-streaming-service](https://www.designgurus.io/answers/detail/designing-netflixlike-streaming-service)  
8. NoSQL Polyglot Persistence: Tools and Integrations with Neo4j, acessado em outubro 19, 2025, [https://neo4j.com/blog/cypher-and-gql/nosql-polyglot-persistence-tools-integrations/](https://neo4j.com/blog/cypher-and-gql/nosql-polyglot-persistence-tools-integrations/)  
9. How to manage users and authentication in MySQL \- Prisma, acessado em outubro 19, 2025, [https://www.prisma.io/dataguide/mysql/authentication-and-authorization/user-management-and-authentication](https://www.prisma.io/dataguide/mysql/authentication-and-authorization/user-management-and-authentication)  
10. Satori Guide: MySQL Authentication, acessado em outubro 19, 2025, [https://satoricyber.com/mysql-security/satori-guide-mysql-authentication/](https://satoricyber.com/mysql-security/satori-guide-mysql-authentication/)  
11. Video streaming app data model \- Eraser, acessado em outubro 19, 2025, [https://www.eraser.io/examples/video-streaming-app-data-model](https://www.eraser.io/examples/video-streaming-app-data-model)  
12. Difference between PostgreSQL and MongoDB \- GeeksforGeeks, acessado em outubro 19, 2025, [https://www.geeksforgeeks.org/postgresql/difference-between-postgresql-and-mongodb/](https://www.geeksforgeeks.org/postgresql/difference-between-postgresql-and-mongodb/)  
13. MySQL add user: how to create and grant privileges \- Hostinger, acessado em outubro 19, 2025, [https://www.hostinger.com/tutorials/how-create-mysql-user-and-grant-permissions](https://www.hostinger.com/tutorials/how-create-mysql-user-and-grant-permissions)  
14. MySQL Enterprise Authentication, acessado em outubro 19, 2025, [https://www.mysql.com/products/enterprise/security.html](https://www.mysql.com/products/enterprise/security.html)  
15. MySQL Secure Deployment Guide :: 11 Enabling Authentication, acessado em outubro 19, 2025, [https://dev.mysql.com/doc/mysql-secure-deployment-guide/5.7/en/secure-deployment-configure-authentication.html](https://dev.mysql.com/doc/mysql-secure-deployment-guide/5.7/en/secure-deployment-configure-authentication.html)  
16. Postgres vs. MongoDB: a Complete Comparison in 2025 \- Bytebase, acessado em outubro 19, 2025, [https://www.bytebase.com/blog/postgres-vs-mongodb/](https://www.bytebase.com/blog/postgres-vs-mongodb/)  
17. PostgreSQL vs MongoDB: Choosing the Right Database for Your Data Projects \- DataCamp, acessado em outubro 19, 2025, [https://www.datacamp.com/blog/postgresql-vs-mongodb](https://www.datacamp.com/blog/postgresql-vs-mongodb)  
18. Mediastream Broadcasting For Consumers Across Latin America ..., acessado em outubro 19, 2025, [https://www.mongodb.com/solutions/customer-case-studies/mediastream](https://www.mongodb.com/solutions/customer-case-studies/mediastream)  
19. Store Large Files with GridFS \- Node.js Driver \- MongoDB Docs, acessado em outubro 19, 2025, [https://www.mongodb.com/docs/drivers/node/current/crud/gridfs/](https://www.mongodb.com/docs/drivers/node/current/crud/gridfs/)  
20. Is storing videos in mongodb gridFS a good idea? \- Google Groups, acessado em outubro 19, 2025, [https://groups.google.com/g/mongodb-user/c/T\_cCqXOcals](https://groups.google.com/g/mongodb-user/c/T_cCqXOcals)  
21. How to use MongoDB or other document database to keep video files, with options of adding to existing binary files and parallel read/write \- Stack Overflow, acessado em outubro 19, 2025, [https://stackoverflow.com/questions/13012444/how-to-use-mongodb-or-other-document-database-to-keep-video-files-with-options](https://stackoverflow.com/questions/13012444/how-to-use-mongodb-or-other-document-database-to-keep-video-files-with-options)  
22. GridFS for Self-Managed Deployments \- Database Manual \- MongoDB Docs, acessado em outubro 19, 2025, [https://www.mongodb.com/docs/manual/core/gridfs/](https://www.mongodb.com/docs/manual/core/gridfs/)  
23. JSONB PostgreSQL: How To Store & Index JSON Data \- ScaleGrid, acessado em outubro 19, 2025, [https://scalegrid.io/blog/using-jsonb-in-postgresql-how-to-effectively-store-index-json-data-in-postgresql/](https://scalegrid.io/blog/using-jsonb-in-postgresql-how-to-effectively-store-index-json-data-in-postgresql/)  
24. How to Query JSON Metadata in PostgreSQL | TigerData, acessado em outubro 19, 2025, [https://www.tigerdata.com/learn/how-to-query-json-metadata-in-postgresql](https://www.tigerdata.com/learn/how-to-query-json-metadata-in-postgresql)  
25. How to store and query JSON data in Postgres \- YouTube, acessado em outubro 19, 2025, [https://www.youtube.com/watch?v=nxeUiRz4G-M\&vl=en](https://www.youtube.com/watch?v=nxeUiRz4G-M&vl=en)  
26. Performance of JSON vs metadata table \- Stack Overflow, acessado em outubro 19, 2025, [https://stackoverflow.com/questions/36894395/performance-of-json-vs-metadata-table](https://stackoverflow.com/questions/36894395/performance-of-json-vs-metadata-table)  
27. Using Apache Superset to Visualize PostgreSQL® JSON Data (Pipeline Series Part 7), acessado em outubro 19, 2025, [https://www.instaclustr.com/blog/apache-superset-pipeline-series-part-7/](https://www.instaclustr.com/blog/apache-superset-pipeline-series-part-7/)  
28. Postgres vs mongoDb \- better choice for backend : r/dataengineering \- Reddit, acessado em outubro 19, 2025, [https://www.reddit.com/r/dataengineering/comments/1mnyo1z/postgres\_vs\_mongodb\_better\_choice\_for\_backend/](https://www.reddit.com/r/dataengineering/comments/1mnyo1z/postgres_vs_mongodb_better_choice_for_backend/)  
29. What is a Streaming Database? Definition & Best Practices \- Qlik, acessado em outubro 19, 2025, [https://www.qlik.com/us/streaming-data/database-streaming](https://www.qlik.com/us/streaming-data/database-streaming)  
30. Data Streaming Architecture: Components, Process, & Diagrams \- Estuary, acessado em outubro 19, 2025, [https://estuary.dev/blog/data-streaming-architecture/](https://estuary.dev/blog/data-streaming-architecture/)  
31. The Rise of Streaming Data: The Right Architecture to Transform Analytics, Disaster Recovery, and IoT \- Yugabyte, acessado em outubro 19, 2025, [https://www.yugabyte.com/blog/streaming-data-architecture/](https://www.yugabyte.com/blog/streaming-data-architecture/)  
32. Polyglot Persistence: NoSQL & RDBMS | Design and Execute, acessado em outubro 19, 2025, [https://www.designandexecute.com/designs/polyglot-persistence-nosql-rdbms/](https://www.designandexecute.com/designs/polyglot-persistence-nosql-rdbms/)  
33. Recommendation Engine \- Memgraph, acessado em outubro 19, 2025, [https://memgraph.com/recommendation-engine](https://memgraph.com/recommendation-engine)  
34. Neo4j Graph Database & Analytics | Graph Database Management System, acessado em outubro 19, 2025, [https://neo4j.com/](https://neo4j.com/)  
35. Recommendation Engine & System Use Cases with Graph Databases \- Neo4j, acessado em outubro 19, 2025, [https://neo4j.com/use-cases/real-time-recommendation-engine/](https://neo4j.com/use-cases/real-time-recommendation-engine/)  
36. Graph Database For Recommendation Systems \- NebulaGraph, acessado em outubro 19, 2025, [https://www.nebula-graph.io/posts/use-cases-of-graph-databases-in-real-time-recommendation](https://www.nebula-graph.io/posts/use-cases-of-graph-databases-in-real-time-recommendation)  
37. How Web Scraping and Graph Databases Can Power Recommendation Engines \- Zyte, acessado em outubro 19, 2025, [https://www.zyte.com/blog/web-scraping-graphdb-recommend-engines/](https://www.zyte.com/blog/web-scraping-graphdb-recommend-engines/)  
38. Why Are SQL Databases Outdated for the Real-Time Recommendation Engines, acessado em outubro 19, 2025, [https://memgraph.com/blog/faster-recommendations-with-graph-databases](https://memgraph.com/blog/faster-recommendations-with-graph-databases)  
39. Time-Series Databases vs. Streaming Databases: Key Differences & Use Cases, acessado em outubro 19, 2025, [https://www.risingwave.com/blog/streaming-vs-time-series-database-comparison/](https://www.risingwave.com/blog/streaming-vs-time-series-database-comparison/)  
40. Time-Series Database – Amazon Timestream \- AWS, acessado em outubro 19, 2025, [https://aws.amazon.com/timestream/](https://aws.amazon.com/timestream/)  
41. Streaming Database: An Overview with Use Cases \- Hazelcast, acessado em outubro 19, 2025, [https://hazelcast.com/foundations/data-and-middleware-technologies/streaming-database/](https://hazelcast.com/foundations/data-and-middleware-technologies/streaming-database/)