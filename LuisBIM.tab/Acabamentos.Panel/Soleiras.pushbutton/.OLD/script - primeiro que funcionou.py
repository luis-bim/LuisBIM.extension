# -*- coding: utf-8 -*-
# pylint: disable=E0401,W0703,C0103,W0613

# --- SEÇÃO 1: IMPORTAÇÕES E REFERÊNCIAS (BASEADO NO SEU SCRIPT) ---
import clr
import System

# Referências .NET para UI
clr.AddReference("PresentationFramework")
clr.AddReference("PresentationCore")

# Referências da API do Revit
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
import Autodesk
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import TaskDialog
from Autodesk.Revit.UI.Selection import ISelectionFilter, ObjectType
from Autodesk.Revit.Exceptions import OperationCanceledException

# Imports do .NET para as janelas WPF (mantido do script de soleiras)
from System.Windows import Window, Thickness, WindowStartupLocation
from System.Windows.Controls import Button, TextBlock, StackPanel, Grid
from System.Windows.Media import Brushes

# --- SEÇÃO 2: FUNÇÕES E CLASSES ---

# --- Funções de Pop-up (WPF) ---
def show_confirmation_popup():
    popup = Window(); popup.Title = "Atenção!"; popup.Width = 450; popup.Height = 220; popup.WindowStartupLocation = WindowStartupLocation.CenterScreen; popup.Background = Brushes.White; popup.Topmost = True
    panel = StackPanel(); panel.Margin = Thickness(15)
    message_text = TextBlock(); message_text.Text = "Caso ja exista soleira em alguma porta selecionada esse processo irá criar outra idêntica, causando erros de quantitativos.\n\nDeseja prosseguir?"; message_text.TextWrapping = System.Windows.TextWrapping.Wrap; message_text.Foreground = Brushes.Black; message_text.Margin = Thickness(0, 0, 0, 20)
    button_grid = Grid(); col1 = System.Windows.Controls.ColumnDefinition(); col2 = System.Windows.Controls.ColumnDefinition(); button_grid.ColumnDefinitions.Add(col1); button_grid.ColumnDefinitions.Add(col2)
    yes_button = Button(); yes_button.Content = "SIM"; yes_button.Background = Brushes.DodgerBlue; yes_button.Foreground = Brushes.White; yes_button.Margin = Thickness(5); yes_button.Height = 30
    def yes_click(sender, e): popup.DialogResult = True; popup.Close()
    yes_button.Click += yes_click; Grid.SetColumn(yes_button, 0)
    no_button = Button(); no_button.Content = "NÃO"; no_button.Background = Brushes.DodgerBlue; no_button.Foreground = Brushes.White; no_button.Margin = Thickness(5); no_button.Height = 30
    def no_click(sender, e): popup.DialogResult = False; popup.Close()
    no_button.Click += no_click; Grid.SetColumn(no_button, 1)
    button_grid.Children.Add(yes_button); button_grid.Children.Add(no_button); panel.Children.Add(message_text); panel.Children.Add(button_grid); popup.Content = panel
    return popup.ShowDialog()

def show_generic_popup(title, message):
    if not message: return
    TaskDialog.Show(title, message)

# --- Filtro de Seleção (Estrutura idêntica ao seu script de ambientes) ---
TARGET_DOOR_FAMILY_NAME = "ARQ-PORT-MAD-PORTA DE GIRO 1 FOLHA EM MADEIRA PINTADA"

class TargetDoorSelectionFilter(ISelectionFilter):
    def AllowElement(self, elem):
        if isinstance(elem, FamilyInstance) and elem.Category and elem.Category.Id == ElementId(BuiltInCategory.OST_Doors):
            door_type = doc.GetElement(elem.GetTypeId())
            if door_type and door_type.Family.Name == TARGET_DOOR_FAMILY_NAME:
                return True
        return False
        
    def AllowReference(self, reference, position):
        return False

# --- SEÇÃO 3: LÓGICA PRINCIPAL ---
try:
    # Acesso ao Revit (idêntico ao seu script)
    doc = __revit__.ActiveUIDocument.Document
    uidoc = __revit__.ActiveUIDocument

    # Seleção interativa (idêntica ao seu script)
    door_filter = TargetDoorSelectionFilter()
    prompt = "Selecione as portas da família '{}' para locar as soleiras".format(TARGET_DOOR_FAMILY_NAME)
    selected_references = uidoc.Selection.PickObjects(ObjectType.Element, door_filter, prompt)
    doors_to_process = [doc.GetElement(ref.ElementId) for ref in selected_references]

    if doors_to_process:
        if show_confirmation_popup() == True:
            # Lógica de criação de soleiras (transplantada para cá)
            soleira_family_name = "ARQ-SLRA-ARDS-SOLEIRA EM ARDOSIA"
            param_name_length = "COMPRIMENTO PEITORIL"
            param_name_width = "LARGURA PEITORIL"
            FINISH_THICKNESS_M = 0.06
            METERS_TO_FEET = 1 / 0.3048
            FEET_TO_METERS = 0.3048
            FEET_TO_CM = 30.48
            TOLERANCE = 0.001

            all_symbols = FilteredElementCollector(doc).OfClass(FamilySymbol).ToElements()
            soleira_types_by_name = {}
            template_symbol = None
            for s in all_symbols:
                if s.Family.Name == soleira_family_name:
                    if not template_symbol: template_symbol = s
                    type_name_raw = s.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString()
                    type_name_normalized = type_name_raw.upper().strip()
                    soleira_types_by_name[type_name_normalized] = s
            
            if not template_symbol:
                show_generic_popup("Erro Crítico", "A família de soleira '{}' não foi encontrada no projeto!".format(soleira_family_name))
            else:
                newly_created_sills = []; doors_with_duplicates = []
                t = Transaction(doc, "Locar Soleiras Selecionadas")
                t.Start()
                try:
                    for door in doors_to_process:
                        door_type = doc.GetElement(door.GetTypeId())
                        largura_param = door_type.get_Parameter(BuiltInParameter.DOOR_WIDTH)
                        door_length_m = largura_param.AsDouble() * FEET_TO_METERS if largura_param else 0
                        host_wall = door.Host
                        if not host_wall: continue
                        wall_type = doc.GetElement(host_wall.GetTypeId())
                        wall_width_param = wall_type.get_Parameter(BuiltInParameter.WALL_ATTR_WIDTH_PARAM)
                        wall_width_bare_m = wall_width_param.AsDouble() * FEET_TO_METERS if wall_width_param else 0
                        door_location = door.Location.Point
                        search_box = BoundingBoxXYZ(); search_box.Min = XYZ(door_location.X - 0.5, door_location.Y - 0.5, door_location.Z - 0.5); search_box.Max = XYZ(door_location.X + 0.5, door_location.Y + 0.5, door_location.Z + 0.5)
                        outline = Outline(search_box.Min, search_box.Max); bbox_filter = BoundingBoxIntersectsFilter(outline)
                        existing_sills = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_GenericModel).WherePasses(bbox_filter)
                        found_duplicate = False
                        for sill in existing_sills:
                            if sill.Symbol.Family.Name == soleira_family_name: found_duplicate = True; break
                        if found_duplicate: doors_with_duplicates.append(door.Id); continue
                        target_length_ft = door_length_m * METERS_TO_FEET
                        target_finished_width_ft = (wall_width_bare_m + FINISH_THICKNESS_M) * METERS_TO_FEET
                        width_cm = int(round(target_finished_width_ft * FEET_TO_CM)); length_cm = int(round(target_length_ft * FEET_TO_CM))
                        target_type_name_raw = "SOLEIRA EM ARDOSIA-({}X{}cm)".format(width_cm, length_cm)
                        target_type_name_normalized = target_type_name_raw.upper().strip()
                        symbol_to_use = None
                        if target_type_name_normalized in soleira_types_by_name: symbol_to_use = soleira_types_by_name[target_type_name_normalized]
                        else:
                            new_symbol = template_symbol.Duplicate(target_type_name_raw)
                            symbol_to_use = new_symbol
                            soleira_types_by_name[target_type_name_normalized] = new_symbol
                        if symbol_to_use:
                            symbol_to_use.LookupParameter(param_name_width).Set(target_finished_width_ft)
                            symbol_to_use.LookupParameter(param_name_length).Set(target_length_ft)
                            if not symbol_to_use.IsActive: symbol_to_use.Activate(); doc.Regenerate()
                            level = doc.GetElement(door.LevelId)
                            new_instance = doc.Create.NewFamilyInstance(door_location, symbol_to_use, host_wall, level, Structure.StructuralType.NonStructural)
                            doc.Regenerate()
                            if hasattr(door.Location, 'Rotation'):
                                angle = door.Location.Rotation
                                if abs(angle) > TOLERANCE:
                                    axis = Line.CreateBound(new_instance.Location.Point, XYZ(new_instance.Location.Point.X, new_instance.Location.Point.Y, new_instance.Location.Point.Z + 1))
                                    ElementTransformUtils.RotateElement(doc, new_instance.Id, axis, angle)
                                    doc.Regenerate()
                            newly_created_sills.append(new_instance)
                    t.Commit()
                    if doors_with_duplicates:
                        ids_text = ", ".join([str(id.IntegerValue) for id in doors_with_duplicates])
                        show_generic_popup("Aviso de Duplicatas", "Já existia uma soleira nas portas de ID:\n" + ids_text)
                    if newly_created_sills:
                        count = len(newly_created_sills)
                        message = "Foi inserida 1 soleira com sucesso." if count == 1 else "Foram inseridas {} soleiras com sucesso.".format(count)
                        show_generic_popup("Processo Concluído", message)
                except Exception as e:
                    t.RollBack()
                    show_generic_popup("Erro na Transação", "Ocorreu um erro e a operação foi revertida:\n" + str(e))

except OperationCanceledException:
    # Captura o 'Esc' durante a seleção (idêntico ao seu script)
    print("Operação cancelada pelo usuário.")
except Exception as e:
    # Captura qualquer outro erro (idêntico ao seu script)
    show_generic_popup("Erro Crítico", "Ocorreu um erro inesperado:\n" + str(e))