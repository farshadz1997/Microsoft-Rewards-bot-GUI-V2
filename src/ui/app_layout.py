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
from datetime import datetime


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
        self.light_theme_color = self.get_light_theme_color()
        self.dark_theme_color = self.get_dark_theme_color()
        self.color_scheme = self.get_color_scheme()
        self.page.theme = theme.Theme(color_scheme_seed=self.light_theme_color)
        self.page.dark_theme = theme.Theme(color_scheme_seed=self.dark_theme_color)
        self.page.window_height = 820
        self.page.window_width = 1280
        self.page.window_max_height = 820
        self.page.window_max_width = 1280
        self.page.window_min_height = 700
        self.page.window_min_width = 1080
        self.page.on_resize = self.on_page_resize
        self.page.window_maximizable = False
        self.page.window_center()
        self.page.on_route_change = self.on_route_change
        self.page.on_error = self.save_app_error
        self.is_farmer_running: bool = False
        self.ui()
        self.page.update()
        self.auto_start_if_needed()
        
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
            actions_alignment="center"
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
        self.toggle_theme_button.icon = (
            ft.icons.MODE_NIGHT if self.page.theme_mode == "light" else ft.icons.WB_SUNNY_ROUNDED
        )
        self.change_color_scheme()
        
    def change_color_scheme(self):
        self.color_scheme = self.get_color_scheme()
        self.page.snack_bar.bgcolor = self.color_scheme
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
        self.page.client_storage.set("MRFarmer.auto_start", False)
        ## farmer settings
        self.page.client_storage.set("MRFarmer.daily_quests", True)
        self.page.client_storage.set("MRFarmer.punch_cards", True)
        self.page.client_storage.set("MRFarmer.more_activities", True)
        self.page.client_storage.set("MRFarmer.pc_search", True)
        self.page.client_storage.set("MRFarmer.mobile_search", True)
        self.page.client_storage.set("MRFarmer.msn_shopping_game", False)
        ## theme settings
        self.page.client_storage.set("MRFarmer.light_theme_color", LIGHT_SEED_COLOR)
        self.page.client_storage.set("MRFarmer.light_widgets_color", LIGHT_SEED_COLOR)
        self.page.client_storage.set("MRFarmer.dark_theme_color", DARK_SEED_COLOR)
        self.page.client_storage.set("MRFarmer.dark_widgets_color", ft.colors.INDIGO_300)
        # telegram
        self.page.client_storage.set("MRFarmer.telegram_token", "")
        self.page.client_storage.set("MRFarmer.telegram_chat_id", "")
        self.page.client_storage.set("MRFarmer.send_to_telegram", False)
        # discord
        self.page.client_storage.set("MRFarmer.discord_webhook_url", "")
        self.page.client_storage.set("MRFarmer.send_to_discord", False)
    
    def get_light_theme_color(self):
        if not self.page.client_storage.contains_key("MRFarmer.light_theme_color"):
            self.page.client_storage.set("MRFarmer.light_theme_color", LIGHT_SEED_COLOR)
            return LIGHT_SEED_COLOR
        else:
            return self.page.client_storage.get("MRFarmer.light_theme_color")
        
    def get_dark_theme_color(self):
        if not self.page.client_storage.contains_key("MRFarmer.dark_theme_color"):
            self.page.client_storage.set("MRFarmer.light_theme_color", DARK_SEED_COLOR)
            return DARK_SEED_COLOR
        else:
            return self.page.client_storage.get("MRFarmer.dark_theme_color")
        
    def get_color_scheme(self):
        if self.page.theme_mode == "light":
            if not self.page.client_storage.contains_key("MRFarmer.light_widgets_color"):
                self.page.client_storage.set("MRFarmer.light_widgets_color", LIGHT_SEED_COLOR)
            return self.page.client_storage.get("MRFarmer.light_widgets_color")
        elif self.page.theme_mode == "dark":
            if not self.page.client_storage.contains_key("MRFarmer.dark_widgets_color"):
                self.page.client_storage.set("MRFarmer.dark_widgets_color", ft.colors.INDIGO_300)
            return self.page.client_storage.get("MRFarmer.dark_widgets_color")
            
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
    
    def save_app_error(self, e):
        if e.data == "type 'bool' is not a subtype of type 'List<dynamic>?' in type cast":
            return
        if not self.page.client_storage.get("MRFarmer.save_errors"):
            with open(f"{Path.cwd()}/errors.txt", "a") as f:
                f.write(f"\n-------------------{datetime.now()}-------------------\r\n")
                f.write("APP_ERROR:\n")
                f.write(f"{e.data}\n")
            
    def get_farming_status(self):
        """checks by farmer to know stop or continue farming"""
        return self.is_farmer_running
    
    def auto_start_if_needed(self):
        """Start to Farm if auto start is enabled at startup"""
        if self.page.session.contains_key("MRFarmer.accounts") and self.page.client_storage.get("MRFarmer.auto_start"):
            self.home_page.start(None)
        elif not self.page.session.contains_key("MRFarmer.accounts") and self.page.client_storage.get("MRFarmer.auto_start"):
            self.display_error("Auto start failed", "Could not start auto farming because there is no accounts")
            self.page.update()
            
    def on_page_resize(self, e: ft.ControlEvent):
        width = float(e.data.split(",")[0])
        if width < 1140:
            self.settings_page.msn_shopping_game_switch.label = "MSN"
            self.page.update()
        elif width >= 1140 and self.settings_page.msn_shopping_game_switch.label == "MSN":
            self.settings_page.msn_shopping_game_switch.label = "MSN shopping Game"
            self.page.update()