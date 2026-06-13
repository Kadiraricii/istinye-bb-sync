from __future__ import annotations

from core.config import (
    ACCENT, ACCENT_BG, BG_BASE, BG_ELEVATED, BG_HOVER,
    BORDER, BORDER_FAINT, CORNER_RADIUS, ERROR, SUCCESS, TEXT_PRIMARY,
    TEXT_SECONDARY, TEXT_TERTIARY, WARNING,
)

# ── CustomTkinter appearance ──────────────────────────────────
CTK_APPEARANCE = "dark"
CTK_COLOR_THEME = "dark-blue"

# ── Font tuples ───────────────────────────────────────────────
FONT_HERO    = ("Inter", 22, "bold")
FONT_HEADING = ("Inter", 15, "bold")
FONT_BODY    = ("Inter", 13)
FONT_SMALL   = ("Inter", 11)
FONT_MONO    = ("JetBrains Mono", 11)

# ── Widget defaults (dicts for ctk **kwargs) ──────────────────
BTN_PRIMARY = dict(
    fg_color=ACCENT,
    hover_color="#0284c7",
    text_color="#ffffff",
    corner_radius=CORNER_RADIUS,
    font=FONT_BODY,
    height=40,
)

BTN_SECONDARY = dict(
    fg_color=BG_HOVER,
    hover_color=BORDER,
    text_color=TEXT_PRIMARY,
    corner_radius=CORNER_RADIUS,
    font=FONT_BODY,
    height=40,
)

BTN_GHOST = dict(
    fg_color="transparent",
    hover_color=BG_HOVER,
    text_color=TEXT_SECONDARY,
    corner_radius=CORNER_RADIUS,
    font=FONT_SMALL,
    height=32,
)

ENTRY = dict(
    fg_color=BG_ELEVATED,
    border_color=BORDER,
    border_width=1,
    text_color=TEXT_PRIMARY,
    placeholder_text_color=TEXT_TERTIARY,
    corner_radius=CORNER_RADIUS,
    font=FONT_BODY,
    height=40,
)

FRAME_CARD = dict(
    fg_color=BG_ELEVATED,
    corner_radius=8,
    border_width=1,
    border_color=BORDER,
)

FRAME_SELECTED = dict(
    fg_color=BG_ELEVATED,
    corner_radius=8,
    border_width=1,
    border_color=ACCENT,
)

# ── Status dot colours ────────────────────────────────────────
DOT_IDLE    = TEXT_TERTIARY
DOT_BUSY    = WARNING
DOT_OK      = SUCCESS
DOT_ERROR   = ERROR

# Re-export config colours so screens only import from theme
__all__ = [
    "CTK_APPEARANCE", "CTK_COLOR_THEME",
    "FONT_HERO", "FONT_HEADING", "FONT_BODY", "FONT_SMALL", "FONT_MONO",
    "BTN_PRIMARY", "BTN_SECONDARY", "BTN_GHOST",
    "ENTRY", "FRAME_CARD", "FRAME_SELECTED",
    "DOT_IDLE", "DOT_BUSY", "DOT_OK", "DOT_ERROR",
    "BG_BASE", "BG_ELEVATED", "BG_HOVER", "BORDER", "BORDER_FAINT",
    "ACCENT", "ACCENT_BG", "SUCCESS", "WARNING", "ERROR",
    "TEXT_PRIMARY", "TEXT_SECONDARY", "TEXT_TERTIARY",
    "CORNER_RADIUS",
]
