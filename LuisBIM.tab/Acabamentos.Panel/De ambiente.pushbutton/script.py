# -*- coding: utf-8 -*-
#pylint: disable=E0401,W0703,C0103,W0613

import clr
import System

# --- SEÇÃO 1: IMPORTAÇÕES E REFERÊNCIAS ---

# --- Importações para Log de Uso (MODIFICADO E PADRONIZADO) ---
import os
import csv
from datetime import datetime
import time
import socket
from io import open 

# Referências .NET para UI e Sistema
clr.AddReference("PresentationFramework")
clr.AddReference("PresentationCore")
clr.AddReference("WindowsBase")
clr.AddReference("System.Xml")
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")

# Referências da API do Revit
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
import Autodesk
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import TaskDialog
from Autodesk.Revit.UI.Selection import ISelectionFilter, ObjectType

# Imports específicos das bibliotecas
from System.Collections.Generic import List
from System.Windows import Window
from System.Windows.Controls import (ComboBox, RadioButton, Button, TextBox,
                                     Grid, GroupBox, StackPanel, CheckBox,
                                     TextBlock, Label as WpfLabel)
from System.Windows.Markup import XamlReader
from System.IO import StringReader
from System.Xml import XmlReader

# Imports do Windows Forms para a nova janela de progresso
from System.Windows.Forms import Form, ProgressBar, Label, Button as WinButton, Application, FormBorderStyle, FormStartPosition
from System.Drawing import Point, Size


# --- SEÇÃO 2: DEFINIÇÃO DAS JANELAS E CLASSES HELPER ---

# --- XAML da Janela Principal (Configurações - MANTIDA EM WPF) ---
xaml_settings_string = """
<Window
    xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
    Title="Criar Revestimentos de Parede e Piso"
    SizeToContent="Height" Width="550"
    WindowStartupLocation="CenterScreen" ResizeMode="NoResize" ShowInTaskbar="False" Topmost="True"
    Background="White">
    <StackPanel Margin="15">
        <Button x:Name="btnTutorial"
                Content="ACHOU CONFUSO? CLIQUE AQUI PARA VER O TUTORIAL"
                Margin="0,0,0,15" Padding="8" FontWeight="Bold"
                Background="#007ACC" Foreground="White" BorderThickness="0"/>

        <StackPanel Orientation="Horizontal" Margin="0,0,0,10">
            <CheckBox x:Name="chkCreateWalls" Content="Criar Revestimentos de Parede" IsChecked="True" VerticalAlignment="Center" FontWeight="Bold"/>
            <CheckBox x:Name="chkCreateFloors" Content="Criar Revestimentos de Piso" IsChecked="True" Margin="20,0,0,0" VerticalAlignment="Center" FontWeight="Bold"/>
        </StackPanel>
        <GroupBox x:Name="groupWalls" Header="Configurações de Parede" Padding="10">
            <StackPanel>
                <Grid>
                    <Grid.ColumnDefinitions><ColumnDefinition Width="Auto"/><ColumnDefinition Width="*"/></Grid.ColumnDefinitions>
                    <Label Content="Tipo de Parede:" Grid.Column="0" VerticalAlignment="Center"/>
                    <ComboBox x:Name="comboWallTypes" Grid.Column="1" Padding="3" DisplayMemberPath="Name"/>
                </Grid>
                <GroupBox Header="Altura dos Revestimentos" Padding="10" Margin="0,10,0,0">
                    <Grid>
                        <Grid.ColumnDefinitions><ColumnDefinition Width="Auto" /><ColumnDefinition Width="*" /></Grid.ColumnDefinitions>
                        <Grid.RowDefinitions><RowDefinition Height="Auto" /><RowDefinition Height="Auto" /></Grid.RowDefinitions>
                        <RadioButton x:Name="radioValor" Content="Valor" Grid.Row="0" Grid.Column="0" IsChecked="True" VerticalAlignment="Center" Margin="0,0,10,0"/>
                        <StackPanel Grid.Row="0" Grid.Column="1" Orientation="Horizontal">
                            <TextBox x:Name="txtValor" Width="120" Padding="3" VerticalContentAlignment="Center"/>
                            <ComboBox x:Name="comboUnidades" Width="120" Margin="10,0,0,0" Padding="3"/>
                        </StackPanel>
                        <RadioButton x:Name="radioNivel" Content="Por Nível" Grid.Row="1" Grid.Column="0" Margin="0,10,10,0" VerticalAlignment="Center"/>
                        <ComboBox x:Name="comboNiveis" Grid.Row="1" Grid.Column="1" Margin="0,10,0,0" Padding="3" DisplayMemberPath="Name" IsEnabled="False"/>
                    </Grid>
                </GroupBox>
            </StackPanel>
        </GroupBox>
        <GroupBox x:Name="groupFloors" Header="Configurações de Piso" Padding="10" Margin="0,10,0,0">
            <Grid>
                <Grid.ColumnDefinitions><ColumnDefinition Width="Auto"/><ColumnDefinition Width="*"/></Grid.ColumnDefinitions>
                <Grid.RowDefinitions><RowDefinition Height="Auto"/><RowDefinition Height="Auto"/><RowDefinition Height="Auto"/></Grid.RowDefinitions>
                
                <Label Content="Tipo de Piso:" Grid.Row="0" Grid.Column="0" VerticalAlignment="Center" Margin="0,0,10,0"/>
                <ComboBox x:Name="comboFloorTypes" Grid.Row="0" Grid.Column="1" Padding="3" DisplayMemberPath="Name"/>
                
                <Label Content="Nível do Piso:" Grid.Row="1" Grid.Column="0" VerticalAlignment="Center" Margin="0,10,10,0"/>
                <ComboBox x:Name="comboFloorLevels" Grid.Row="1" Grid.Column="1" Margin="0,10,0,0" Padding="3" DisplayMemberPath="Name"/>
                
                <Label Content="Deslocamento do Piso (cm):" Grid.Row="2" Grid.Column="0" VerticalAlignment="Center" Margin="0,10,10,0"/>
                <TextBox x:Name="txtOffsetValue" Grid.Row="2" Grid.Column="1" Width="100" Padding="3" VerticalContentAlignment="Center" Margin="0,10,0,0" HorizontalAlignment="Left"/>
            </Grid>
        </GroupBox>
        <Button x:Name="btnOk"
                Content="CRIAR REVESTIMENTOS"
                Margin="0,20,0,0" Padding="8" FontWeight="Bold"
                Background="#007ACC" Foreground="White" BorderThickness="0"/>
    </StackPanel>
</Window>
"""

class ComboBoxItem(object):
    def __init__(self, name, value):
        self.Name = name; self.Value = value

class WpfConfigForm:
    def __init__(self, wall_data, floor_data, level_data, default_level_id=None):
        string_reader = StringReader(xaml_settings_string)
        xml_reader = XmlReader.Create(string_reader)
        self.win = XamlReader.Load(xml_reader)
        self.result = None
        self.default_level_id = default_level_id

        # Controles
        self.btn_tutorial = self.win.FindName("btnTutorial")
        self.chk_create_walls = self.win.FindName("chkCreateWalls")
        self.chk_create_floors = self.win.FindName("chkCreateFloors")
        self.group_walls = self.win.FindName("groupWalls")
        self.group_floors = self.win.FindName("groupFloors")
        self.btn_ok = self.win.FindName("btnOk")
        self.combo_wall_types = self.win.FindName("comboWallTypes")
        self.radio_valor = self.win.FindName("radioValor")
        self.radio_nivel = self.win.FindName("radioNivel")
        self.txt_valor = self.win.FindName("txtValor")
        self.combo_unidades = self.win.FindName("comboUnidades")
        self.combo_niveis = self.win.FindName("comboNiveis")
        self.combo_floor_types = self.win.FindName("comboFloorTypes")
        self.combo_floor_levels = self.win.FindName("comboFloorLevels")
        self.txt_offset_value = self.win.FindName("txtOffsetValue")

        self.popular_combos(wall_data, floor_data, level_data)
        self.definir_padroes()
        self.conectar_eventos()

    def popular_combos(self, wall_data, floor_data, level_data):
        self.combo_wall_types.ItemsSource = [ComboBoxItem(n, i) for n, i in zip(wall_data['names'], wall_data['ids'])]
        self.combo_floor_types.ItemsSource = [ComboBoxItem(n, i) for n, i in zip(floor_data['names'], floor_data['ids'])]
        level_items = [ComboBoxItem(n, i) for n, i in zip(level_data['names'], level_data['ids'])]
        self.combo_niveis.ItemsSource = level_items
        self.combo_floor_levels.ItemsSource = level_items
        self.combo_unidades.ItemsSource = ["em MM", "em M", "em CM"]

    def definir_padroes(self):
        if self.combo_wall_types.Items.Count > 0: self.combo_wall_types.SelectedIndex = 0
        if self.combo_floor_types.Items.Count > 0: self.combo_floor_types.SelectedIndex = 0

        found_level = False
        if self.default_level_id and self.combo_floor_levels.Items.Count > 0:
            for item in self.combo_floor_levels.ItemsSource:
                if item.Value and self.default_level_id and item.Value.IntegerValue == self.default_level_id.IntegerValue:
                    self.combo_floor_levels.SelectedItem = item
                    found_level = True
                    break
        if not found_level and self.combo_floor_levels.Items.Count > 0:
            self.combo_floor_levels.SelectedIndex = 0

        if self.combo_niveis.Items.Count > 0:
             self.combo_niveis.SelectedItem = self.combo_floor_levels.SelectedItem

        if self.combo_unidades.Items.Count > 2: self.combo_unidades.SelectedIndex = 2

        self.txt_valor.Text = "350"
        self.radio_valor.IsChecked = True
        self.txt_offset_value.Text = "0"
        
        self.radio_button_changed(None, None)
        self.toggle_groups(None, None)

    def conectar_eventos(self):
        self.chk_create_walls.Checked += self.toggle_groups; self.chk_create_walls.Unchecked += self.toggle_groups
        self.chk_create_floors.Checked += self.toggle_groups; self.chk_create_floors.Unchecked += self.toggle_groups
        self.radio_valor.Checked += self.radio_button_changed; self.radio_nivel.Checked += self.radio_button_changed
        self.btn_ok.Click += self.ok_button_click
        self.btn_tutorial.Click += self.tutorial_button_click

    def tutorial_button_click(self, sender, e):
        import System
        System.Diagnostics.Process.Start("https://drive.google.com/file/d/1iuzBQgp1hEIrWP5lKJxI1q8tarGGKGTb/view")

    def toggle_groups(self, sender, e):
        self.group_walls.IsEnabled = self.chk_create_walls.IsChecked; self.group_floors.IsEnabled = self.chk_create_floors.IsChecked

    def radio_button_changed(self, sender, e):
        is_valor_checked = self.radio_valor.IsChecked
        self.txt_valor.IsEnabled = is_valor_checked; self.combo_unidades.IsEnabled = is_valor_checked
        self.combo_niveis.IsEnabled = not is_valor_checked

    def ok_button_click(self, sender, e):
        output = {"create_walls": False, "wall_settings": {}, "create_floors": False, "floor_settings": {}}
        if self.chk_create_walls.IsChecked:
            output["create_walls"] = True
            if self.combo_wall_types.SelectedItem is None: TaskDialog.Show("Erro", "Selecione um tipo de parede."); return
            output["wall_settings"]["type_id"] = self.combo_wall_types.SelectedItem.Value
            if self.radio_valor.IsChecked:
                output["wall_settings"]["method"] = "Valor"
                try: output["wall_settings"]["value"] = float(self.txt_valor.Text.replace(',', '.')); output["wall_settings"]["unit"] = self.combo_unidades.SelectedItem
                except ValueError: TaskDialog.Show("Erro", "Insira um número válido para a altura da parede."); return
            else:
                if self.combo_niveis.SelectedItem is None: TaskDialog.Show("Erro", "Selecione um nível para a parede."); return
                output["wall_settings"]["method"] = "Nivel"; output["wall_settings"]["level_id"] = self.combo_niveis.SelectedItem.Value
        
        if self.chk_create_floors.IsChecked:
            output["create_floors"] = True
            if self.combo_floor_types.SelectedItem is None or self.combo_floor_levels.SelectedItem is None: TaskDialog.Show("Erro", "Selecione um tipo de piso e um nível."); return
            output["floor_settings"]["type_id"] = self.combo_floor_types.SelectedItem.Value
            output["floor_settings"]["level_id"] = self.combo_floor_levels.SelectedItem.Value

            try:
                output["floor_settings"]["offset_cm"] = float(self.txt_offset_value.Text.replace(',', '.'))
            except ValueError:
                TaskDialog.Show("Erro", "Insira um valor numérico válido para o deslocamento do piso."); return

        if not output["create_walls"] and not output["create_floors"]: TaskDialog.Show("Aviso", "Nenhuma tarefa foi selecionada."); return
        self.result = output; self.win.Close()

    def show(self): self.win.ShowDialog()

class WinFormsProgressWindow:
    def __init__(self):
        self.interrupt = False
        self.win = Form()
        self.win.Text = "Criando Revestimentos..."
        self.win.Size = Size(350, 140)
        self.win.FormBorderStyle = FormBorderStyle.FixedToolWindow
        self.win.StartPosition = FormStartPosition.CenterScreen
        self.win.TopMost = True
        self.win.FormClosing += self.closing_event
        self.lbl_status = Label()
        self.lbl_status.Text = "Processando..."
        self.lbl_status.Location = Point(10, 15)
        self.lbl_status.AutoSize = True
        self.progress_bar = ProgressBar()
        self.progress_bar.Location = Point(10, 40)
        self.progress_bar.Size = Size(315, 20)
        self.btn_interrupt = WinButton()
        self.btn_interrupt.Text = "Cancelar"
        self.btn_interrupt.Location = Point(125, 70)
        self.btn_interrupt.Click += self.interrupt_click
        self.win.Controls.Add(self.lbl_status)
        self.win.Controls.Add(self.progress_bar)
        self.win.Controls.Add(self.btn_interrupt)
    def set_max(self, max_val): self.progress_bar.Maximum = max_val
    def update(self, current_val, total_val):
        self.progress_bar.Value = current_val
        self.lbl_status.Text = "{} / {} Ambientes Processados".format(current_val, total_val)
        self.lbl_status.Location = Point((self.win.ClientSize.Width - self.lbl_status.Width) / 2, 15)
        Application.DoEvents() 
    def interrupt_click(self, sender, e): self.interrupt = True; self.win.Close()
    def closing_event(self, sender, e): self.interrupt = True
    def show(self): self.win.Show()
    def close(self): self.win.Close()

# --- SEÇÃO 3: FUNÇÕES HELPER ---

# **** NOVA FUNÇÃO DE LOG (PADRONIZADA) ****
def gravar_log_padronizado(status, start_time, doc):
    """Função centralizada para escrever o log em CSV no formato padrão."""
    try:
        # --- CAMINHO DO LOG ---
        log_folder = r"G:\Drives compartilhados\BIM\AUTOMACAO\LOGS\USO DOS COMANDOS"
        # --------------------
        
        # Define o nome do arquivo de log específico para este script
        log_file = os.path.join(log_folder, "AcabamentoPorAmbiente.csv")

        if not os.path.exists(log_folder):
            os.makedirs(log_folder)
            
        file_exists = os.path.isfile(log_file)
        
        duration = time.time() - start_time
        user_name = os.environ.get('USERNAME', 'N/A')
        
        ip_address = 'N/A'
        try:
            ip_address = socket.gethostbyname(socket.gethostname())
        except:
            pass

        project_number = doc.ProjectInformation.Number if doc.ProjectInformation.Number else ""
        file_path = doc.PathName if doc.PathName else ""
        
        revit_version = doc.Application.VersionName
        
        log_data = [
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            user_name,
            ip_address,
            project_number,
            file_path,
            'AcabamentoPorAmbiente',  # Nome do comando
            "{:.3f}".format(duration),
            status,
            revit_version
        ]

        header = [
            'data_hora', 'usuario', 'IP', 'NumeroProjeto', 'Caminho do arquivo', 
            'NomeComando', 'DuracaoSegundos', 'Status', 'VersaoRevit'
        ]
        
        with open(log_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=',')
            if not file_exists:
                writer.writerow(header)
            writer.writerow(log_data)

    except Exception as e_log:
        print("FALHA CRÍTICA AO GRAVAR O LOG: {}".format(str(e_log)))


def safe_get(d, key, default=None):
    if isinstance(d, dict): return d.get(key, default)
    try:
        if hasattr(d, 'ContainsKey') and d.ContainsKey(key): return d[key]
    except: pass
    return default

def unitConverterToInternal(value, units):
    if value != 0: _footToMm = 304.8
    else: return 0
    if units == "em MM": return float(value)/_footToMm
    elif units == "em M": return (float(value)*1000)/_footToMm
    elif units == "em CM": return (float(value)*10)/_footToMm
    return 0

def join_geometry(doc, list_of_wall_lists):
    for wall_list in list_of_wall_lists:
        if len(wall_list) < 2: continue
        for i in range(len(wall_list)):
            try: JoinGeometryUtils.JoinGeometry(doc, wall_list[i], wall_list[i-1])
            except: pass

def create_walls_for_room(doc, room, wall_settings, creation_level_id, floor_settings=None):
    wall_type_id = safe_get(wall_settings, "type_id")
    if not wall_type_id: return None
    created_walls_in_room = []
    
    level_id_to_use = creation_level_id if creation_level_id else room.LevelId

    base_offset_internal = 0.0
    if floor_settings:
        offset_cm = safe_get(floor_settings, "offset_cm", 0.0)
        base_offset_internal = offset_cm / 30.48 

    opt = SpatialElementBoundaryOptions(); opt.SpatialElementBoundaryLocation = SpatialElementBoundaryLocation.Finish
    boundaries = room.GetBoundarySegments(opt)
    all_curves = []
    if len(boundaries) > 0:
        for bnd in boundaries:
            for seg in bnd:
                try:
                    ele_seg = doc.GetElement(seg.ElementId)
                    if isinstance(ele_seg, Wall) and ele_seg.WallType.Kind == WallKind.Curtain: continue
                    if ele_seg.Category.Id != ElementId(BuiltInCategory.OST_RoomSeparationLines): all_curves.append((seg.GetCurve(), ele_seg))
                except: pass
    for wall_curve, host_wall in all_curves:
        try:
            skirting = None
            if safe_get(wall_settings, "method") == "Valor":
                height = unitConverterToInternal(safe_get(wall_settings, "value", 0), safe_get(wall_settings, "unit"))
                if height <= 0: continue
                skirting = Wall.Create(doc, wall_curve, wall_type_id, level_id_to_use, height, base_offset_internal, True, False)
            else:
                top_level_id = safe_get(wall_settings, "level_id")
                if top_level_id is None: continue
                skirting = Wall.Create(doc, wall_curve, wall_type_id, level_id_to_use, 1.0, base_offset_internal, True, False)
                skirting.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE).Set(top_level_id)
                skirting.get_Parameter(BuiltInParameter.WALL_TOP_OFFSET).Set(0)
            
            if skirting:
                skirting.Flip(); doc.Regenerate()
                offset_vector = skirting.Orientation * (skirting.Width / 2.0)
                ElementTransformUtils.MoveElement(doc, skirting.Id, offset_vector)
                JoinGeometryUtils.JoinGeometry(doc, skirting, host_wall)
                created_walls_in_room.append(skirting)
        except: pass
    return created_walls_in_room

def create_floor_for_room(doc, room, floor_settings):
    floor_type_id = safe_get(floor_settings, "type_id")
    level_id = safe_get(floor_settings, "level_id")
    if not floor_type_id or not level_id: return
    opt = SpatialElementBoundaryOptions()
    boundaries = room.GetBoundarySegments(opt)
    curveLoops = List[CurveLoop]()
    if len(boundaries) > 0:
        for bnd in boundaries:
            curveLoop = CurveLoop()
            for seg in bnd: curveLoop.Append(seg.GetCurve())
            if not curveLoop.IsOpen() and curveLoop.GetExactLength() > 0.01: curveLoops.Add(curveLoop)
        if curveLoops.Count > 0:
            try:
                floor = Floor.Create(doc, curveLoops, floor_type_id, level_id)
                
                offset_cm = safe_get(floor_settings, "offset_cm", 0.0)
                internal_offset = offset_cm / 30.48
                
                param = floor.get_Parameter(BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM)
                if param: param.Set(internal_offset)
            except: pass

class RoomSelectionFilter(ISelectionFilter):
    def AllowElement(self, element): return isinstance(element, Autodesk.Revit.DB.Architecture.Room)
    def AllowReference(self, refer, point): return False

# --- SEÇÃO 4: BLOCO DE EXECUÇÃO PRINCIPAL E UNIFICADO ---
doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
app = __revit__.Application

# Define um start_time inicial para o caso de erro crítico antes da UI
start_time = time.time()

try:
    active_view = doc.ActiveView
    if active_view.ViewType in [ViewType.ProjectBrowser, ViewType.SystemBrowser]:
        open_ui_views = uidoc.GetOpenUIViews()
        if open_ui_views.Count > 0: active_view = doc.GetElement(open_ui_views[0].ViewId)

    active_level_id = None
    if hasattr(active_view, "GenLevel") and active_view.GenLevel is not None:
        active_level_id = active_view.GenLevel.Id

    wall_data, floor_data = {'names': [], 'ids': []}, {'names': [], 'ids': []}
    wall_types = FilteredElementCollector(doc).OfClass(WallType).WhereElementIsElementType().ToElements()
    floor_types = FilteredElementCollector(doc).OfClass(FloorType).WhereElementIsElementType().ToElements()
    levels = FilteredElementCollector(doc).OfClass(Level).WhereElementIsNotElementType().ToElements()

    for t in wall_types:
        if t.Kind == WallKind.Basic:
            name = Element.Name.GetValue(t)
            if name.startswith("ARQ-PARE-CERM") or name.startswith("ARQ-PARE-TINT"):
                wall_data['names'].append(name); wall_data['ids'].append(t.Id)
    floor_prefixes = ("ARQ-PISO-CERM", "ARQ-PISO-GNLT", "ARQ-PISO-CON", "ARQ-PISO-VIN", "ARQ-PISO-CARP", "ARQ-REVE")
    for t in floor_types:
        name = Element.Name.GetValue(t)
        # --- AQUI ESTÁ A CORREÇÃO ---
        if not t.IsFoundationSlab and name.startswith(floor_prefixes) and "-LAJE" not in name:
            floor_data['names'].append(name); floor_data['ids'].append(t.Id)
    sorted_levels = sorted(levels, key=lambda x: x.Elevation)
    level_data = {'names': [Element.Name.GetValue(lvl) for lvl in sorted_levels], 'ids': [lvl.Id for lvl in sorted_levels]}

    if not wall_data['names'] and not floor_data['names']:
        TaskDialog.Show("Erro", "Nenhum tipo de parede ou piso válido foi encontrado.")
    else:
        wpf_form = WpfConfigForm(wall_data, floor_data, level_data, active_level_id)
        start_time = time.time() # <-- Reinicia o contador de tempo antes da UI
        wpf_form.show()
        user_settings = wpf_form.result
        
        if user_settings is None:
             gravar_log_padronizado("Cancelado", start_time, doc)

        elif user_settings and (safe_get(user_settings, "create_walls") or safe_get(user_settings, "create_floors")):
            all_rooms = []
            try:
                picked_refs = uidoc.Selection.PickObjects(ObjectType.Element, RoomSelectionFilter(), "Selecione os ambientes")
                for r in picked_refs: all_rooms.append(doc.GetElement(r.ElementId))
            except: 
                gravar_log_padronizado("Cancelado", start_time, doc)
                all_rooms = [] 

            if len(all_rooms) > 0:
                progress_win = WinFormsProgressWindow()
                progress_win.set_max(len(all_rooms))
                progress_win.show()

                t = Transaction(doc, "Criar Revestimentos")
                t.Start()
                try:
                    all_created_walls, counter = [], 0
                    total_rooms = len(all_rooms)
                    for room in all_rooms:
                        counter += 1
                        
                        if counter % 5 == 0 or counter == total_rooms:
                            progress_win.update(counter, total_rooms)

                        if progress_win.interrupt: break

                        if safe_get(user_settings, "create_floors"):
                            create_floor_for_room(doc, room, user_settings["floor_settings"])
                        if safe_get(user_settings, "create_walls"):
                            floor_settings_for_walls = user_settings.get("floor_settings", {})
                            walls_from_room = create_walls_for_room(doc, room, user_settings["wall_settings"], active_level_id, floor_settings_for_walls)
                            if walls_from_room: all_created_walls.append(walls_from_room)

                    if all_created_walls: join_geometry(doc, all_created_walls)

                    if progress_win.interrupt:
                        t.RollBack()
                        TaskDialog.Show("Cancelado", "Operação cancelada pelo usuário.")
                        gravar_log_padronizado("Cancelado", start_time, doc)
                    else:
                        t.Commit()
                        gravar_log_padronizado("Sucesso", start_time, doc)
                        
                except Exception as ex:
                    t.RollBack()
                    TaskDialog.Show("Erro na Criação", "Ocorreu um erro: " + str(ex))
                    gravar_log_padronizado("Falha", start_time, doc)
                finally:
                    progress_win.close()

except Exception as ex:
    TaskDialog.Show("Erro Crítico", "Ocorreu um erro inesperado: " + str(ex))
    gravar_log_padronizado("Falha", start_time, doc)