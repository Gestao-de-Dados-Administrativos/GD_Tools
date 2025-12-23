# Guia do repo_link.py - Script Unificado

## Descrição

O `repo_link.py` é um script unificado que combina as funcionalidades dos scripts `repo_link_central.py` e `repo_link_cpd.py`, permitindo acesso tanto ao repositório Central quanto ao CPD através de configuração via arquivo `.env`.

## Configuração Inicial

### 1. Criar arquivo .env

Copie o arquivo `.env.example` para `.env`:

```bash
cp .env.example .env
```

### 2. Configurar credenciais

Edite o arquivo `.env` e preencha as credenciais:

```env
# Configuração do ambiente (CPD ou CENTRAL)
AMBIENTE=CENTRAL

# Credenciais CPD
CPD_ID_USER=seu_id_cpd
CPD_USERNAME=seu_usuario_cpd
CPD_PASSWORD=sua_senha_cpd
CPD_BASE_URL=http://10.0.10.22:41112/gw

# Credenciais CENTRAL
CENTRAL_ID_USER=seu_id_central
CENTRAL_USERNAME=seu_usuario_central
CENTRAL_PASSWORD=sua_senha_central
CENTRAL_BASE_URL=https://repositorio.caeddigital.net/gw
```

### 3. Instalar dependências

```bash
pip install -r Repo_link/requirements.txt
```

## Uso

### Exemplo básico

```python
from repo_link import baixa_dado_adm

# Baixa formulário usando ambiente padrão (definido em .env)
caminho = baixa_dado_adm(
    formulario='ESCOLA',
    subprograma='2024',
    fonte='SP'
)
```

### Especificar ambiente explicitamente

```python
# Forçar uso do ambiente CPD
caminho = baixa_dado_adm(
    formulario='ESCOLA',
    subprograma='2024',
    fonte='SP',
    ambiente='CPD'
)

# Forçar uso do ambiente CENTRAL
caminho = baixa_dado_adm(
    formulario='ESCOLA',
    subprograma='2024',
    fonte='SP',
    ambiente='CENTRAL'
)
```

### Baixar com filtro

```python
# Filtro com operador '='
caminho = baixa_dado_adm(
    formulario='ESCOLA',
    subprograma='2024',
    fonte='SP',
    filtro_coluna='CD_MUNICIPIO',
    filtro_op='=',
    filtro_valor='3550308'
)

# Filtro com operador 'in' (lista de valores)
caminho = baixa_dado_adm(
    formulario='TURMA',
    subprograma='2024',
    fonte='SP',
    filtro_coluna='CD_ESCOLA',
    filtro_op='in',
    filtro_valor=['001', '002', '003']
)
```

### Especificar destino

```python
# Baixar para pasta específica
caminho = baixa_dado_adm(
    formulario='ESCOLA',
    subprograma='2024',
    fonte='SP',
    destino='dados/escolas'
)
```

## Formulários Suportados

### Formulários Especiais (com código fixo)

- `USUARIO` → L185
- `APP_LOGISTICA` → L062
- `L005` → Base Planejada
- `L009` → Sujeito
- `L204` → Instrumento
- `L008` → Decodificação (somente CPD)
- `L021` → Solicitação de Verificação (somente CPD)
- `L010` → Solicitação de Recodificação (somente CPD)

### Formulários Dinâmicos (Dados Administrativos)

Qualquer formulário de dados administrativos pode ser baixado usando o nome do formulário (ex: 'ESCOLA', 'TURMA', 'SALA_DE_APLICACAO', etc.)

## Funções Utilitárias

### Validar CPF

```python
from repo_link import cpf_validator

if cpf_validator('12345678901'):
    print("CPF válido")
```

### Gerar código único

```python
from repo_link import gerar_codigo_unico

codigo = gerar_codigo_unico(tamanho=12)
print(codigo)  # Exemplo: 'a3b5c7d9e1f2'
```

### Codificar número em base 36

```python
from repo_link import base36_encode

encoded = base36_encode(1234567890)
print(encoded)  # 'kf12oi'
```

## Diferenças entre Ambientes

### CPD
- URL: `http://10.0.10.22:41112/gw`
- Suporta formulários L008, L021, L010
- Acesso interno

### CENTRAL
- URL: `https://repositorio.caeddigital.net/gw`
- Não suporta L008, L021, L010
- Acesso externo

## Troubleshooting

### Erro: "Credenciais não configuradas"

Verifique se o arquivo `.env` existe e está preenchido corretamente.

### Erro: "Tempo limite excedido"

O arquivo pode estar demorando para processar. Aumente o tempo limite ou tente novamente mais tarde.

### Erro de autenticação

Verifique se as credenciais no `.env` estão corretas para o ambiente que está usando.

## Migração dos Scripts Antigos

### De repo_link_central.py

```python
# Antes
from repo_link_central import baixa_dado_adm
caminho = baixa_dado_adm('ESCOLA', '2024', 'SP')

# Depois (usando .env com AMBIENTE=CENTRAL)
from repo_link import baixa_dado_adm
caminho = baixa_dado_adm('ESCOLA', '2024', 'SP')

# Ou explicitamente
caminho = baixa_dado_adm('ESCOLA', '2024', 'SP', ambiente='CENTRAL')
```

### De repo_link_cpd.py

```python
# Antes
from repo_link_cpd import baixa_dado_adm
caminho = baixa_dado_adm('ESCOLA', '2024', 'SP')

# Depois (usando .env com AMBIENTE=CPD)
from repo_link import baixa_dado_adm
caminho = baixa_dado_adm('ESCOLA', '2024', 'SP')

# Ou explicitamente
caminho = baixa_dado_adm('ESCOLA', '2024', 'SP', ambiente='CPD')
```

## Notas

- As funções `generate_payload` e `cadastro_usuarios` estão marcadas como "EM CONSTRUÇÃO" nos scripts originais e foram mantidas assim nesta versão.
- O script cria automaticamente pastas de destino se elas não existirem.
- Arquivos CSV extraídos são automaticamente renomeados para manter consistência.
