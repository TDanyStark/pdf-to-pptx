"""Paquete de la aplicación PDF->PPTX con Flet."""

from .conversion import convert_pdf_to_pptx, PdfConversionResult, IMG_DPI
from .ui import flet_main, launch_app

__all__ = [
    "convert_pdf_to_pptx",
    "PdfConversionResult",
    "IMG_DPI",
    "flet_main",
    "launch_app",
]
