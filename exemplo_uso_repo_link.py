"""
Exemplos de uso do repo_link.py
"""

from repo_link import baixa_dado_adm, cpf_validator, gerar_codigo_unico

def exemplo_basico():
    """Exemplo básico de download"""
    print("=== Exemplo Básico ===")

    # Baixa formulário ESCOLA usando ambiente padrão do .env
    caminho = baixa_dado_adm(
        formulario='ESCOLA',
        subprograma='2024',
        fonte='SP'
    )

    if caminho:
        print(f"Arquivo baixado em: {caminho}")
    else:
        print("Erro ao baixar arquivo")


def exemplo_com_ambiente():
    """Exemplo especificando ambiente"""
    print("\n=== Exemplo com Ambiente Específico ===")

    # Baixa do ambiente CENTRAL
    caminho = baixa_dado_adm(
        formulario='TURMA',
        subprograma='2024',
        fonte='SP',
        ambiente='CENTRAL'
    )

    if caminho:
        print(f"Arquivo baixado do CENTRAL em: {caminho}")


def exemplo_com_filtro():
    """Exemplo com filtro"""
    print("\n=== Exemplo com Filtro ===")

    # Filtro simples (=)
    caminho = baixa_dado_adm(
        formulario='ESCOLA',
        subprograma='2024',
        fonte='SP',
        filtro_coluna='CD_MUNICIPIO',
        filtro_op='=',
        filtro_valor='3550308'  # São Paulo
    )

    if caminho:
        print(f"Arquivo filtrado baixado em: {caminho}")


def exemplo_filtro_multiplo():
    """Exemplo com filtro múltiplo (in)"""
    print("\n=== Exemplo com Filtro Múltiplo ===")

    # Filtro com múltiplos valores
    caminho = baixa_dado_adm(
        formulario='ESCOLA',
        subprograma='2024',
        fonte='SP',
        filtro_coluna='CD_MUNICIPIO',
        filtro_op='in',
        filtro_valor=['3550308', '3304557', '2927408']  # SP, RJ, Salvador
    )

    if caminho:
        print(f"Arquivo com filtro múltiplo baixado em: {caminho}")


def exemplo_com_destino():
    """Exemplo especificando pasta de destino"""
    print("\n=== Exemplo com Destino ===")

    caminho = baixa_dado_adm(
        formulario='ESCOLA',
        subprograma='2024',
        fonte='SP',
        destino='dados_2024/escolas'
    )

    if caminho:
        print(f"Arquivo baixado em pasta específica: {caminho}")


def exemplo_formularios_especiais():
    """Exemplo de download de formulários especiais"""
    print("\n=== Exemplo de Formulários Especiais ===")

    # Download de usuários
    caminho_usuarios = baixa_dado_adm(
        formulario='USUARIO',
        subprograma='2024',
        fonte='SP'
    )

    # Download de sujeitos
    caminho_sujeitos = baixa_dado_adm(
        formulario='L009',
        subprograma='2024',
        fonte='SP'
    )

    print(f"Usuários: {caminho_usuarios}")
    print(f"Sujeitos: {caminho_sujeitos}")


def exemplo_funcoes_auxiliares():
    """Exemplo de funções auxiliares"""
    print("\n=== Funções Auxiliares ===")

    # Validar CPF
    cpf = '12345678901'
    if cpf_validator(cpf):
        print(f"CPF {cpf} é válido")
    else:
        print(f"CPF {cpf} é inválido")

    # Gerar código único
    codigo = gerar_codigo_unico(tamanho=12)
    print(f"Código único gerado: {codigo}")


def exemplo_completo():
    """Exemplo completo com todos os parâmetros"""
    print("\n=== Exemplo Completo ===")

    caminho = baixa_dado_adm(
        formulario='TURMA',
        subprograma='2024',
        fonte='SP',
        destino='dados_turmas',
        filtro_coluna='CD_ESCOLA',
        filtro_op='in',
        filtro_valor=['001', '002', '003'],
        ambiente='CENTRAL'
    )

    if caminho:
        print(f"Download completo realizado: {caminho}")

        # Processar arquivo baixado
        import pandas as pd
        df = pd.read_csv(caminho, sep=';', encoding='latin-1')
        print(f"Total de registros: {len(df)}")
        print(f"Colunas: {', '.join(df.columns)}")


if __name__ == '__main__':
    print("Exemplos de uso do repo_link.py")
    print("=" * 50)
    print("\nNOTA: Certifique-se de que o arquivo .env está configurado!")
    print("=" * 50)

    # Descomente o exemplo que deseja executar

    # exemplo_basico()
    # exemplo_com_ambiente()
    # exemplo_com_filtro()
    # exemplo_filtro_multiplo()
    # exemplo_com_destino()
    # exemplo_formularios_especiais()
    # exemplo_funcoes_auxiliares()
    # exemplo_completo()

    print("\nPara executar os exemplos, descomente a função desejada no código.")
