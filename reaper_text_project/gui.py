from __future__ import annotations

from pathlib import Path
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QDialog,
    QDialogButtonBox,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QLineEdit,
    QDoubleSpinBox,
    QCheckBox,
    QMessageBox,
    QGroupBox,
)

from .generator import GeneratorConfig, generate_project


class MainWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("ReaperCore")
        self.resize(700, 200)
        self._last_auto_output = "output/project_from_text.rpp"

        layout = QVBoxLayout(self)

        self.source_edit = QLineEdit()
        self.output_edit = QLineEdit("output/project_from_text.rpp")
        self.script_edit = QLineEdit()
        self.source_edit.textChanged.connect(self._on_source_changed)

        layout.addLayout(self._path_row("Carpeta de audio", self.source_edit, True))
        layout.addLayout(self._path_row("Archivo .rpp salida", self.output_edit, False, save=True))
        layout.addLayout(self._path_row("Script Order", self.script_edit, False))

        self.db_range = QDoubleSpinBox()
        self.db_range.setRange(0.0, 24.0)
        self.db_range.setValue(6.0)
        self.db_range.setSingleStep(0.5)
        self.spacing = QDoubleSpinBox()
        self.spacing.setRange(0.0, 30.0)
        self.spacing.setValue(3.0)

        db_row = QHBoxLayout()
        db_row.addWidget(QLabel("Rango dB total"))
        db_row.addWidget(self.db_range)
        db_row.addWidget(QLabel("Silencio (s)"))
        db_row.addWidget(self.spacing)
        layout.addLayout(db_row)

        self.fx_all = QCheckBox("Incluir cadena FabFilter")
        self.fx_all.setChecked(False)
        self.fx_ds = QCheckBox("Pro-DS")
        self.fx_comp = QCheckBox("Pro-C2")
        self.fx_eq = QCheckBox("Pro-Q3")
        self.fx_mb = QCheckBox("Pro-MB")
        self.fx_lim = QCheckBox("Pro-L2")
        for cb in [self.fx_ds, self.fx_comp, self.fx_eq, self.fx_mb, self.fx_lim]:
            cb.setChecked(True)

        layout.addWidget(self.fx_all)
        self.fx_process_btn = QPushButton("Seleccionar procesos…")
        self.fx_process_btn.setEnabled(False)
        self.fx_process_btn.clicked.connect(self._open_fx_dialog)
        self.fx_all.toggled.connect(self._toggle_fx_controls)
        layout.addWidget(self.fx_process_btn)

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
                f, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo")
                if f:
                    edit.setText(f)

        btn.clicked.connect(choose)
        row.addWidget(btn)
        return row

    def _toggle_fx_controls(self, enabled: bool) -> None:
        self.fx_process_btn.setEnabled(enabled)

    def _open_fx_dialog(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Seleccionar procesos")
        dialog_layout = QVBoxLayout(dialog)

        box = QGroupBox("Procesos FabFilter")
        grid = QGridLayout()
        process_options = [
            ("Pro-DS", self.fx_ds.isChecked()),
            ("Pro-C2", self.fx_comp.isChecked()),
            ("Pro-Q3", self.fx_eq.isChecked()),
            ("Pro-MB", self.fx_mb.isChecked()),
            ("Pro-L2", self.fx_lim.isChecked()),
        ]
        dialog_checkboxes: list[QCheckBox] = []
        for idx, (label, checked) in enumerate(process_options):
            checkbox = QCheckBox(label)
            checkbox.setChecked(checked)
            dialog_checkboxes.append(checkbox)
            grid.addWidget(checkbox, idx // 2, idx % 2)
        box.setLayout(grid)
        dialog_layout.addWidget(box)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        dialog_layout.addWidget(button_box)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.fx_ds.setChecked(dialog_checkboxes[0].isChecked())
            self.fx_comp.setChecked(dialog_checkboxes[1].isChecked())
            self.fx_eq.setChecked(dialog_checkboxes[2].isChecked())
            self.fx_mb.setChecked(dialog_checkboxes[3].isChecked())
            self.fx_lim.setChecked(dialog_checkboxes[4].isChecked())

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

        half_range = self.db_range.value() / 2.0
        cfg = GeneratorConfig(
            source_root=Path(self.source_edit.text().strip()),
            output_file=Path(self.output_edit.text().strip()),
            min_db=-half_range,
            max_db=half_range,
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
