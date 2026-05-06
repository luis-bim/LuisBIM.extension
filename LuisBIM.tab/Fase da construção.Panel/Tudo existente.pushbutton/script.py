# -*- coding: utf-8 -*-
import clr
import sys

# Referências à API do Revit UI e DB
clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInParameter,
    Phase,
    Transaction
)
from Autodesk.Revit.UI import TaskDialog, TaskDialogCommonButtons, TaskDialogResult

# 0. Pop-up de confirmação
res = TaskDialog.Show(
    "Confirmação",
    "Esse comando irá mudar a fase da construção de TODO seu projeto para \"Existente\", é uma decisão muito séria.\n\nDeseja continuar?",
    TaskDialogCommonButtons.Yes | TaskDialogCommonButtons.No
)
if res != TaskDialogResult.Yes:
    sys.exit()  # Sai sem fazer nada se o usuário não confirmar

# Obter o documento ativo
doc = __revit__.ActiveUIDocument.Document

# 1. Encontrar a fase chamada "Existente"
phase_existente = None
for ph in FilteredElementCollector(doc).OfClass(Phase):
    if ph.Name.lower() == "existente":
        phase_existente = ph
        break

if phase_existente is None:
    TaskDialog.Show("Erro", "Fase 'Existente' não encontrada no documento.")
    sys.exit()

# 2. Iniciar transação para alterar a fase de criação de todos os elementos
t = Transaction(doc, "Definir fase de criação para Existente")
t.Start()

# 3. Percorrer todas as instâncias do projeto e alterar PHASE_CREATED
elements = FilteredElementCollector(doc).WhereElementIsNotElementType().ToElements()
for elem in elements:
    param = elem.get_Parameter(BuiltInParameter.PHASE_CREATED)
    if param and not param.IsReadOnly:
        param.Set(phase_existente.Id)

t.Commit()

# 4. Aviso de conclusão
TaskDialog.Show("Concluído", "A fase de criação de todos os elementos foi atualizada para 'Existente'.")
