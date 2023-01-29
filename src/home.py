import flet as ft
from datetime import datetime
import json
import copy


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
        self.open_accounts_button = ft.FloatingActionButton(
            "Open",
            expand=1,
            height=self.accounts_path.height,
            icon=ft.icons.FILE_OPEN,
            bgcolor=self.color_scheme,
            on_click=lambda _: self.pick_accounts_file.pick_files(
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["json",]
            )
        )
        
        # Timer control
        self.timer_field = ft.TextField(
            label="Set time",
            helper_text="Set time in 24h format (HH:MM) if you want to run it at specific time",
            border_color=self.color_scheme,
            icon=ft.icons.TIMER,
            multiline=False,
            expand=5,
            error_style=ft.TextStyle(color=ft.colors.RED_300),
            on_change=self.is_time_valid,
            max_length=5,
        )
        self.timer_switch = ft.Switch(
            label="Enable timer",
            active_color=self.color_scheme,
            on_change=self.timer_switch_event,
            expand=1,
        )
        
        self.main_card = ft.Card(
            expand=6,
            content=ft.Container(
                margin=ft.margin.all(15),
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text(
                                    "Farmer",
                                    size=24,
                                    weight=ft.FontWeight.BOLD,
                                    text_align="center",
                                    expand=6
                                )
                            ]
                        ),
                        ft.Divider(),
                        ft.Row(
                            controls=[
                                self.accounts_path,
                                self.open_accounts_button,
                            ]
                        ),
                        ft.Row(
                            controls=[
                                self.timer_field,
                                self.timer_switch
                            ]
                        )
                    ]
                )
            )
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
                            self.main_card,
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
        if e.files:
            if self.is_account_file_valid(e.files[0].path):
                self.page.client_storage.set("MRFarmer.accounts_path", e.files[0].path)
                self.look_for_log_in_accounts()
                self.accounts_path.value = e.files[0].path
                if self.start_button.disabled:
                    self.start_button.disabled = False
                self.parent.accounts_page.sync_accounts()
                self.page.update()
                
    def disable_start_button(self):
        self.start_button.disabled = True
        self.page.update()
    
    def is_account_file_valid(self, path, on_start: bool = False):
        """Check to see wheather selected file json readable or not to display error"""
        try:
            accounts: list = json.load(open(path, "r"))
            for account in accounts:
                if not all(key in account for key in ("username", "password")):
                    error_account = copy.deepcopy(account)
                    error_account["password"] = "*****"
                    error_account.pop("log", None)
                    error_account.pop("mobile_user_agent", None)
                    error_account.pop("proxy", None)
                    raise KeyError(f"Lookup to find either username or password in {error_account} failed.")
        except KeyError as e:
            if not on_start:
                self.parent.display_error("Key error", e)
            else:
                self.page.client_storage.set("MRFarmer.accounts_path", "")
                self.disable_start_button()
            return False
        except json.decoder.JSONDecodeError:
            if not on_start:
                self.parent.display_error("JSON error", "Selected file is not a valid JSON file. Make sure it doesn't have typo.")
            else:
                self.page.client_storage.set("MRFarmer.accounts_path", "")
                self.disable_start_button()
            return False
        except FileNotFoundError:
            self.page.client_storage.set("MRFarmer.accounts_path", "")
            self.disable_start_button()
            return False
        else:
            self.accounts = accounts
            return True
      
    def is_time_valid(self, e):
        try:
            datetime.strptime(e.data, "%H:%M")
            if len(e.data) < 5:
                raise ValueError
        except ValueError:
            self.timer_switch.disabled = True
            self.timer_switch.value = False
            self.page.client_storage.set("MRFarmer.timer_switch", False)
            self.timer_field.error_text = "Invalid time"
            self.page.update()
        else:
            self.page.client_storage.set("MRFarmer.timer", e.data)
            if self.timer_switch.disabled:
                self.timer_switch.disabled = False
                self.page.update()
            if self.timer_field.error_text:
                self.timer_field.error_text = None
                self.page.update()
                
    def timer_switch_event(self, e):
        self.page.client_storage.set("MRFarmer.timer_switch", self.timer_switch.value)
        self.timer_field.disabled = not self.timer_switch.value
        self.page.update()
        
    def set_initial_values(self):
        """Get values from client storage and set them to controls"""
        if self.is_account_file_valid(self.page.client_storage.get("MRFarmer.accounts_path"), on_start=True):
            self.accounts_path.value = self.page.client_storage.get("MRFarmer.accounts_path")
            self.look_for_log_in_accounts()
        else:
            self.page.client_storage.set("MRFarmer_accounts_path", "")
            self.accounts_path.value = ""
        self.accounts_path.value = self.page.client_storage.get("MRFarmer.accounts_path")
        self.timer_field.value = self.page.client_storage.get("MRFarmer.timer")
        self.timer_switch.value = self.page.client_storage.get("MRFarmer.timer_switch")
        self.page.update()
        
    def clear_accounts_path(self, e):
        self.accounts_path.value = ""
        self.page.client_storage.set("MRFarmer.accounts_path", "")
        self.page.session.remove("MRFarmer.accounts")
        self.parent.accounts_page.remove_accounts()
        self.start_button.disabled = True
        self.page.update()
        
    def toggle_theme_mode(self, color_scheme):
        self.color_scheme = color_scheme
        self.open_accounts_button.bgcolor = color_scheme
        self.accounts_path.border_color = color_scheme
        self.timer_field.border_color = color_scheme
        self.timer_switch.active_color = color_scheme
    
    def look_for_log_in_accounts(self):
        """check for log in account and create it if not exist for each account in accounts file"""
        default_log_dict = {
            "Last check": "Not farmed yet",
            "Today's points": 0,
            "Points": 0,
            "Daily": False,
            "Punch cards": False,
            "More promotions": False,
            "PC searches": False,
            "Mobile searches": False
        }
        for account in self.accounts:
            need_to_update = False
            if not account.get("log", False):
                account["log"] = default_log_dict
                need_to_update = True
            elif not isinstance(account["log"], dict):
                account["log"] = default_log_dict
                need_to_update = True
        else:
            self.page.session.set("MRFarmer.accounts", self.accounts)
            if need_to_update:
                self.parent.update_accounts_file()
                