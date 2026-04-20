"""Entry point principal para ejecutar la GUI directamente.

Uso recomendado:
    python main.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from reaper_text_project.gui import run_gui
except Exception as exc:  # noqa: BLE001
    print("No se pudo iniciar la GUI desde main.py")
    print(f"Detalle: {exc}")
    print("\nInstala dependencias con:")
    print("  pip install -e .")
    input("\nPresiona Enter para cerrar...")
    raise SystemExit(1) from exc


if __name__ == "__main__":
    run_gui()
