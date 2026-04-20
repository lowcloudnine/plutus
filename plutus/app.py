"""PyQt6 UI for recording precious metal holdings."""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

from PyQt6.QtCore import QDate, QSize, Qt
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .database import Database, Holding, VALID_METALS


LIGHT_THEME = {
    "window": "#eef2f7",
    "panel": "#ffffff",
    "panel_alt": "#f7f9fc",
    "sidebar": "#f5f7fb",
    "text": "#183153",
    "muted": "#6d7c93",
    "border": "#d7dfeb",
    "primary": "#183e8d",
    "primary_soft": "#e9effb",
    "accent": "#3ea3dc",
    "success": "#28a745",
    "danger": "#db5c66",
    "selection": "#d9e6ff",
}

DARK_THEME = {
    "window": "#111827",
    "panel": "#182233",
    "panel_alt": "#111b2b",
    "sidebar": "#0f1726",
    "text": "#edf2ff",
    "muted": "#99a8c2",
    "border": "#26344a",
    "primary": "#6d95ff",
    "primary_soft": "#1b2d52",
    "accent": "#48b7f0",
    "success": "#57c785",
    "danger": "#f07a82",
    "selection": "#1f3156",
}


def stylesheet(theme: dict[str, str]) -> str:
    return """
    QWidget {{
        background: {window};
        color: {text};
        font-size: 14px;
    }}
    QMainWindow {{
        background: {window};
    }}
    QLabel#titleLabel {{
        font-size: 34px;
        font-weight: 700;
    }}
    QLabel#sectionTitle {{
        font-size: 20px;
        font-weight: 700;
    }}
    QLabel#eyebrowLabel {{
        color: {muted};
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
    }}
    QLabel#metricValue {{
        font-size: 24px;
        font-weight: 700;
    }}
    QLabel#metricCaption {{
        color: {muted};
        font-size: 12px;
    }}
    QLabel#detailValue {{
        font-size: 22px;
        font-weight: 700;
    }}
    QLabel#detailCaption {{
        color: {muted};
        font-size: 12px;
        font-weight: 600;
    }}
    QLabel#notesBox {{
        background: {panel_alt};
        border: 1px solid {border};
        border-radius: 16px;
        padding: 14px;
    }}
    QFrame#sidebar,
    QFrame#contentCard,
    QFrame#filterCard,
    QFrame#listCard,
    QFrame#detailCard,
    QFrame#summaryCard,
    QFrame#statCard {{
        background: {panel};
        border: 1px solid {border};
        border-radius: 22px;
    }}
    QFrame#sidebar {{
        background: {sidebar};
    }}
    QFrame#summaryCard {{
        background: {panel_alt};
    }}
    QPushButton {{
        background: {panel};
        color: {text};
        border: 1px solid {border};
        border-radius: 14px;
        padding: 10px 16px;
        font-weight: 600;
    }}
    QPushButton:hover {{
        border-color: {primary};
    }}
    QPushButton#primaryButton {{
        background: {accent};
        color: white;
        border-color: transparent;
    }}
    QPushButton#primaryButton:hover {{
        background: {primary};
    }}
    QPushButton#dangerButton {{
        color: {danger};
    }}
    QPushButton#navButton {{
        text-align: left;
        padding: 14px 18px;
        background: transparent;
        border: none;
        border-radius: 16px;
        color: {muted};
    }}
    QPushButton#navButton:checked {{
        background: {primary_soft};
        color: {primary};
    }}
    QPushButton#themeButton {{
        min-width: 90px;
    }}
    QPushButton#themeButton:checked {{
        background: {primary};
        color: white;
        border-color: transparent;
    }}
    QLineEdit,
    QComboBox,
    QDateEdit,
    QPlainTextEdit {{
        background: {panel};
        border: 1px solid {border};
        border-radius: 14px;
        padding: 10px 12px;
        selection-background-color: {selection};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    QGroupBox {{
        border: 1px solid {border};
        border-radius: 18px;
        margin-top: 14px;
        padding-top: 12px;
        background: {panel_alt};
        font-weight: 700;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 14px;
        padding: 0 6px;
    }}
    QListWidget {{
        background: transparent;
        border: none;
        outline: none;
        padding: 0;
    }}
    QListWidget::item {{
        background: {panel};
        border: 1px solid {border};
        border-radius: 18px;
        margin: 0 0 12px 0;
        padding: 14px;
    }}
    QListWidget::item:selected {{
        background: {selection};
        border-color: {primary};
        color: {text};
    }}
    QTableWidget {{
        background: {panel};
        alternate-background-color: {panel_alt};
        border: 1px solid {border};
        border-radius: 16px;
        gridline-color: {border};
        selection-background-color: {selection};
    }}
    QHeaderView::section {{
        background: {panel_alt};
        color: {muted};
        border: none;
        border-bottom: 1px solid {border};
        padding: 10px;
        font-weight: 700;
    }}
    QMessageBox {{
        background: {window};
    }}
    """.format(**theme)


def default_database_path() -> Path:
    home = Path.home()
    return home / ".local" / "share" / "plutus" / "plutus.sqlite3"


class HoldingDialog(QDialog):
    def __init__(self, parent: QWidget | None = None, holding: Holding | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Holding")
        self.setModal(True)
        self.resize(420, 420)

        self.metal = QComboBox()
        self.metal.addItems(list(VALID_METALS))

        self.quantity = QDoubleSpinBox()
        self.quantity.setDecimals(4)
        self.quantity.setRange(0.0001, 1_000_000)

        self.unit_cost = QDoubleSpinBox()
        self.unit_cost.setDecimals(2)
        self.unit_cost.setPrefix("$")
        self.unit_cost.setRange(0.0, 10_000_000)

        self.vendor = QLineEdit()

        self.purchased_on = QDateEdit()
        self.purchased_on.setCalendarPopup(True)
        self.purchased_on.setDisplayFormat("yyyy-MM-dd")
        self.purchased_on.setDate(QDate.currentDate())

        self.notes = QPlainTextEdit()
        self.notes.setPlaceholderText("Optional notes")

        form = QFormLayout()
        form.addRow("Metal", self.metal)
        form.addRow("Quantity (oz)", self.quantity)
        form.addRow("Unit Cost", self.unit_cost)
        form.addRow("Vendor", self.vendor)
        form.addRow("Purchased On", self.purchased_on)
        form.addRow("Notes", self.notes)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(buttons)
        self.setLayout(layout)

        self._holding_id: int | None = None
        if holding is not None:
            self.load_holding(holding)

    def load_holding(self, holding: Holding) -> None:
        self._holding_id = holding.id
        self.metal.setCurrentText(holding.metal)
        self.quantity.setValue(holding.quantity)
        self.unit_cost.setValue(holding.unit_cost)
        self.vendor.setText(holding.vendor)
        parsed_date = QDate.fromString(holding.purchased_on, "yyyy-MM-dd")
        self.purchased_on.setDate(parsed_date if parsed_date.isValid() else QDate.currentDate())
        self.notes.setPlainText(holding.notes)

    def to_holding(self) -> Holding:
        return Holding(
            id=self._holding_id,
            metal=self.metal.currentText(),
            quantity=float(self.quantity.value()),
            unit_cost=float(self.unit_cost.value()),
            vendor=self.vendor.text().strip(),
            purchased_on=self.purchased_on.date().toString("yyyy-MM-dd"),
            notes=self.notes.toPlainText().strip(),
        )


class MainWindow(QMainWindow):
    ENTRY_HEADERS = ("Status", "Metal", "Quantity", "Unit Cost", "Vendor", "Total")

    def __init__(self, database: Database) -> None:
        super().__init__()
        self.database = database
        self.holdings: list[Holding] = []
        self.filtered_holdings: list[Holding] = []
        self.current_theme = "light"
        self.setWindowTitle("Plutus")
        self.resize(1380, 860)
        self.setMinimumSize(1180, 760)

        root = QWidget()
        outer = QHBoxLayout(root)
        outer.setContentsMargins(18, 18, 18, 18)
        outer.setSpacing(18)

        sidebar = self._build_sidebar()
        content = self._build_content()

        outer.addWidget(sidebar)
        outer.addWidget(content, 1)
        self.setCentralWidget(root)

        self.apply_theme("light")
        self.refresh_table()

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(230)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        brand = QLabel("plutus")
        brand.setObjectName("sectionTitle")

        subtitle = QLabel("metal portfolio")
        subtitle.setObjectName("eyebrowLabel")

        search_button = QPushButton("Search Holdings")
        search_button.setObjectName("primaryButton")

        layout.addWidget(brand)
        layout.addWidget(subtitle)
        layout.addSpacing(8)
        layout.addWidget(search_button)
        layout.addSpacing(12)

        nav_labels = ("Holdings", "Transactions", "Reports", "Clients")
        for index, label in enumerate(nav_labels):
            button = QPushButton(label)
            button.setObjectName("navButton")
            button.setCheckable(True)
            button.setChecked(index == 0)
            layout.addWidget(button)

        layout.addStretch()

        theme_label = QLabel("Theme")
        theme_label.setObjectName("eyebrowLabel")
        self.light_theme_button = QPushButton("Light")
        self.light_theme_button.setObjectName("themeButton")
        self.light_theme_button.setCheckable(True)
        self.light_theme_button.clicked.connect(lambda: self.apply_theme("light"))

        self.dark_theme_button = QPushButton("Dark")
        self.dark_theme_button.setObjectName("themeButton")
        self.dark_theme_button.setCheckable(True)
        self.dark_theme_button.clicked.connect(lambda: self.apply_theme("dark"))

        theme_row = QHBoxLayout()
        theme_row.setSpacing(8)
        theme_row.addWidget(self.light_theme_button)
        theme_row.addWidget(self.dark_theme_button)

        layout.addWidget(theme_label)
        layout.addLayout(theme_row)
        return sidebar

    def _build_content(self) -> QFrame:
        card = QFrame()
        card.setObjectName("contentCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(18)

        layout.addWidget(self._build_header())
        layout.addWidget(self._build_filters())

        main_row = QHBoxLayout()
        main_row.setSpacing(18)
        main_row.addWidget(self._build_holdings_panel(), 4)
        main_row.addWidget(self._build_detail_panel(), 6)
        layout.addLayout(main_row, 1)

        return card

    def _build_header(self) -> QWidget:
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)

        title_block = QVBoxLayout()
        title_block.setSpacing(2)

        eyebrow = QLabel("Portfolio Console")
        eyebrow.setObjectName("eyebrowLabel")

        title = QLabel("Holdings")
        title.setObjectName("titleLabel")

        title_block.addWidget(eyebrow)
        title_block.addWidget(title)
        title_row.addLayout(title_block)
        title_row.addStretch()

        layout.addLayout(title_row)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(14)

        self.total_value_metric = self._create_metric_card("Total Value")
        self.total_ounces_metric = self._create_metric_card("Total Ounces")
        self.position_count_metric = self._create_metric_card("Positions")

        stats_row.addWidget(self.total_value_metric["card"])
        stats_row.addWidget(self.total_ounces_metric["card"])
        stats_row.addWidget(self.position_count_metric["card"])
        layout.addLayout(stats_row)

        return wrapper

    def _create_metric_card(self, caption: str) -> dict[str, QLabel | QFrame]:
        card = QFrame()
        card.setObjectName("statCard")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(4)

        value = QLabel("--")
        value.setObjectName("metricValue")

        label = QLabel(caption)
        label.setObjectName("metricCaption")

        layout.addWidget(value)
        layout.addWidget(label)
        return {"card": card, "value": value}

    def _build_filters(self) -> QFrame:
        card = QFrame()
        card.setObjectName("filterCard")

        layout = QGridLayout(card)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setHorizontalSpacing(14)
        layout.setVerticalSpacing(10)

        self.metal_filter = QComboBox()
        self.metal_filter.currentIndexChanged.connect(self.apply_filters)

        self.vendor_filter = QComboBox()
        self.vendor_filter.currentIndexChanged.connect(self.apply_filters)

        self.year_filter = QComboBox()
        self.year_filter.currentIndexChanged.connect(self.apply_filters)

        self.search_filter = QLineEdit()
        self.search_filter.setPlaceholderText("Search vendor, notes, or date")
        self.search_filter.textChanged.connect(self.apply_filters)

        layout.addWidget(self._labeled_widget("Metal", self.metal_filter), 0, 0)
        layout.addWidget(self._labeled_widget("Vendor", self.vendor_filter), 0, 1)
        layout.addWidget(self._labeled_widget("Year", self.year_filter), 0, 2)
        layout.addWidget(self._labeled_widget("Search", self.search_filter), 0, 3)

        return card

    def _labeled_widget(self, label_text: str, widget: QWidget) -> QWidget:
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        label = QLabel(label_text)
        label.setObjectName("eyebrowLabel")
        layout.addWidget(label)
        layout.addWidget(widget)
        return wrapper

    def _build_holdings_panel(self) -> QFrame:
        card = QFrame()
        card.setObjectName("listCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        add_button = QPushButton("+ Add New Holding")
        add_button.clicked.connect(self.add_holding)

        header = QLabel("Tracked Holdings")
        header.setObjectName("sectionTitle")

        self.holdings_list = QListWidget()
        self.holdings_list.currentItemChanged.connect(self._on_list_selection_changed)

        layout.addWidget(add_button)
        layout.addWidget(header)
        layout.addWidget(self.holdings_list, 1)
        return card

    def _build_detail_panel(self) -> QFrame:
        card = QFrame()
        card.setObjectName("detailCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(16)

        top_row = QHBoxLayout()
        title = QLabel("Holding Detail")
        title.setObjectName("sectionTitle")

        edit_button = QPushButton("Edit")
        edit_button.setObjectName("primaryButton")
        edit_button.clicked.connect(self.edit_selected_holding)

        delete_button = QPushButton("Delete")
        delete_button.setObjectName("dangerButton")
        delete_button.clicked.connect(self.delete_selected_holding)

        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_table)

        top_row.addWidget(title)
        top_row.addStretch()
        top_row.addWidget(refresh_button)
        top_row.addWidget(edit_button)
        top_row.addWidget(delete_button)

        self.detail_title = QLabel("Select a holding")
        self.detail_title.setObjectName("titleLabel")
        self.detail_title.setWordWrap(True)

        self.detail_badge = QLabel("No selection")
        self.detail_badge.setObjectName("eyebrowLabel")

        summary = QFrame()
        summary.setObjectName("summaryCard")
        summary_layout = QGridLayout(summary)
        summary_layout.setContentsMargins(18, 18, 18, 18)
        summary_layout.setHorizontalSpacing(22)
        summary_layout.setVerticalSpacing(14)

        self.detail_fields: dict[str, QLabel] = {}
        details = (
            ("Metal", 0, 0),
            ("Quantity", 0, 1),
            ("Unit Cost", 0, 2),
            ("Total Cost", 1, 0),
            ("Vendor", 1, 1),
            ("Purchased", 1, 2),
        )
        for name, row, column in details:
            block = self._create_detail_field(name)
            self.detail_fields[name] = block["value"]
            summary_layout.addWidget(block["widget"], row, column)

        notes_title = QLabel("Notes")
        notes_title.setObjectName("sectionTitle")
        self.notes_label = QLabel("No notes for this holding.")
        self.notes_label.setObjectName("notesBox")
        self.notes_label.setWordWrap(True)
        self.notes_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        entries_title = QLabel("Acquisition Breakdown")
        entries_title.setObjectName("sectionTitle")

        self.detail_table = QTableWidget(0, len(self.ENTRY_HEADERS))
        self.detail_table.setHorizontalHeaderLabels(self.ENTRY_HEADERS)
        self.detail_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.detail_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.detail_table.setAlternatingRowColors(True)
        self.detail_table.verticalHeader().setVisible(False)
        self.detail_table.horizontalHeader().setStretchLastSection(True)

        layout.addLayout(top_row)
        layout.addWidget(self.detail_badge)
        layout.addWidget(self.detail_title)
        layout.addWidget(summary)
        layout.addWidget(notes_title)
        layout.addWidget(self.notes_label)
        layout.addWidget(entries_title)
        layout.addWidget(self.detail_table, 1)
        return card

    def _create_detail_field(self, caption: str) -> dict[str, QLabel | QWidget]:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        value = QLabel("--")
        value.setObjectName("detailValue")

        label = QLabel(caption)
        label.setObjectName("detailCaption")

        layout.addWidget(value)
        layout.addWidget(label)
        return {"widget": widget, "value": value}

    def apply_theme(self, theme_name: str) -> None:
        self.current_theme = theme_name
        theme = LIGHT_THEME if theme_name == "light" else DARK_THEME
        self.setStyleSheet(stylesheet(theme))
        self.light_theme_button.setChecked(theme_name == "light")
        self.dark_theme_button.setChecked(theme_name == "dark")

    def refresh_table(self) -> None:
        self.holdings = self.database.list_holdings()
        self._populate_filter_options()
        self.apply_filters()
        self._update_metrics()

    def _populate_filter_options(self) -> None:
        vendors = sorted({holding.vendor for holding in self.holdings if holding.vendor})
        years = sorted(
            {holding.purchased_on[:4] for holding in self.holdings if len(holding.purchased_on) >= 4},
            reverse=True,
        )

        self._reset_combobox(self.metal_filter, ["All Metals", *VALID_METALS])
        self._reset_combobox(self.vendor_filter, ["All Vendors", *vendors])
        self._reset_combobox(self.year_filter, ["All Years", *years])

    def _reset_combobox(self, box: QComboBox, values: list[str]) -> None:
        current = box.currentText()
        box.blockSignals(True)
        box.clear()
        box.addItems(values)
        if current in values:
            box.setCurrentText(current)
        box.blockSignals(False)

    def apply_filters(self) -> None:
        selected_metal = self.metal_filter.currentText()
        selected_vendor = self.vendor_filter.currentText()
        selected_year = self.year_filter.currentText()
        query = self.search_filter.text().strip().lower()

        def matches(holding: Holding) -> bool:
            if selected_metal and selected_metal != "All Metals" and holding.metal != selected_metal:
                return False
            if selected_vendor and selected_vendor != "All Vendors" and holding.vendor != selected_vendor:
                return False
            if selected_year and selected_year != "All Years" and not holding.purchased_on.startswith(selected_year):
                return False
            if query:
                haystack = " ".join(
                    (
                        holding.metal,
                        holding.vendor,
                        holding.purchased_on,
                        holding.notes,
                    )
                ).lower()
                if query not in haystack:
                    return False
            return True

        current_id = self._current_holding_id()
        self.filtered_holdings = [holding for holding in self.holdings if matches(holding)]
        self._populate_holdings_list(current_id)
        self._update_metrics()

    def _populate_holdings_list(self, preferred_id: int | None = None) -> None:
        self.holdings_list.blockSignals(True)
        self.holdings_list.clear()

        selected_row = 0
        for index, holding in enumerate(self.filtered_holdings):
            item = QListWidgetItem(self._holding_card_text(holding))
            item.setData(Qt.ItemDataRole.UserRole, holding.id)
            item.setSizeHint(QSize(0, 104))
            item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.holdings_list.addItem(item)
            if preferred_id is not None and holding.id == preferred_id:
                selected_row = index

        self.holdings_list.blockSignals(False)

        if self.filtered_holdings:
            self.holdings_list.setCurrentRow(selected_row)
            self._show_holding_detail(self.filtered_holdings[selected_row])
        else:
            self._show_holding_detail(None)

    def _holding_card_text(self, holding: Holding) -> str:
        vendor = holding.vendor or "Direct purchase"
        notes = holding.notes.strip() or "No notes"
        preview = notes[:44] + "..." if len(notes) > 44 else notes
        return (
            f"{holding.metal} | {holding.quantity:.4f} oz\n"
            f"{vendor}\n"
            f"{holding.purchased_on} | Total ${holding.total_cost:,.2f}\n"
            f"{preview}"
        )

    def _update_metrics(self) -> None:
        total_value = sum(holding.total_cost for holding in self.filtered_holdings)
        total_ounces = sum(holding.quantity for holding in self.filtered_holdings)

        self.total_value_metric["value"].setText(f"${total_value:,.2f}")
        self.total_ounces_metric["value"].setText(f"{total_ounces:.4f} oz")
        self.position_count_metric["value"].setText(str(len(self.filtered_holdings)))

    def _on_list_selection_changed(
        self, current: QListWidgetItem | None, _: QListWidgetItem | None
    ) -> None:
        if current is None:
            self._show_holding_detail(None)
            return
        holding_id = current.data(Qt.ItemDataRole.UserRole)
        holding = next((item for item in self.filtered_holdings if item.id == holding_id), None)
        self._show_holding_detail(holding)

    def _show_holding_detail(self, holding: Holding | None) -> None:
        if holding is None:
            self.detail_badge.setText("No selection")
            self.detail_title.setText("Select a holding")
            for label in self.detail_fields.values():
                label.setText("--")
            self.notes_label.setText("No notes for this holding.")
            self.detail_table.setRowCount(0)
            return

        self.detail_badge.setText(f"{holding.metal} Position")
        self.detail_title.setText(f"{holding.vendor or 'Direct Purchase'}")
        self.detail_fields["Metal"].setText(holding.metal)
        self.detail_fields["Quantity"].setText(f"{holding.quantity:.4f} oz")
        self.detail_fields["Unit Cost"].setText(f"${holding.unit_cost:,.2f}")
        self.detail_fields["Total Cost"].setText(f"${holding.total_cost:,.2f}")
        self.detail_fields["Vendor"].setText(holding.vendor or "Direct purchase")
        self.detail_fields["Purchased"].setText(holding.purchased_on or "--")
        self.notes_label.setText(holding.notes.strip() or "No notes for this holding.")
        self._populate_detail_table(holding)

    def _populate_detail_table(self, holding: Holding) -> None:
        self.detail_table.setRowCount(1)
        values = (
            "Recorded",
            holding.metal,
            f"{holding.quantity:.4f} oz",
            f"${holding.unit_cost:,.2f}",
            holding.vendor or "Direct purchase",
            f"${holding.total_cost:,.2f}",
        )
        for column, value in enumerate(values):
            item = QTableWidgetItem(value)
            self.detail_table.setItem(0, column, item)
        self.detail_table.resizeColumnsToContents()

    def _current_holding_id(self) -> int | None:
        current = self.holdings_list.currentItem()
        if current is None:
            return None
        return current.data(Qt.ItemDataRole.UserRole)

    def selected_holding(self) -> Holding | None:
        holding_id = self._current_holding_id()
        if holding_id is None:
            return None
        return next((holding for holding in self.filtered_holdings if holding.id == holding_id), None)

    def add_holding(self) -> None:
        dialog = HoldingDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.database.add_holding(dialog.to_holding())
            self.refresh_table()

    def edit_selected_holding(self) -> None:
        holding = self.selected_holding()
        if holding is None:
            self._show_message("Select a holding before editing.")
            return
        dialog = HoldingDialog(self, holding)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated = replace(dialog.to_holding(), id=holding.id)
            self.database.update_holding(updated)
            self.refresh_table()

    def delete_selected_holding(self) -> None:
        holding = self.selected_holding()
        if holding is None:
            self._show_message("Select a holding before deleting.")
            return
        answer = QMessageBox.question(
            self,
            "Delete Holding",
            f"Delete the selected {holding.metal.lower()} holding?",
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.database.delete_holding(holding.id or 0)
            self.refresh_table()

    def _show_message(self, text: str) -> None:
        QMessageBox.information(self, "Plutus", text)
def build_application(database_path: Path | None = None) -> tuple[QApplication, MainWindow]:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    db = Database(database_path or default_database_path())
    window = MainWindow(db)
    app.aboutToQuit.connect(db.close)
    return app, window


def main() -> int:
    app, window = build_application()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
