# 📥 Download Nuvem CAED

Sistema para download e importação automática de dados educacionais da API CAED Digital para SQL Server.

---

## 📋 Descrição

Este notebook Python realiza:
- Download de dados da API CAED Digital via requisições HTTP
- Processamento e normalização dos dados com Pandas
- Importação automática para banco de dados SQL Server

---

## 🚀 Início Rápido

### Pré-requisitos

- Python 3.8+
- SQL Server com ODBC Driver 17
- Acesso à API CAED Digital

### Instalação

```bash
# Clone ou baixe este repositório

# Instale as dependências
pip install -r requirements.txt
```

### Configuração

Edite as configurações no notebook `Download_Nuvem_Organizado.ipynb`:

```python
# API
URL_BASE = 'https://parc.caeddigital.net/portal/classes'
HEADERS = {
    'X-Parse-Master-Key': 'SUA_CHAVE_AQUI',  # ⚠️ Configure sua chave
    # ...
}

# Banco de Dados
SERVIDOR = 'seu_servidor,porta'
BANCO_DE_DADOS = 'seu_banco'

# Processamento
COLLECTIONS = ['E_1308_ENTURMACAO']  # Collections desejadas

# Configuração do Where
WHERE_CLAUSE = {"excluido": False} # Filtro para consulta das collections
```

### Execução

1. Abra o notebook no Jupyter:
   ```bash
   jupyter notebook Download_Nuvem_Organizado.ipynb
   ```

2. Execute todas as células em ordem (Cell → Run All)

3. Acompanhe o progresso no console

---

## 📁 Estrutura do Projeto

```
.
├── Download_Nuvem_Organizado.ipynb  # Notebook principal
├── README.md                         # Este arquivo
└── requirements.txt                  # Dependências Python
```

---

## 🔧 Configurações Disponíveis

### Collections

Adicione ou remova collections da lista:

```python
COLLECTIONS = [
    'E_1308_ENTURMACAO',
    'E_1308_ESTUDANTE',
    'E_1308_TURMA'
]
```

### Batch Size

Ajuste o número de registros por requisição:

```python
BATCH_SIZE = 10000  # Padrão: 10.000
```

### Modo de Importação

Escolha como tratar tabelas existentes:

```python
# No SQL, altere if_exists:
if_exists='append'   # Adiciona registros (padrão)
if_exists='replace'  # Substitui tabela inteira
if_exists='fail'     # Falha se tabela existir
```

---

## 📊 Uso

### Exemplo Básico

```python
# O notebook já faz tudo automaticamente, mas você pode usar as funções:

# Baixar dados
df = obter_todos_dados_api('E_1308_ENTURMACAO')

# Ver dados
print(df.head())
print(f"Total: {len(df)} registros")

# Importar para SQL
df.to_sql('nome_tabela', engine, if_exists='append')
```

### Filtros Personalizados

Para adicionar filtros customizados, modifique a função:

```python
payload = json.dumps({
    "where": {
        "excluido": False,
        "CD_MUNICIPIO": "12345"  # Adicione mais filtros aqui
    },
    "limit": batch_size,
    "skip": skip
})
```

---

## ⚠️ Troubleshooting

### Erro de Conexão com SQL Server

```
Erro: [Microsoft][ODBC Driver 17 for SQL Server]...
```

**Solução**:
1. Verifique se o ODBC Driver 17 está instalado
2. Teste a conexão com o SQL Server
3. Confirme credenciais e permissões

### Timeout na API

```
Erro ao acessar a API: Timeout
```

**Solução**:
```python
# Adicione timeout na requisição
response = requests.get(url, headers=HEADERS, data=payload, timeout=60)
```

### Memória Insuficiente

```
MemoryError
```

**Solução**:
- Diminua o BATCH_SIZE para 5000
- Processe uma collection por vez
- Feche outros programas

### Caracteres Especiais

```
UnicodeDecodeError ou caracteres estranhos
```

**Solução**:
```python
# No SQL, converta para string antes
df = df.astype(str)
```

---

## 🔐 Segurança

### ⚠️ IMPORTANTE: Proteja suas credenciais!

**Não commite credenciais no Git!**

#### Opção 1: Arquivo .env (Recomendado)

```bash
# Crie arquivo .env
API_MASTER_KEY=sua_chave_aqui
DB_PASSWORD=sua_senha_aqui

# Adicione ao .gitignore
echo ".env" >> .gitignore
```

```python
# No notebook, use:
from dotenv import load_dotenv
import os

load_dotenv()
API_MASTER_KEY = os.getenv('API_MASTER_KEY')
```

#### Opção 2: Variáveis de Ambiente

```bash
# Windows
set API_MASTER_KEY=sua_chave

# Linux/Mac
export API_MASTER_KEY=sua_chave
```

#### Opção 3: Input Manual

```python
from getpass import getpass
API_MASTER_KEY = getpass('Digite a Master Key: ')
```

---

## 📈 Performance

### Tempos Estimados

| Registros | Tempo Download | Tempo Importação |
|-----------|---------------|------------------|
| 10.000    | ~30s          | ~10s            |
| 50.000    | ~2min         | ~30s            |
| 100.000   | ~4min         | ~1min           |
| 500.000   | ~20min        | ~5min           |

*Tempos aproximados, variam conforme rede e hardware*

### Otimizações

```python
# SQL Server - Use fast_executemany
engine = create_engine(string_conexao, fast_executemany=True)

# Importação - Use chunksize para grandes volumes
df.to_sql(..., chunksize=1000)
```

---

## 🤝 Contribuindo

Encontrou um bug ou tem uma sugestão?

1. Documente o problema claramente
2. Forneça exemplo reproduzível
3. Sugira uma solução se possível

---

## 📄 Licença

Este projeto é de uso interno.

---

## 📞 Suporte

Para questões sobre:
- **API CAED**: Consulte documentação oficial
- **SQL Server**: Verifique logs e permissões
- **Python/Pandas**: Consulte documentação oficial

---

## 🔄 Changelog

### Versão 1.0 (Original)
- Versão inicial funcional

---

## 📚 Recursos Úteis

- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Requests Documentation](https://requests.readthedocs.io/)
- [ODBC Driver 17 Download](https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)

---

**Desenvolvido para facilitar a integração de dados** 📚