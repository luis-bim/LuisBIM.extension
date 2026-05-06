# -*- coding: utf-8 -*-
import os
import clr

# Caminho da pasta onde está o arquivo (pode ser .rte ou .rvt)
template_folder = r"G:\Drives compartilhados\BIM\TEMPLATES\ARQUITETURA\TEMPLATE COMPLEMENTAR"

# Lista de possíveis nomes do arquivo
file_options = ["DETALHE-TIPICO.rte", "DETALHE-TIPICO.rvt"]

# Procura pelo arquivo na pasta, independente da extensão
template_file = None
for f in file_options:
    full_path = os.path.join(template_folder, f)
    if os.path.exists(full_path):
        template_file = f
        break

if template_file is None:
    raise Exception("Arquivo 'DETALHE-TIPICO.rte' ou 'DETALHE-TIPICO.rvt' não encontrado na pasta.")

template_full_path = os.path.join(template_folder, template_file)

# Tenta abrir o arquivo no Revit utilizando o método do pyRevit
try:
    novo_doc = __revit__.OpenAndActivateDocument(template_full_path)
except Exception as e:
    print("Erro ao abrir o arquivo: {}".format(e))
    raise
