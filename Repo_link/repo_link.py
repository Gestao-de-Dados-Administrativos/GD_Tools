"""
Sistema unificado de integração com o Repositório CAED
Suporta ambientes: Central e CPD

Autor: Refatoração do sistema original
Data: 2024
"""

import os
import io
import json
import time
import uuid
import zipfile
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import requests
import pandas as pd
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()


# ==================== CONSTANTES ====================

class FormularioConfig:
    """Configurações dos formulários disponíveis"""
    
    L185 = {
        'codigo': 'L185',
        'nome': 'Leiaute de Usuário - v3',
        'colunas': list(range(1, 72)),
        'servico': {'id': 15, 'nome': 'US'},
        'layout': {
            'codigo': 185,
            'id': 170,
            'idServico': 15,
            'nomeServico': 'US',
            'referenciaServico': 'REPOSITÓRIO DE USUÁRIOS'
        }
    }
    
    L062 = {
        'codigo': 'L062',
        'nome': 'Leiaute de Controle de usuários e pontos de entrega.',
        'colunas': list(range(1, 16)),
        'servico': {'id': 15, 'nome': 'US'},
        'layout': {
            'codigo': '062',
            'id': 190,
            'idServico': 15,
            'nomeServico': 'US',
            'referenciaServico': 'REPOSITÓRIO DE USUÁRIOS'
        }
    }
    
    L204 = {
        'codigo': 'L204',
        'nome': 'Leiaute de Instrumento',
        'colunas': list(range(1, 42)),
        'servico': {'id': 6, 'nome': 'IN'},
        'layout': {
            'codigo': '204',
            'id': 173,
            'idServico': 6,
            'nomeServico': 'IN',
            'referenciaServico': 'REPOSITÓRIO DE INSTRUMENTOS'
        }
    }
    
    L005 = {
        'codigo': 'L005',
        'nome': 'Leiaute de base planejada',
        'colunas': list(range(1, 117)),
        'servico': {'id': 1, 'nome': 'DA'},
        'layout': {
            'codigo': '005',
            'id': 5,
            'idServico': 1,
            'nomeServico': 'DA',
            'referenciaServico': 'REPOSITÓRIO DE DADOS'
        }
    }
    
    L009 = {
        'codigo': 'L009',
        'nome': 'Leiaute de sujeito',
        'colunas': list(range(1, 98)),
        'servico': {'id': 3, 'nome': 'SU'},
        'layout': {
            'codigo': '009',
            'id': 9,
            'idServico': 3,
            'nomeServico': 'SU',
            'referenciaServico': 'REPOSITÓRIO DE SUJEITOS'
        }
    }
    
    L008 = {
        'codigo': 'L008',
        'nome': 'Leiaute de item',
        'colunas': list(range(1, 60)),
        'servico': {'id': 2, 'nome': 'IT'},
        'layout': {
            'codigo': '008',
            'id': 8,
            'idServico': 2,
            'nomeServico': 'IT',
            'referenciaServico': 'REPOSITÓRIO DE ITENS'
        }
    }


# ==================== CLASSE DE CONFIGURAÇÃO ====================

class Config:
    """Gerencia as configurações do ambiente"""
    
    def __init__(self):
        self.ambiente = os.getenv('AMBIENTE', 'central').lower()
        self._carregar_config()
    
    def _carregar_config(self):
        """Carrega as configurações baseado no ambiente"""
        if self.ambiente == 'central':
            self.id_user = os.getenv('CENTRAL_ID_USER')
            self.username = os.getenv('CENTRAL_USER')
            self.senha = os.getenv('CENTRAL_SENHA')
            self.base_url = os.getenv('CENTRAL_BASE_URL')
        elif self.ambiente == 'cpd':
            self.id_user = os.getenv('CPD_ID_USER')
            self.username = os.getenv('CPD_USER')
            self.senha = os.getenv('CPD_SENHA')
            self.base_url = os.getenv('CPD_BASE_URL')
        else:
            raise ValueError(f"Ambiente inválido: {self.ambiente}. Use 'central' ou 'cpd'")
        
        # Valida se todas as configurações foram carregadas
        if not all([self.id_user, self.username, self.senha, self.base_url]):
            raise ValueError(f"Configurações incompletas para o ambiente '{self.ambiente}'")
    
    def get_url(self, endpoint: str) -> str:
        """Retorna a URL completa para um endpoint"""
        return f"{self.base_url}{endpoint}"


# ==================== CLASSE PRINCIPAL ====================

class RepositorioCAED:
    """Classe principal para interação com o Repositório CAED"""
    
    def __init__(self):
        self.config = Config()
        self.bearer_token = None
    
    def autenticar(self) -> str:
        """
        Autentica no sistema e retorna o token Bearer
        
        Returns:
            str: Token de autenticação
        """
        url = self.config.get_url('/gw/login/auth/login')
        payload = {
            "username": self.config.username,
            "password": self.config.senha
        }
        headers = {"Content-Type": "application/json; charset=utf-8"}
        
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            self.bearer_token = response.json().get("token")
            return self.bearer_token
        else:
            raise Exception(f"Erro na autenticação: {response.status_code} - {response.text}")
    
    def pegar_colunas(self, subprograma: str, codigo_form: str) -> List[int]:
        """
        Obtém as colunas disponíveis para um formulário
        
        Args:
            subprograma: Código do subprograma
            codigo_form: Código do formulário
            
        Returns:
            List[int]: Lista com a ordem das colunas
        """
        if not self.bearer_token:
            self.autenticar()
        
        url = self.config.get_url(
            f'/gw/formulario/formulario/download/campos-formulario/{subprograma}/{codigo_form}/055'
        )
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.bearer_token}'
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            colunas = [campo['ordem'] for campo in data['camposFormularios']]
            return colunas
        else:
            print(f'Erro ao fazer a requisição: {response.status_code}')
            return []
    
    def _criar_filtro(self, filtro_op: str, filtro_coluna: str, 
                     filtro_tamanho: str, filtro_tipo: str, 
                     filtro_valor: str) -> List[Dict]:
        """Cria o objeto de filtro para requisições"""
        if filtro_op:
            return [{
                "operador": filtro_op,
                "coluna": filtro_coluna,
                "tamanho": filtro_tamanho,
                "tipoCampo": filtro_tipo,
                "valor1": filtro_valor,
            }]
        return []
    
    def _criar_estrutura_base(self, fonte: str, subprograma: str, 
                             id_user: str) -> Dict:
        """Cria a estrutura base comum a todos os payloads"""
        return {
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
            "transferencia": False
        }
    
    def exportar_payload(self, codigo_form: str, colunas: List[int],
                        subprograma: str, fonte: str,
                        filtro_op: str = '', filtro_valor: str = '',
                        filtro_coluna: str = '', filtro_tamanho: str = '',
                        filtro_tipo: str = '') -> Dict:
        """
        Cria o payload para exportação de dados
        
        Args:
            codigo_form: Código do formulário
            colunas: Lista de colunas
            subprograma: Código do subprograma
            fonte: Código da fonte
            filtro_op: Operador do filtro (opcional)
            filtro_valor: Valor do filtro (opcional)
            filtro_coluna: Coluna do filtro (opcional)
            filtro_tamanho: Tamanho do campo filtrado (opcional)
            filtro_tipo: Tipo do campo filtrado (opcional)
            
        Returns:
            Dict: Payload completo
        """
        # Busca configuração do formulário
        config_form = getattr(FormularioConfig, codigo_form, None)
        
        if not config_form:
            # Formulário genérico (AD)
            return self._criar_payload_generico(
                codigo_form, colunas, subprograma, fonte,
                filtro_op, filtro_valor, filtro_coluna, 
                filtro_tamanho, filtro_tipo
            )
        
        # Cria estrutura base
        payload = self._criar_estrutura_base(fonte, subprograma, self.config.id_user)
        
        # Adiciona dados específicos do formulário
        payload.update({
            "fileNames": [""],
            "servico": config_form['servico'],
            "formulario": {
                "codigo": config_form['codigo'],
                "nome": config_form['nome']
            },
            "layout": config_form['layout'],
            "filtrosAvancados": self._criar_filtro(
                filtro_op, filtro_coluna, filtro_tamanho,
                filtro_tipo, filtro_valor
            ),
            "colunas": config_form['colunas']
        })
        
        return payload
    
    def _criar_payload_generico(self, codigo_form: str, colunas: List[int],
                               subprograma: str, fonte: str,
                               filtro_op: str, filtro_valor: str,
                               filtro_coluna: str, filtro_tamanho: str,
                               filtro_tipo: str) -> Dict:
        """Cria payload para formulários genéricos (AD)"""
        payload = self._criar_estrutura_base(fonte, subprograma, self.config.id_user)
        
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
            "filtrosAvancados": self._criar_filtro(
                filtro_op, filtro_coluna, filtro_tamanho,
                filtro_tipo, filtro_valor
            ),
            "colunas": colunas
        })
        
        return payload
    
    def cat_nm_campo(self, subprograma: str, codigo_form: str, 
                    campo_filtro: str) -> Tuple[Optional[int], Optional[int], Optional[str]]:
        """
        Busca informações de um campo específico
        
        Args:
            subprograma: Código do subprograma
            codigo_form: Código do formulário
            campo_filtro: Nome do campo a buscar
            
        Returns:
            Tuple: (ordem, tamanho, tipo) do campo ou (None, None, None)
        """
        if not self.bearer_token:
            self.autenticar()
        
        # Mapeia formulários para seus códigos de layout
        layout_map = {
            'L185': '185', 'L062': '185', 'L005': '005',
            'L009': '009', 'L204': '204'
        }
        
        layout_code = layout_map.get(codigo_form, '055')
        url = self.config.get_url(
            f'/gw/formulario/formulario/download/campos-formulario/'
            f'{subprograma}/{codigo_form}/{layout_code}'
        )
        
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'Authorization': f'Bearer {self.bearer_token}'
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
    
    def get_formulario_code(self, partial_name: str, subprograma: str) -> Tuple[Optional[str], str]:
        """
        Busca o código de um formulário pelo nome parcial
        
        Args:
            partial_name: Nome parcial do formulário
            subprograma: Código do subprograma
            
        Returns:
            Tuple: (código_formulário, nome_completo)
        """
        if not self.bearer_token:
            self.autenticar()
        
        url = self.config.get_url(
            f'/gw/formulario/formulario/download/formularios/'
            f'{subprograma}/AD/{self.config.id_user}'
        )
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.bearer_token}'
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            for item in data:
                if partial_name in item['nomeFormulario']:
                    return item['codigo'], item['nomeFormulario']
            return None, partial_name
        else:
            print(f"Erro ao buscar formulário: {response.status_code}")
            return None, partial_name
    
    def verificar_arquivo_disponivel(self, nome_arquivo_parcial: str,
                                     data_atual: str, total_items: int) -> Optional[str]:
        """
        Verifica se um arquivo está disponível para download
        
        Args:
            nome_arquivo_parcial: Nome parcial do arquivo
            data_atual: Data atual no formato YYYY-MM-DD
            total_items: Total de itens
            
        Returns:
            str: Nome completo do arquivo ou None
        """
        if not self.bearer_token:
            self.autenticar()
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.bearer_token}'
        }
        
        params = {
            "idGrupo": 1,
            "page": 0,
            "ultimaSemana": data_atual,
            "size": 10,
            "sort": "id,desc"
        }
        
        url = self.config.get_url('/gw/repositorio/historico')
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            for item in data.get("content", []):
                if (item["nomeArquivo"].startswith(nome_arquivo_parcial) and 
                    item["tpStatus"] == "S"):
                    return item["nomeArquivo"]
        
        return None
    
    def get_total_items(self, data_atual: str) -> Optional[int]:
        """
        Obtém o total de itens no histórico
        
        Args:
            data_atual: Data atual no formato YYYY-MM-DD
            
        Returns:
            int: Total de itens ou None
        """
        if not self.bearer_token:
            self.autenticar()
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.bearer_token}'
        }
        
        params = {
            "idGrupo": 1,
            "ultimaSemana": data_atual
        }
        
        url = self.config.get_url('/gw/repositorio/historico/totalItems')
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
    
    def baixar_dado_adm(self, formulario: str, subprograma: str, fonte: str,
                       destino: str = '', filtro_coluna: str = '',
                       filtro_op: str = '', filtro_valor: str = '') -> Optional[str]:
        """
        Baixa formulários do AD do repositório
        
        Args:
            formulario: Nome do formulário (ex: 'ESCOLA', 'TURMA', etc)
            subprograma: Código do programa
            fonte: Código da fonte
            destino: Caminho de destino (opcional)
            filtro_coluna: Coluna para filtro (opcional)
            filtro_op: Operador de filtro (opcional)
            filtro_valor: Valor do filtro (opcional)
            
        Returns:
            str: Caminho do arquivo baixado ou None
        """
        # Autentica
        if not self.bearer_token:
            self.autenticar()
        
        data_atual = datetime.now().strftime('%Y-%m-%d')
        
        # Headers
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.bearer_token}'
        }
        
        # Define o código do formulário e nome parcial
        partial_name = f'FORM_{formulario}_{subprograma}'
        colunas = ''
        
        # Mapeia formulários especiais
        form_map = {
            'USUARIO': ('L185', f'FORM_{formulario}_{subprograma}'),
            'APP_LOGISTICA': ('L062', 'APP_LOGISTICA'),
            'L005': ('L005', 'L005'),
            'L009': ('L009', 'L009'),
            'L204': ('L204', 'L204'),
            'L008': ('L008', 'L008')
        }
        
        if formulario in form_map:
            codigo_form, partial_name = form_map[formulario]
        else:
            codigo_form, partial_name = self.get_formulario_code(partial_name, subprograma)
            if not codigo_form:
                print(f"Nenhum formulário encontrado com nome de {partial_name}.")
                return None
            colunas = self.pegar_colunas(subprograma, codigo_form)
        
        # Processa filtros
        if filtro_op == 'in':
            if not isinstance(filtro_valor, list):
                filtro_valor = filtro_valor.split('|||')
            filtro_valor = '§'.join(filtro_valor)
        elif filtro_op == '=':
            filtro_valor = str(filtro_valor)
        
        if filtro_coluna:
            filtro_coluna, filtro_tamanho, filtro_tipo = self.cat_nm_campo(
                subprograma, codigo_form, filtro_coluna
            )
        else:
            filtro_tamanho = ''
            filtro_tipo = ''
        
        # Gera o payload
        payload = self.exportar_payload(
            codigo_form, colunas, subprograma, fonte,
            filtro_op, filtro_valor, filtro_coluna,
            filtro_tamanho, filtro_tipo
        )
        payload.update({"historico": False})
        
        # Solicita exportação
        url_exportacao = self.config.get_url('/gw/repositorio/download/solicitarExportacao')
        response = requests.post(url_exportacao, json=payload, headers=headers)
        
        if response.status_code != 200:
            print(f"Erro na solicitação de exportação: {response.status_code}")
            try:
                error_message = response.json().get('error', 'Erro desconhecido')
                print("Erro:", error_message)
            except ValueError:
                print("Resposta:", response.text)
            return None
        
        data = response.json()
        print(f"Solicitação de Download {partial_name.upper()} realizada com sucesso, aguarde...")
        
        nome_arquivo = data.get('nomeArquivo')
        if not nome_arquivo:
            print(f"Nome do arquivo não encontrado na resposta.")
            return None
        
        nome_arquivo_parcial = "_".join(nome_arquivo.split("_")[:-1])
        total_items = self.get_total_items(data_atual)
        
        if total_items is None:
            print(f"Erro ao obter totalItems.")
            return None
        
        # Aguarda arquivo ficar disponível
        tempo_limite = 600
        tempo_inicial = time.time()
        arquivo_disponivel = None
        
        while time.time() - tempo_inicial < tempo_limite:
            arquivo_disponivel = self.verificar_arquivo_disponivel(
                nome_arquivo_parcial, data_atual, total_items
            )
            if arquivo_disponivel:
                break
            time.sleep(5)
        
        if not arquivo_disponivel:
            print(f"Tempo limite excedido. O arquivo ainda não está disponível.")
            return None
        
        # Download do arquivo
        download_url = self.config.get_url(f'/gw/repositorio/download/arquivo/{arquivo_disponivel}')
        download_response = requests.get(download_url, headers=headers)
        
        if download_response.status_code != 200:
            print(f"Erro ao baixar o arquivo: {download_response.status_code}")
            print("Detalhes:", download_response.text)
            return None
        
        # Define nome do arquivo
        file_name = f"{arquivo_disponivel}_{partial_name[:-5].upper()}.zip".replace('FORM_', '')
        if codigo_form in ['L005', 'L009', 'L204', 'L008']:
            file_name = f"{arquivo_disponivel}_{codigo_form}.zip"
        
        # Salva arquivo
        destino_original = os.getcwd()
        if destino:
            destino_completo = os.path.join(os.getcwd(), destino)
            os.makedirs(destino_completo, exist_ok=True)
            os.chdir(destino_completo)
        
        with open(file_name, "wb") as f:
            f.write(download_response.content)
        
        print(f"Arquivo ZIP baixado com sucesso: {file_name}")
        
        # Extrai o conteúdo
        with zipfile.ZipFile(io.BytesIO(download_response.content), 'r') as zip_ref:
            zip_ref.extractall(os.getcwd())
        
        print(f"Conteúdo extraído com sucesso")
        
        # Renomeia arquivo CSV
        csv_name = file_name.replace('.zip', '.csv')
        os.rename(arquivo_disponivel + '.csv', csv_name)
        
        os.chdir(destino_original)
        
        if destino:
            return os.path.join(destino, csv_name)
        return csv_name


# ==================== FUNÇÕES AUXILIARES ====================

def base36_encode(number: int) -> str:
    """
    Codifica um número em base 36
    
    Args:
        number: Número a ser codificado
        
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


def gerar_codigo_unico(tamanho: int = 12) -> str:
    """
    Gera um código único em base 36
    
    Args:
        tamanho: Tamanho do código a ser gerado
        
    Returns:
        str: Código único gerado
    """
    unique_id = uuid.uuid4()
    unique_number = unique_id.int
    base36_str = base36_encode(unique_number)
    
    if len(base36_str) > tamanho:
        return base36_str[:tamanho]
    else:
        return base36_str.zfill(tamanho)


def cpf_validator(cpf: str) -> bool:
    """
    Valida se um CPF é válido
    
    Args:
        cpf: CPF a ser validado
        
    Returns:
        bool: True se válido, False caso contrário
    """
    cpf_ = str(cpf)
    numeros = [int(digito) for digito in cpf_ if digito.isdigit()]
    
    if len(numeros) != 11:
        return False
    
    # Valida primeiro dígito
    soma_produtos = sum(a * b for a, b in zip(numeros[0:9], range(10, 1, -1)))
    digito_esperado = (soma_produtos * 10 % 11) % 10
    if numeros[9] != digito_esperado:
        return False
    
    # Valida segundo dígito
    soma_produtos = sum(a * b for a, b in zip(numeros[0:10], range(11, 1, -1)))
    digito_esperado = (soma_produtos * 10 % 11) % 10
    if numeros[10] != digito_esperado:
        return False
    
    return True


# ==================== FUNÇÕES DE COMPATIBILIDADE ====================

# Funções mantidas para compatibilidade com código existente
def consulta_cadastro() -> pd.DataFrame:
    """
    DEPRECATED: Use a classe Config ao invés desta função
    Retorna as configurações do ambiente atual
    """
    config = Config()
    return pd.DataFrame({
        'ID_USER': [config.id_user],
        'USER': [config.username],
        'SENHA': [config.senha]
    })


def get_bearer_token(password: str, username: str, url: str) -> str:
    """
    DEPRECATED: Use repo.autenticar() ao invés desta função
    """
    repo = RepositorioCAED()
    return repo.autenticar()


# ==================== EXEMPLO DE USO ====================

# if __name__ == "__main__":
#     # Exemplo de uso
#     print("Inicializando sistema...")
    
#     # Cria instância
#     repo = RepositorioCAED()
    
#     # Autentica
#     print(f"Ambiente: {repo.config.ambiente}")
#     print("Autenticando...")
#     token = repo.autenticar()
#     print(f"Token obtido: {token[:20]}...")
    
    # Exemplo de download (comentado para não executar automaticamente)
    # caminho = repo.baixar_dado_adm(
    #     formulario='ESCOLA',
    #     subprograma='SEU_SUBPROGRAMA',
    #     fonte='SUA_FONTE',
    #     destino='downloads'
    # )
    # print(f"Arquivo baixado em: {caminho}")