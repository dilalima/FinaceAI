# FinanceAI

Assistente financeiro pessoal construído com Python e FastAPI.

## Estado atual

A Etapa 1 fornece a estrutura inicial do backend, configuração por ambiente e
um endpoint de saúde. Os módulos financeiros serão adicionados incrementalmente.

## Requisitos

- Python 3.13 ou superior compatível;
- MySQL será necessário a partir da etapa de persistência.

## Configuração local

No PowerShell, crie e ative um ambiente virtual:

```powershell
py -m venv .venv
& .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Se o PowerShell bloquear `Activate.ps1`, use a permissão temporária apenas
nesta sessão:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
& .\.venv\Scripts\Activate.ps1
```

Também é possível executar os comandos sem ativar o ambiente:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

O arquivo `.env` é local e não deve ser versionado. Altere os valores antes de
usar o banco de dados ou autenticação.

Para o banco criado no MySQL Workbench, ajuste `DATABASE_URL` com o usuário e a
senha reais, por exemplo:

```text
DATABASE_URL=mysql+pymysql://SEU_USUARIO:SUA_SENHA@localhost:3306/financeai
```

Não coloque a senha no código nem no Git.

## Executar a aplicação

```powershell
python -m uvicorn app.main:app --reload
```

Sem ativar o ambiente virtual, use:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Depois, acesse `http://127.0.0.1:8000/health`.

Para validar a conexão com o MySQL, acesse
`http://127.0.0.1:8000/health/database`.

## Autenticação

Endpoints disponíveis:

- `POST /auth/register` para criar uma conta;
- `POST /auth/login` para obter um token JWT;
- `GET /auth/me` para consultar o usuário autenticado usando `Authorization: Bearer <token>`.

## Contas e movimentações

Com um token JWT, a API oferece:

- `POST /finance/accounts` e `GET /finance/accounts`;
- `POST /finance/transactions` e `GET /finance/transactions`;
- `POST /finance/transfers` e `GET /finance/transfers`.

Transferências entre contas são armazenadas separadamente e não entram como
receitas ou despesas.

## Dashboard

Com um token JWT, `GET /dashboard/summary` retorna saldo total, receitas,
despesas, economia, pendências, despesas por categoria e evolução dos últimos
seis meses.

## Relatórios

Com um token JWT, estão disponíveis `GET /reports/monthly`,
`GET /reports/annual`, `GET /reports/export.xlsx` e `GET /reports/export.pdf`.
Os relatórios aceitam `year` e `month` como filtros quando aplicável.

## Planejamento

Endpoints protegidos: `POST/GET /planning/goals`, `POST/GET /planning/budgets`
e `GET /planning/alerts`. Os alertas são gerados quando uma categoria atinge
80% do orçamento mensal.

## Assistente financeiro

Configure `OPENAI_API_KEY` no `.env` para habilitar `POST /assistant/chat`.
O módulo usa a OpenAI Responses API por meio de um provider separado e envia ao
modelo somente o resumo financeiro do usuário autenticado.

## Importação CSV

`POST /imports/transactions.csv` aceita um arquivo UTF-8 com as colunas
`date,description,amount,type,category,account_id`. As colunas opcionais são
`status` e `due_date`. Cada registro recebe origem `csv` e um hash para evitar
duplicações. Integrações bancárias reais dependerão de um provedor autorizado
de Open Finance.

As migrações serão executadas com:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

## Validar

```powershell
python -m pytest
```

Sem ativar o ambiente virtual, use:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

## Próximas etapas

1. Configurar MySQL, SQLAlchemy e Alembic.
2. Implementar usuários e autenticação.
3. Implementar contas, transferências e movimentações.
4. Adicionar dashboard, relatórios, planejamento, IA e importação CSV.
