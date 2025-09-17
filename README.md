# Sistema de Scraping e Migração de Conteúdo Senac

Sistema Python abrangente para extração de conteúdo do site Senac DF e migração para a plataforma Liferay DXP. Esta solução de nível empresarial oferece capacidades automatizadas de extração, processamento e migração de conteúdo com tratamento robusto de erros e recursos de processamento em lote.

## Funcionalidades

### Sistema de Web Scraping
- Extração de conteúdo multi-thread do site Senac DF
- Coleta de URLs com suporte a paginação
- Parâmetros de scraping configuráveis (workers, delays, tentativas)
- Processamento em lote com intervalos automáticos de salvamento
- Tratamento abrangente de erros e mecanismos de retry
- Logging detalhado e relatórios de estatísticas

### Sistema de Migração de Conteúdo
- Migração automatizada para plataforma Liferay DXP
- Capacidades de upload de documentos e imagens
- Criação de conteúdo estruturado com organização adequada de pastas
- Modos de desenvolvimento e produção
- Processamento em lote com delays configuráveis
- Estatísticas de migração e relatórios em tempo real
- Arquitetura empresarial profissional

## Requisitos do Sistema

- Python 3.7+
- Conexão ativa com a internet para web scraping
- Acesso à instância Liferay DXP para migração de conteúdo
- Pacotes Python necessários (veja seção Dependências)

## Instalação

1. Clone o repositório:
```bash
git clone <repository-url>
cd senac_scrap
```

2. Instale as dependências necessárias:
```bash
pip install -r requirements.txt
```
Nota: Se requirements.txt não existir, instale os seguintes pacotes:
```bash
pip install requests beautifulsoup4 cloudscraper python-dotenv asyncio aiohttp
```

3. Configure as variáveis de ambiente:
```bash
cp .env.example .env
```

4. Edite o arquivo `.env` com sua configuração (veja seção Configuração).

## Configuração

### Variáveis de Ambiente

Crie um arquivo `.env` baseado no `.env.example` e configure o seguinte:

#### Configuração do Liferay
```
LIFERAY_BASE_URL=https://sua-instancia-liferay.com
LIFERAY_SITE_ID=20117
LIFERAY_USERNAME=seu_usuario
LIFERAY_PASSWORD=sua_senha
LIFERAY_TIMEOUT=30
```

#### Configuração da Biblioteca de Documentos
```
LIFERAY_PARENT_FOLDER_ID=32365  # ID da pasta pai para upload de imagens
```

#### Configuração de Conteúdo Estruturado
```
STRUCTURED_CONTENT_STRUCTURE_ID=40374  # ID da estrutura "Notícia"
STRUCTURED_CONTENT_PARENT_FOLDER_ID=40384  # ID da pasta "Noticias"
```

#### Configuração de Processamento
```
BATCH_SIZE=3
BATCH_DELAY=2.0
NEWS_FILE=noticias_final.json
```

### Configuração do Scraping

Modifique os parâmetros de scraping em `scraper.py`:
```python
scraping_config = ScrapingConfig(
    max_workers=6,              # Número de workers concorrentes
    delay_between_requests=0.3, # Delay entre requisições (segundos)
    max_retries=3,              # Máximo de tentativas de retry
    timeout=20                  # Timeout de requisição (segundos)
)
```

## Uso

### Web Scraping

#### Scraping Básico
Execute o processo completo de scraping:
```bash
python3 scraper.py
```

Isso irá:
1. Ler URLs de `senac_urls.txt`
2. Fazer scraping do conteúdo usando processamento em lote
3. Salvar resultados em `noticias_final.json`
4. Gerar estatísticas detalhadas e logs

#### Scraping Personalizado
Para uso programático:
```python
from src.senac_scraper import SenacScraper
from src.config.scraping_config import ScrapingConfig

# Configurar scraper
config = ScrapingConfig(max_workers=4, delay_between_requests=0.5)
scraper = SenacScraper(config)

# Coletar URLs (opcional)
urls = scraper.collect_urls(start_page=1, end_page=10)

# Fazer scraping do conteúdo
results = scraper.scrape_batch(
    urls_file='senac_urls.txt',
    batch_size=20,
    save_interval=5,
    output_file='output.json'
)
```

### Migração de Conteúdo

#### Executar Sistema de Migração
```bash
python3 content_migration_system.py
```

O sistema de migração irá:
1. Ler conteúdo extraído de `noticias_final.json`
2. Fazer upload de imagens para a Biblioteca de Documentos do Liferay
3. Criar entradas de conteúdo estruturado
4. Organizar conteúdo nas pastas apropriadas
5. Fornecer estatísticas detalhadas de migração

#### Modo de Desenvolvimento
Para testes com itens limitados, habilite o modo de desenvolvimento na configuração:
```python
dev_mode = True
max_dev_items = 3
```

## Estrutura de Arquivos

```
senac_scrap/
├── scraper.py                          # Ponto de entrada principal do scraping
├── content_migration_system.py         # Ponto de entrada principal da migração
├── config_manager.py                   # Gerenciamento de configuração
├── senac_urls.txt                      # Arquivo de URLs de entrada
├── noticias_final.json                 # Saída do conteúdo extraído
├── .env                                # Configuração de ambiente
├── .env.example                        # Template de ambiente
├── src/
│   ├── senac_scraper.py               # Classe principal do scraper
│   ├── config/
│   │   └── scraping_config.py         # Configuração de scraping
│   ├── services/
│   │   ├── scraping_service.py        # Operações de web scraping
│   │   ├── url_collector_service.py   # Coleta de URLs
│   │   ├── liferay_client.py          # Cliente da API Liferay
│   │   ├── document_service.py        # Manipulação de documentos
│   │   ├── structured_content_service.py # Criação de conteúdo
│   │   ├── folder_service.py          # Gerenciamento de pastas
│   │   └── bulk_processor.py          # Processamento em lote
│   ├── core/
│   │   └── http_client.py             # Utilitários do cliente HTTP
│   ├── models/                        # Modelos de dados
│   └── utils/                         # Funções utilitárias
└── logs/                              # Logs da aplicação
```

## Arquivos de Entrada/Saída

### Arquivos de Entrada
- `senac_urls.txt` - Arquivo de texto contendo URLs para fazer scraping (uma por linha)
- `.env` - Arquivo de configuração de ambiente

### Arquivos de Saída
- `noticias_final.json` - Arquivo JSON contendo conteúdo extraído com estrutura:
```json
[
  {
    "title": "Título do Artigo",
    "content": "Conteúdo do artigo...",
    "date": "2024-01-01",
    "url": "url_fonte",
    "images": ["url_imagem1", "url_imagem2"]
  }
]
```
- `*.log` - Logs da aplicação para debug e monitoramento

## Logging

O sistema fornece logging abrangente:
- Saída no console para monitoramento em tempo real
- Logging baseado em arquivo para registros persistentes
- Níveis de log configuráveis
- Relatório detalhado de erros e estatísticas

Arquivos de log são criados automaticamente:
- `scraper.log` - Operações de web scraping
- `liferay_content_processor.log` - Operações de migração

## Tratamento de Erros

### Erros de Scraping
- Mecanismos automáticos de retry para requisições falhadas
- Tratamento gracioso de timeouts de rede
- Detecção e pulo de URLs inválidas
- Logging abrangente de erros

### Erros de Migração
- Validação de credenciais e conectividade do Liferay
- Tratamento de erros de upload de arquivo
- Recuperação de erros de criação de conteúdo estruturado
- Relatório detalhado de erros com contexto

## Considerações de Performance

### Performance do Scraping
- Workers concorrentes configuráveis (padrão: 6)
- Delays de requisição para respeitar recursos do servidor
- Processamento em lote para otimizar uso de memória
- Intervalos automáticos de salvamento para prevenir perda de dados

### Performance da Migração
- Tamanhos de lote configuráveis para processamento
- Delays entre operações para prevenir limitação de rate da API
- Operações assíncronas para melhor throughput
- Processamento eficiente em memória de grandes datasets

## Solução de Problemas

### Problemas Comuns

#### Problemas de Scraping
- **Timeouts de conexão**: Aumente valores de timeout na configuração
- **Rate limiting**: Aumente delays entre requisições
- **Arquivo de URLs faltando**: Garanta que `senac_urls.txt` existe e contém URLs válidas

#### Problemas de Migração
- **Erros de autenticação**: Verifique credenciais do Liferay no arquivo `.env`
- **Pasta não encontrada**: Verifique IDs de pasta na configuração de ambiente
- **Falhas de upload**: Verifique conectividade de rede e permissões de arquivo

### Modo Debug
Habilite logging detalhado modificando o nível de log:
```python
logging.basicConfig(level=logging.DEBUG)
```

## Contribuindo

1. Siga a arquitetura e padrões de código existentes
2. Mantenha tratamento abrangente de erros
3. Atualize documentação para novas funcionalidades
4. Teste componentes de scraping e migração
5. Garanta logging adequado para debugging
