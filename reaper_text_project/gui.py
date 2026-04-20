from __future__ import annotations

from pathlib import Path
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QLineEdit,
    QDoubleSpinBox,
    QCheckBox,
    QMessageBox,
)

from .generator import GeneratorConfig, generate_project


class MainWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Reaper Text Project Builder")
        self.resize(700, 420)
        self._last_auto_output = "output/project_from_text.rpp"

        layout = QVBoxLayout(self)

        self.source_edit = QLineEdit()
        self.output_edit = QLineEdit("output/project_from_text.rpp")
        self.script_edit = QLineEdit()
        self.source_edit.textChanged.connect(self._on_source_changed)

        layout.addLayout(self._path_row("Carpeta de audio", self.source_edit, True))
        layout.addLayout(self._path_row("Archivo .rpp salida", self.output_edit, False, save=True))
        layout.addLayout(self._path_row("Script order (CSV/XLSX/TXT)", self.script_edit, False))

        self.min_db = QDoubleSpinBox()
        self.min_db.setRange(-60.0, 12.0)
        self.min_db.setValue(-3.0)
        self.max_db = QDoubleSpinBox()
        self.max_db.setRange(-60.0, 12.0)
        self.max_db.setValue(3.0)
        self.spacing = QDoubleSpinBox()
        self.spacing.setRange(0.0, 30.0)
        self.spacing.setValue(2.0)

        db_row = QHBoxLayout()
        db_row.addWidget(QLabel("Pre-FX min dB"))
        db_row.addWidget(self.min_db)
        db_row.addWidget(QLabel("Pre-FX max dB"))
        db_row.addWidget(self.max_db)
        db_row.addWidget(QLabel("Silencio (s)"))
        db_row.addWidget(self.spacing)
        layout.addLayout(db_row)

        self.fx_all = QCheckBox("Incluir cadena FabFilter")
        self.fx_all.setChecked(True)
        self.fx_ds = QCheckBox("Pro-DS")
        self.fx_comp = QCheckBox("Pro-C2")
        self.fx_eq = QCheckBox("Pro-Q3")
        self.fx_mb = QCheckBox("Pro-MB")
        self.fx_lim = QCheckBox("Pro-L2")
        for cb in [self.fx_ds, self.fx_comp, self.fx_eq, self.fx_mb, self.fx_lim]:
            cb.setChecked(True)

        fx_row = QHBoxLayout()
        fx_row.addWidget(self.fx_all)
        for cb in [self.fx_ds, self.fx_comp, self.fx_eq, self.fx_mb, self.fx_lim]:
            fx_row.addWidget(cb)
        layout.addLayout(fx_row)

        self.btn_generate = QPushButton("Generar .RPP")
        self.btn_generate.clicked.connect(self._generate)
        layout.addWidget(self.btn_generate)

    def _path_row(self, title: str, edit: QLineEdit, is_dir: bool, save: bool = False) -> QHBoxLayout:
        row = QHBoxLayout()
        row.addWidget(QLabel(title))
        row.addWidget(edit)
        btn = QPushButton("...")

        def choose() -> None:
            if save:
                f, _ = QFileDialog.getSaveFileName(self, "Save RPP", edit.text() or "project.rpp", "Reaper Project (*.rpp)")
                if f:
                    edit.setText(f)
            elif is_dir:
                d = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta")
                if d:
                    edit.setText(d)
            else:
                f, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo", "", "Data (*.csv *.xlsx *.xls *.txt)")
                if f:
                    edit.setText(f)

        btn.clicked.connect(choose)
        row.addWidget(btn)
        return row

    def _on_source_changed(self, source_text: str) -> None:
        source = Path(source_text.strip())
        if not source_text.strip():
            return
        if not source.exists() or not source.is_dir():
            return

        suggested = str((source / "project_from_text.rpp").resolve())
        current_output = self.output_edit.text().strip()
        if not current_output or current_output == self._last_auto_output or current_output == "output/project_from_text.rpp":
            self.output_edit.setText(suggested)
            self._last_auto_output = suggested

    def _generate(self) -> None:
        if not self.source_edit.text().strip() or not self.output_edit.text().strip():
            QMessageBox.warning(self, "Faltan datos", "Indica al menos la carpeta de audio y ruta de salida")
            return

        cfg = GeneratorConfig(
            source_root=Path(self.source_edit.text().strip()),
            output_file=Path(self.output_edit.text().strip()),
            min_db=self.min_db.value(),
            max_db=self.max_db.value(),
            spacing_seconds=self.spacing.value(),
            use_fx_chain=self.fx_all.isChecked(),
            include_ds=self.fx_ds.isChecked(),
            include_comp=self.fx_comp.isChecked(),
            include_eq=self.fx_eq.isChecked(),
            include_multiband=self.fx_mb.isChecked(),
            include_limiter=self.fx_lim.isChecked(),
            include_script_order=bool(self.script_edit.text().strip()),
            script_path=Path(self.script_edit.text().strip()) if self.script_edit.text().strip() else None,
        )

        try:
            generate_project(cfg)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Error", str(exc))
            return

        QMessageBox.information(self, "OK", f"Proyecto generado en:\n{cfg.output_file}")


def run_gui() -> None:
    app = QApplication([])
    w = MainWindow()
    w.show()
    app.exec()
