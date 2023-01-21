import flet as ft
from datetime import time, datetime

class Home(ft.UserControl):
    def __init__(self, app_layout, page: ft.Page):
        super().__init__()
        self.app_layout = app_layout
        self.page = page
        
        self.pick_accounts_file = ft.FilePicker(on_result=self.pick_accounts_result)
        self.page.overlay.append(self.pick_accounts_file)
        self.page.update()
        
        # Accounts controls
        self.accounts_controls = []
        self.accounts_path = ft.TextField(
            label="Accounts Path",
            icon=ft.icons.FILE_OPEN,
            border_color=ft.colors.BLUE_300,
            read_only=True,
            multiline=False,
            expand=5
        )
        self.open_accounts_button = ft.ElevatedButton(
            "Open",
            width=150,
            expand=1,
            height=self.accounts_path.height,
            icon=ft.icons.FILE_OPEN,
            style=ft.ButtonStyle(
                shape={
                    ft.MaterialState.DEFAULT: ft.RoundedRectangleBorder(radius=5),
                },
                padding=ft.padding.all(20)
            ),
            on_click=lambda _: self.pick_accounts_file.pick_files(
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["json",]
            )
        )
        
        # Timer control
        self.timer_field = ft.TextField(
            label="Set time",
            helper_text="Set time in 24h format (HH:MM)",
            border_color=ft.colors.BLUE_300,
            icon=ft.icons.TIMER,
            multiline=False,
            expand=5,
            error_style=ft.TextStyle(color=ft.colors.RED_300),
            on_change=self.is_time_valid,
            max_length=5,
        )
        self.timer_check_box = ft.Checkbox(
            label="Actice timer",
            height=self.timer_field.height,
            fill_color={"hovered": "blue", "selected": "green", "": "blue"},
            on_change=self.timer_checkbox,
            expand=1,
            scale=1.2,
        )
        
    def build(self):
        return ft.Container(
            margin=ft.margin.all(25),
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment="stretch",
                controls=[
                    ft.Row(
                        controls=[
                            self.accounts_path,
                            self.open_accounts_button
                        ]
                    ),
                    ft.Row(
                        controls=[
                            self.timer_field,
                            self.timer_check_box
                        ]
                    )
                ]
            )
        )
        
    def pick_accounts_result(self, e: ft.FilePickerResultEvent):
        self.accounts_path.value = e.files[0].path if e.files else None
        self.page.update()
        
    def is_time_valid(self, e):
        if e.data == "":
            self.timer_field.error_text = None
            self.timer_field.value = "00:00"
            e.data = "00:00"
            self.page.update()
        try:
            datetime.strptime(e.data, "%H:%M")
            if len(e.data) < 5:
                raise ValueError
        except ValueError:
            self.timer_check_box.disabled = True
            self.timer_check_box.value = False
            self.timer_field.error_text = "Invalid time"
            self.page.update()
        else:
            if self.timer_check_box.disabled:
                self.timer_check_box.disabled = False
                self.page.update()
            if self.timer_field.error_text:
                self.timer_field.error_text = None
                self.page.update()
                
    def timer_checkbox(self, e):
        if e.data == "true":
            self.timer_field.disabled = False
        else:
            self.timer_field.disabled = True
        self.page.update()