# -*- coding: utf-8 -*-
import os
import re
import clr

# ==============================================================================
# BLOCO DE CONFIGURAÇÃO DE CAMINHOS
# ==============================================================================

# Defina aqui a pasta onde o script deve buscar os arquivos
TARGET_FOLDER = r"G:\Drives compartilhados\BIM\TEMPLATES\ARQUITETURA"

# Se precisar de um log ou pasta secundária no futuro, adicione aqui:
# LOG_PATH = r"C:\Caminho\Log.txt"

# ==============================================================================
# BLOCO DE REGRAS DE NOMENCLATURA (REGEX)
# ==============================================================================

# 1. Prefixo fixo que o arquivo deve ter
FILE_PREFIX = r"ARQUITETURA_TEMPLATE"

# 2. Extensões permitidas (separadas por pipe |)
ALLOWED_EXTENSIONS = r"rte|rvt"

# 3. Padrão para encontrar o número da versão/edição
# O (\d+) captura apenas números inteiros. 
# O (?!\.\d) impede que ele pegue arquivos de backup do Revit (.0001.rvt)
REGEX_PATTERN = r"^" + FILE_PREFIX + r"(\d+)\.(" + ALLOWED_EXTENSIONS + r")$"

# Compilação da regra (ignore_case garante que .RTE ou .rte funcionem)
FILE_REGEX = re.compile(REGEX_PATTERN, re.IGNORECASE)

# ==============================================================================
# LÓGICA DE FILTRAGEM E BUSCA
# ==============================================================================

def get_latest_file(folder, regex):
    """Varre a pasta e retorna o caminho do arquivo com a maior numeração."""
    if not os.path.exists(folder):
        return None, "O caminho especificado não existe: {}".format(folder)

    files = os.listdir(folder)
    highest_version = -1
    best_match = None

    for f in files:
        match = regex.match(f)
        if match:
            # Pegamos o grupo (1) da regex, que é a nossa numeração (\d+)
            current_version = int(match.group(1))
            
            if current_version > highest_version:
                highest_version = current_version
                best_match = f
    
    if best_match:
        return os.path.join(folder, best_match), None
    return None, "Nenhum arquivo compatível com a regra '{}' foi encontrado.".format(FILE_PREFIX)

# ==============================================================================
# EXECUÇÃO NO REVIT
# ==============================================================================

def main():
    # 1. Busca o arquivo seguindo os blocos de configuração acima
    full_path, error = get_latest_file(TARGET_FOLDER, FILE_REGEX)

    if error:
        print("ERRO DE BUSCA: {}".format(error))
        return

    # 2. Tenta abrir no Revit
    try:
        print("Abrindo versão mais recente: {}".format(os.path.basename(full_path)))
        __revit__.OpenAndActivateDocument(full_path)
    except Exception as e:
        print("ERRO AO ABRIR NO REVIT: {}".format(e))

if __name__ == "__main__":
    main()