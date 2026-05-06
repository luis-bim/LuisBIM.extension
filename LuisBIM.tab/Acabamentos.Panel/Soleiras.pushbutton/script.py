# -*- coding: utf-8 -*-
# pylint: disable=E0401,W0703,C0103,W0613

# --- SEÇÃO 1: IMPORTAÇÕES E REFERÊNCIAS ---
import clr
import System
import io

# Imports para a função de LOG
import os
import csv
from datetime import datetime
import socket
import getpass

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

# Imports do .NET para as janelas WPF
from System.Windows import (Window, Thickness, WindowStartupLocation, SizeToContent, 
                            VerticalAlignment, ResizeMode, FontWeights)
from System.Windows.Controls import Button, TextBlock, StackPanel, Grid, Viewbox
from System.Windows.Media import Brushes, Geometry, BrushConverter
from System.Windows.Shapes import Path

# --- SEÇÃO 2: FUNÇÕES E CLASSES ---

# --- Função de Log (VERSÃO FINAL CORRIGIDA) ---
def gravar_log_padronizado(status, start_time, doc):
    """
    Grava um log padronizado em um arquivo CSV de rede.
    """
    try:
        end_time = datetime.now()
        duration = round((end_time - start_time).total_seconds(), 2)
        
        # --- Definições do Log ---
        log_folder = r"G:\Drives compartilhados\BIM\AUTOMACAO\LOGS\USO DOS COMANDOS"
        log_file = os.path.join(log_folder, "SoleiraAutomatica.csv")
        command_name = "SoleiraAutomatica"
        
        # --- Coleta de Dados ---
        timestamp = end_time.strftime("%Y-%m-%d %H:%M:%S")
        username = getpass.getuser()
        ip_address = socket.gethostbyname(socket.gethostname())
        file_path = doc.PathName or "Arquivo não salvo"
        revit_version = doc.Application.VersionName
        
        proj_info = doc.ProjectInformation
        param = proj_info.LookupParameter("Número do projeto")
        project_number = param.AsString() if param and param.HasValue else "N/A"

        # --- Estrutura do CSV ---
        header = [
            "data_hora", "usuario", "IP", "NumeroProjeto", 
            "Caminho do arquivo", "NomeComando", "DuracaoSegundos", 
            "Status", "VersaoRevit"
        ]
        log_data = [
            timestamp, username, ip_address, project_number, 
            file_path, command_name, duration, 
            status, revit_version
        ]
        
        # --- Escrita do Arquivo ---
        if not os.path.exists(log_folder):
            os.makedirs(log_folder)
            
        file_exists = os.path.isfile(log_file)
        
        with io.open(log_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(header)
            writer.writerow(log_data)
            
    except Exception as log_error:
        print("ERRO AO GRAVAR O LOG: " + str(log_error))


# --- Funções de Pop-up (WPF) ---
def show_selection_prompt_popup():
    popup = Window()
    popup.Title = "Criar Soleiras"
    popup.Width = 450
    popup.SizeToContent = SizeToContent.Height 
    popup.WindowStartupLocation = WindowStartupLocation.CenterScreen
    popup.Background = Brushes.White
    popup.Topmost = True
    popup.ResizeMode = ResizeMode.NoResize
    
    panel = StackPanel()
    panel.Margin = Thickness(15)

    tutorial_button = Button()
    tutorial_button.Content = "CLIQUE AQUI PARA VER O TUTORIAL"
    tutorial_button.Margin = Thickness(0, 0, 0, 15)
    
    tutorial_button.Background = BrushConverter().ConvertFromString("#007ACC")
    tutorial_button.Foreground = Brushes.White
    tutorial_button.FontWeight = FontWeights.Bold
    tutorial_button.BorderThickness = Thickness(0)
    tutorial_button.Padding = Thickness(8)

    def tutorial_click(sender, e):
        System.Diagnostics.Process.Start("http://www.aindanaofizessevideo.com")
        
    tutorial_button.Click += tutorial_click

    message_text = TextBlock()
    message_text.Text = "Caso já exista soleira em alguma porta selecionada, este processo irá criar outra idêntica, causando erros de quantitativos. Recomendo selecionar as portas com cuidado."
    message_text.TextWrapping = System.Windows.TextWrapping.Wrap
    message_text.Foreground = Brushes.Black
    message_text.Margin = Thickness(0, 0, 0, 20)
    
    select_button = Button()
    select_button.Content = "SELECIONAR PORTAS"
    select_button.Background = BrushConverter().ConvertFromString("#007ACC")
    select_button.Foreground = Brushes.White
    select_button.FontWeight = FontWeights.Bold
    select_button.BorderThickness = Thickness(0)
    select_button.Padding = Thickness(8)
    
    def select_click(sender, e):
        popup.DialogResult = True
        popup.Close()
        
    select_button.Click += select_click
    
    panel.Children.Add(tutorial_button)
    panel.Children.Add(message_text)
    panel.Children.Add(select_button)
    
    popup.Content = panel
    
    return popup.ShowDialog()

def show_success_popup(title, message):
    popup = Window()
    popup.Title = title
    popup.Width = 450
    popup.SizeToContent = SizeToContent.Height
    popup.WindowStartupLocation = WindowStartupLocation.CenterScreen
    popup.Background = Brushes.White
    popup.Topmost = True
    popup.ResizeMode = ResizeMode.NoResize

    main_panel = StackPanel()
    main_panel.Margin = Thickness(15)

    content_panel = StackPanel()
    content_panel.Orientation = System.Windows.Controls.Orientation.Horizontal
    
    check_icon = Path()
    check_icon.Stroke = Brushes.Green
    check_icon.StrokeThickness = 4
    check_icon.Data = Geometry.Parse("M 5,15 L 15,25 L 30,10")
    
    icon_viewbox = Viewbox()
    icon_viewbox.Width = 30
    icon_viewbox.Height = 30
    icon_viewbox.Child = check_icon
    icon_viewbox.Margin = Thickness(0, 0, 15, 0)
    
    message_text = TextBlock()
    message_text.Text = message
    message_text.FontSize = 16
    message_text.TextWrapping = System.Windows.TextWrapping.Wrap
    message_text.VerticalAlignment = VerticalAlignment.Center

    content_panel.Children.Add(icon_viewbox)
    content_panel.Children.Add(message_text)

    ok_button = Button()
    ok_button.Content = "OK"
    ok_button.Margin = Thickness(0, 25, 0, 0)
    ok_button.Background = BrushConverter().ConvertFromString("#007ACC")
    ok_button.Foreground = Brushes.White
    ok_button.FontWeight = FontWeights.Bold
    ok_button.BorderThickness = Thickness(0)
    ok_button.Padding = Thickness(8)

    def ok_click(sender, e):
        popup.Close()
    ok_button.Click += ok_click
    
    main_panel.Children.Add(content_panel)
    main_panel.Children.Add(ok_button)

    popup.Content = main_panel
    popup.ShowDialog()

def show_generic_popup(title, message):
    if not message: return
    TaskDialog.Show(title, message)

# --- Filtro de Seleção (MODIFICADO) ---
class TargetDoorSelectionFilter(ISelectionFilter):
    def AllowElement(self, elem):
        # A verificação agora permite QUALQUER elemento que seja da categoria Portas.
        if isinstance(elem, FamilyInstance) and elem.Category and elem.Category.Id == ElementId(BuiltInCategory.OST_Doors):
            return True  # Se for uma porta, permite a seleção.
        return False # Se não for uma porta, bloqueia.
        
    def AllowReference(self, reference, position):
        return False

# --- SEÇÃO 3: LÓGICA PRINCIPAL ---
try:
    doc = __revit__.ActiveUIDocument.Document
    uidoc = __revit__.ActiveUIDocument
    
    start_time = datetime.now()

    if show_selection_prompt_popup() == True:
        try:
            door_filter = TargetDoorSelectionFilter()
            prompt = "Selecione as portas para locar as soleiras"
            selected_references = uidoc.Selection.PickObjects(ObjectType.Element, door_filter, prompt)
            doors_to_process = [doc.GetElement(ref.ElementId) for ref in selected_references]
        except OperationCanceledException:
            doors_to_process = []
            gravar_log_padronizado("Cancelado", start_time, doc)
            print("Seleção cancelada pelo usuário.")

        if doors_to_process:
            soleira_family_name = "ARQ-SLRA-GNT-SOLEIRA DE GRANITO"
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
                gravar_log_padronizado("Falha", start_time, doc)
            else:
                newly_created_sills = []
                doors_with_duplicates = []
                
                t = Transaction(doc, "Locar e Unir Soleiras")
                t.Start()
                try:
                    for door in doors_to_process:
                        host_wall = door.Host
                        if not host_wall: continue

                        altura_peitoril_ft = 0.0

                        param_peitoril = door.LookupParameter("Altura do peitoril")
                        if param_peitoril and param_peitoril.HasValue:
                            altura_peitoril_ft = param_peitoril.AsDouble()

                        door_type = doc.GetElement(door.GetTypeId())
                        largura_param = door_type.get_Parameter(BuiltInParameter.DOOR_WIDTH)
                        door_length_m = largura_param.AsDouble() * FEET_TO_METERS if largura_param else 0
                        wall_type = doc.GetElement(host_wall.GetTypeId())
                        wall_width_param = wall_type.get_Parameter(BuiltInParameter.WALL_ATTR_WIDTH_PARAM)
                        wall_width_bare_m = wall_width_param.AsDouble() * FEET_TO_METERS if wall_width_param else 0
                        door_location = door.Location.Point
                        search_box = BoundingBoxXYZ()
                        search_box.Min = XYZ(door_location.X - 0.5, door_location.Y - 0.5, door_location.Z - 0.5)
                        search_box.Max = XYZ(door_location.X + 0.5, door_location.Y + 0.5, door_location.Z + 0.5)
                        outline = Outline(search_box.Min, search_box.Max)
                        bbox_filter = BoundingBoxIntersectsFilter(outline)
                        existing_sills = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_GenericModel).WherePasses(bbox_filter)
                        found_duplicate = False
                        for sill in existing_sills:
                            if sill.Symbol.Family.Name == soleira_family_name: found_duplicate = True; break
                        if found_duplicate: doors_with_duplicates.append(door.Id); continue
                        target_length_ft = door_length_m * METERS_TO_FEET
                        target_finished_width_ft = (wall_width_bare_m + FINISH_THICKNESS_M) * METERS_TO_FEET
                        width_cm = int(round(target_finished_width_ft * FEET_TO_CM)); length_cm = int(round(target_length_ft * FEET_TO_CM))
                        
                        target_type_name_raw = "SOLEIRA DE GRANITO-({}x{}cm)".format(width_cm, length_cm)
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
                            
                            param_elevacao_soleira = new_instance.LookupParameter("Elevação do nível")
                            if param_elevacao_soleira and not param_elevacao_soleira.IsReadOnly:
                                param_elevacao_soleira.Set(altura_peitoril_ft)
                            
                            if hasattr(door.Location, 'Rotation'):
                                angle = door.Location.Rotation
                                if abs(angle) > TOLERANCE:
                                    axis = Line.CreateBound(new_instance.Location.Point, XYZ(new_instance.Location.Point.X, new_instance.Location.Point.Y, new_instance.Location.Point.Z + 1))
                                    ElementTransformUtils.RotateElement(doc, new_instance.Id, axis, angle)
                                    doc.Regenerate()
                            sill_bbox = new_instance.get_BoundingBox(None)
                            if sill_bbox:
                                sill_outline = Outline(sill_bbox.Min, sill_bbox.Max)
                                intersecting_filter = BoundingBoxIntersectsFilter(outline)
                                wall_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Walls).WherePasses(intersecting_filter).ToElements()
                                for wall in wall_collector:
                                    try:
                                        if not JoinGeometryUtils.AreElementsJoined(doc, new_instance, wall):
                                            JoinGeometryUtils.JoinGeometry(doc, new_instance, wall)
                                    except: pass
                                floor_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Floors).WherePasses(intersecting_filter).ToElements()
                                for floor in floor_collector:
                                    try:
                                        if not JoinGeometryUtils.AreElementsJoined(doc, new_instance, floor):
                                            JoinGeometryUtils.JoinGeometry(doc, new_instance, floor)
                                    except: pass
                            newly_created_sills.append(new_instance)
                    t.Commit()
                    gravar_log_padronizado("Sucesso", start_time, doc)
                    
                    if doors_with_duplicates:
                        ids_text = ", ".join([str(id.IntegerValue) for id in doors_with_duplicates])
                        show_generic_popup("Aviso de Duplicatas", "Já existia uma soleira nas portas de ID:\n" + ids_text)
                    
                    if newly_created_sills:
                        count = len(newly_created_sills)
                        message = "Foi inserida e unida 1 soleira com sucesso." if count == 1 else "Foram inseridas e unidas {} soleiras com sucesso.".format(count)
                        
                        # --- ALTERAÇÃO ---
                        # A lista de detalhes do peitoril foi removida da mensagem final.
                        show_success_popup("Processo Concluído", message)

                except Exception as e:
                    t.RollBack()
                    gravar_log_padronizado("Falha", start_time, doc)
                    show_generic_popup("Erro na Transação", "Ocorreu um erro e a operação foi revertida:\n" + str(e))
    else:
        gravar_log_padronizado("Cancelado", start_time, doc)
        

except OperationCanceledException:
    gravar_log_padronizado("Cancelado", start_time, doc)
    print("Operação cancelada pelo usuário (principal).")
except Exception as e:
    if 'start_time' in locals() and 'doc' in locals():
        gravar_log_padronizado("Falha", start_time, doc)
    show_generic_popup("Erro Crítico", "Ocorreu um erro inesperado:\n" + str(e))