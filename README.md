# Delfos - Teste Técnico

Este projeto configura uma infraestrutura completa de dados, simulando um ambiente real com banco fonte, API de consumo e banco alvo para analytics.

## Como Rodar o Projeto

### Pré-requisitos
- Docker e Docker Compose
- Python 3.10+
- Pip

### 1. Subir a Infraestrutura
O projeto utiliza Docker Compose para orquestrar dois bancos PostgreSQL (`db_fonte` e `db_alvo`) e a API de dados (`api_conector`).

```bash
# Na raiz do projeto
docker compose up -d --build
```
Isso iniciará:
- **db_source**: Porta externa 5433
- **db_target**: Porta externa 5434
- **api_conector**: Porta externa 8000

### 2. Popular o Banco Fonte

#### Via Docker
Execute o script de setup diretamente pelo container da API (sem necessidade de instalar Python/libs na sua máquina):

```bash
docker compose exec api_conector python scripts/init_db_fonte.py
```

#### Via Python
Caso prefira rodar localmente:

```bash
pip install -r requirements.txt
python scripts/init_db_fonte.py
```

### 3. Executar o ETL
O script de ETL extrai dados da API, transforma e carrega no banco alvo.
**Observação**: Ao rodar localmente (fora do Docker), é necessário sobrescrever o host do banco alvo para `localhost`.

```bash
# Exemplo para rodar dados de uma data específica
DB_TARGET_HOST=localhost python3 -m etl.main --date 2025-12-25
```

### 4. Orquestração com Dagster
O Dagster é utilizado para orquestrar o processo de ETL diariamente, oferecendo interface visual, backfill e monitoramento.

1.  **Iniciar o Dagster**:
    ```bash
    dagster dev -m orchestrator
    ```

2.  **Acessar a UI**:
    Abra o navegador em [http://localhost:3000](http://localhost:3000).

3.  **Executar Job**:
    - Vá até a aba "Assets".
    - Clique em `daily_wind_etl`.
    - Clique em "Materialize" e escolha uma data de partição (lembre-se que o script de init gera dados apenas para os últimos 10 dias).

4.  **Agendamento**:
    O job está configurado para rodar diariamente à meia-noite (UTC). Ative o schedule na aba "Overview" > "Schedules".

---

## Período de Dados

O script de inicialização (`scripts/init_db_fonte.py`) gera dados retroativos de **10 dias** a partir do momento da sua execução.
- **Frequência**: 1 minuto.
- **Volume**: ~14.400 registros.
- **Variáveis**: `timestamp`, `wind_speed` (simulado com aleatoriedade), `power` (curva de potência baseada no vento) e `ambient_temperature`.

---

## API de Dados

O projeto expõe uma API RESTful (`api_conector`) desenvolvida com **FastAPI** para consultar os dados brutos do banco fonte.

### Endpoint: `GET /data`

Retorna uma lista de registros em formato JSON.

#### Parâmetros de Consulta:
- `start_date` (opcional): Filtra registros a partir desta data/hora (ISO 8601).
- `end_date` (opcional): Filtra registros até esta data/hora (ISO 8601).
- `columns` (opcional): Lista separada por vírgulas das colunas desejadas. Permite otimizar a transferência de dados selecionando apenas o necessário (ex: `wind_speed,power`).

#### Exemplo de Uso:
```bash
# Busca apenas velocidade do ar e potência para um intervalo específico
curl "http://localhost:8000/data?start_date=2025-12-25T00:00:00&end_date=2025-12-25T01:00:00&columns=wind_speed,power"
```

A API roda dentro do Docker e é acessível internamente pelos serviços (como o script ETL) via `http://api_conector:8000`.

---

## 🏗 Decisões de Design

### 1. Modelagem do Banco Alvo (Analytics)
Optou-se por uma modelagem **Vertical (EAV-like/Tabela Fato de Sinais)** em vez de uma tabela larga (wide).

- **Tabela `Signal`**: Armazena os metadados das variáveis (ex: `wind_speed_mean`, `power_max`).
    - *Vantagem*: Flexibilidade. Novos KPIs ou sensores podem ser adicionados sem alterar o esquema da tabela de dados (DDL).
- **Tabela `Data`**: Tabela fato contendo `timestamp`, `signal_id` e `value`.
    - *Vantagem*: Otimiza o armazenamento para séries temporais esparsas e normaliza a estrutura de consulta.

### 2. ETL e Agregação
- **Extração**: Feita via API (`api_conector`) para simular um cenário real de desacoplamento entre a fonte de dados (talvez um SCADA legado) e o pipeline de dados. O uso de `httpx` garante performance.
- **Transformação (Pandas)**:
    - **Janelamento**: Foi utilizado `resample('10min')` para reduzir a granularidade e suavizar ruídos.
    - **Métricas**: Para cada janela de 10 minutos, calculamos estatísticas descritivas (`mean`, `min`, `max`, `std`) que são fundamentais para análise de performance de ativos de energia.
    - **Flattening**: O DataFrame, originalmente "largo" após a agregação, é transformado para o formato "longo" para se adequar ao modelo de dados de destino.

---

## 📂 Estrutura de Pastas

- `/api`: Código da aplicação FastAPI.
- `/etl`: Lógica do pipeline (Extract, Transform, Load).
- `/scripts`: Scripts auxiliares de setup (infraestrutura).
- `/orchestrator`: Orquestração com Dagster.
- `docker-compose.yml`: Orquestração dos serviços.
