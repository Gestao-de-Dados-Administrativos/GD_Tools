import requests
import zipfile
import io
import time
import os
import json
from datetime import datetime
import pandas as pd
import uuid

class RepoLink:
    """Classe unificada para acesso aos repositórios Central e CPD"""
    
    def __init__(self, ambiente='central'):
        """
        Inicializa a classe com o ambiente especificado.
        
        Args:
            ambiente (str): 'central' ou 'cpd'
        """
        self.ambiente = ambiente.lower()
        self.configurar_ambiente()
        self.bearer = None
        
    def configurar_ambiente(self):
        """Configura URLs e nomes de arquivos baseado no ambiente"""
        if self.ambiente == 'central':
            self.base_url = "https://repositorio.caeddigital.net"
            self.acesso_file = 'acesso.csv'
        elif self.ambiente == 'cpd':
            self.base_url = "http://10.0.10.22:41112"
            self.acesso_file = 'acesso_cpd.csv'
        else:
            raise ValueError("Ambiente deve ser 'central' ou 'cpd'")
    
    def pegar_colunas(self, subprograma, codigo_form):
        """Obtém a lista de colunas de um formulário"""
        url = f'{self.base_url}/gw/formulario/formulario/download/campos-formulario/{subprograma}/{codigo_form}/055'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.bearer}'
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            colunas = []
            
            for campo in data['camposFormularios']:
                ordem = campo['ordem']
                colunas.append(ordem)
            
            return colunas
        else:
            print(f'Erro ao fazer a requisição: {response.status_code}')
            return []
    
    def exportar_payload(self, id_user, codigo_form, colunas, subprograma, fonte, 
                        filtro_op='', filtro_valor='', filtro_coluna='', 
                        filtro_tamanho='', filtro_tipo=''):
        """Gera o payload para exportação baseado no código do formulário"""
        
        # Configuração base do filtro
        if filtro_op != '':
            filtro = [{
                "operador": filtro_op,  
                "coluna": filtro_coluna, 
                "tamanho": filtro_tamanho,
                "tipoCampo": filtro_tipo,
                "valor1": filtro_valor,
            }]
        else:
            filtro = []
        
        # Configurações específicas para cada tipo de formulário
        formularios_config = {
            'L185': {
                "servico": {"id": 15, "nome": "US"},
                "formulario": {"codigo": "L185", "nome": "Leiaute de Usuário - v3"},
                "layout": {"codigo": 185, "id": 170, "idServico": 15, "nomeServico": "US", "referenciaServico": "REPOSITÓRIO DE USUÁRIOS"},
                "colunas": list(range(1, 72))
            },
            'L062': {
                "servico": {"id": 15, "nome": "US"},
                "formulario": {"codigo": "L062", "nome": "Leiaute de Controle de usuários e pontos de entrega."},
                "layout": {"codigo": "062", "id": 190, "idServico": 15, "nomeServico": "US", "referenciaServico": "REPOSITÓRIO DE USUÁRIOS"},
                "colunas": list(range(1, 16))
            },
            'L204': {
                "servico": {"id": 6, "nome": "IN"},
                "formulario": {"codigo": "L204", "nome": "Leiaute de Instrumento"},
                "layout": {"codigo": "204", "id": 173, "idServico": 6, "nomeServico": "IN", "referenciaServico": "REPOSITÓRIO DE INSTRUMENTOS"},
                "colunas": list(range(1, 42))
            },
            'L005': {
                "servico": {"id": 1, "nome": "DA"},
                "formulario": {"codigo": "L005", "nome": "Leiaute de base planejada"},
                "layout": {"codigo": "005", "id": 5, "idServico": 1, "nomeServico": "DA", "referenciaServico": "REPOSITÓRIO DE DADOS"},
                "colunas": list(range(1, 117)),
                "fileNames": ["", ""]
            },
            'L009': {
                "servico": {"id": 3, "nome": "SU"},
                "formulario": {"codigo": "L009", "nome": "Leiaute de sujeito"},
                "layout": {"codigo": "009", "id": 9, "idServico": 3, "nomeServico": "SU", "referenciaServico": "REPOSITÓRIO DE SUJEITOS"},
                "colunas": list(range(1, 98)),
                "fileNames": ["", ""]
            },
            'L008': {
                "servico": {"id": 1, "nome": "DA"},
                "formulario": {"codigo": "L008", "nome": "Leiaute de decodificação"},
                "layout": {"codigo": "008", "id": 8, "idServico": 1, "nomeServico": "DA", "referenciaServico": "REPOSITÓRIO DE DADOS"},
                "colunas": list(range(1, 227)),
                "fileNames": ["", ""]
            },
            'L021': {
                "servico": {"id": 10, "nome": "SO"},
                "formulario": {"codigo": "L021", "nome": "Leiaute de solicitação de verificação"},
                "layout": {"codigo": "021", "id": 17, "idServico": 10, "nomeServico": "SO", "referenciaServico": "REPOSITÓRIO DE SOLICITAÇÃO"},
                "colunas": list(range(1, 27)),
                "fileNames": ["", ""]
            },
            'L010': {
                "servico": {"id": 10, "nome": "SO"},
                "formulario": {"codigo": "L010", "nome": "Leiaute de solicitação de recodificação"},
                "layout": {"codigo": "010", "id": 148, "idServico": 10, "nomeServico": "SO", "referenciaServico": "REPOSITÓRIO DE SOLICITAÇÃO"},
                "colunas": list(range(1, 27)),
                "fileNames": ["", ""]
            }
        }
        
        # Configuração padrão para formulários AD
        config_padrao = {
            "servico": {"id": 13, "nome": "AD", "referenciaServico": "REPOSITÓRIO DE DADOS ADMINISTRATIVOS", "instanciaServico": "REPOSITORIO_DADO_ADMINISTRATIVO"},
            "formulario": {"codigo": codigo_form},
            "layout": {"codigo": "055", "nome": "Leiaute de dado administrativo", "id": 125, "idServico": 13, "nomeServico": "AD", "referenciaServico": "REPOSITORIO_DADOS_ADMINISTRATIVOS"},
            "colunas": colunas,
            "fileNames": [""]
        }
        
        # Seleciona a configuração apropriada
        if codigo_form in formularios_config:
            config = formularios_config[codigo_form]
            file_names = config.get("fileNames", [""])
        else:
            config = config_padrao
            file_names = [""]
        
        # Remove 'fileNames' do config para não duplicar
        config = {k: v for k, v in config.items() if k != "fileNames"}
        
        # Monta o payload completo
        payload = {
            "fileNames": file_names,
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
                "grupoSelecionado": {"id": 1, "descricao": "ADM", "ativo": True}
            },
            "transferencia": False,
            "filtrosAvancados": filtro
        }
        
        # Adiciona as configurações específicas
        payload.update(config)
        
        return payload
    
    def get_bearer_token(self, password, username):
        """Obtém token de autenticação"""
        url = f"{self.base_url}/gw/login/auth/login"
        payload = {"username": username, "password": password}
        headers = {"Content-Type": "application/json; charset=utf-8"}
        
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            token = response.json().get("token")
            return token
        else:
            raise Exception(f"Error: {response.status_code}, {response.text}")
    
    def get_formulario_code(self, subprograma, id_user, partial_name):
        """Obtém o código do formulário pelo nome parcial"""
        url = f'{self.base_url}/gw/formulario/formulario/download/formularios/{subprograma}/AD/{id_user}'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.bearer}'
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
    
    def verificar_arquivo_disponivel(self, nome_arquivo_parcial, data_atual, total_items):
        """Verifica se o arquivo está disponível para download"""
        historico_params = {
            "idGrupo": 1,
            "ultimaSemana": data_atual, 
            "totalItems": total_items,
            "page": 0,
            "size": 10,
            "sort": "id,desc"
        }
        historico_url = f"{self.base_url}/gw/repositorio/historico"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.bearer}'
        }
        
        response = requests.get(historico_url, headers=headers, params=historico_params)
        
        if response.status_code == 200:
            data = response.json()
            for item in data.get("content", []):
                if item["nomeArquivo"].startswith(nome_arquivo_parcial) and item["tpStatus"] == "S":
                    return item["nomeArquivo"]
        return None
    
    def get_total_items(self, data_atual):
        """Obtém o total de itens no histórico"""
        total_items_url = f"{self.base_url}/gw/repositorio/historico/totalItems"
        params = {"idGrupo": 1, "ultimaSemana": data_atual}
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.bearer}'
        }
        
        response = requests.get(total_items_url, headers=headers, params=params)
        if response.status_code == 200:
            try:
                return int(response.text)
            except ValueError:
                print("Erro ao converter a resposta para inteiro.")
                return None
        else:
            print(f"Erro ao obter totalItems: {response.status_code}")
            return None
    
    def cat_nm_campo(self, subprograma, codigo_form, campo_filtro):
        """Obtém informações de um campo específico"""
        # Define a URL base baseada no código do formulário
        base_urls = {
            'L185': '185',
            'L062': '185',
            'L005': '005',
            'L009': '009',
            'L204': '204',
            'L008': '008',
            'L021': '021',
            'L010': '010'
        }
        
        layout_code = base_urls.get(codigo_form, '055')
        url = f'{self.base_url}/gw/formulario/formulario/download/campos-formulario/{subprograma}/{codigo_form}/{layout_code}'
        
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'Authorization': f'Bearer {self.bearer}'
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
    
    def baixa_dado_adm(self, formulario, subprograma, fonte, destino='', 
                      filtro_coluna='', filtro_op='', filtro_valor=''):
        """
        Baixa formulários do repositório
        
        Args:
            formulario (str): Nome do formulário a ser baixado
            subprograma (str): Código de programa de origem da avaliação
            fonte (str): Código fonte do programa
            destino (str): Caminho onde fazer o download
            filtro_coluna (str): Coluna para aplicar filtro
            filtro_op (str): Tipo de filtro ('in', '=', etc.)
            filtro_valor (str/list): Valor(es) para filtro
        """
        # Carrega credenciais
        caminho_arquivo = os.path.abspath(__file__)
        caminho_diretorio = os.path.dirname(caminho_arquivo)
        cadastro = pd.read_csv(os.path.join(caminho_diretorio, self.acesso_file))
        
        id_user = str(cadastro.ID_USER.values[0])
        password = cadastro.SENHA.values[0]
        username = cadastro.USER.values[0]
        
        # Obtém token
        self.bearer = self.get_bearer_token(password, username)
        
        data_atual = datetime.now().strftime('%Y-%m-%d')
        
        # URLs
        solicitar_exportacao_url = f"{self.base_url}/gw/repositorio/download/solicitarExportacao"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.bearer}'
        }
        
        # Mapeamento de formulários especiais
        formularios_especiais = {
            'USUARIO': ('L185', f'FORM_{formulario}_{subprograma}', ''),
            'APP_LOGISTICA': ('L062', 'APP_LOGISTICA', ''),
            'L005': ('L005', 'L005', ''),
            'L009': ('L009', 'L009', ''),
            'L204': ('L204', 'L204', ''),
            'L008': ('L008', 'L008', ''),
            'L021': ('L021', 'L021', ''),
            'L010': ('L010', 'L010', '')
        }
        
        # Define código, nome parcial e colunas
        if formulario in formularios_especiais:
            codigo_form, partial_name, colunas = formularios_especiais[formulario]
        else:
            partial_name = f'FORM_{formulario}_{subprograma}'
            codigo_form, partial_name = self.get_formulario_code(subprograma, id_user, partial_name)
            if not codigo_form:
                print(f"Nenhum formulário encontrado com nome de {partial_name}.")
                return 0
            colunas = self.pegar_colunas(subprograma, codigo_form)
        
        # Processa filtros
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
        
        if filtro_coluna != '':
            filtro_coluna, filtro_tamanho, filtro_tipo = self.cat_nm_campo(subprograma, codigo_form, filtro_coluna)
        else:
            filtro_tamanho = ''
            filtro_tipo = ''
        
        # Gera e envia payload
        payload = self.exportar_payload(id_user, codigo_form, colunas, subprograma, fonte, 
                                       filtro_op, filtro_valor, filtro_coluna, filtro_tamanho, filtro_tipo)
        payload.update({"historico": False})
        
        response = requests.post(solicitar_exportacao_url, json=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"Solicitação de Download {partial_name.upper()} realizada com sucesso, aguarde...")
            
            nome_arquivo = data.get('nomeArquivo')
            if nome_arquivo:
                nome_arquivo_parcial = "_".join(nome_arquivo.split("_")[:-1])
                total_items = self.get_total_items(data_atual)
                
                if total_items is not None:
                    # Aguarda arquivo ficar disponível
                    tempo_limite = 600
                    tempo_inicial = time.time()
                    arquivo_disponivel = None
                    
                    while time.time() - tempo_inicial < tempo_limite:
                        arquivo_disponivel = self.verificar_arquivo_disponivel(nome_arquivo_parcial, data_atual, total_items)
                        if arquivo_disponivel:
                            break
                        time.sleep(5)
                    
                    if arquivo_disponivel:
                        # Faz download do arquivo
                        download_url = f"{self.base_url}/gw/repositorio/download/arquivo/{arquivo_disponivel}"
                        download_response = requests.get(download_url, headers=headers)
                        
                        if download_response.status_code == 200:
                            # Define nome do arquivo
                            mapeamento_nomes = {
                                'L005': f"{arquivo_disponivel}_L005.zip",
                                'L009': f"{arquivo_disponivel}_L009.zip",
                                'L204': f"{arquivo_disponivel}_L204.zip",
                                'L008': f"{arquivo_disponivel}_L008.zip",
                                'L021': f"{arquivo_disponivel}_L021.zip",
                                'L010': f"{arquivo_disponivel}_L010.zip"
                            }
                            
                            file_name = mapeamento_nomes.get(codigo_form, 
                                                           f"{arquivo_disponivel}_{partial_name[:-5].upper()}.zip".replace('FORM_', ''))
                            
                            # Salva arquivo
                            destino_0 = os.getcwd()
                            if destino:
                                os.makedirs(destino, exist_ok=True)
                                destino_path = os.path.join(os.getcwd(), destino)
                                os.chdir(destino_path)
                            
                            with open(file_name, "wb") as f:
                                f.write(download_response.content)
                            print(f"Arquivo ZIP baixado com sucesso: {file_name}")
                            
                            # Extrai conteúdo
                            with zipfile.ZipFile(io.BytesIO(download_response.content), 'r') as zip_ref:
                                zip_ref.extractall(os.getcwd())
                            print(f"Conteúdo do arquivo ZIP extraído com sucesso: {file_name}")
                            
                            # Renomeia arquivo CSV
                            os.rename(arquivo_disponivel + '.csv', file_name.replace('.zip', '.csv'))
                            os.chdir(destino_0)
                            
                            return os.path.join(destino if destino else '', file_name.replace('.zip', '.csv'))
                        else:
                            print(f"Erro ao baixar o arquivo ZIP: {download_response.status_code}")
                            print("Detalhes:", download_response.text)
                    else:
                        print("Tempo limite excedido. Arquivo não disponível.")
                else:
                    print("Erro ao obter totalItems.")
            else:
                print("Nome do arquivo não encontrado na resposta.")
        else:
            print(f"Erro na solicitação: {response.status_code}")
            try:
                error_message = response.json().get('error', 'Nenhuma mensagem de erro')
                print("Erro:", error_message)
            except ValueError:
                print("Resposta:", response.text)
        
        return None
    
    def consulta_cadastro(self):
        """Consulta o cadastro de usuário"""
        caminho_arquivo = os.path.abspath(__file__)
        caminho_diretorio = os.path.dirname(caminho_arquivo)
        return pd.read_csv(os.path.join(caminho_diretorio, self.acesso_file))
    
    def edita_cadastro(self, novo_cadastro):
        """Edita o cadastro de usuário"""
        caminho_arquivo = os.path.abspath(__file__)
        caminho_diretorio = os.path.dirname(caminho_arquivo)
        arquivo_acesso = os.path.join(caminho_diretorio, self.acesso_file)
        
        old = pd.read_csv(arquivo_acesso)
        
        if list(old.columns) != list(novo_cadastro.columns):
            return 'Erro! Colunas do novo cadastro inválidas. Conferir cadastro.'
        
        novo_cadastro.to_csv(arquivo_acesso, index=False)
        return 'Alteração de cadastro realizada com sucesso!'
    
    @staticmethod
    def base36_encode(number):
        """Codifica um número em base 36"""
        alphabet = '0123456789abcdefghijklmnopqrstuvwxyz'
        if number == 0:
            return alphabet[0]
        base36 = []
        while number:
            number, i = divmod(number, 36)
            base36.append(alphabet[i])
        return ''.join(reversed(base36))
    
    @staticmethod
    def gerar_codigo_unico(tamanho=12):
        """Gera um código único em base 36"""
        unique_id = uuid.uuid4()
        unique_number = unique_id.int
        base36_str = RepoLink.base36_encode(unique_number)
        
        if len(base36_str) > tamanho:
            return base36_str[:tamanho]
        else:
            return base36_str.zfill(tamanho)
    
    @staticmethod
    def cpf_validator(cpf):
        """Valida se um CPF é válido"""
        cpf_str = str(cpf)
        numeros = [int(digito) for digito in cpf_str if digito.isdigit()]
        
        if len(numeros) != 11:
            return False
        
        # Valida primeiro dígito verificador
        soma = sum(a * b for a, b in zip(numeros[0:9], range(10, 1, -1)))
        digito_esperado = (soma * 10 % 11) % 10
        if numeros[9] != digito_esperado:
            return False
        
        # Valida segundo dígito verificador
        soma = sum(a * b for a, b in zip(numeros[0:10], range(11, 1, -1)))
        digito_esperado = (soma * 10 % 11) % 10
        if numeros[10] != digito_esperado:
            return False
        
        return True
    
    def generate_payload(self, nome, email, cpf, dc_senha, agregados, layout, key, fonte, programa, fl_master='0', op='I'):
        """EM CONSTRUÇÃO - Gera payload para cadastro de usuários"""
        return "EM CONSTRUÇÃO"
    
    def cadastro_usuarios(self, url, key, fonte, programa, df, op):
        """EM CONSTRUÇÃO - Cadastra usuários em lote"""
        return "EM CONSTRUÇÃO"


# Funções de conveniência para compatibilidade com código existente
def baixa_dado_adm(formulario, subprograma, fonte, destino='', filtro_coluna='', filtro_op='', filtro_valor='', ambiente='central'):
    """
    Função de conveniência para compatibilidade com código existente
    
    Args:
        ambiente (str): 'central' ou 'cpd'
    """
    repo = RepoLink(ambiente=ambiente)
    return repo.baixa_dado_adm(formulario, subprograma, fonte, destino, filtro_coluna, filtro_op, filtro_valor)

def consulta_cadastro(ambiente='central'):
    """Consulta cadastro do ambiente especificado"""
    repo = RepoLink(ambiente=ambiente)
    return repo.consulta_cadastro()

def edita_cadastro(novo_cadastro, ambiente='central'):
    """Edita cadastro do ambiente especificado"""
    repo = RepoLink(ambiente=ambiente)
    return repo.edita_cadastro(novo_cadastro)

def cpf_validator(cpf):
    """Valida CPF (função estática)"""
    return RepoLink.cpf_validator(cpf)

def gerar_codigo_unico(tamanho=12):
    """Gera código único (função estática)"""
    return RepoLink.gerar_codigo_unico(tamanho)