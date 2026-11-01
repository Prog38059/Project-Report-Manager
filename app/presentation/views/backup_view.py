"""Backup and restore management view."""

from typing import Optional
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFileDialog,
    QInputDialog,
    QMessageBox,
)

from app.application.services.backup_service import BackupService
from app.config import AppConfig


class BackupView(QWidget):
    """View managing manual/automated backups and restore verification."""

    def __init__(self, backup_service: BackupService, config: AppConfig, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.backup_service = backup_service
        self.config = config

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header bar
        header = QHBoxLayout()
        title = QLabel("Backup & Disaster Recovery")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #202124;")
        header.addWidget(title)
        header.addStretch()

        btn_backup = QPushButton("💾 Backup Now")
        btn_backup.setStyleSheet("background-color: #1a73e8; color: white; padding: 6px 14px; font-weight: bold;")
        btn_backup.clicked.connect(self.trigger_backup)

        btn_restore = QPushButton("🔄 Restore from Backup Zip...")
        btn_restore.clicked.connect(self.trigger_restore)

        header.addWidget(btn_restore)
        header.addWidget(btn_backup)
        layout.addLayout(header)

        info = QLabel(
            "Backups create a transactionally consistent copy of the SQLite database and all managed attachments, "
            "bundled into a zip archive with cryptographic SHA-256 manifests."
        )
        info.setStyleSheet("color: #5f6368; font-size: 13px;")
        layout.addWidget(info)

        # Local Backups Table
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Archive Filename", "Size (Bytes)", "SHA-256 Hash", "Location"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        self.refresh()

    def refresh(self) -> None:
        self.table.setRowCount(0)
        if not self.config.backups_dir.exists():
            return

        backup_files = sorted(self.config.backups_dir.glob("*.zip"), key=lambda f: f.stat().st_mtime, reverse=True)
        for f in backup_files:
            row = self.table.rowCount()
            self.table.insertRow(row)

            self.table.setItem(row, 0, QTableWidgetItem(f.name))
            self.table.setItem(row, 1, QTableWidgetItem(f"{f.stat().st_size:,}"))

            # Calculate or show hash prefix
            import hashlib
            h = hashlib.sha256(f.read_bytes()).hexdigest()
            self.table.setItem(row, 2, QTableWidgetItem(h[:16] + "..."))
            self.table.setItem(row, 3, QTableWidgetItem(str(f.parent)))

    def trigger_backup(self) -> None:
        note, ok = QInputDialog.getText(self, "Backup Note", "Enter optional note for this backup:")
        if not ok:
            return

        try:
            zip_path = self.backup_service.create_backup(notes=note or None)
            QMessageBox.information(self, "Backup Successful", f"Backup created successfully:\n{zip_path.name}")
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Backup Failed", f"Error during backup: {e}")

    def trigger_restore(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Backup Zip File",
            str(self.config.backups_dir),
            "Zip Files (*.zip)",
        )
        if not file_path:
            return

        confirm = QMessageBox.warning(
            self,
            "Confirm Restore",
            "Restoring will unpack to a staging area and verify integrity before replacing files.\n"
            "Do you want to proceed with verification and restore?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return

        try:
            result = self.backup_service.verify_and_restore(Path(file_path), self.config.base_dir)
            QMessageBox.information(
                self,
                "Restore Complete",
                f"Successfully verified and restored {result['verified_files_count']} files.\n"
                f"Schema version: {result['schema_version']}",
            )
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Restore Failed", f"Verification or restore error: {e}")
