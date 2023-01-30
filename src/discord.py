import flet as ft
import requests


class Discord(ft.UserControl):
    def __init__(self, parent, page: ft.Page):
        from .app_layout import UserInterface
        super().__init__()
        self.parent: UserInterface = parent
        self.page = page
        self.color_scheme = parent.color_scheme
        
        self.ui()
        self.set_initial_values()
        self.page.update()
        
    def ui(self):
        self.webhook_field = ft.TextField(
            label="Webhook URL",
            helper_text="Webhook url from your server",
            error_style=ft.TextStyle(color="red"),
            label_style=ft.TextStyle(size=16),
            text_size=12,
            expand=6,
            border_color=self.color_scheme,
            height=85,
            on_change=self.webhook_on_change,
            suffix=ft.IconButton(
                icon=ft.icons.CLEAR,
                icon_size=14,
                icon_color=self.color_scheme,
                on_click=lambda e: self.clear_field(e, self.webhook_field),
            )
        )
        self.paste_button = ft.TextButton(
            text="Paste",
            icon=ft.icons.PASTE,
            icon_color=self.color_scheme,
            expand=1,
            tooltip="Paste from clipboard",
            on_click=lambda e: self.paste_event(e, self.webhook_field),
        )
        self.discord_switch = ft.Switch(
            label="Send to Discord",
            active_color=self.color_scheme,
            tooltip="Save webhook url and send log messages to your Discord server",
            on_change=self.discord_switch_event,
        )
        self.delete_button = ft.TextButton(
            text="Delete",
            icon=ft.icons.DELETE,
            icon_color=self.color_scheme,
            on_click=self.delete_click,
        )
        self.save_button = ft.TextButton(
            text="Save",
            icon=ft.icons.SAVE,
            icon_color=self.color_scheme,
            on_click=self.save,
        )
        self.test_message_field = ft.TextField(
            label="Test message",
            helper_text="Send a test message to your Discord server",
            border_color=self.color_scheme,
            expand=6,
            height=85,
            error_style=ft.TextStyle(color="red"),
            suffix=ft.IconButton(
                icon=ft.icons.CLEAR,
                icon_size=14,
                icon_color=self.color_scheme,
                on_click=lambda e: self.clear_field(e, self.test_message_field),
            )
        )
        self.send_message_button = ft.TextButton(
            text="Send",
            icon=ft.icons.SEND,
            expand=1,
            icon_color=self.color_scheme,
            on_click=self.send_message,
        )
        self.discord_card = ft.Card(
            expand=12,
            content=ft.Container(
                margin=ft.margin.all(15),
                height=600,
                alignment=ft.alignment.top_left,
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text(
                                    value="Discord settings",
                                    weight=ft.FontWeight.BOLD,
                                    size=24,
                                    expand=6,
                                    text_align="center",
                                )
                            ],
                        ),
                        ft.Divider(),
                        ft.Row(
                            controls=[
                                self.webhook_field,
                                self.paste_button
                            ]
                        ),
                        ft.Row(
                            controls=[
                                self.discord_switch,
                                self.delete_button,
                                self.save_button,
                            ],
                            alignment="end"
                        ),
                        ft.Divider(),
                        ft.Row(
                            controls=[
                                self.test_message_field,
                                self.send_message_button,
                            ]
                        )
                    ],
                    alignment=ft.MainAxisAlignment.START,
                )
            )
        )
    
    def build(self):
        return ft.Container(
            margin=ft.margin.all(25),
            alignment=ft.alignment.top_center,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.START,
                horizontal_alignment="stretch",
                controls=[
                    ft.Row(
                        controls=[self.discord_card],
                        alignment=ft.MainAxisAlignment.CENTER,
                    )
                ]
            )
        ) 
    
    def set_initial_values(self):
        self.webhook_field.value = self.page.client_storage.get("MRFarmer.discord_webhook_url")
        self.discord_switch.value = self.page.client_storage.get("MRFarmer.send_to_discord")
        self.page.update()
    
    def toggle_theme_mode(self, color_scheme):
        self.color_scheme = color_scheme
        # webhook field
        self.webhook_field.border_color = color_scheme
        self.webhook_field.suffix.icon_color = color_scheme
        self.paste_button.icon_color = color_scheme
        # witch and buttons
        self.discord_switch.active_color = color_scheme
        self.delete_button.icon_color = color_scheme
        self.save_button.icon_color = color_scheme
        # test message
        self.test_message_field.border_color = color_scheme
        self.send_message_button.icon_color = color_scheme
        
    
    def clear_field(self, e, control: ft.TextField):
        if control.label == "Webhook URL":
            self.discord_switch.value = False
            self.page.client_storage.set("MRFarmer.send_to_discord", False)
        control.value = ""
        self.page.update()
        
    def paste_event(self, e, control: ft.TextField):
        value = self.page.get_clipboard()
        control.value = value
        if control.error_text:
            control.error_text = None
        self.page.update()
        
    def discord_switch_event(self, e):
        if self.is_webhook_url_filled():
            self.page.client_storage.set("MRFarmer.send_to_discord", self.discord_switch.value)
            self.save(e)
        
    def webhook_on_change(self, e):
        if self.discord_switch.value and self.webhook_field.value == "":
            self.webhook_field.error_text = "This field is required"
            self.discord_switch.value = False
            self.page.client_storage.set("MRFarmer.send_to_discord", False)
            self.page.update()
            return None
        else:
            if self.webhook_field.error_text:
                self.webhook_field.error_text = None
                self.page.update()
                
    def delete_click(self, e):
        self.webhook_field.value = ""
        self.discord_switch.value = False
        self.page.client_storage.set("MRFarmer.send_to_discord", False)
        if self.webhook_field.error_text:
            self.webhook_field.error_text = None
        self.page.update()
        
    def save(self, e):
        if self.is_webhook_url_filled():
            self.page.client_storage.set("MRFarmer.discord_webhook_url", self.webhook_field.value)
        
    def send_message(self, e):
        if self.is_webhook_url_filled():
            if self.test_message_field.value == "":
                self.test_message_field.error_text = "This field is required"
                self.page.update()
                return None
            response = requests.post(self.webhook_field.value, json={"content": self.test_message_field.value})
            if response.status_code == 204: # TODO: add error handler
                pass
        
    def is_webhook_url_filled(self):
        if self.webhook_field.value == "":
            self.webhook_field.error_text = "This field is required"
            self.discord_switch.value = False
            self.page.client_storage.set("MRFarmer.send_to_discord", False)
            self.page.update()
            return False
        return True
        
    