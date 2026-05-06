# -*- coding: utf-8 -*-
import os
import clr
import datetime

# Caminho da pasta onde está o template do Revit (.rte ou .rvt)
template_folder = r"G:\Drives compartilhados\BIM\TEMPLATES\ARQUITETURA\TEMPLATE COMPLEMENTAR"
# Lista de possíveis nomes de arquivo
file_options = ["ACABAMENTO-PISO.rte", "ACABAMENTO-PISO.rvt"]

# Variável para armazenar o nome do arquivo encontrado
template_file = None

# Verifica a existência dos arquivos na pasta
for f in file_options:
    full_path = os.path.join(template_folder, f)
    if os.path.exists(full_path):
        template_file = f
        break

if template_file is None:
    raise Exception("Nenhum arquivo 'ACABAMENTO-PISO.rte' ou 'ACABAMENTO-PISO.rvt' encontrado na pasta.")

template_full_path = os.path.join(template_folder, template_file)

# Captura o nome do documento que estava ativo antes de abrir o novo arquivo
try:
    if __revit__.ActiveUIDocument is not None:
        doc_ativo_nome = __revit__.ActiveUIDocument.Document.Title
    else:
        doc_ativo_nome = "Nenhum documento ativo"
except Exception as e:
    doc_ativo_nome = "Erro ao obter documento ativo"

# Tenta abrir o arquivo template no Revit utilizando o método do pyRevit
try:
    novo_doc = __revit__.OpenAndActivateDocument(template_full_path)
    
    # Obtém o ID da máquina e a data/hora atual
    machine_id = os.environ.get('COMPUTERNAME', 'UNKNOWN')
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Cria a linha de log com os campos separados por " --- "
    log_line = u"{0} --- {1} --- {2}\n".format(doc_ativo_nome, machine_id, timestamp)
    
    # Caminho do arquivo de log (arquivo: "abri revestimento piso.txt")
    log_file_path = r"G:\Drives compartilhados\BIM\AUTOMACAO\LOGS\pyRevit\abri revestimento piso.txt"
    try:
        with open(log_file_path, "a") as log_file:
            log_file.write(log_line)
    except Exception as log_e:
        print("Erro ao escrever no log: {}".format(log_e))
        
except Exception as e:
    print("Erro ao abrir o arquivo: {}".format(e))
    raise
