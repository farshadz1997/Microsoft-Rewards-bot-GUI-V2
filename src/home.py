import flet as ft


class Home(ft.UserControl):
    def __init__(self, app_layout, page: ft.Page):
        super().__init__()
        self.app_layout = app_layout
        self.page = page
        
        self.pick_accounts_file = ft.FilePicker(on_result=self.pick_accounts_result)
        self.page.overlay.append(self.pick_accounts_file)
        self.page.update()
        
        self.controls = []
        
        self.accounts_path = ft.TextField(
            label="Accounts Path",
            width=100,
            border_color=ft.colors.BLUE_300,
            read_only=True,
            multiline=False,
            expand=True
        )
        self.controls.append(self.accounts_path)
        
        self.open_accounts_button = ft.ElevatedButton(
            "Open",
            width=150,
            height=self.accounts_path.height,
            icon=ft.icons.FILE_OPEN,
            on_click=lambda _: self.pick_accounts_file.pick_files(
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["json",]
            )
        )
        self.controls.append(self.open_accounts_button)

    def create_page(self):
        return ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=self.controls,
        )
        
    def pick_accounts_result(self, e: ft.FilePickerResultEvent):
        self.accounts_path.value = e.files[0].path if e.files else None
        self.page.update()