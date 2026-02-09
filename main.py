import sqlite3
import os
from datetime import datetime
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.app import MDApp
from kivymd.uix.pickers import MDDatePicker, MDTimePicker
from kivymd.uix.list import ThreeLineListItem
from kivy.core.window import Window
from kivy.clock import Clock
from plyer import notification 
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivy.utils import platform

# Configuración visual
if platform != 'ios' and platform != 'android':
    Window.size = (360, 640)

KV = '''
ScreenManager:
    NotesListScreen:
    CreateNoteScreen:

<NotesListScreen>:
    name: 'list'
    MDBoxLayout:
        orientation: 'vertical'
        MDTopAppBar:
            title: "Mis Notas"
            md_bg_color: 0.5, 0, 0, 1
            elevation: 4
        
        ScrollView:
            MDList:
                id: container

    MDFloatingActionButton:
        icon: "plus"
        md_bg_color: 0.5, 0, 0, 1
        pos_hint: {"center_x": .85, "center_y": .1}
        on_release: app.preparar_nueva_nota()

<CreateNoteScreen>:
    name: 'create'
    MDBoxLayout:
        orientation: 'vertical'
        padding: "16dp"
        spacing: "10dp"

        MDTopAppBar:
            id: toolbar
            title: "Nueva Nota"
            left_action_items: [["arrow-left", lambda x: app.go_back()]]
            md_bg_color: 0.5, 0, 0, 1

        MDTextField:
            id: title_field
            hint_text: "Título"
            font_size: "24sp"
            bold: True
            mode: "rectangle"

        MDTextField:
            id: desc_field
            hint_text: "Descripción..."
            multiline: True
            mode: "rectangle"
            size_hint_y: None
            height: "200dp"

        MDRectangleFlatIconButton:
            icon: "bell-outline"
            text: "Cambiar Fecha/Hora"
            line_color: 0.5, 0, 0, 1
            text_color: 0.5, 0, 0, 1
            on_release: app.show_date_picker()

        MDLabel:
            id: reminder_info
            text: "Sin recordatorio"
            theme_text_color: "Secondary"
            font_style: "Caption"

        MDRaisedButton:
            id: save_button
            text: "GUARDAR"
            md_bg_color: 0.5, 0, 0, 1
            pos_hint: {"center_x": .5}
            size_hint_x: 0.8
            on_release: app.save_note()
'''

class NotesListScreen(Screen): pass
class CreateNoteScreen(Screen): pass

class NotasApp(MDApp):
    fecha_final = ""
    edit_id = None
    dialogo_opciones = None

    def build(self):
        self.theme_cls.primary_palette = "Red"
        self.init_db()
        Clock.schedule_interval(self.check_reminders, 10)
        return Builder.load_string(KV)

    def on_start(self):
        # Pedir permisos en iOS
        if platform == 'ios':
            try:
                from pyobjus import autoclass
                UNUserNotificationCenter = autoclass('UNUserNotificationCenter')
                center = UNUserNotificationCenter.currentNotificationCenter()
                center.requestAuthorizationWithOptions_completionHandler_(7, None)
            except:
                print("No se pudo solicitar permiso de notificación")
        self.load_notes()

    def init_db(self):
        # En iOS el almacenamiento persistente suele estar en 'Documents'
        if platform == 'ios':
            from os.path import expanduser
            ruta_db = os.path.join(expanduser("~"), "Documents", "notas.db")
        else:
            ruta_script = os.path.dirname(os.path.abspath(__file__))
            ruta_db = os.path.join(ruta_script, 'notas.db')
            
        self.conn = sqlite3.connect(ruta_db, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS notas 
                            (id INTEGER PRIMARY KEY, titulo TEXT, desc TEXT, fecha TEXT, avisado INTEGER DEFAULT 0)''')
        self.conn.commit()

    def load_notes(self):
        container = self.root.get_screen('list').ids.container
        container.clear_widgets()
        self.cursor.execute("SELECT id, titulo, desc, fecha FROM notas ORDER BY id DESC")
        for nota in self.cursor.fetchall():
            item = ThreeLineListItem(
                text=f"[b]{nota[1]}[/b]",
                secondary_text=nota[2],
                tertiary_text=f"🔔 {nota[3]}" if nota[3] else "Sin aviso",
                on_release=lambda x, n=nota: self.mostrar_opciones(n)
            )
            container.add_widget(item)

    def mostrar_opciones(self, nota):
        self.nota_actual = nota
        self.dialogo_opciones = MDDialog(
            title="Opciones",
            buttons=[
                MDFlatButton(text="EDITAR", on_release=self.preparar_edicion),
                MDFlatButton(text="BORRAR", text_color=(0.5, 0, 0, 1), on_release=self.eliminar_nota),
            ],
        )
        self.dialogo_opciones.open()

    def eliminar_nota(self, *args):
        self.cursor.execute("DELETE FROM notas WHERE id = ?", (self.nota_actual[0],))
        self.conn.commit()
        self.dialogo_opciones.dismiss()
        self.load_notes()

    def preparar_nueva_nota(self):
        self.edit_id = None
        screen = self.root.get_screen('create')
        screen.ids.toolbar.title = "Nueva Nota"
        screen.ids.title_field.text = ""
        screen.ids.desc_field.text = ""
        screen.ids.reminder_info.text = "Sin recordatorio"
        self.fecha_final = ""
        self.root.current = 'create'

    def preparar_edicion(self, *args):
        self.dialogo_opciones.dismiss()
        nota = self.nota_actual
        self.edit_id = nota[0]
        screen = self.root.get_screen('create')
        screen.ids.toolbar.title = "Editar Nota"
        screen.ids.title_field.text = nota[1]
        screen.ids.desc_field.text = nota[2]
        screen.ids.reminder_info.text = f"Fecha: {nota[3]}" if nota[3] else "Sin recordatorio"
        self.fecha_final = nota[3]
        self.root.current = 'create'

    def save_note(self):
        titulo = self.root.get_screen('create').ids.title_field.text
        desc = self.root.get_screen('create').ids.desc_field.text
        if not titulo.strip(): return

        if self.edit_id:
            self.cursor.execute("UPDATE notas SET titulo=?, desc=?, fecha=?, avisado=0 WHERE id=?",
                               (titulo, desc, self.fecha_final, self.edit_id))
        else:
            self.cursor.execute("INSERT INTO notas (titulo, desc, fecha, avisado) VALUES (?, ?, ?, 0)",
                               (titulo, desc, self.fecha_final))
        self.conn.commit()
        self.load_notes()
        self.go_back()

    def check_reminders(self, dt):
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:00")
        self.cursor.execute("SELECT id, titulo, desc FROM notas WHERE fecha <= ? AND avisado = 0 AND fecha != ''", (ahora,))
        for p in self.cursor.fetchall():
            notification.notify(title=f"Aviso: {p[1]}", message=p[2])
            self.cursor.execute("UPDATE notas SET avisado = 1 WHERE id = ?", (p[0],))
            self.conn.commit()

    def go_back(self):
        self.root.current = 'list'

    def show_date_picker(self):
        d = MDDatePicker()
        d.bind(on_save=self.on_date_save)
        d.open()

    def on_date_save(self, instance, value, date_range):
        self.temp_date = value
        t = MDTimePicker()
        t.bind(on_save=self.on_time_save)
        t.open()

    def on_time_save(self, instance, time):
        self.fecha_final = f"{self.temp_date} {time.strftime('%H:%M:00')}"
        self.root.get_screen('create').ids.reminder_info.text = f"Programado: {self.fecha_final}"

if __name__ == '__main__':
    NotasApp().run()