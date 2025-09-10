"""Interfaz Flet de la aplicación PDF -> PPTX (estructura tipo componente)."""
from __future__ import annotations

import os
import threading
import flet as ft

from .conversion import convert_pdf_to_pptx, IMG_DPI

__all__ = ["flet_main", "launch_app", "PDFToPPTApp"]


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def get_default_downloads_dir() -> str:
    """Intenta obtener la carpeta Descargas del usuario de forma portable."""
    home = os.path.expanduser("~")
    candidates = [
        os.path.join(os.environ.get("USERPROFILE", home), "Downloads"),
        os.path.join(home, "Downloads"),
    ]
    for c in candidates:
        if os.path.isdir(c):
            return c
    return home


# ---------------------------------------------------------------------------
# Botones personalizados (similar al ejemplo de CalculatorApp)
# ---------------------------------------------------------------------------
class BaseActionButton(ft.ElevatedButton):
    def __init__(self, text: str, on_click, icon: str | None = None, disabled: bool = False):
        super().__init__()
        self.text = text
        self.icon = icon
        self.on_click = on_click
        self.disabled = disabled
        self.data = text  # opcional si se quisiera distinguir
        self.expand = 1


class PrimaryButton(BaseActionButton):
    def __init__(self, text: str, on_click, icon: str | None = None, disabled: bool = False):
        super().__init__(text, on_click, icon, disabled)
        # Estilos con estados para mostrar gris cuando está deshabilitado
        self.style = ft.ButtonStyle(
            bgcolor={
                ft.ControlState.DEFAULT: ft.Colors.BLUE,
                ft.ControlState.HOVERED: ft.Colors.BLUE_700,
                ft.ControlState.FOCUSED: ft.Colors.BLUE_700,
                ft.ControlState.DISABLED: ft.Colors.GREY_800,
            },
            color={
                ft.ControlState.DEFAULT: ft.Colors.WHITE,
                ft.ControlState.DISABLED: ft.Colors.WHITE24,
            },
        )


class SecondaryButton(BaseActionButton):
    def __init__(self, text: str, on_click, icon: str | None = None, disabled: bool = False):
        super().__init__(text, on_click, icon, disabled)
        self.style = ft.ButtonStyle(
            bgcolor={
                ft.ControlState.DEFAULT: ft.Colors.GREY_800,
                ft.ControlState.HOVERED: ft.Colors.GREY_700,
                ft.ControlState.FOCUSED: ft.Colors.GREY_700,
                ft.ControlState.DISABLED: ft.Colors.GREY_900,
            },
            color={
                ft.ControlState.DEFAULT: ft.Colors.WHITE70,
                ft.ControlState.DISABLED: ft.Colors.WHITE24,
            },
        )


# ---------------------------------------------------------------------------
# Componente raíz de la aplicación
# ---------------------------------------------------------------------------
class PDFToPPTApp(ft.Container):
    """Control raíz que encapsula todo el flujo de conversión PDF -> PPTX."""

    CONTENT_MAX_WIDTH = 600

    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page

        # Estado
        self.pdf_path: str | None = None
        self.output_dir: str = get_default_downloads_dir()
        self.processing: bool = False
        self.thread: threading.Thread | None = None

        # Controles reutilizados
        self.log_view = ft.ListView(expand=True, auto_scroll=True, spacing=4)
        self.progress_bar = ft.ProgressBar(value=0, expand=True)
        self.progress_text = ft.Text("Progreso: 0%", size=12)
        self.pdf_label = ft.Text("Ningún PDF seleccionado", italic=True)
        self.output_label = ft.Text(
            self.output_dir,
            selectable=True,
            size=13,
            max_lines=1,  # fuerza una sola línea
            overflow=ft.TextOverflow.ELLIPSIS,
            tooltip=self.output_dir,
            expand=True,
        )

        self.process_btn = PrimaryButton(
            "Procesar PDF", icon="play_arrow", on_click=self._on_process, disabled=True
        )
        self.reset_btn = SecondaryButton(
            "Limpiar", icon="clear", on_click=self._clear_state, disabled=True
        )

        # FilePickers (se añaden a overlay del page)
        self.pdf_picker = ft.FilePicker(on_result=self._on_pdf_picked)
        self.dir_picker = ft.FilePicker(on_result=self._on_dir_picked)
        self.page.overlay.extend([self.pdf_picker, self.dir_picker])

        # Construcción de layout
        self.content = self._build_layout()
        self.width = self.CONTENT_MAX_WIDTH
        self.alignment = ft.alignment.top_center
        self.padding = 0

        # Mensaje inicial
        self._append_log("Listo. Seleccione un PDF para comenzar.")

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    def _build_layout(self) -> ft.Control:
        # Zona de selección de PDF
        drop_zone = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(name="picture_as_pdf", size=70, color=ft.Colors.AMBER),
                    ft.Text(
                        "Usa el botón para seleccionar el PDF",
                        size=15,
                        weight=ft.FontWeight.W_500,
                    ),
                    ft.ElevatedButton(
                        "Seleccionar PDF", icon="upload_file", on_click=self._pick_pdf
                    ),
                    self.pdf_label,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            ),
            height=230,
            bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.AMBER_50),
            border=ft.border.all(1, ft.Colors.AMBER),
            border_radius=18,
            padding=20,
        )

        # Selector de carpeta
        output_selector = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text("Carpeta destino", weight=ft.FontWeight.BOLD),
                    ft.Text("-", opacity=0.6),
                    ft.Container(content=self.output_label, expand=True),
                    ft.TextButton(
                        "Cambiar carpeta", icon="folder_open", on_click=self._pick_folder
                    ),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=16,
            border=ft.border.all(1, ft.Colors.BLUE_GREY_700),
            border_radius=14,
        )

        actions_row = ft.Row(
            controls=[self.process_btn, self.reset_btn], spacing=16
        )

        progress_section = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        self.progress_bar,
                        self.progress_text,
                    ],
                    spacing=16,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            spacing=8,
        )

        log_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Log", weight=ft.FontWeight.BOLD),
                    ft.Divider(height=1),
                    ft.Container(content=self.log_view, height=120),
                ],
                spacing=6,
            ),
            padding=18,
            border=ft.border.all(1, ft.Colors.BLUE_GREY_700),
            border_radius=14,
        )

        main_column = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("PDF -> PPTX", size=32, weight=ft.FontWeight.BOLD),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                drop_zone,
                output_selector,
                actions_row,
                progress_section,
                log_card,
                ft.Text("©Daniel Amado 2025", size=12, opacity=0.5),
            ],
            spacing=20,
            expand=False,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )
        return main_column

    # ------------------------------------------------------------------
    # Acciones / callbacks
    # ------------------------------------------------------------------
    def _append_log(self, message: str):
        self.log_view.controls.append(ft.Text(message, size=12))
        self.page.update()

    def _set_progress(self, val: float):
        self.progress_bar.value = val
        self.progress_text.value = f"Progreso: {int(val * 100)}%"
        self.page.update()

    def _on_pdf_picked(self, e: ft.FilePickerResultEvent):
        if e.files:
            f = e.files[0]
            self.pdf_path = f.path
            self.pdf_label.value = os.path.basename(f.path)
            self._append_log(f"PDF seleccionado: {f.path}")
            self.process_btn.disabled = False
            self.reset_btn.disabled = False  # Activar también el botón de limpiar tras seleccionar PDF
        else:
            self._append_log("Selección de PDF cancelada")
        self.page.update()

    def _on_dir_picked(self, e: ft.FilePickerResultEvent):
        if e.path:
            self.output_dir = e.path
            self.output_label.value = e.path
            self.output_label.tooltip = e.path  # mantener tooltip actualizado
            self._append_log(f"Directorio destino: {e.path}")
            self.page.update()

    # Métodos para abrir diálogos
    def _pick_pdf(self, _):
        self.pdf_picker.pick_files(
            allow_multiple=False,
            allowed_extensions=["pdf"],
            file_type=ft.FilePickerFileType.CUSTOM,
        )

    def _pick_folder(self, _):
        self.dir_picker.get_directory_path()

    def _clear_state(self, _):
        if self.processing:
            return
        self.pdf_path = None
        self.pdf_label.value = "Ningún PDF seleccionado"
        self.process_btn.disabled = True
        self.reset_btn.disabled = True
        self.log_view.controls.clear()
        self._set_progress(0)
        self._append_log("Estado limpiado")
        self.page.update()

    # Hilo de conversión
    def _run_conversion_thread(self):
        try:
            self._append_log("Iniciando conversión...")
            convert_pdf_to_pptx(
                self.pdf_path,
                self.output_dir,
                dpi=IMG_DPI,
                log=self._append_log,
                progress=self._set_progress,
            )
            self._append_log("Conversión finalizada.")
        except Exception as ex:  # pragma: no cover - logging
            self._append_log(f"ERROR: {ex}")
        finally:
            self.processing = False
            self.process_btn.disabled = False
            self.reset_btn.disabled = False
            self.page.update()

    def _on_process(self, _):
        if not self.pdf_path:
            self._append_log("Seleccione un PDF primero.")
            return
        if self.processing:
            return
        self.processing = True
        self.process_btn.disabled = True
        self.reset_btn.disabled = True
        self._set_progress(0)
        self._append_log("Preparando...")
        self.thread = threading.Thread(target=self._run_conversion_thread, daemon=True)
        self.thread.start()
        self.page.update()


# ---------------------------------------------------------------------------
# Punto de entrada Flet
# ---------------------------------------------------------------------------
def flet_main(page: ft.Page):
    """Configura la página y añade el componente raíz."""
    page.title = "PDF a PPTX"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.window.width = 600
    page.window.height = 800
    page.window.resizable = False
    page.window.icon = "icon.ico"
    page.scroll = ft.ScrollMode.AUTO
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    app = PDFToPPTApp(page)
    page.add(app)


def launch_app():  # API pública similar a la anterior
    ft.app(target=flet_main)
