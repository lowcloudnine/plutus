"""PyQt6 UI behavior for recording precious metal holdings."""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

from PyQt6.QtCore import QDate, QSettings, QSize, Qt
from PyQt6.QtWidgets import (
    QApplication,
    QBoxLayout,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..database import (
    Contact,
    Database,
    DatabaseError,
    Holding,
    VALID_METALS,
    encrypt_plaintext_database,
    is_plaintext_sqlite_database,
)
from .styles import THEMES, stylesheet

DATABASE_PATH_KEY = "storage/database_path"


def default_database_path() -> Path:
    home = Path.home()
    return home / ".local" / "share" / "plutus" / "plutus.sqlite3"


def database_settings() -> QSettings:
    return QSettings("Plutus", "Plutus")


def load_database_path() -> Path | None:
    raw_value = database_settings().value(DATABASE_PATH_KEY)
    if not raw_value:
        return None
    return Path(str(raw_value)).expanduser()


def save_database_path(database_path: Path) -> None:
    database_settings().setValue(DATABASE_PATH_KEY, str(database_path))


def clear_database_path() -> None:
    database_settings().remove(DATABASE_PATH_KEY)


def _bundle_roots() -> set[Path]:
    if not getattr(sys, "frozen", False):
        return set()

    roots: set[Path] = set()
    executable_dir = Path(sys.executable).resolve().parent
    roots.add(executable_dir)

    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        roots.add(Path(meipass).resolve())

    return roots


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def validate_database_path(database_path: Path) -> str | None:
    resolved_path = database_path.expanduser().resolve(strict=False)
    for root in _bundle_roots():
        if _is_within(resolved_path, root):
            return (
                "Plutus cannot store its SQLite database inside the application bundle "
                "or next to the packaged executable. Choose a folder in your home "
                "directory, Documents, or another writable data location."
            )
    return None


class DatabaseLocationDialog(QDialog):
    def __init__(
        self,
        parent: QWidget | None = None,
        suggested_path: Path | None = None,
        *,
        eyebrow_text: str = "First Launch",
        accept_text: str = "Use This Location",
        cancel_text: str = "Quit",
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Choose Database Location")
        self.setModal(True)
        self.setMinimumSize(620, 440)
        self.resize(620, 440)

        selected_path = suggested_path or default_database_path()

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(24, 24, 24, 24)
        root_layout.setSpacing(18)

        hero = QFrame()
        hero.setObjectName("contentCard")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(22, 22, 22, 22)
        hero_layout.setSpacing(10)

        eyebrow = QLabel(eyebrow_text)
        eyebrow.setObjectName("eyebrowLabel")

        title = QLabel("Choose where Plutus stores your portfolio database")
        title.setObjectName("sectionTitle")
        title.setWordWrap(True)
        title.setMinimumHeight(34)

        message = QLabel(
            "Plutus saves your holdings in a local SQLite file. Pick a location you control. "
            "The app will remember this path and reuse it on future launches."
        )
        message.setWordWrap(True)
        message.setMinimumHeight(44)

        guidance = QLabel(
            "A folder under your home directory or Documents is a good choice. "
            "Packaged app folders are blocked."
        )
        guidance.setObjectName("eyebrowLabel")
        guidance.setWordWrap(True)
        guidance.setMinimumHeight(36)

        hero_layout.addWidget(eyebrow)
        hero_layout.addWidget(title)
        hero_layout.addWidget(message)
        hero_layout.addWidget(guidance)

        chooser_card = QFrame()
        chooser_card.setObjectName("summaryCard")
        chooser_layout = QVBoxLayout(chooser_card)
        chooser_layout.setContentsMargins(18, 18, 18, 18)
        chooser_layout.setSpacing(12)

        field_label = QLabel("Database File")
        field_label.setObjectName("eyebrowLabel")

        path_row = QHBoxLayout()
        path_row.setContentsMargins(0, 0, 0, 0)
        path_row.setSpacing(10)

        self.path_input = QLineEdit(str(selected_path))
        self.path_input.setPlaceholderText(str(default_database_path()))

        browse_button = QPushButton("Browse")
        browse_button.setObjectName("primaryButton")
        browse_button.clicked.connect(self._browse_for_path)

        path_row.addWidget(self.path_input, 1)
        path_row.addWidget(browse_button)

        help_text = QLabel("Plutus will create the file if it does not already exist.")
        help_text.setObjectName("detailCaption")
        help_text.setWordWrap(True)
        help_text.setMinimumHeight(22)

        chooser_layout.addWidget(field_label)
        chooser_layout.addLayout(path_row)
        chooser_layout.addWidget(help_text)

        buttons = QDialogButtonBox()
        self.choose_button = buttons.addButton(accept_text, QDialogButtonBox.ButtonRole.AcceptRole)
        self.cancel_button = buttons.addButton(cancel_text, QDialogButtonBox.ButtonRole.RejectRole)
        self.choose_button.setObjectName("primaryButton")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        root_layout.addWidget(hero)
        root_layout.addWidget(chooser_card)
        root_layout.addStretch()
        root_layout.addWidget(buttons)

    def _browse_for_path(self) -> None:
        selected_path, _ = QFileDialog.getSaveFileName(
            self,
            "Choose SQLite Database Location",
            self.path_input.text().strip() or str(default_database_path()),
            "SQLite Database (*.sqlite3 *.sqlite *.db);;All Files (*)",
        )
        if selected_path:
            self.path_input.setText(selected_path)

    def selected_database_path(self) -> Path:
        database_path = Path(self.path_input.text().strip()).expanduser()
        if database_path.suffix.lower() not in {".sqlite3", ".sqlite", ".db"}:
            database_path = database_path.with_suffix(".sqlite3")
        return database_path


class DatabasePasswordDialog(QDialog):
    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        database_path: Path,
        confirm_password: bool,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Database Password")
        self.setModal(True)
        self.setMinimumSize(520, 300)
        self.resize(520, 300)
        self.confirm_password = confirm_password

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(24, 24, 24, 24)
        root_layout.setSpacing(16)

        card = QFrame()
        card.setObjectName("contentCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(22, 22, 22, 22)
        card_layout.setSpacing(10)

        eyebrow = QLabel("Encrypted Database")
        eyebrow.setObjectName("eyebrowLabel")

        title_text = "Create a database password" if confirm_password else "Unlock database"
        title = QLabel(title_text)
        title.setObjectName("sectionTitle")
        title.setWordWrap(True)

        detail_text = (
            "Choose the password Plutus will use to encrypt this SQLite database."
            if confirm_password
            else "Enter the password for this encrypted SQLite database."
        )
        detail = QLabel(f"{detail_text}\n{database_path}")
        detail.setWordWrap(True)
        detail.setMinimumHeight(52)

        card_layout.addWidget(eyebrow)
        card_layout.addWidget(title)
        card_layout.addWidget(detail)

        form_card = QFrame()
        form_card.setObjectName("summaryCard")
        form_layout = QFormLayout(form_card)
        form_layout.setContentsMargins(18, 18, 18, 18)
        form_layout.setSpacing(12)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Database password")
        form_layout.addRow("Password", self.password_input)

        self.confirm_input: QLineEdit | None = None
        if confirm_password:
            self.confirm_input = QLineEdit()
            self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.confirm_input.setPlaceholderText("Repeat password")
            form_layout.addRow("Confirm", self.confirm_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept_if_valid)
        buttons.rejected.connect(self.reject)

        root_layout.addWidget(card)
        root_layout.addWidget(form_card)
        root_layout.addStretch()
        root_layout.addWidget(buttons)

    def _accept_if_valid(self) -> None:
        password = self.password()
        if not password:
            QMessageBox.warning(self, "Password Required", "Enter a database password.")
            return
        if self.confirm_input is not None and password != self.confirm_input.text():
            QMessageBox.warning(self, "Password Mismatch", "The database passwords do not match.")
            return
        self.accept()

    def password(self) -> str:
        return self.password_input.text()


def prompt_for_database_path(parent: QWidget | None = None) -> Path | None:
    suggested_path = default_database_path()
    while True:
        dialog = DatabaseLocationDialog(parent, suggested_path)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            answer = QMessageBox.question(
                parent,
                "Database Location Required",
                (
                    "Plutus needs a database location before it can start.\n\n"
                    "Do you want to quit instead of choosing a SQLite file?"
                ),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer == QMessageBox.StandardButton.Yes:
                return None
            continue

        database_path = dialog.selected_database_path()
        suggested_path = database_path

        validation_error = validate_database_path(database_path)
        if validation_error is not None:
            QMessageBox.critical(parent, "Invalid Database Location", validation_error)
            continue

        try:
            database_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            QMessageBox.critical(
                parent,
                "Invalid Database Location",
                f"Plutus could not use that location:\n{exc}",
            )
            continue

        return database_path


def resolve_database_path(
    database_path: Path | None = None, parent: QWidget | None = None
) -> Path | None:
    if database_path is not None:
        resolved_path = database_path.expanduser()
        validation_error = validate_database_path(resolved_path)
        if validation_error is not None:
            raise ValueError(validation_error)
        return resolved_path

    saved_path = load_database_path()
    if saved_path is not None:
        validation_error = validate_database_path(saved_path)
        if validation_error is None:
            if saved_path.exists():
                return saved_path
            clear_database_path()
            QMessageBox.warning(
                parent,
                "Saved Database Not Found",
                (
                    "The previously selected SQLite database could not be found:\n"
                    f"{saved_path}\n\n"
                    "Choose a database location to continue."
                ),
            )
        else:
            clear_database_path()
            QMessageBox.warning(parent, "Saved Database Location Reset", validation_error)

    chosen_path = prompt_for_database_path(parent)
    if chosen_path is not None:
        save_database_path(chosen_path)
    return chosen_path


def open_database_with_password(database_path: Path, parent: QWidget | None = None) -> Database | None:
    while True:
        is_existing_database = database_path.exists() and database_path.stat().st_size > 0
        needs_setup_password = (
            not is_existing_database or is_plaintext_sqlite_database(database_path)
        )
        dialog = DatabasePasswordDialog(
            parent,
            database_path=database_path,
            confirm_password=needs_setup_password,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None

        password = dialog.password()
        if is_plaintext_sqlite_database(database_path):
            answer = QMessageBox.question(
                parent,
                "Encrypt Existing Database",
                (
                    "This database is currently an unencrypted SQLite file.\n\n"
                    "Encrypt it now using the password you entered?"
                ),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if answer != QMessageBox.StandardButton.Yes:
                continue

            try:
                encrypt_plaintext_database(database_path, password)
            except DatabaseError as exc:
                QMessageBox.critical(parent, "Database Encryption Failed", str(exc))
                continue

        try:
            return Database(database_path, password)
        except DatabaseError as exc:
            QMessageBox.critical(parent, "Database Error", str(exc))


class ContactDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Contact")
        self.setModal(True)
        self.resize(460, 560)

        self.name = QLineEdit()
        self.name.setPlaceholderText("Company or individual")
        self.address_line1 = QLineEdit()
        self.address_line2 = QLineEdit()
        self.city = QLineEdit()
        self.state = QLineEdit()
        self.postal_code = QLineEdit()
        self.country = QLineEdit()
        self.phone = QLineEdit()
        self.url = QLineEdit()
        self.is_buyer = QCheckBox("Buyer")
        self.is_seller = QCheckBox("Seller")
        self.is_seller.setChecked(True)

        form = QFormLayout()
        form.addRow("Name", self.name)
        form.addRow("Address", self.address_line1)
        form.addRow("Address 2", self.address_line2)
        form.addRow("City", self.city)
        form.addRow("State", self.state)
        form.addRow("Postal Code", self.postal_code)
        form.addRow("Country", self.country)
        form.addRow("Phone", self.phone)
        form.addRow("URL", self.url)

        roles = QHBoxLayout()
        roles.addWidget(self.is_buyer)
        roles.addWidget(self.is_seller)
        roles.addStretch()
        form.addRow("Role", roles)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept_if_valid)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def _accept_if_valid(self) -> None:
        if not self.name.text().strip():
            QMessageBox.warning(self, "Name Required", "Enter a company or individual name.")
            return
        if not self.is_buyer.isChecked() and not self.is_seller.isChecked():
            QMessageBox.warning(self, "Role Required", "Choose buyer, seller, or both.")
            return
        self.accept()

    def to_contact(self) -> Contact:
        return Contact(
            id=None,
            name=self.name.text().strip(),
            address_line1=self.address_line1.text().strip(),
            address_line2=self.address_line2.text().strip(),
            city=self.city.text().strip(),
            state=self.state.text().strip(),
            postal_code=self.postal_code.text().strip(),
            country=self.country.text().strip(),
            phone=self.phone.text().strip(),
            url=self.url.text().strip(),
            is_buyer=self.is_buyer.isChecked(),
            is_seller=self.is_seller.isChecked(),
        )


class HoldingDialog(QDialog):
    def __init__(
        self,
        database: Database,
        parent: QWidget | None = None,
        holding: Holding | None = None,
    ) -> None:
        super().__init__(parent)
        self.database = database
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

        self.vendor = QComboBox()
        self.add_contact_button = QPushButton("New Contact")
        self.add_contact_button.clicked.connect(self.add_contact)

        vendor_row = QHBoxLayout()
        vendor_row.addWidget(self.vendor, 1)
        vendor_row.addWidget(self.add_contact_button)

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
        form.addRow("Vendor", vendor_row)
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
        self._load_contacts()
        if holding is not None:
            self.load_holding(holding)

    def _load_contacts(self, selected_contact_id: int | None = None) -> None:
        self.vendor.blockSignals(True)
        self.vendor.clear()
        self.vendor.addItem("Direct purchase", None)
        for contact in self.database.list_contacts(sellers_only=True):
            self.vendor.addItem(contact.name, contact.id)
        if selected_contact_id is not None:
            index = self.vendor.findData(selected_contact_id)
            if index >= 0:
                self.vendor.setCurrentIndex(index)
        self.vendor.blockSignals(False)

    def add_contact(self) -> None:
        dialog = ContactDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        contact = dialog.to_contact()
        contact_id = self.database.add_contact(contact)
        self._load_contacts(contact_id)

    def load_holding(self, holding: Holding) -> None:
        self._holding_id = holding.id
        self.metal.setCurrentText(holding.metal)
        self.quantity.setValue(holding.quantity)
        self.unit_cost.setValue(holding.unit_cost)
        self._load_contacts(holding.contact_id)
        parsed_date = QDate.fromString(holding.purchased_on, "yyyy-MM-dd")
        self.purchased_on.setDate(parsed_date if parsed_date.isValid() else QDate.currentDate())
        self.notes.setPlainText(holding.notes)

    def to_holding(self) -> Holding:
        contact_id = self.vendor.currentData()
        return Holding(
            id=self._holding_id,
            metal=self.metal.currentText(),
            quantity=float(self.quantity.value()),
            unit_cost=float(self.unit_cost.value()),
            contact_id=int(contact_id) if contact_id is not None else None,
            vendor=self.vendor.currentText() if contact_id is not None else "",
            purchased_on=self.purchased_on.date().toString("yyyy-MM-dd"),
            notes=self.notes.toPlainText().strip(),
        )


class MainWindow(QMainWindow):
    ENTRY_HEADERS = ("Status", "Metal", "Quantity", "Unit Cost", "Vendor", "Total")
    PHONE_WIDTH = 620
    TABLET_WIDTH = 980

    def __init__(self, database: Database) -> None:
        super().__init__()
        self.database = database
        self.holdings: list[Holding] = []
        self.filtered_holdings: list[Holding] = []
        self.current_theme = "light"
        self.setWindowTitle("Plutus")
        self.resize(1380, 860)
        self.setMinimumSize(360, 640)

        self._filter_fields: list[QWidget] = []

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(18, 18, 18, 18)
        root_layout.setSpacing(18)

        top_bar = self._build_top_bar()

        self.outer_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.outer_layout.setContentsMargins(0, 0, 0, 0)
        self.outer_layout.setSpacing(18)

        content = self._build_content()

        root_layout.addWidget(top_bar)
        self.outer_layout.addWidget(content, 1)
        root_layout.addLayout(self.outer_layout, 1)
        scroll.setWidget(root)
        self.setCentralWidget(scroll)

        self.apply_theme("light")
        self._apply_responsive_layout()
        self.refresh_table()

    def _build_top_bar(self) -> QFrame:
        top_bar = QFrame()
        top_bar.setObjectName("topBar")

        layout = QHBoxLayout(top_bar)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(12)

        title = QLabel("Plutus")
        title.setObjectName("sectionTitle")

        # subtitle = QLabel("Portfolio Console")
        # subtitle.setObjectName("eyebrowLabel")

        label_stack = QVBoxLayout()
        label_stack.setContentsMargins(0, 0, 0, 0)
        label_stack.setSpacing(2)
        label_stack.addWidget(title)
        # label_stack.addWidget(subtitle)

        self.theme_toggle_button = QPushButton()
        self.theme_toggle_button.setObjectName("themeToggleButton")
        self.theme_toggle_button.setFlat(True)
        self.theme_toggle_button.clicked.connect(self.toggle_theme)
        self.theme_toggle_button.setCursor(Qt.CursorShape.PointingHandCursor)

        settings_button = QPushButton("⚙")
        settings_button.setObjectName("topIconButton")
        settings_button.setFlat(True)
        settings_button.setToolTip("Change database location")
        settings_button.clicked.connect(self.change_database_location)
        settings_button.setCursor(Qt.CursorShape.PointingHandCursor)

        layout.addLayout(label_stack)
        layout.addStretch()
        layout.addWidget(settings_button)
        layout.addWidget(self.theme_toggle_button)
        return top_bar

    def _build_content(self) -> QFrame:
        card = QFrame()
        card.setObjectName("contentCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(18)

        layout.addWidget(self._build_header())
        layout.addWidget(self._build_filters())

        self.main_row = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.main_row.setSpacing(18)
        self.holdings_panel = self._build_holdings_panel()
        self.detail_panel = self._build_detail_panel()
        self.main_row.addWidget(self.holdings_panel, 4)
        self.main_row.addWidget(self.detail_panel, 6)
        layout.addLayout(self.main_row, 1)

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

        self.stats_row = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.stats_row.setSpacing(14)

        self.total_value_metric = self._create_metric_card("Total Value")
        self.total_ounces_metric = self._create_metric_card("Total Ounces")
        self.position_count_metric = self._create_metric_card("Positions")

        self.stats_row.addWidget(self.total_value_metric["card"])
        self.stats_row.addWidget(self.total_ounces_metric["card"])
        self.stats_row.addWidget(self.position_count_metric["card"])
        layout.addLayout(self.stats_row)

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

        self.filter_layout = layout
        self._filter_fields = [
            self._labeled_widget("Metal", self.metal_filter),
            self._labeled_widget("Vendor", self.vendor_filter),
            self._labeled_widget("Year", self.year_filter),
            self._labeled_widget("Search", self.search_filter),
        ]
        self._arrange_filter_fields(columns=4)

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

        self.detail_top_row = QBoxLayout(QBoxLayout.Direction.LeftToRight)
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

        self.detail_top_row.addWidget(title)
        self.detail_top_row.addStretch()
        self.detail_top_row.addWidget(refresh_button)
        self.detail_top_row.addWidget(edit_button)
        self.detail_top_row.addWidget(delete_button)

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
        self.detail_blocks: list[QWidget] = []
        details = ("Metal", "Quantity", "Unit Cost", "Total Cost", "Vendor", "Purchased")
        for name in details:
            block = self._create_detail_field(name)
            self.detail_fields[name] = block["value"]
            self.detail_blocks.append(block["widget"])

        self.summary_layout = summary_layout
        self._arrange_detail_summary(columns=3)

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

        layout.addLayout(self.detail_top_row)
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
        self.setStyleSheet(stylesheet(THEMES[theme_name]))
        next_theme = "dark" if theme_name == "light" else "light"
        icon = "☾" if theme_name == "light" else "☀"
        self.theme_toggle_button.setText(icon)
        self.theme_toggle_button.setToolTip(f"Switch to {next_theme} theme")

    def toggle_theme(self) -> None:
        self.apply_theme("dark" if self.current_theme == "light" else "light")

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._apply_responsive_layout()

    def _apply_responsive_layout(self) -> None:
        width = self.width()
        is_phone = width <= self.PHONE_WIDTH
        is_tablet = width <= self.TABLET_WIDTH

        self.outer_layout.setDirection(
            QBoxLayout.Direction.TopToBottom if is_phone else QBoxLayout.Direction.LeftToRight
        )
        self.main_row.setDirection(
            QBoxLayout.Direction.TopToBottom if is_tablet else QBoxLayout.Direction.LeftToRight
        )
        self.stats_row.setDirection(
            QBoxLayout.Direction.TopToBottom if is_phone else QBoxLayout.Direction.LeftToRight
        )
        self.detail_top_row.setDirection(
            QBoxLayout.Direction.TopToBottom if is_phone else QBoxLayout.Direction.LeftToRight
        )

        self.holdings_panel.setMinimumWidth(0)
        self.detail_panel.setMinimumWidth(0)

        columns = 1 if is_phone else 2 if is_tablet else 4
        self._arrange_filter_fields(columns)
        self._arrange_detail_summary(1 if is_phone else 2 if is_tablet else 3)

    def _arrange_filter_fields(self, columns: int) -> None:
        while self.filter_layout.count():
            item = self.filter_layout.takeAt(0)
            if item.widget() is not None:
                item.widget().setParent(None)

        for index, widget in enumerate(self._filter_fields):
            row = index // columns
            column = index % columns
            self.filter_layout.addWidget(widget, row, column)

    def _arrange_detail_summary(self, columns: int) -> None:
        while self.summary_layout.count():
            item = self.summary_layout.takeAt(0)
            if item.widget() is not None:
                item.widget().setParent(None)

        for index, widget in enumerate(self.detail_blocks):
            row = index // columns
            column = index % columns
            self.summary_layout.addWidget(widget, row, column)

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
        dialog = HoldingDialog(self.database, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.database.add_holding(dialog.to_holding())
            self.refresh_table()

    def edit_selected_holding(self) -> None:
        holding = self.selected_holding()
        if holding is None:
            self._show_message("Select a holding before editing.")
            return
        dialog = HoldingDialog(self.database, self, holding)
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

    def change_database_location(self) -> None:
        suggested_path = self.database.db_path
        while True:
            dialog = DatabaseLocationDialog(
                self,
                suggested_path,
                eyebrow_text="Settings",
                accept_text="Switch Database",
                cancel_text="Cancel",
            )
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return

            database_path = dialog.selected_database_path()
            suggested_path = database_path

            validation_error = validate_database_path(database_path)
            if validation_error is not None:
                QMessageBox.critical(self, "Invalid Database Location", validation_error)
                continue

            try:
                database_path.parent.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                QMessageBox.critical(
                    self,
                    "Invalid Database Location",
                    f"Plutus could not use that location:\n{exc}",
                )
                continue

            current_path = self.database.db_path.expanduser().resolve(strict=False)
            selected_path = database_path.expanduser().resolve(strict=False)
            if selected_path == current_path:
                self._show_message("Plutus is already using that database location.")
                return

            answer = QMessageBox.question(
                self,
                "Switch Database",
                (
                    "Switch Plutus to this SQLite database?\n\n"
                    f"{selected_path}\n\n"
                    "Existing holdings stay in the current database file unless you choose "
                    "that file again later."
                ),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                continue

            new_database = open_database_with_password(database_path, self)
            if new_database is None:
                return

            old_database = self.database
            self.database = new_database
            save_database_path(database_path)
            old_database.close()
            self.refresh_table()
            self._show_message(f"Database location updated:\n{selected_path}")
            return

    def close_database(self) -> None:
        self.database.close()

    def _show_message(self, text: str) -> None:
        QMessageBox.information(self, "Plutus", text)


def build_application(database_path: Path | None = None) -> tuple[QApplication, MainWindow]:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(stylesheet(THEMES["light"]))
    resolved_database_path = resolve_database_path(database_path)
    if resolved_database_path is None:
        raise SystemExit(0)
    db = open_database_with_password(resolved_database_path)
    if db is None:
        raise SystemExit(0)
    window = MainWindow(db)
    app.aboutToQuit.connect(window.close_database)
    return app, window


def main() -> int:
    app, window = build_application()
    window.show()
    return app.exec()
