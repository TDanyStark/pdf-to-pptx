"""Interfaz Flet para convertir PDF a PPTX usando imagenes."""
from __future__ import annotations

import os
import threading
import flet as ft

from .conversion import convert_pdf_to_pptx, IMG_DPI

__all__ = ["flet_main", "launch_app", "PDFToPPTApp"]


def get_default_downloads_dir() -> str:
    """Obtiene la carpeta Descargas del usuario de forma portable."""
    home = os.path.expanduser("~")
    candidates = [
        os.path.join(os.environ.get("USERPROFILE", home), "Downloads"),
        os.path.join(home, "Downloads"),
    ]
    for candidate in candidates:
        if os.path.isdir(candidate):
            return candidate
    return home


class PDFToPPTApp(ft.Container):
    """UI principal que convierte PDF a PPTX como imagenes."""

    def __init__(self, page: ft.Page):
        super().__init__()
        self._page = page

        self.pdf_path: str | None = None
        self.output_dir: str = get_default_downloads_dir()
        self.processing: bool = False
        self.thread: threading.Thread | None = None

        self.log_view = ft.ListView(expand=True, spacing=4, auto_scroll=True)
        self.progress_bar = ft.ProgressBar(value=0)
        self.progress_text = ft.Text("Progreso: 0%", size=12)
        self.pdf_label = ft.Text(
            "Ningun PDF seleccionado",
            italic=True,
            size=12,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        self.output_label = ft.Text(
            self.output_dir,
            size=12,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
        )

        header = ft.Row(
            controls=[ft.Text("PDF a PPTX", size=26, weight=ft.FontWeight.BOLD)],
            alignment=ft.MainAxisAlignment.CENTER,
        )

        pick_pdf = ft.Button(
            content="Buscar PDF",
            icon=ft.Icons.UPLOAD_FILE,
            on_click=self._browse_pdf,
        )

        pick_dir = ft.Button(
            content="Buscar carpeta",
            icon=ft.Icons.FOLDER_OPEN,
            on_click=self._browse_output_dir,
        )

        self.process_btn = ft.Button(
            content="Procesar PDF",
            icon=ft.Icons.PLAY_ARROW,
            on_click=self._on_process,
        )
        self.process_btn.disabled = True

        self.reset_btn = ft.OutlinedButton(
            content="Limpiar",
            icon=ft.Icons.CLEAR,
            on_click=self._clear_state,
        )
        self.reset_btn.disabled = True

        pdf_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(ft.Icons.PICTURE_AS_PDF, size=64),
                    pick_pdf,
                    ft.Container(
                        content=self.pdf_label,
                        padding=8,
                        border=ft.border.all(1, ft.Colors.BLUE_GREY_200),
                        border_radius=8,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            padding=16,
            border=ft.border.all(1, ft.Colors.AMBER),
            border_radius=12,
        )

        output_card = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text("Carpeta destino:", weight=ft.FontWeight.BOLD),
                    ft.Container(
                        content=self.output_label,
                        padding=8,
                        border=ft.border.all(1, ft.Colors.BLUE_GREY_200),
                        border_radius=8,
                        expand=True,
                    ),
                    pick_dir,
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            padding=12,
            border=ft.border.all(1, ft.Colors.BLUE_GREY_400),
            border_radius=12,
        )

        progress_row = ft.Row(
            controls=[self.progress_bar, self.progress_text],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        log_card = ft.Container(
            content=ft.Column(
                controls=[ft.Text("Log", weight=ft.FontWeight.BOLD), self.log_view],
                spacing=6,
            ),
            height=160,
            padding=12,
            border=ft.border.all(1, ft.Colors.BLUE_GREY_400),
            border_radius=12,
        )

        self.content = ft.Column(
            controls=[
                header,
                pdf_card,
                output_card,
                ft.Row(controls=[self.process_btn, self.reset_btn], spacing=8),
                progress_row,
                log_card,
                ft.Text("PDF convertido como imagenes (no editable)", size=11, opacity=0.6),
            ],
            spacing=16,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )
        self.padding = 20

    def _append_log(self, message: str):
        self.log_view.controls.append(ft.Text(message, size=12))
        self._page.update()

    def _set_progress(self, val: float):
        self.progress_bar.value = val
        self.progress_text.value = f"Progreso: {int(val * 100)}%"
        self._page.update()

    def _apply_pdf_path(self):
        if not self.pdf_path:
            self._append_log("Seleccione un PDF.")
            return
        if not os.path.isfile(self.pdf_path):
            self._append_log("La ruta del PDF no es valida.")
            return
        self.pdf_label.value = os.path.basename(self.pdf_path)
        self.process_btn.disabled = False
        self.reset_btn.disabled = False
        self._append_log(f"PDF seleccionado: {self.pdf_path}")
        self._page.update()

    def _apply_output_dir(self):
        if not self.output_dir:
            self._append_log("Seleccione la carpeta destino.")
            return
        if not os.path.isdir(self.output_dir):
            self._append_log("La carpeta destino no es valida.")
            return
        self.output_label.value = self.output_dir
        self._append_log(f"Directorio destino: {self.output_dir}")
        self._page.update()

    async def _browse_pdf(self, _):
        files = await ft.FilePicker().pick_files(
            allow_multiple=False,
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["pdf"],
        )
        if files:
            self.pdf_path = files[0].path
            self._apply_pdf_path()

    async def _browse_output_dir(self, _):
        path = await ft.FilePicker().get_directory_path()
        if path:
            self.output_dir = path
            self._apply_output_dir()

    def _clear_state(self, _):
        if self.processing:
            return
        self.pdf_path = None
        self.pdf_label.value = "Ningun PDF seleccionado"
        self.process_btn.disabled = True
        self.reset_btn.disabled = True
        self.log_view.controls.clear()
        self._set_progress(0)
        self._append_log("Estado limpiado")
        self._page.update()

    def _run_conversion_thread(self):
        try:
            self._append_log("Iniciando conversion...")
            convert_pdf_to_pptx(
                self.pdf_path,
                self.output_dir,
                dpi=IMG_DPI,
                log=self._append_log,
                progress=self._set_progress,
            )
            self._append_log("Conversion finalizada.")
        except Exception as ex:  # pragma: no cover - logging
            self._append_log(f"ERROR: {ex}")
        finally:
            self.processing = False
            self.process_btn.disabled = False
            self.reset_btn.disabled = False
            self._page.update()

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
        self._page.update()


def flet_main(page: ft.Page):
    """Configura la pagina y carga el control principal."""
    page.title = "PDF a PPTX"
    page.padding = 20
    page.window.width = 640
    page.window.height = 820
    page.window.resizable = False
    page.scroll = ft.ScrollMode.AUTO
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    app = PDFToPPTApp(page)
    page.add(app)


def launch_app():
    ft.app(target=flet_main)
