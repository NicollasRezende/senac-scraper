# Sistema de Migração de Conteúdo Senac

Solução de web scraping e migração de conteúdo de nível empresarial para o portal Senac-DF. Este sistema fornece extração automatizada de conteúdo do site do Senac-DF e migração contínua para Liferay DXP com gerenciamento de documentos e criação de conteúdo estruturado.

## Funcionalidades

- **Web Scraping**: Extração automatizada de conteúdo do site do Senac-DF
- **Migração de Conteúdo**: Migração profissional para Liferay DXP
- **Gerenciamento de Documentos**: Criação automatizada de pastas e upload de arquivos
- **Conteúdo Estruturado**: Criação automatizada de conteúdo estruturado com mapeamento adequado de campos
- **Processamento em Lotes**: Processamento configurável em lotes com tratamento de erros
- **Arquitetura Profissional**: Estrutura de código de nível empresarial com logging abrangente

## Componentes do Sistema

### 1. Sistema de Web Scraping
- Extração de artigos de notícias do portal Senac-DF
- Processamento em lotes com limitação de taxa
- Tratamento abrangente de erros e lógica de retry

### 2. Sistema de Migração de Conteúdo
- Migração automatizada para Liferay DXP
- Criação e gerenciamento de pastas de documentos
- Criação de conteúdo estruturado com referências de imagem
- Logging profissional e estatísticas

## Estrutura do Projeto

```
senac_scrap/
├── scraper.py                          # Ponto de entrada do web scraping
├── content_migration_system.py         # Sistema de migração Liferay (principal)
├── config_manager.py                   # Gerenciamento de configuração
├── noticias_final.json                 # Dados de conteúdo extraídos
├── .env                                # Configuração de ambiente
├── .env.example                        # Template de configuração
└── src/
    ├── config/
    │   ├── scraping_config.py          # Configuração de scraping
    │   └── liferay_config.py           # Configuração do Liferay
    ├── core/
    │   ├── content_extractor.py        # Lógica de extração de conteúdo
    │   └── http_client.py              # Utilitários de cliente HTTP
    ├── models/
    │   └── news_article.py             # Modelos de dados
    ├── services/
    │   ├── scraping_service.py         # Serviços de scraping
    │   ├── liferay_client.py           # Cliente API Liferay
    │   ├── document_service.py         # Gerenciamento de documentos
    │   ├── folder_service.py           # Gerenciamento de pastas
    │   ├── structured_content_service.py    # Criação de conteúdo
    │   └── structured_content_folder_service.py  # Gerenciamento de pastas de conteúdo
    └── utils/
        ├── file_handler.py             # Utilitários de arquivo
        ├── rate_limiter.py             # Limitação de taxa
        └── statistics.py               # Rastreamento de estatísticas
```

## Início Rápido

### Pré-requisitos

1. Python 3.8+
2. Dependências necessárias (instalar via requirements.txt se disponível)
3. Instância Liferay DXP (para migração)
4. Configuração de ambiente

### Configuração de Ambiente

Copie `.env.example` para `.env` e configure:

```bash
cp .env.example .env
```

Edite `.env` com sua configuração:

```bash
# Configuração Liferay
LIFERAY_BASE_URL=http://localhost:8080
LIFERAY_SITE_ID=20117
LIFERAY_USERNAME=seu-usuario
LIFERAY_PASSWORD=sua-senha

# Configuração da Biblioteca de Documentos
LIFERAY_PARENT_FOLDER_ID=32365

# Configuração de Conteúdo Estruturado
STRUCTURED_CONTENT_STRUCTURE_ID=40374
STRUCTURED_CONTENT_PARENT_FOLDER_ID=40384

# Configuração de Processamento
BATCH_SIZE=1
BATCH_DELAY=2.0
DEV_MODE=True  # Definir como False para produção
MAX_DEV_ITEMS=3
```

## Uso

### 1. Web Scraping

Extrair conteúdo do site do Senac-DF:

```bash
# Executar o web scraper
python3 scraper.py
```

Isso irá:
- Ler URLs do `senac_urls.txt`
- Extrair conteúdo de cada URL
- Salvar resultados em `noticias_final.json`
- Gerar estatísticas de scraping e logs

### 2. Migração de Conteúdo

Migrar conteúdo extraído para o Liferay:

```bash
# Executar o sistema de migração
python3 content_migration_system.py
```

Isso irá:
- Criar pastas de documentos para cada item de notícia
- Fazer upload de imagens em destaque e imagens de conteúdo
- Criar pastas de conteúdo estruturado dentro da pasta pai "Noticias"
- Criar conteúdo estruturado com mapeamento adequado de campos (`img` e `content`)
- Gerar estatísticas abrangentes de migração

### 3. Modo de Desenvolvimento vs Produção

**Modo de Desenvolvimento** (padrão):
- Processa apenas 3 itens para teste
- Logging detalhado de debug
- Definir `DEV_MODE=True` no `.env`

**Modo de Produção**:
- Processa todos os itens do conjunto de dados
- Nível padrão de logging
- Definir `DEV_MODE=False` no `.env`

## Configuração Avançada

### Configuração de Scraping

```python
from src.config.scraping_config import ScrapingConfig
from src.senac_scraper import SenacScraper

config = ScrapingConfig(
    max_workers=6,                    # Workers concorrentes
    delay_between_requests=0.3,       # Limitação de taxa
    max_retries=3,                    # Tentativas de retry
    timeout=20                        # Timeout de requisição
)

scraper = SenacScraper(scraping_config=config)
```

### Configuração de Migração

A configuração é gerenciada através de variáveis de ambiente e do sistema `config_manager.py`:

```python
from config_manager import ConfigurationManager

# Carregar configuração de desenvolvimento
config = ConfigurationManager.get_development_config()

# Carregar configuração de produção
config = ConfigurationManager.get_production_config()
```

## Estrutura de Conteúdo

### Formato de Dados Extraídos
```json
{
  "url": "https://exemplo.com/artigo-noticia",
  "title": "Título do Artigo",
  "author": "Nome do Autor",
  "date": "28/05/2023",
  "featured_image": "https://exemplo.com/imagem.jpg",
  "content": "<p>Conteúdo do artigo...</p>",
  "content_images": [
    {
      "src": "https://exemplo.com/imagem-conteudo.jpg",
      "alt": "Descrição da imagem",
      "width": "1024",
      "height": "682"
    }
  ]
}
```

### Mapeamento da Estrutura Liferay
- **Pastas de Documentos**: Criadas para cada item de notícia para armazenar imagens
- **Pastas de Conteúdo Estruturado**: Criadas dentro da pasta pai "Noticias"
- **Campos de Conteúdo Estruturado**:
  - `img`: Referência de imagem em destaque (referência do campo: "img")
  - `content`: Conteúdo de texto rico (referência do campo: "content")

## Monitoramento e Logging

### Arquivos de Log
- `scraper.log`: Operações de web scraping
- `liferay_content_processor.log`: Operações de migração

### Rastreamento de Estatísticas
O sistema de migração fornece estatísticas abrangentes:
- Total de itens processados
- Taxas de sucesso/falha
- Duração do processamento
- Pastas de documentos criadas
- Imagens carregadas
- Pastas de conteúdo criadas
- Itens de conteúdo estruturado criados

## Tratamento de Erros

- **Degradação Elegante**: Sistema continua processando mesmo se itens individuais falharem
- **Lógica de Retry**: Retry automático para falhas transitórias
- **Logging Abrangente**: Informações detalhadas de erro para solução de problemas
- **Mecanismos de Fallback**: Usa pastas de fallback quando a criação específica de pasta falha

## Solução de Problemas

### Problemas Comuns

1. **Erros de Conexão**: Verificar disponibilidade da instância Liferay e credenciais
2. **Erros de Permissão**: Verificar se o usuário tem permissões necessárias no Liferay
3. **Limitação de Taxa**: Ajustar `BATCH_DELAY` se encontrar limites de taxa
4. **Problemas de Memória**: Reduzir `BATCH_SIZE` para conjuntos de dados grandes

### Modo Debug

Habilitar logging detalhado definindo `DEV_MODE=True` no seu arquivo `.env`.

## Suporte

Para problemas e questões:
1. Verificar os arquivos de log para informações detalhadas de erro
2. Verificar configuração de ambiente
3. Garantir que a instância Liferay está acessível e adequadamente configurada

## Histórico de Versões

- **v1.0.0**: Lançamento inicial com arquitetura profissional, tratamento abrangente de erros e capacidades completas de migração
