import flet as ft
from datetime import datetime
import json
import copy
from ..core.farmer import Farmer, WebDriver


class Home(ft.UserControl):
    def __init__(self, parent, page: ft.Page):
        from .app_layout import UserInterface 
        super().__init__()
        self.parent: UserInterface = parent
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
            border_color=self.color_scheme,
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
            label="Timer",
            tooltip="By enabling this bot will run at the time you entered when you start it",
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
        self.current_account_label = ft.Text("Current account: None")
        self.current_points_label = ft.Text("Current point:")
        self.current_point = ft.Text("0")
        self.section_label = ft.Text("Section:")
        self.section = ft.Text("-")
        self.detail_label = ft.Text("Detail:")
        self.detail = ft.Text("-")
        self.proxy_label = ft.Text("Proxy:")
        self.proxy = ft.Text("-")
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
                                self.current_point
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Row(
                            controls=[
                                self.section_label,
                                self.section
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Row(
                            controls=[
                                self.detail_label,
                                self.detail
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Row(
                            controls=[
                                self.proxy_label,
                                self.proxy
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                ),
            margin=ft.margin.all(15),
            ),
            expand=3,
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
        self.number_of_suspended_accounts = ft.Text("0")
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
                                self.number_of_suspended_accounts
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
        self.start_progress_ring = ft.ProgressRing(color="blue", scale=0.75, visible=False)
        self.start_icon = ft.Icon(ft.icons.START, color="blue")
        self.start_button = ft.ElevatedButton(
            on_click=self.start,
            scale=1.3,
            content=ft.Row(
                controls=[
                    self.start_progress_ring,
                    self.start_icon,
                    ft.Text("Start", color="blue", text_align="center")
                ]
            )
        )
        self.stop_progress_ring = ft.ProgressRing(color="red", scale=0.75, visible=False)
        self.stop_icon = ft.Icon(ft.icons.STOP, color="red")
        self.stop_button = ft.ElevatedButton(
            disabled=True,
            scale=1.3,
            on_click=self.stop,
            content=ft.Row(
                controls=[
                    self.stop_progress_ring,
                    self.stop_icon,
                    ft.Text("Stop", color="red", text_align="center")
                ]
            )
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
                            spacing=40,
                            alignment=ft.MainAxisAlignment.CENTER
                        ),
                        margin=ft.margin.symmetric(vertical=20)
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
        '''Check to see wheather selected file json readable or not to display error if all good then set account to self.accounts'''
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
            self.start_button.disabled = True
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
        """check for log in account and create it if not exist for each account in accounts file then save accounts in session"""
        need_to_update = False
        default_log_dict = {
            "Last check": "Not farmed yet",
            "Today's points": 0,
            "Points": 0,
            "Daily": False,
            "Punch cards": False,
            "More promotions": False,
            "MSN shopping game": False,
            "PC searches": False,
            "Mobile searches": False
        }
        if len(self.accounts) == 0:
            self.accounts.append({"username": "your email", "password": "your password"})
        for account in self.accounts:
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
                
    def update_section(self, message: str):
        self.section.value = message
        self.page.update()
        
    def update_detail(self, message: str):
        self.detail.value = message
        self.page.update()
        
    def update_points_counter(self, point: int):
        self.current_point.value = str(point)
        self.page.update()
    
    def update_current_account(self, account: str):
        self.current_account_label.value = account.capitalize()
        self.page.update()
    
    def update_proxy(self, proxy: str):
        self.proxy.value = proxy
        self.page.update()
      
    def update_overall_infos(self):
        self.number_of_accounts.value = len(self.accounts)
        self.number_of_finished_accounts.value = len(self.farmer.finished_accounts)
        self.number_of_locked_accounts.value = len(self.farmer.locked_accounts)
        self.number_of_suspended_accounts.value = len(self.farmer.suspended_accounts)
        self.page.update()
        
    def start(self, e):
        self.start_button.disabled = True
        self.parent.is_farmer_running = True
        self.page.floating_action_button.disabled = True
        self.accounts_path.disabled = True
        self.open_accounts_button.disabled = True
        self.timer_field.disabled = True
        self.timer_switch.disabled = True
        self.start_icon.visible = False
        self.start_progress_ring.visible = True
        self.page.update()
        self.farmer = Farmer(self.page, self.parent, self, self.parent.accounts_page)
        self.stop_button.disabled = False
        self.update_overall_infos()
        self.start_icon.visible = True
        self.start_progress_ring.visible = False
        self.page.update()
        self.farmer.perform_run()
        
    def stop(self, e):
        self.stop_button.disabled = True
        self.stop_progress_ring.visible = True
        self.stop_icon.visible = False
        self.parent.is_farmer_running = False
        self.page.update()
        if isinstance(self.farmer.browser, WebDriver):
            self.farmer.browser.quit()
        self.finished()
        
    def finished(self):
        self.parent.is_farmer_running = False
        self.current_point.value = 0
        self.section.value =  "-"
        self.detail.value = "-"
        self.current_account_label.value = "Current account: None"
        self.proxy.value = "-"
        self.stop_button.disabled = True
        self.start_button.disabled = False
        self.page.floating_action_button.disabled = False
        self.accounts_path.disabled = False
        self.open_accounts_button.disabled = False
        self.timer_field.disabled = False
        self.timer_switch.disabled = False
        self.stop_progress_ring.visible = False
        self.stop_icon.visible = True
        self.page.update()
        