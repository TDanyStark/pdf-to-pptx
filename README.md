# PDF -> PPTX (Flet App)

Convierte un PDF en una presentación PPTX donde cada página se coloca como una imagen a pantalla completa (estilo *cover* para evitar bordes). Interfaz moderna en modo oscuro construida con [Flet](https://flet.dev/).

## Características
- Selección de PDF (botón) y mensaje informativo para drag & drop.
- Selección de carpeta destino (por defecto la carpeta Descargas del usuario).
- Barra de progreso basada en número de páginas.
- Log en tiempo real de cada paso y errores.
- Salida organizada: `<carpeta_destino>/<nombre_pdf>/<nombre_pdf>.pptx` + carpeta `pages/` con las imágenes (se eliminó la subcarpeta `_output`).

## Requisitos
```bash
pip install -r requirements.txt
```
(Contiene: flet, pymupdf, python-pptx, Pillow)

## Ejecutar
```bash
python main.py
```
La app abrirá una ventana de Flet.

## Estructura del Código
```text
app/
	__init__.py        # Exporta API principal
	conversion.py      # Lógica de conversión PDF -> imágenes -> PPTX
	ui.py              # Construcción de la interfaz Flet
main.py              # Punto de entrada (lanza la app)
```

## Notas
- El progreso es estimado: 10% inicial, 80% distribuido por páginas, resto al guardar.
- El drag & drop nativo de archivos puede variar según la plataforma; se ofrece botón siempre confiable.
- Cambia `IMG_DPI` en `app/conversion.py` si deseas más o menos resolución.

## Empaquetar (Opcional)
Usa PyInstaller o Flet pack. Ejemplo rápido PyInstaller:
```bash
pyinstaller --noconfirm --onefile --name pdf2pptx main.py
```
Para mejor soporte UI nativa, ver documentación de `flet pack`.

## Futuras mejoras sugeridas
- Procesar múltiples PDFs en cola.
- Cancelación del proceso en curso.
- Configuración de DPI y calidad JPG desde la interfaz.
- Previsualización de páginas.

---
© 2025
