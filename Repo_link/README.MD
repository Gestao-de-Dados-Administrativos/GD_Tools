# Sistema Unificado de Integração com Repositório CAED

Sistema refatorado e unificado para integração com o Repositório CAED, suportando os ambientes Central e CPD.

## 📋 Características

- ✅ Unificação dos scripts `repo_link_central.py` e `repo_link_cpd.py`
- ✅ Código refatorado e organizado com classes
- ✅ Configurações movidas para arquivo `.env`
- ✅ Suporte a múltiplos ambientes (Central e CPD)
- ✅ Melhor tratamento de erros
- ✅ Documentação completa
- ✅ Type hints para melhor IDE support

## 🚀 Instalação

1. **Clone ou baixe o projeto**

2. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

3. **Configure o arquivo .env:**
```bash
cp .env.example .env
```

4. **Edite o arquivo .env com suas credenciais:**
```env
# Escolha o ambiente: 'central' ou 'cpd'
AMBIENTE=central

# Configure as credenciais de cada ambiente
CENTRAL_ID_USER=seu_id
CENTRAL_USER=seu_usuario
CENTRAL_SENHA=sua_senha
CENTRAL_BASE_URL=https://repositorio.caeddigital.net

CPD_ID_USER=seu_id
CPD_USER=seu_usuario
CPD_SENHA=sua_senha
CPD_BASE_URL=http://10.0.10.22:41112
```

## 💻 Uso

### Exemplo Básico

```python
from repo_link import RepositorioCAED

# Cria instância
repo = RepositorioCAED()

# Autentica (automático na primeira requisição)
token = repo.autenticar()
print(f"Autenticado com sucesso!")

# Baixa dados
caminho = repo.baixar_dado_adm(
    formulario='ESCOLA',
    subprograma='SEU_SUBPROGRAMA',
    fonte='SUA_FONTE',
    destino='downloads'
)
print(f"Arquivo salvo em: {caminho}")
```

### Mudando de Ambiente

Para alternar entre ambientes, basta mudar a variável `AMBIENTE` no arquivo `.env`:

```env
# Para ambiente Central
AMBIENTE=central

# Para ambiente CPD
AMBIENTE=cpd
```

### Uso com Filtros

```python
# Baixa com filtro
caminho = repo.baixar_dado_adm(
    formulario='ESCOLA',
    subprograma='SEU_SUBPROGRAMA',
    fonte='SUA_FONTE',
    destino='downloads',
    filtro_coluna='TP_DEPENDENCIA_ADMINISTRATIVA',
    filtro_op='=',
    filtro_valor='1'
)
```

### Operadores de Filtro Disponíveis

- `=` : Igual a
- `in` : Pertence a (use lista ou string separada por `|||`)

Exemplo com `in`:
```python
# Usando lista
filtro_valor = ['1', '2', '3']

# Ou usando string
filtro_valor = '1|||2|||3'
```

## 📚 Formulários Suportados

O sistema suporta os seguintes formulários:

- **L185**: Leiaute de Usuário - v3
- **L062**: Leiaute de Controle de usuários e pontos de entrega
- **L204**: Leiaute de Instrumento
- **L005**: Leiaute de base planejada
- **L009**: Leiaute de sujeito
- **L008**: Leiaute de item
- **Formulários AD**: Qualquer formulário administrativo

## 🔧 Funções Auxiliares

### Validação de CPF

```python
from repo_link import cpf_validator

if cpf_validator('12345678900'):
    print("CPF válido!")
else:
    print("CPF inválido!")
```

### Gerar Código Único

```python
from repo_link import gerar_codigo_unico

codigo = gerar_codigo_unico(tamanho=12)
print(f"Código gerado: {codigo}")
```

## 📁 Estrutura de Arquivos

```
.
├── repo_link.py          # Script principal unificado
├── requirements.txt      # Dependências do projeto
├── .env                  # Configurações (não versionar!)
├── .env.example         # Exemplo de configurações
└── README.md            # Esta documentação
```

## 🔒 Segurança

⚠️ **IMPORTANTE**: 
- Nunca versione o arquivo `.env` com credenciais reais
- Adicione `.env` ao seu `.gitignore`
- Use o `.env.example` apenas como template

Exemplo de `.gitignore`:
```
.env
*.csv
downloads/
__pycache__/
*.pyc
```

## 🆕 Mudanças em Relação aos Scripts Antigos

### Antes (repo_link_central.py / repo_link_cpd.py)

```python
# Credenciais em CSV
cadastro = pd.read_csv('acesso.csv')

# Duas versões do script
# URL hardcoded no código
```

### Agora (repo_link.py)

```python
# Credenciais no .env
# Script único
# Configuração por ambiente
# Melhor organização com classes
```

### Migração do Código Antigo

Se você tem código usando as funções antigas, elas ainda funcionam:

```python
# Código antigo (ainda funciona)
from repo_link import consulta_cadastro, get_bearer_token

cadastro = consulta_cadastro()  # Retorna DataFrame com config atual

# Código novo (recomendado)
from repo_link import RepositorioCAED

repo = RepositorioCAED()
token = repo.autenticar()
```

## 🐛 Solução de Problemas

### Erro: "Configurações incompletas"
- Verifique se todas as variáveis no `.env` estão preenchidas
- Confirme que o arquivo `.env` está no mesmo diretório do script

### Erro de autenticação
- Verifique se as credenciais estão corretas
- Confirme se está usando o ambiente correto (central/cpd)

### Timeout no download
- O tempo limite padrão é 600 segundos (10 minutos)
- Arquivos muito grandes podem demorar mais
- Verifique sua conexão com o servidor

## 📝 Exemplo Completo

```python
from repo_link import RepositorioCAED
import os

def main():
    # Inicializa o repositório
    repo = RepositorioCAED()
    
    print(f"Ambiente configurado: {repo.config.ambiente}")
    print(f"URL base: {repo.config.base_url}")
    
    # Autentica
    print("Autenticando...")
    repo.autenticar()
    print("✓ Autenticado com sucesso!")
    
    # Baixa múltiplos formulários
    formularios = ['ESCOLA', 'TURMA', 'ALUNO']
    
    for form in formularios:
        print(f"\n{'='*50}")
        print(f"Baixando: {form}")
        print('='*50)
        
        try:
            caminho = repo.baixar_dado_adm(
                formulario=form,
                subprograma='SEU_PROGRAMA',
                fonte='SUA_FONTE',
                destino='downloads'
            )
            
            if caminho:
                print(f"✓ Sucesso! Arquivo: {caminho}")
                
                # Verifica tamanho do arquivo
                tamanho = os.path.getsize(caminho) / (1024*1024)  # MB
                print(f"  Tamanho: {tamanho:.2f} MB")
            else:
                print(f"✗ Falha ao baixar {form}")
                
        except Exception as e:
            print(f"✗ Erro: {str(e)}")
    
    print("\n✓ Processo concluído!")

if __name__ == "__main__":
    main()
```

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique a documentação acima
2. Consulte os exemplos de uso
3. Verifique as mensagens de erro detalhadas no console

## 📄 Licença

Este é um projeto interno CAED.