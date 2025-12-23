"""
Script unificado para acesso ao repositório CAED (Central e CPD)
Gerencia download de formulários e dados administrativos
"""

import requests
import zipfile
import io
import time
import os
import json
from datetime import datetime
from pathlib import Path
import pandas as pd
import uuid
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

class RepositorioConfig:
    """Configuração do ambiente do repositório"""

    def __init__(self, ambiente=None):
        """
        Inicializa configuração do ambiente

        Args:
            ambiente (str): 'CPD' ou 'CENTRAL'. Se None, usa variável de ambiente AMBIENTE
        """
        self.ambiente = ambiente or os.getenv('AMBIENTE', 'CENTRAL')
        self._carregar_config()

    def _carregar_config(self):
        """Carrega configurações baseadas no ambiente"""
        if self.ambiente.upper() == 'CPD':
            self.id_user = os.getenv('CPD_ID_USER')
            self.username = os.getenv('CPD_USERNAME')
            self.password = os.getenv('CPD_PASSWORD')
            self.base_url = os.getenv('CPD_BASE_URL', 'http://10.0.10.22:41112/gw')
        else:  # CENTRAL
            self.id_user = os.getenv('CENTRAL_ID_USER')
            self.username = os.getenv('CENTRAL_USERNAME')
            self.password = os.getenv('CENTRAL_PASSWORD')
            self.base_url = os.getenv('CENTRAL_BASE_URL', 'https://repositorio.caeddigital.net/gw')

    def validar(self):
        """Valida se todas as credenciais estão configuradas"""
        if not all([self.id_user, self.username, self.password]):
            raise ValueError(f"Credenciais não configuradas para ambiente {self.ambiente}. Verifique o arquivo .env")
        return True


def get_bearer_token(config):
    """
    Obtém token de autenticação

    Args:
        config (RepositorioConfig): Configuração do ambiente

    Returns:
        str: Token de autenticação
    """
    url = f"{config.base_url}/login/auth/login"
    payload = {
        "username": config.username,
        "password": config.password
    }
    headers = {
        "Content-Type": "application/json; charset=utf-8"
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json().get("token")
    else:
        raise Exception(f"Erro ao obter token: {response.status_code}, {response.text}")


def pegar_colunas(subprograma, codigo_form, bearer, config):
    """
    Obtém lista de colunas de um formulário

    Args:
        subprograma (str): Código do subprograma
        codigo_form (str): Código do formulário
        bearer (str): Token de autenticação
        config (RepositorioConfig): Configuração do ambiente

    Returns:
        list: Lista com índices das colunas
    """
    url = f'{config.base_url}/formulario/formulario/download/campos-formulario/{subprograma}/{codigo_form}/055'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {bearer}'
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        colunas = [campo['ordem'] for campo in data['camposFormularios']]
        return colunas
    else:
        print(f'Erro ao fazer a requisição: {response.status_code}')
        return []


def cat_nm_campo(subprograma, codigo_form, bearer, campo_filtro, config):
    """
    Obtém informações de um campo específico

    Args:
        subprograma (str): Código do subprograma
        codigo_form (str): Código do formulário
        bearer (str): Token de autenticação
        campo_filtro (str): Nome do campo a buscar
        config (RepositorioConfig): Configuração do ambiente

    Returns:
        tuple: (ordem, tamanho, tipo) do campo
    """
    # Mapeamento de códigos de formulário para seus códigos de layout
    layout_map = {
        'L185': '185', 'L062': '185', 'L005': '005', 'L009': '009',
        'L204': '204', 'L008': '008', 'L021': '021', 'L010': '010'
    }

    layout_code = layout_map.get(codigo_form, '055')
    url = f'{config.base_url}/formulario/formulario/download/campos-formulario/{subprograma}/{codigo_form}/{layout_code}'

    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'Authorization': f'Bearer {bearer}'
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        for campo in data['camposFormularios']:
            if campo['nomeCampo'] == campo_filtro:
                return campo['ordem'], campo['tamanho'], campo['tipo']
        print(f"Campo {campo_filtro} não encontrado.")
        return None, None, None
    else:
        print(f'Erro ao fazer a requisição: {response.status_code}')
        return None, None, None


def exportar_payload(id_user, codigo_form, colunas, subprograma, fonte,
                    filtro_op='', filtro_valor='', filtro_coluna='',
                    filtro_tamanho='', filtro_tipo=''):
    """
    Gera payload para exportação de dados

    Args:
        id_user (str): ID do usuário
        codigo_form (str): Código do formulário
        colunas (list): Lista de colunas
        subprograma (str): Código do subprograma
        fonte (str): Código da fonte
        filtro_op (str): Operador de filtro
        filtro_valor (str): Valor do filtro
        filtro_coluna (str): Coluna do filtro
        filtro_tamanho (str): Tamanho do campo de filtro
        filtro_tipo (str): Tipo do campo de filtro

    Returns:
        dict: Payload para requisição
    """
    # Prepara filtro
    filtro = []
    if filtro_op:
        filtro = [{
            "operador": filtro_op,
            "coluna": filtro_coluna,
            "tamanho": filtro_tamanho,
            "tipoCampo": filtro_tipo,
            "valor1": filtro_valor,
        }]

    # Configurações específicas por tipo de formulário
    form_configs = {
        'L185': {
            "fileNames": [""],
            "servico": {"id": 15, "nome": "US"},
            "formulario": {"codigo": "L185", "nome": "Leiaute de Usuário - v3"},
            "layout": {"codigo": 185, "id": 170, "idServico": 15, "nomeServico": "US",
                      "referenciaServico": "REPOSITÓRIO DE USUÁRIOS"},
            "colunas": list(range(1, 72))
        },
        'L062': {
            "fileNames": [""],
            "servico": {"id": 15, "nome": "US"},
            "formulario": {"codigo": "L062", "nome": "Leiaute de Controle de usuários e pontos de entrega."},
            "layout": {"codigo": "062", "id": 190, "idServico": 15, "nomeServico": "US",
                      "referenciaServico": "REPOSITÓRIO DE USUÁRIOS"},
            "colunas": list(range(1, 16))
        },
        'L204': {
            "fileNames": [""],
            "servico": {"id": 6, "nome": "IN"},
            "formulario": {"codigo": "L204", "nome": "Leiaute de Instrumento"},
            "layout": {"codigo": "204", "id": 173, "idServico": 6, "nomeServico": "IN",
                      "referenciaServico": "REPOSITÓRIO DE INSTRUMENTOS"},
            "colunas": list(range(1, 42))
        },
        'L008': {
            "fileNames": ["", ""],
            "servico": {"id": 1, "nome": "DA"},
            "formulario": {"codigo": "L008", "nome": "Leiaute de decodificação"},
            "layout": {"codigo": "008", "id": 8, "idServico": 1, "nomeServico": "DA",
                      "referenciaServico": "REPOSITÓRIO DE DADOS"},
            "colunas": list(range(1, 227))
        },
        'L021': {
            "fileNames": ["", ""],
            "servico": {"id": 10, "nome": "SO"},
            "formulario": {"codigo": "L021", "nome": "Leiaute de solicitação de verificação"},
            "layout": {"codigo": "021", "id": 17, "idServico": 10, "nomeServico": "SO",
                      "referenciaServico": "REPOSITÓRIO DE SOLICITAÇÃO"},
            "colunas": list(range(1, 27))
        },
        'L010': {
            "fileNames": ["", ""],
            "servico": {"id": 10, "nome": "SO"},
            "formulario": {"codigo": "L010", "nome": "Leiaute de solicitação de recodificação"},
            "layout": {"codigo": "010", "id": 148, "idServico": 10, "nomeServico": "SO",
                      "referenciaServico": "REPOSITÓRIO DE SOLICITAÇÃO"},
            "colunas": list(range(1, 27))
        },
        'L005': {
            "fileNames": ["", ""],
            "servico": {"id": 1, "nome": "DA"},
            "formulario": {"codigo": "L005", "nome": "Leiaute de base planejada"},
            "layout": {"codigo": "005", "id": 5, "idServico": 1, "nomeServico": "DA",
                      "referenciaServico": "REPOSITÓRIO DE DADOS"},
            "colunas": list(range(1, 117))
        },
        'L009': {
            "fileNames": ["", ""],
            "servico": {"id": 3, "nome": "SU"},
            "formulario": {"codigo": "L009", "nome": "Leiaute de sujeito"},
            "layout": {"codigo": "009", "id": 9, "idServico": 3, "nomeServico": "SU",
                      "referenciaServico": "REPOSITÓRIO DE SUJEITOS"},
            "colunas": list(range(1, 98))
        }
    }

    # Base do payload
    payload = {
        "fonte": {
            "codigo": fonte,
            "ativo": True,
            "fonteDadoTipo": {"id": 2, "codigo": 2},
            "fonteDadoPadrao": None
        },
        "programa": {
            "codigo": subprograma,
            "ativo": True,
            "programaTipo": {"id": 2, "codigo": 2},
            "fonteDado": {
                "codigo": fonte,
                "ativo": True,
                "fonteDadoTipo": {"id": 2, "codigo": 2},
                "fonteDadoPadrao": None
            },
            "nomeArquivoEspecificacao": None,
            "nomeReduzido": None
        },
        "usuario": {
            "id": id_user,
            "grupoSelecionado": {
                "id": 1,
                "descricao": "ADM",
                "ativo": True
            }
        },
        "transferencia": False,
        "filtrosAvancados": filtro
    }

    # Aplica configuração específica ou usa padrão (AD)
    if codigo_form in form_configs:
        config = form_configs[codigo_form]
        payload.update(config)
    else:
        # Configuração padrão para dados administrativos
        payload.update({
            "fileNames": [""],
            "servico": {
                "id": 13,
                "nome": "AD",
                "referenciaServico": "REPOSITÓRIO DE DADOS ADMINISTRATIVOS",
                "instanciaServico": "REPOSITORIO_DADO_ADMINISTRATIVO"
            },
            "formulario": {"codigo": codigo_form},
            "layout": {
                "codigo": "055",
                "nome": "Leiaute de dado administrativo",
                "id": 125,
                "idServico": 13,
                "nomeServico": "AD",
                "referenciaServico": "REPOSITORIO_DADOS_ADMINISTRATIVOS"
            },
            "colunas": colunas
        })

    return payload


def get_formulario_code(bearer, subprograma, partial_name, config):
    """
    Obtém código do formulário pelo nome parcial

    Args:
        bearer (str): Token de autenticação
        subprograma (str): Código do subprograma
        partial_name (str): Nome parcial do formulário
        config (RepositorioConfig): Configuração do ambiente

    Returns:
        tuple: (codigo_form, partial_name)
    """
    url = f'{config.base_url}/formulario/formulario/download/formularios/{subprograma}/AD/{config.id_user}'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {bearer}'
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        formularios_data = response.json()

        if isinstance(formularios_data, list):
            formularios = formularios_data
        elif 'formularios' in formularios_data:
            formularios = formularios_data['formularios']
        else:
            formularios = []

        for formulario in formularios:
            if partial_name.upper() == formulario['nome'].upper():
                print(f"O código do formulário {partial_name} é: {formulario['codigo']}")
                return formulario['codigo'], partial_name

        print("Nenhum formulário com a parte do nome fornecida foi encontrado.")
        return None, None
    else:
        print(f'Erro ao fazer a requisição: {response.status_code}')
        print('Detalhes do erro:', response.text)
        return None, None


def get_total_items(data_atual, headers, config):
    """
    Obtém total de itens no histórico

    Args:
        data_atual (str): Data atual no formato YYYY-MM-DD
        headers (dict): Headers da requisição
        config (RepositorioConfig): Configuração do ambiente

    Returns:
        int: Total de itens
    """
    url = f"{config.base_url}/repositorio/historico/totalItems"
    params = {
        "idGrupo": 1,
        "ultimaSemana": data_atual
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        try:
            return int(response.text)
        except ValueError:
            print("Erro ao converter a resposta para inteiro.")
            return None
    else:
        print(f"Erro ao obter totalItems: {response.status_code}")
        return None


def verificar_arquivo_disponivel(nome_arquivo_parcial, data_atual, total_items, headers, config):
    """
    Verifica se arquivo está disponível para download

    Args:
        nome_arquivo_parcial (str): Nome parcial do arquivo
        data_atual (str): Data atual no formato YYYY-MM-DD
        total_items (int): Total de itens
        headers (dict): Headers da requisição
        config (RepositorioConfig): Configuração do ambiente

    Returns:
        str: Nome do arquivo disponível ou None
    """
    url = f"{config.base_url}/repositorio/historico"
    params = {
        "idGrupo": 1,
        "ultimaSemana": data_atual,
        "totalItems": total_items,
        "page": 0,
        "size": 10,
        "sort": "id,desc"
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        for item in data.get("content", []):
            if item["nomeArquivo"].startswith(nome_arquivo_parcial) and item["tpStatus"] == "S":
                return item["nomeArquivo"]
    return None


def baixa_dado_adm(formulario, subprograma, fonte, destino='', filtro_coluna='',
                   filtro_op='', filtro_valor='', ambiente=None):
    """
    Baixa formulários do repositório

    Args:
        formulario (str): Nome do formulário (ex: 'ESCOLA', 'TURMA', 'USUARIO')
        subprograma (str): Código do programa de origem
        fonte (str): Código fonte do programa
        destino (str): Caminho de destino do download
        filtro_coluna (str): Coluna para aplicar filtro
        filtro_op (str): Operador de filtro ('in', '=')
        filtro_valor (str|list): Valor(es) para filtrar
        ambiente (str): 'CPD' ou 'CENTRAL'. Se None, usa variável AMBIENTE do .env

    Returns:
        str: Caminho do arquivo baixado
    """
    # Configura ambiente
    config = RepositorioConfig(ambiente)
    config.validar()

    # Obtém token de autenticação
    bearer = get_bearer_token(config)

    data_atual = datetime.now().strftime('%Y-%m-%d')

    # Headers
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {bearer}'
    }

    # Mapeamento de formulários especiais
    formularios_especiais = {
        'USUARIO': ('L185', f'FORM_{formulario}_{subprograma}'),
        'APP_LOGISTICA': ('L062', 'APP_LOGISTICA'),
        'L005': ('L005', 'L005'),
        'L009': ('L009', 'L009'),
        'L204': ('L204', 'L204'),
        'L008': ('L008', 'L008'),
        'L021': ('L021', 'L021'),
        'L010': ('L010', 'L010')
    }

    partial_name = f'FORM_{formulario}_{subprograma}'

    if formulario in formularios_especiais:
        codigo_form, partial_name = formularios_especiais[formulario]
        colunas = ''
    else:
        codigo_form, partial_name = get_formulario_code(bearer, subprograma, partial_name, config)
        if not codigo_form:
            print(f"Nenhum formulário encontrado com nome de {partial_name}.")
            return None
        colunas = pegar_colunas(subprograma, codigo_form, bearer, config)

    # Processa filtro
    if filtro_op == 'in':
        if not isinstance(filtro_valor, list):
            filtro_valor = filtro_valor.split('|||')
        filtro_valor = '§'.join(filtro_valor)
    elif filtro_op == '=':
        if not isinstance(filtro_valor, str):
            try:
                filtro_valor = str(filtro_valor)
            except:
                print("Valor do filtro inválido para operador '='")
                return None

    if filtro_coluna:
        filtro_coluna, filtro_tamanho, filtro_tipo = cat_nm_campo(
            subprograma, codigo_form, bearer, filtro_coluna, config
        )
    else:
        filtro_tamanho = ''
        filtro_tipo = ''

    # Gera payload
    payload = exportar_payload(
        config.id_user, codigo_form, colunas, subprograma, fonte,
        filtro_op, filtro_valor, filtro_coluna, filtro_tamanho, filtro_tipo
    )
    payload.update({"historico": False})

    # Solicita exportação
    url_exportacao = f"{config.base_url}/repositorio/download/solicitarExportacao"
    response = requests.post(url_exportacao, json=payload, headers=headers)

    if response.status_code != 200:
        print(f"Erro na solicitação de exportação para {partial_name}: {response.status_code}")
        try:
            error_message = response.json().get('error', 'Nenhuma mensagem de erro fornecida.')
            print("Erro:", error_message)
        except ValueError:
            print("Resposta:", response.text)
        return None

    data = response.json()
    print(f"Solicitação de Download {partial_name.upper()} realizada com sucesso, aguarde..")

    nome_arquivo = data.get('nomeArquivo')
    if not nome_arquivo:
        print(f"Nome do arquivo não encontrado na resposta para {partial_name}.")
        return None

    nome_arquivo_parcial = "_".join(nome_arquivo.split("_")[:-1])
    total_items = get_total_items(data_atual, headers, config)

    if total_items is None:
        print(f"Erro ao obter totalItems para {partial_name}.")
        return None

    # Aguarda arquivo ficar disponível
    tempo_limite = 600
    tempo_inicial = time.time()
    arquivo_disponivel = None

    while time.time() - tempo_inicial < tempo_limite:
        arquivo_disponivel = verificar_arquivo_disponivel(
            nome_arquivo_parcial, data_atual, total_items, headers, config
        )
        if arquivo_disponivel:
            break
        time.sleep(5)

    if not arquivo_disponivel:
        print(f"Tempo limite excedido. O arquivo para {partial_name} ainda não está disponível para download.")
        return None

    # Download do arquivo
    download_url = f"{config.base_url}/repositorio/download/arquivo/{arquivo_disponivel}"
    download_response = requests.get(download_url, headers=headers)

    if download_response.status_code != 200:
        print(f"Erro ao baixar o arquivo ZIP para {partial_name}: {download_response.status_code}")
        print("Detalhes do erro ao baixar:", download_response.text)
        return None

    # Define nome do arquivo
    file_name = f"{arquivo_disponivel}_{partial_name[:-5].upper()}.zip".replace('FORM_', '')

    # Ajusta nome para formulários especiais
    for form_code in ['L005', 'L009', 'L204', 'L008', 'L021', 'L010']:
        if codigo_form == form_code:
            file_name = f"{arquivo_disponivel}_{form_code}.zip"
            break

    # Gerencia diretório de destino
    destino_0 = os.getcwd()
    if destino:
        destino_path = os.path.join(os.getcwd(), destino)
        os.makedirs(destino_path, exist_ok=True)
        os.chdir(destino_path)

    # Salva e extrai arquivo
    with open(file_name, "wb") as f:
        f.write(download_response.content)
    print(f"Arquivo ZIP baixado com sucesso: {file_name}")

    with zipfile.ZipFile(io.BytesIO(download_response.content), 'r') as zip_ref:
        zip_ref.extractall(os.getcwd())
    print(f"Conteúdo do arquivo ZIP extraído com sucesso: {file_name}")

    # Renomeia arquivo CSV
    csv_name = file_name.replace('.zip', '.csv')
    os.rename(arquivo_disponivel + '.csv', csv_name)

    os.chdir(destino_0)

    if destino:
        return os.path.join(destino_path, csv_name)
    return csv_name


# Funções auxiliares

def base36_encode(number):
    """
    Codifica um número em base 36

    Args:
        number (int): Número a ser codificado

    Returns:
        str: Número codificado em base 36
    """
    alphabet = '0123456789abcdefghijklmnopqrstuvwxyz'

    if number == 0:
        return alphabet[0]

    base36 = []
    while number:
        number, i = divmod(number, 36)
        base36.append(alphabet[i])

    return ''.join(reversed(base36))


def gerar_codigo_unico(tamanho=12):
    """
    Gera um código único em base 36

    Args:
        tamanho (int): Tamanho do código a ser gerado

    Returns:
        str: Código único em base 36
    """
    unique_id = uuid.uuid4()
    unique_number = unique_id.int
    base36_str = base36_encode(unique_number)

    if len(base36_str) > tamanho:
        return base36_str[:tamanho]
    else:
        return base36_str.zfill(tamanho)


def cpf_validator(cpf):
    """
    Valida se um CPF é válido

    Args:
        cpf (str): CPF a ser validado

    Returns:
        bool: True se válido, False caso contrário
    """
    cpf_str = str(cpf)
    numeros = [int(digito) for digito in cpf_str if digito.isdigit()]

    if len(numeros) != 11:
        return False

    # Valida primeiro dígito verificador
    soma_produtos = sum(a * b for a, b in zip(numeros[0:9], range(10, 1, -1)))
    digito_esperado = (soma_produtos * 10 % 11) % 10
    if numeros[9] != digito_esperado:
        return False

    # Valida segundo dígito verificador
    soma_produtos = sum(a * b for a, b in zip(numeros[0:10], range(11, 1, -1)))
    digito_esperado = (soma_produtos * 10 % 11) % 10
    if numeros[10] != digito_esperado:
        return False

    return True


# Funções em construção (mantidas para compatibilidade)

def generate_payload(nome, email, cpf, dc_senha, agregados, layout, key, fonte, programa, fl_master='0', op='I'):
    """EM CONSTRUÇÃO"""
    return "EM CONSTRUÇÃO"


def cadastro_usuarios(url, key, fonte, programa, df, op):
    """EM CONSTRUÇÃO"""
    return "EM CONSTRUÇÃO"
