"""Styling helpers for the Plutus desktop UI."""

from __future__ import annotations

LIGHT_THEME = {
    "window": "#f1f3f4",
    "panel": "#ffffff",
    "panel_alt": "#f7f7f4",
    "sidebar": "#f7f7f4",
    "text": "#1f2933",
    "muted": "#6f7479",
    "border": "#c8ccd0",
    "primary": "#b58a2a",
    "primary_soft": "#f4e7bf",
    "accent": "#d6ad3f",
    "success": "#28a745",
    "danger": "#b75d5d",
    "selection": "#f4e7bf",
}

DARK_THEME = {
    "window": "#141414",
    "panel": "#1d1d1b",
    "panel_alt": "#25231f",
    "sidebar": "#181816",
    "text": "#f2f0e8",
    "muted": "#aaa69a",
    "border": "#4b4a45",
    "primary": "#d6b24c",
    "primary_soft": "#3a3120",
    "accent": "#c4c7c9",
    "success": "#57c785",
    "danger": "#d97878",
    "selection": "#3a3120",
}

THEMES = {
    "light": LIGHT_THEME,
    "dark": DARK_THEME,
}


def stylesheet(theme: dict[str, str]) -> str:
    return """
    QWidget {{
        background: {window};
        color: {text};
        font-size: 14px;
    }}
    QLabel {{
        background: transparent;
        color: {text};
    }}
    QMainWindow {{
        background: {window};
    }}
    QDialog {{
        background: {window};
        color: {text};
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
    QFrame#topBar,
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
    QFrame#topBar {{
        background: {panel};
        border-radius: 18px;
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
    QPushButton#themeToggleButton,
    QPushButton#topIconButton {{
        background: transparent;
        border: none;
        border-radius: 12px;
        font-size: 20px;
        min-width: 44px;
        min-height: 44px;
        padding: 0;
    }}
    QPushButton#themeToggleButton:hover,
    QPushButton#topIconButton:hover {{
        background: {primary_soft};
        color: {primary};
    }}
    QLineEdit,
    QComboBox,
    QDateEdit,
    QPlainTextEdit {{
        background: {panel};
        color: {text};
        border: 1px solid {border};
        border-radius: 14px;
        padding: 10px 12px;
        selection-background-color: {selection};
    }}
    QLineEdit:focus,
    QComboBox:focus,
    QDateEdit:focus,
    QPlainTextEdit:focus {{
        border-color: {primary};
    }}
    QLineEdit:disabled,
    QComboBox:disabled,
    QDateEdit:disabled,
    QPlainTextEdit:disabled {{
        background: {panel_alt};
        color: {muted};
    }}
    QLineEdit::placeholder {{
        color: {muted};
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
