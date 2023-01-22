import flet as ft
from datetime import datetime
from pathlib import Path


class Home(ft.UserControl):
    def __init__(self, parent, page: ft.Page):
        super().__init__()
        self.parent = parent
        self.page = page
        self.color_scheme = parent.color_scheme
        
        self.ui()
        self.page.update()
        self.set_initial_values()
        
    def ui(self):
        self.pick_accounts_file = ft.FilePicker(on_result=self.pick_accounts_result)
        self.page.overlay.append(self.pick_accounts_file)
        
        # Accounts controls
        self.accounts_controls = []
        self.accounts_path = ft.TextField(
            label="Accounts Path",
            height=75,
            icon=ft.icons.FILE_OPEN,
            border_color=ft.colors.BLUE_300 if self.page.theme_mode == "light" else ft.colors.INDIGO_300,
            read_only=True,
            multiline=False,
            expand=5,
            suffix=ft.IconButton(
                icon=ft.icons.CLEAR,
                on_click=self.clear_accounts_path,
            ),
        )
        self.open_accounts_button = ft.ElevatedButton(
            "Open",
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
            border_color=self.color_scheme,
            icon=ft.icons.TIMER,
            multiline=False,
            expand=5,
            error_style=ft.TextStyle(color=ft.colors.RED_300),
            on_change=self.is_time_valid,
            max_length=5,
        )
        self.timer_check_box = ft.Checkbox(
            label="Enable timer",
            height=self.timer_field.height,
            fill_color=self.color_scheme,
            on_change=self.timer_checkbox,
            expand=1,
            scale=1.2,
        )
        
        # Card to display current account, points counter, section and detail
        self.current_account_label = ft.Text("Current account")
        self.current_points_label = ft.Text("Current point:")
        self.current_points = ft.Text("0")
        self.section_label = ft.Text("Section:")
        self.section = ft.Text("-")
        self.detail_label = ft.Text("Detail:")
        self.detail = ft.Text("-")
        self.account_description_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.ListTile(
                            title=self.current_account_label,
                            leading=ft.Icon(ft.icons.EMAIL),
                            subtitle=ft.Text("Information about current account"),
                        ),
                        ft.Row(
                            controls=[
                                self.current_points_label,
                                self.current_points
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            expand=True
                        ),
                        ft.Row(
                            controls=[
                                self.section_label,
                                self.section
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            expand=True
                        ),
                        ft.Row(
                            controls=[
                                self.detail_label,
                                self.detail
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            expand=True
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                ),
            margin=ft.margin.all(15),
            ),
            height=270,
            expand=3,
            disabled=False,
            margin=ft.margin.symmetric(vertical=25)
        )
        
        # Card to display overall information about all accounts
        self.number_of_accounts_label = ft.Text("All: ", text_align="left")
        self.number_of_accounts = ft.Text("0", text_align="right")
        self.finished_accounts_label = ft.Text("Finished: ")
        self.number_of_finished_accounts = ft.Text("0")
        self.locked_accounts_label = ft.Text("Locked: ")
        self.number_of_locked_accounts = ft.Text("0")
        self.suspended_accounts_label = ft.Text("Suspended: ")
        self.number_of_supended_accounts = ft.Text("0")
        self.overall_description_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.ListTile(
                            leading=ft.Icon(ft.icons.INFO),
                            title=ft.Text("Accounts informations"),
                            subtitle=ft.Text("Overall information about all accounts"),
                        ),
                        ft.Row(
                            controls=[
                                self.number_of_accounts_label,
                                self.number_of_accounts
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        ft.Row(
                            controls=[
                                self.finished_accounts_label,
                                self.number_of_finished_accounts
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        ft.Row(
                            controls=[
                                self.locked_accounts_label,
                                self.number_of_locked_accounts
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        ft.Row(
                            controls=[
                                self.suspended_accounts_label,
                                self.number_of_supended_accounts
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                ),
            margin=ft.margin.all(15),
            ),
            expand=3,
            margin=ft.margin.symmetric(vertical=25)
        )
        
        # Start and stop buttons
        self.start_button = ft.ElevatedButton(
            text="Start",
            icon=ft.icons.START,
        )
        self.stop_button = ft.ElevatedButton(
            text="Stop",
            icon=ft.icons.STOP,
            disabled=True,
            color="red",
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
                    ),
                    ft.Row(
                        controls=[
                            self.account_description_card,
                            self.overall_description_card
                        ]
                    ),
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                self.stop_button,
                                self.start_button
                            ],
                            alignment=ft.MainAxisAlignment.CENTER
                        ),
                        margin=ft.margin.symmetric(vertical=25)
                    )
                ]
            )
        )
        
    def pick_accounts_result(self, e: ft.FilePickerResultEvent):
        self.accounts_path.value = e.files[0].path if e.files else None
        self.page.client_storage.set("MRFarmer.accounts_path", self.accounts_path.value)
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
            self.page.client_storage.set("MRFarmer.timer", e.data)
            if self.timer_check_box.disabled:
                self.timer_check_box.disabled = False
                self.page.update()
            if self.timer_field.error_text:
                self.timer_field.error_text = None
                self.page.update()
                
    def timer_checkbox(self, e):
        self.page.client_storage.set("MRFarmer.timer_checkbox", True if e.data == "true" else False)
        if e.data == "true":
            self.timer_field.disabled = False
        else:
            self.timer_field.disabled = True
        self.page.update()
        
    def set_initial_values(self):
        """Get values from client storage and set them to controls"""
        self.accounts_path.value = self.page.client_storage.get("MRFarmer.accounts_path")
        self.timer_field.value = self.page.client_storage.get("MRFarmer.timer")
        self.timer_check_box.value = self.page.client_storage.get("MRFarmer.timer_checkbox")
        self.page.update()
        
    def clear_accounts_path(self, e):
        self.accounts_path.value = None
        self.page.client_storage.remove("MRFarmer.accounts_path")
        self.page.update()
        
    def toggle_theme_mode(self, color_scheme):
        self.color_scheme = color_scheme
        self.accounts_path.border_color = self.color_scheme
        self.timer_field.border_color = self.color_scheme
        self.timer_check_box.fill_color = self.color_scheme
        