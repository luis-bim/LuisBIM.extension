# -*- coding: utf-8 -*-

__title__ = "Checar\nPontos"
__doc__ = "Exibe uma tabela comparativa entre o Survey Point e o Project Base Point e os seleciona no modelo."

import clr
import System

# --- Importações do Revit API ---
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
from System.Collections.Generic import List

# --- Importações WPF / Interface Gráfica ---
clr.AddReference('PresentationFramework')
clr.AddReference('PresentationCore')
clr.AddReference('WindowsBase')
clr.AddReference('System.Xml')

from System.IO import StringReader
from System.Xml import XmlReader
from System.Windows.Markup import XamlReader
from System.Windows import (Window, Thickness, VerticalAlignment, HorizontalAlignment, 
                            FontWeights, SizeToContent, TextAlignment)
from System.Windows.Controls import (TextBlock, Label, Grid, StackPanel, 
                                     GroupBox, Button, TextBox)
from System.Windows.Media import Brushes, BrushConverter
from System.Globalization import CultureInfo

# --- Configuração do Documento (PyRevit) ---
uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document

# --- Constantes ---
FEET_TO_METERS = 0.3048
PI = System.Math.PI

# --- Funções Auxiliares ---

def format_coord_to_br(value_in_feet):
    """Converte de pés para metros e formata para o padrão brasileiro."""
    meters = value_in_feet * FEET_TO_METERS
    return meters.ToString("N3", CultureInfo("pt-BR"))

def get_param_value_as_formatted_string(element, param_name, is_angle=False):
    """Busca o valor numérico, converte e formata."""
    try:
        param = element.LookupParameter(param_name)
        if not param:
            # Tenta buscar pelo BuiltInParameter se o nome falhar (opcional, mantendo simples por enquanto)
            return "Não encontrado"
        
        if is_angle:
            degrees = param.AsDouble() * (180.0 / PI)
            return degrees.ToString("N2", CultureInfo("pt-BR")) + u"°"
        
        value_in_feet = param.AsDouble()
        return format_coord_to_br(value_in_feet)
    except Exception as e:
        return "Erro"

def create_cell(content, row, col, is_header=False, align='Center'):
    """Cria a célula da tabela (TextBox somente leitura)."""
    text_box = TextBox()
    text_box.Text = unicode(content)
    
    # Alinhamento
    try:
        text_box.TextAlignment = getattr(TextAlignment, align)
    except:
        text_box.TextAlignment = TextAlignment.Center
        
    text_box.VerticalContentAlignment = VerticalAlignment.Center
    text_box.Padding = Thickness(5)
    
    # Estilo "Rótulo" mas copiável
    text_box.IsReadOnly = True
    text_box.BorderThickness = Thickness(0)
    
    if is_header:
        text_box.FontWeight = FontWeights.Bold
        text_box.Background = BrushConverter().ConvertFromString("#EEE")
    else:
        text_box.Background = Brushes.White

    Grid.SetRow(text_box, row)
    Grid.SetColumn(text_box, col)
    return text_box

# --- Lógica Principal: Coletar Elementos ---

survey_point = None
project_base_point = None

# Coletor único para BasePoint
collector = FilteredElementCollector(doc).OfClass(BasePoint)

for bp in collector:
    if bp.IsShared:
        survey_point = bp
    else:
        project_base_point = bp

# --- Lógica de Seleção no Revit ---
ids_to_select = List[ElementId]()
if survey_point: ids_to_select.Add(survey_point.Id)
if project_base_point: ids_to_select.Add(project_base_point.Id)

if ids_to_select.Count > 0:
    uidoc.Selection.SetElementIds(ids_to_select)

# --- Processamento de Dados para a Tabela ---

# Se algum ponto faltar, criar dados vazios para não quebrar o script
sp_data = {"x": "-", "y": "-", "z": "-", "ns": "-", "lo": "-", "el": "-", "ang": "-"}
pbp_data = {"x": "-", "y": "-", "z": "-", "ns": "-", "lo": "-", "el": "-", "ang": "-"}

# Extrair Ponto de Vistoria (SP)
if survey_point:
    bbox = survey_point.get_BoundingBox(None)
    if bbox:
        center = (bbox.Min + bbox.Max) / 2.0
        sp_data["x"] = format_coord_to_br(center.X)
        sp_data["y"] = format_coord_to_br(center.Y)
        sp_data["z"] = format_coord_to_br(center.Z)
        sp_data["ns"] = get_param_value_as_formatted_string(survey_point, "N/S")
        sp_data["lo"] = get_param_value_as_formatted_string(survey_point, "L/O")
        sp_data["el"] = get_param_value_as_formatted_string(survey_point, "Elev")
        sp_data["ang"] = "N/A"

# Extrair Ponto Base do Projeto (PBP)
if project_base_point:
    bbox = project_base_point.get_BoundingBox(None)
    if bbox:
        center = (bbox.Min + bbox.Max) / 2.0
        pbp_data["x"] = format_coord_to_br(center.X)
        pbp_data["y"] = format_coord_to_br(center.Y)
        pbp_data["z"] = format_coord_to_br(center.Z)
        pbp_data["ns"] = get_param_value_as_formatted_string(project_base_point, "N/S")
        pbp_data["lo"] = get_param_value_as_formatted_string(project_base_point, "L/O")
        pbp_data["el"] = get_param_value_as_formatted_string(project_base_point, "Elev")
        pbp_data["ang"] = get_param_value_as_formatted_string(project_base_point, "Ângulo para norte verdadeiro", is_angle=True)
        # Tentar parametro ingles se o portugues falhar
        if "Erro" in pbp_data["ang"] or "Não" in pbp_data["ang"]:
             pbp_data["ang"] = get_param_value_as_formatted_string(project_base_point, "Angle to True North", is_angle=True)


# --- Definição e Criação da Interface (WPF) ---

xaml_string = """
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        Title="Coordenadas dos Pontos Base" 
        Width="1100" 
        SizeToContent="WidthAndHeight" 
        WindowStartupLocation="CenterScreen" 
        Topmost="True" 
        ResizeMode="CanResizeWithGrip">
    
    <StackPanel Margin="15">
        <Grid x:Name="dataGrid" ShowGridLines="True" Margin="0,0,0,10">
            <Grid.ColumnDefinitions>
                <ColumnDefinition Width="Auto" MinWidth="260" /> 
                <ColumnDefinition Width="Auto" MinWidth="80" />  
                <ColumnDefinition Width="Auto" MinWidth="80" />  
                <ColumnDefinition Width="Auto" MinWidth="80" />  
                <ColumnDefinition Width="Auto" MinWidth="110" /> 
                <ColumnDefinition Width="Auto" MinWidth="110" /> 
                <ColumnDefinition Width="Auto" MinWidth="110" /> 
                <ColumnDefinition Width="*" MinWidth="150" />  
            </Grid.ColumnDefinitions>
            <Grid.RowDefinitions>
                <RowDefinition Height="Auto" /> 
                <RowDefinition Height="Auto" /> 
                <RowDefinition Height="Auto" /> 
            </Grid.RowDefinitions>
        </Grid>
        
        <Button x:Name="btnClose" Content="Fechar" Width="100" HorizontalAlignment="Right" Margin="0,10,0,0" IsDefault="True" />
    </StackPanel>
</Window>
"""

try:
    reader = StringReader(xaml_string)
    xml_reader = XmlReader.Create(reader)
    window = XamlReader.Load(xml_reader)
    
    grid = window.FindName("dataGrid")
    
    # --- Linha 0: Headers ---
    headers = ["PONTO", "X(m)", "Y(m)", "Z(m)", "N/S(m)", "L/O(m)", "ELEV.(m)", "ANG. NORTE(°)"]
    for i, h in enumerate(headers):
        grid.Children.Add(create_cell(h, 0, i, True))
    
    # --- Linha 1: Ponto de Vistoria (SP) ---
    grid.Children.Add(create_cell(u"▲ PONTO DE LEVANTAMENTO (Survey)", 1, 0, align='Left'))
    grid.Children.Add(create_cell(sp_data["x"], 1, 1, align='Right'))
    grid.Children.Add(create_cell(sp_data["y"], 1, 2, align='Right'))
    grid.Children.Add(create_cell(sp_data["z"], 1, 3, align='Right'))
    grid.Children.Add(create_cell(sp_data["ns"], 1, 4, align='Right'))
    grid.Children.Add(create_cell(sp_data["lo"], 1, 5, align='Right'))
    grid.Children.Add(create_cell(sp_data["el"], 1, 6, align='Right'))
    grid.Children.Add(create_cell(sp_data["ang"], 1, 7, align='Center'))
    
    # --- Linha 2: Ponto Base do Projeto (PBP) ---
    grid.Children.Add(create_cell(u"⌖ PONTO BASE DO PROJETO", 2, 0, align='Left'))
    grid.Children.Add(create_cell(pbp_data["x"], 2, 1, align='Right'))
    grid.Children.Add(create_cell(pbp_data["y"], 2, 2, align='Right'))
    grid.Children.Add(create_cell(pbp_data["z"], 2, 3, align='Right'))
    grid.Children.Add(create_cell(pbp_data["ns"], 2, 4, align='Right'))
    grid.Children.Add(create_cell(pbp_data["lo"], 2, 5, align='Right'))
    grid.Children.Add(create_cell(pbp_data["el"], 2, 6, align='Right'))
    grid.Children.Add(create_cell(pbp_data["ang"], 2, 7, align='Right'))

    # --- Eventos ---
    def close_click(sender, e):
        window.Close()

    window.FindName("btnClose").Click += close_click
    
    # Exibir Janela (PyRevit lida com o Loop de Mensagens, ShowDialog é seguro aqui)
    window.ShowDialog()

except Exception as e:
    # Fallback simples caso a GUI falhe
    print("Erro ao criar interface: {}".format(e))