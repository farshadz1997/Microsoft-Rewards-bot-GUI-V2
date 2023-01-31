import flet as ft
from flet import theme
from .home import Home
from .settings import Settings
from .telegram import Telegram
from .discord import Discord
from .accounts import Accounts
from ..core.farmer import PC_USER_AGENT, MOBILE_USER_AGENT
from .responsive_menu_layout import ResponsiveMenuLayout
from pathlib import Path
import json


LIGHT_SEED_COLOR = ft.colors.TEAL
DARK_SEED_COLOR = ft.colors.INDIGO

class UserInterface:
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Microsoft Rewards Farmer"
        self.page.window_prevent_close = True
        self.page.on_window_event = self.window_event
        if not self.page.client_storage.get("MRFarmer.has_run_before"):
            self.first_time_setup()
        self.page.theme_mode = self.page.client_storage.get("MRFarmer.theme_mode")
        self.color_scheme = ft.colors.TEAL if self.page.theme_mode == "light" else ft.colors.INDIGO_300
        self.page.theme = theme.Theme(color_scheme_seed=LIGHT_SEED_COLOR)
        self.page.dark_theme = theme.Theme(color_scheme_seed=DARK_SEED_COLOR)
        self.page.window_height = 820
        self.page.window_width = 1280
        self.page.window_resizable = False
        self.page.window_maximizable = False
        self.page.window_center()
        self.page.on_route_change = self.on_route_change
        self.is_farmer_running: bool = False
        self.ui()
        self.page.update()
        
        
    def ui(self):
        menu_button = ft.IconButton(ft.icons.MENU)
        
        self.toggle_theme_button = ft.IconButton(
            ft.icons.MODE_NIGHT if self.page.theme_mode == "light" else ft.icons.WB_SUNNY_ROUNDED,
            on_click=self.toggle_theme_mode,
        )
        
        self.page.appbar = ft.AppBar(
            title=ft.Text("Microsoft Rewards Farmer", font_family="Pacifico"),
            leading=menu_button,
            leading_width=40,
            bgcolor=ft.colors.SURFACE_VARIANT,
            actions=[
                self.toggle_theme_button
            ]
        )
        # Exit dialog confirmation
        self.exit_dialog = ft.AlertDialog(
            modal=False,
            title=ft.Text("Exit confirmation"),
            content=ft.Text("Do you really want to exit?"),
            actions=[
                ft.ElevatedButton("Yes", on_click=lambda _: self.page.window_destroy()),
                ft.OutlinedButton("No", on_click=self.no_click),
            ],
            actions_alignment="end",
        )
        
        self.error_dialog = ft.AlertDialog(
            actions=[
                ft.ElevatedButton(
                    text="Ok",
                    on_click=self.close_error)
            ],
            actions_alignment="end"
        )
        
        self.snack_bar_message = ft.Text()
        self.page.snack_bar = ft.SnackBar(content=self.snack_bar_message, bgcolor=self.color_scheme)
        
        self.home_page = Home(self, self.page)
        self.settings_page = Settings(self, self.page)
        self.telegram_page = Telegram(self, self.page)
        self.discord_page = Discord(self, self.page)
        self.accounts_page = Accounts(self, self.page)
        pages = [
            (
                dict(icon=ft.icons.HOME, selected_icon=ft.icons.HOME, label="Home"),
                self.home_page.build()
            ),
            (
                dict(icon=ft.icons.PERSON, selected_icon=ft.icons.PERSON, label="Accounts"),
                self.accounts_page.build()
            ),
            (
                dict(icon=ft.icons.TELEGRAM, selected_icon=ft.icons.TELEGRAM, label="Telegram"),
                self.telegram_page.build()
            ),
            (
                dict(icon=ft.icons.DISCORD, selected_icon=ft.icons.DISCORD, label="Discord"),
                self.discord_page.build()
            ),
            (
                dict(icon=ft.icons.SETTINGS, selected_icon=ft.icons.SETTINGS, label="Settings"),
                self.settings_page.build()
            )
        ]
        
        menu_layout = ResponsiveMenuLayout(self.page, pages, landscape_minimize_to_icons=True)
        menu_button.on_click = lambda e: menu_layout.toggle_navigation()
        self.page.add(menu_layout)
        
    def window_event(self, e):
        if e.data == "close":
            self.page.dialog = self.exit_dialog
            self.exit_dialog.open = True
            self.page.update()
            
    def no_click(self, e):
        self.exit_dialog.open = False
        self.page.update()
    
    def toggle_theme_mode(self, e):
        self.page.theme_mode = "dark" if self.page.theme_mode == "light" else "light"
        self.page.client_storage.set("MRFarmer.theme_mode", self.page.theme_mode)
        self.color_scheme = ft.colors.TEAL if self.page.theme_mode == "light" else ft.colors.INDIGO_300
        self.page.snack_bar.bgcolor = self.color_scheme
        self.toggle_theme_button.icon = (
            ft.icons.MODE_NIGHT if self.page.theme_mode == "light" else ft.icons.WB_SUNNY_ROUNDED
        )
        self.home_page.toggle_theme_mode(self.color_scheme)
        self.settings_page.toggle_theme_mode(self.color_scheme)
        self.telegram_page.toggle_theme_mode(self.color_scheme)
        self.discord_page.toggle_theme_mode(self.color_scheme)
        self.accounts_page.toggle_theme_mode(self.color_scheme)
        self.page.update()
        
    def first_time_setup(self):
        """If it's the first time that app being used, it sets the default values to client storage"""
        directory_path = Path.cwd()
        accounts_path = str(Path(f"{directory_path}\\accounts.json").resolve())
        self.page.client_storage.set("MRFarmer.has_run_before", True)
        self.page.client_storage.set("MRFarmer.theme_mode", "dark")
        # home
        self.page.client_storage.set("MRFarmer.accounts_path", accounts_path)
        self.page.client_storage.set("MRFarmer.timer", "00:00")
        self.page.client_storage.set("MRFarmer.timer_switch", False)
        # settings
        ## user agent
        self.page.client_storage.set("MRFarmer.pc_user_agent", PC_USER_AGENT)
        self.page.client_storage.set("MRFarmer.mobile_user_agent", MOBILE_USER_AGENT)
        ## global settings
        self.page.client_storage.set("MRFarmer.headless", False)
        self.page.client_storage.set("MRFarmer.fast", False)
        self.page.client_storage.set("MRFarmer.session", False)
        self.page.client_storage.set("MRFarmer.save_errors", False)
        self.page.client_storage.set("MRFarmer.shutdown", False)
        self.page.client_storage.set("MRFarmer.edge_webdriver", False)
        self.page.client_storage.set("MRFarmer.use_proxy", False)
        ## farmer settings
        self.page.client_storage.set("MRFarmer.daily_quests", True)
        self.page.client_storage.set("MRFarmer.punch_cards", True)
        self.page.client_storage.set("MRFarmer.more_activities", True)
        self.page.client_storage.set("MRFarmer.pc_search", True)
        self.page.client_storage.set("MRFarmer.mobile_search", True)
        # telegram
        self.page.client_storage.set("MRFarmer.telegram_token", "")
        self.page.client_storage.set("MRFarmer.telegram_chat_id", "")
        self.page.client_storage.set("MRFarmer.send_to_telegram", False)
        # discord
        self.page.client_storage.set("MRFarmer.discord_webhook_url", "")
        self.page.client_storage.set("MRFarmer.send_to_discord", False)
        
    def on_route_change(self, e):
        if e.data == "/accounts":
            self.page.floating_action_button.visible = True
        else:
            self.page.floating_action_button.visible = False
        self.page.update()
    
    def display_error(self, title: str, description: str):
        self.error_dialog.title = ft.Text(title)
        self.error_dialog.content = ft.Text(description)
        self.page.dialog = self.error_dialog
        self.error_dialog.open = True
        self.page.update()
        
    def open_snack_bar(self, message: str):
        self.snack_bar_message.value = message
        self.page.snack_bar.open = True
        self.page.update()
    
    def close_error(self, e):
        self.error_dialog.open = False
        self.page.update()
        
    def update_accounts_file(self):
        with open(self.page.client_storage.get("MRFarmer.accounts_path"), "w") as file:
            file.write(json.dumps(self.page.session.get("MRFarmer.accounts"), indent = 4))
        