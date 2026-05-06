# -*- coding: utf-8 -*-
import os
import re
import datetime

# ==============================================================================
# CONFIGURAÇÕES DE CAMINHOS (MODIFIQUE AQUI)
# ==============================================================================

# 1. Caminho da pasta onde os arquivos estão armazenados
FOLDER_PATH = r"C:\CAMINHO\PARA\SUA\PASTA\AQUI"

# 2. Caminho do arquivo de log (descomente as linhas de log abaixo para usar)
LOG_FILE_PATH = r"C:\CAMINHO\PARA\SEU\LOG\log_uso.txt"

# ==============================================================================
# REGRAS DE NOMENCLATURA E VERSÃO (MODIFIQUE AQUI)
# ==============================================================================

# 3. Prefixo fixo do nome do arquivo (ex: "PROJETO_PADRAO_")
FILE_PREFIX = r"NOME - TODAS AS FOLHAS_V"

# 4. Regex completa para identificar o arquivo:
# Esta regra busca o prefixo + dígitos da versão + evita backups (.0001.rvt)
# Se o padrão mudar drasticamente, altere esta linha:
FILE_PATTERN = re.compile(r"^" + FILE_PREFIX + r"(\d+)(?!\.\d)(?:\.rvt)?$", re.IGNORECASE)

# 5. Como identificar a versão dentro do nome do arquivo para ordenação:
# Se a versão for "V01", a regra busca o que vem após o "V"
VERSION_IDENTIFIER = r"V(\d+)"

# ==============================================================================
# LÓGICA DO SCRIPT (NÃO PRECISA MEXER SE AS REGRAS ACIMA ESTIVEREM CORRETAS)
# ==============================================================================

def extrair_versao(nome_arquivo):
    """Extrai o número da versão para garantir que pegaremos o arquivo mais recente."""
    match = re.search(VERSION_IDENTIFIER, nome_arquivo)
    return int(match.group(1)) if match else 0

def executar():
    # Validação de pasta
    if not os.path.exists(FOLDER_PATH):
        print("ERRO: O caminho especificado não existe: {}".format(FOLDER_PATH))
        return

    arquivos = os.listdir(FOLDER_PATH)
    
    # Filtra arquivos conforme a REGEX definida no bloco 4
    arquivos_validos = [a for a in arquivos if FILE_PATTERN.match(a)]

    if not arquivos_validos:
        print("Nenhum arquivo correspondente ao padrão '{}' encontrado.".format(FILE_PREFIX))
        return

    # Ordena para pegar a versão mais alta (V10 > V09)
    arquivos_validos.sort(key=extrair_versao, reverse=True)
    arquivo_escolhido = arquivos_validos[0]
    caminho_completo = os.path.join(FOLDER_PATH, arquivo_escolhido)

    print("Arquivo mais recente encontrado: {}".format(arquivo_escolhido))

    # --- Interação com o Revit ---
    try:
        # Captura o nome do documento ativo antes da troca
        if __revit__.ActiveUIDocument:
            doc_antigo = __revit__.ActiveUIDocument.Document.Title
        else:
            doc_antigo = "Nenhum documento ativo"

        # Abre e Ativa o novo arquivo
        __revit__.OpenAndActivateDocument(caminho_completo)
        
        # --- Log de Uso ---
        machine_id = os.environ.get('COMPUTERNAME', 'UNKNOWN')
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = u"De: {0} --- Para: {1} --- User: {2} --- Data: {3}\n".format(
            doc_antigo, arquivo_escolhido, machine_id, timestamp
        )

        # Descomente abaixo se quiser salvar o log em arquivo
        # with open(LOG_FILE_PATH, "a") as f:
        #     f.write(log_line)

    except Exception as e:
        print("Erro ao processar no Revit: {}".format(e))

if __name__ == "__main__":
    executar()