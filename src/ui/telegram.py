import flet as ft
from notifiers import get_notifier
from notifiers.exceptions import NotificationError


class Telegram(ft.UserControl):
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
        self.telegram_settings_title = ft.Text(
            value="Telegram settings",
            size=24,
            weight=ft.FontWeight.BOLD,
            selectable=False,
            expand=6,
            text_align="center"
        )
        # token
        self.token_field = ft.TextField(
            label="Token",
            border_color=self.color_scheme,
            expand=6,
            height=80,
            multiline=False,
            icon=ft.icons.TOKEN,
            helper_text="Enter your Telegram bot token",
            suffix=ft.IconButton(
                icon=ft.icons.CLEAR,
                on_click=lambda e: self.clear_text_fields(e, self.token_field),
            ),
            on_change=lambda e: self.text_fields_on_change(e, self.token_field),
            error_style=ft.TextStyle(color="red")
        )
        self.token_paste_button = ft.TextButton(
            text="Paste",
            icon=ft.icons.PASTE,
            icon_color=self.color_scheme,
            tooltip="Paste from clipboard",
            on_click=lambda e: self.paste_from_clipboard(e, self.token_field),
            expand=1
        )
        # chat id
        self.chat_id_field = ft.TextField(
            label="Chat ID",
            border_color=self.color_scheme,
            expand=6,
            height=80,
            multiline=False,
            icon=ft.icons.PERM_IDENTITY,
            helper_text="Enter your Telegram chat ID (Unique integer for each user)",
            suffix=ft.IconButton(
                icon=ft.icons.CLEAR,
                on_click=lambda e: self.clear_text_fields(e, self.chat_id_field),
            ),
            on_change=lambda e: self.text_fields_on_change(e, self.chat_id_field),
            error_style=ft.TextStyle(color="red")
        )
        self.chat_id_paste_button = ft.TextButton(
            text="Paste",
            icon=ft.icons.PASTE,
            icon_color=self.color_scheme,
            tooltip="Paste from clipboard",
            on_click=lambda e: self.paste_from_clipboard(e, self.chat_id_field),
            expand=1
        )
        # Switch & button
        self.send_to_telegram_switch = ft.Switch(
            label="Send to Telegram",
            active_color=self.color_scheme,
            tooltip="Save token and chat id and send log messages to your Telegram account",
            on_change=lambda e: self.send_to_telegram_switch_on_change(e, self.send_to_telegram_switch),
        )
        self.delete_button = ft.TextButton(
            text="Delete",
            icon=ft.icons.DELETE,
            icon_color=self.color_scheme,
            tooltip="Delete saved Telegram settings from storage",
            on_click=self.delete,
        )
        self.save_button = ft.TextButton(
            text="Save",
            icon=ft.icons.SAVE,
            icon_color=self.color_scheme,
            on_click=self.save,
            tooltip="Save token and chat id in storage (It won't save if you don't fill both token and chat id fields)",
        )
        # test message
        self.test_message_field = ft.TextField(
            label="Test message",
            icon=ft.icons.MESSAGE,
            border_color=self.color_scheme,
            helper_text="If you want to send a test message, enter it here",
            height=80,
            expand=6,
            on_change=self.test_message_on_change,
            error_style=ft.TextStyle(color="red"),
            suffix=ft.IconButton(
                icon=ft.icons.CLEAR,
                on_click=lambda e: self.clear_text_fields(e, self.test_message_field),
            ),
        )
        self.progress_ring = ft.ProgressRing(scale=0.7, color=self.color_scheme, visible=False)
        self.send_icon = ft.Icon(name=ft.icons.SEND, color=self.color_scheme)
        self.send_test_message_button = ft.ElevatedButton(
            icon_color=self.color_scheme,
            on_click=self.send_test_message,
            expand=1,
            tooltip="Send message",
            content=ft.Row(
                controls=[
                    self.progress_ring,
                    self.send_icon,
                    ft.Text(value="Send", text_align="center"),
                ],
                alignment="center"
            )
        )
        
        self.telegram_card = ft.Card(
            content=ft.Container(
                height=600,
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                self.telegram_settings_title,
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            vertical_alignment="center"
                        ),
                        ft.Divider(),
                        ft.Row(
                            controls=[
                                self.token_field,
                                self.token_paste_button
                            ]
                        ),
                        ft.Row(
                            controls=[
                                self.chat_id_field,
                                self.chat_id_paste_button
                            ]
                        ),
                        ft.Row(
                            controls=[
                                self.send_to_telegram_switch,
                                self.delete_button,
                                self.save_button
                            ],
                            alignment="end"
                        ),
                        ft.Divider(),
                        ft.Row(
                            controls=[
                                self.test_message_field,
                                self.send_test_message_button
                            ]
                        )
                    ],
                    alignment=ft.MainAxisAlignment.START,
                ),
                margin=ft.margin.all(15)
            ),
            expand=6
        )
        
    
    def build(self):
        return ft.Container(
            margin=ft.margin.all(25),
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment="stretch",
                controls=[
                    ft.Row(
                        controls=[self.telegram_card],
                        alignment=ft.MainAxisAlignment.CENTER,
                    )
                ]
            )
        )
    
    def set_initial_values(self):
        self.token_field.value = self.page.client_storage.get("MRFarmer.telegram_token")
        self.chat_id_field.value = self.page.client_storage.get("MRFarmer.telegram_chat_id")
        self.send_to_telegram_switch.value = self.page.client_storage.get("MRFarmer.send_to_telegram")
        self.page.update()
        
    def toggle_theme_mode(self, color_scheme):
        self.color_scheme = color_scheme
        # token
        self.token_field.border_color = color_scheme
        self.token_paste_button.icon_color = color_scheme
        # chat id
        self.chat_id_field.border_color = color_scheme
        self.chat_id_paste_button.icon_color = color_scheme
        # switch & buttons
        self.send_to_telegram_switch.active_color = color_scheme
        self.delete_button.icon_color = color_scheme
        self.save_button.icon_color = color_scheme
        # test message
        self.test_message_field.border_color = color_scheme
        self.send_icon.color = color_scheme
        self.progress_ring.color = color_scheme
        
    def clear_text_fields(self, e, control: ft.TextField):
        if control.label in ["Token", "Chat ID"]:
            self.send_to_telegram_switch.value = False
            self.page.client_storage.set("MRFarmer.send_to_telegram", False)
        control.value = ""
        self.page.update()
        
    def paste_from_clipboard(self, e, control: ft.TextField):
        value = self.page.get_clipboard()
        control.value = value
        self.are_telegram_fields_filled()
        self.page.update()
        
    def save(self, e):
        if self.are_telegram_fields_filled():
            self.page.update()
            self.page.client_storage.set("MRFarmer.telegram_token", self.token_field.value)
            self.page.client_storage.set("MRFarmer.telegram_chat_id", self.chat_id_field.value)
        
    def delete(self, e):
        self.page.client_storage.remove("MRFarmer.telegram_token")
        self.page.client_storage.remove("MRFarmer.telegram_chat_id")
        self.page.client_storage.set("MRFarmer.send_to_telegram", False)
        self.token_field.value = None
        self.chat_id_field.value = None
        self.send_to_telegram_switch.value = False
        self.page.update()
        
    def send_to_telegram_switch_on_change(self, e, control: ft.Switch):
        if self.are_telegram_fields_filled():
            self.save(e)
            self.page.client_storage.set("MRFarmer.send_to_telegram", control.value)
        
    def text_fields_on_change(self, e, control: ft.TextField):
        telegram_fields = [self.token_field, self.chat_id_field]
        if self.send_to_telegram_switch.value:
            for field in telegram_fields:
                if field.value == "":
                    field.error_text = "This field is required"
            self.page.client_storage.set("MRFarmer.send_to_telegram", False)
            self.send_to_telegram_switch.value = False
            self.page.update()
        else:
            for field in telegram_fields:
                if field.value != "":
                    field.error_text = None
            self.page.update()
    
    def send_test_message(self, e):
        if not self.are_telegram_fields_filled():
            return None
        if self.test_message_field.value == "":
            self.test_message_field.error_text = "This field is required"
            self.page.update()
            return None
        notifier = get_notifier("telegram")
        self.send_test_message_button.disabled = True
        self.send_icon.visible = False
        self.progress_ring.visible = True
        self.page.update()
        try:
            notifier.notify(
                message=self.test_message_field.value,
                token=self.token_field.value,
                chat_id=self.chat_id_field.value,
                raise_on_errors=True
            )
        except NotificationError as e:
            self.parent.open_snack_bar(f"Couldn't send test message {e}")
        else:
            self.parent.open_snack_bar(f"Test message sent successfully")
        self.send_test_message_button.disabled = False
        self.send_icon.visible = True
        self.progress_ring.visible = False
        self.page.update()
        
    def test_message_on_change(self, e):
        if self.test_message_field.value != "" and self.test_message_field.error_text:
            self.test_message_field.error_text = None
            self.page.update()
           
    def are_telegram_fields_filled(self):
        telegram_fields = [self.token_field, self.chat_id_field]
        error = False
        for field in telegram_fields:
            if field.value == "":
                error = True
                field.error_text = "This field is required"
                self.send_to_telegram_switch.value = False
            else:
                if field.error_text:
                    field.error_text = None
                self.page.update()
        if error: 
            self.page.update()
            return False
        return True