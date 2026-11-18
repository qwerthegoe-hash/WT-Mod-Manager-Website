
"""WT Mod Manager 1.2 — unified application theme engine.

Drop-in replacement for ui/theme_engine.py.

Public API:
    ACCENTS
    effective_mode(settings)
    transform_stylesheet(source, settings, apply_accent=True)
    theme_palette(settings)
    accent_color(settings)

All replacements are single-pass and made from original QSS.
This module does not reapply styles on a timer or change window flags.
"""

import re
from functools import lru_cache

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication


# ==========================================
# ACCENT THEMES
# ==========================================

# Each theme:
#   accent, deep accent, hover accent

ACCENTS = {
    "blue": (
        "#4777BA",
        "#365F9C",
        "#4675B5",
    ),
    "green": (
        "#34B887",
        "#197D60",
        "#289F79",
    ),
    "purple": (
        "#9868D9",
        "#6842A8",
        "#8155BD",
    ),
    "red": (
        "#DB6677",
        "#9B3346",
        "#B8465A",
    ),
    "orange": (
        "#DB9C43",
        "#996422",
        "#B77D2C",
    ),
}


# ==========================================
# FONTS AND APPEARANCE MODES
# ==========================================

FONTS = (
    "Segoe UI",
    "Arial",
    "Verdana",
    "Tahoma",
    "Georgia",
)

MODES = (
    "black",
    "white",
    "system",
)


# ==========================================
# LIGHT MODE COLOR MAPPING
# ==========================================

# Left: original dark interface color.
# Right: corresponding light interface color.
#
# Every page can continue using its original
# dark QSS values, which this engine transforms.

LIGHT_COLORS = {
    "#15171B": "#F3F5F9",
    "#1D2026": "#FFFFFF",
    "#13161B": "#EDF1F6",
    "#111317": "#E9EFF6",
    "#14171C": "#F7F9FC",
    "#171B22": "#E7ECF3",
    "#191C22": "#E5EAF1",
    "#15191F": "#D7DEE9",
    "#23272F": "#FFFFFF",
    "#24272D": "#E2E7EE",
    "#242933": "#E0E6EF",
    "#282C33": "#E7EDF4",
    "#292E36": "#E2E8F1",
    "#2A303A": "#D7DFEA",
    "#2C313A": "#E3E9F1",
    "#303742": "#CBD5E1",
    "#343B46": "#CCD5E0",
    "#303640": "#E5EBF2",
    "#30353F": "#E9EDF4",
    "#343A44": "#DCE4EF",
    "#22262D": "#D1DAE6",
    "#383E47": "#CFD6E0",
    "#353A43": "#D6DEE9",
    "#414956": "#BFCAD9",
    "#3A424D": "#CBD3DE",
    "#454C57": "#B5C0CF",
    "#444D5A": "#B2BDCA",
    "#627084": "#8996A7",
    "#647084": "#8895A6",
    "#697382": "#8A95A4",
    "#E9EDF3": "#202A38",
    "#E5EAF2": "#263244",
    "#E7EBF2": "#253044",
    "#DFE4EC": "#293446",
    "#D9E0EB": "#283245",
    "#FFFFFF": "#182334",
    "#F0F2F6": "#1E2A3B",
    "#E3EAF5": "#253044",
    "#E5EDF8": "#FFFFFF",
    "#DCE6F4": "#FFFFFF",
    "#949EAD": "#5B697B",
    "#939EAF": "#566476",
    "#9AA5B5": "#596778",
    "#98A2B3": "#5A697B",
    "#8491A3": "#647389",
    "#AEB9C9": "#536176",
    "#7E8795": "#627187",
    "#8290A3": "#60748D",
    "#7BC8A4": "#237D5C",
}


# ==========================================
# DARK MODE COLOR MAPPING
# ==========================================

DARK_COLORS = {
    "#15171B": "#0F1115",
    "#1D2026": "#191D24",
    "#13161B": "#11141A",
    "#111317": "#0C0F14",
    "#14171C": "#131720",
    "#191C22": "#151922",
    "#353A43": "#333B48",
}


# ==========================================
# ACCENT COLOR REPLACEMENT RULES
# ==========================================

# 0 = main accent
# 1 = deep accent
# 2 = hover accent

ACCENT_REPLACEMENTS = {
    "#4777BA": 0,
    "#6C9AE0": 0,
    "#91A9CC": 0,

    "#365F9C": 1,
    "#284E82": 1,
    "#313B4B": 1,

    "#39475C": 2,
    "#4675B5": 2,
    "#5B8BD2": 2,
}


# ==========================================
# LIGHT MODE FOREGROUND FIXES
# ==========================================

LIGHT_FOREGROUND_FIX = """
QPushButton#Primary,
QPushButton#SoundPrimary,
QPushButton#PersonalLink:hover,
QPushButton#BackButton:hover,
QPushButton#Nav:checked,
QListWidget::item:selected {
    color: #FFFFFF;
}
"""


# ==========================================
# GET EFFECTIVE APPEARANCE MODE
# ==========================================

def effective_mode(settings):
    """
    Returns:
        "black" or "white"

    If mode is "system", the function reads
    the operating system appearance through Qt.

    On Windows, this normally follows
    the Windows light/dark app appearance.
    """

    selected = settings.get(
        "appearance_mode",
        "black",
    )

    if selected == "white":
        return "white"

    if selected != "system":
        return "black"

    app = QApplication.instance()

    if app is None:
        return "black"

    try:
        scheme = (
            app.styleHints().colorScheme()
        )

        if scheme == Qt.ColorScheme.Light:
            return "white"

        if scheme == Qt.ColorScheme.Dark:
            return "black"

    except (
        AttributeError,
        RuntimeError,
    ):
        pass

    # Fallback for platforms where Qt
    # reports an unknown color scheme.

    try:
        background = (
            app.palette().window().color()
        )

        luminance = (
            0.2126 * background.redF()
            + 0.7152 * background.greenF()
            + 0.0722 * background.blueF()
        )

        if luminance >= 0.5:
            return "white"

        return "black"

    except (
        AttributeError,
        RuntimeError,
    ):
        return "black"


# ==========================================
# GET ACCENT COLOR
# ==========================================

def accent_color(settings):
    """
    Returns the current accent color
    as a hexadecimal string.
    """

    theme_name = settings.get("theme", "blue")

    if theme_name == "custom":
        custom = settings.get(
            "custom_hex",
            "#4777BA"
        )

        if (
            isinstance(custom, str)
            and re.fullmatch(
                r"#[0-9a-fA-F]{6}",
                custom
            )
        ):
            return custom.upper()

        return "#4777BA"

    return ACCENTS.get(
        theme_name,
        ACCENTS["blue"]
    )[0]


# ==========================================
# GET ACCENT SHADES
# ==========================================

def accent_shades(settings):
    """
    Return main/deep/hover shades.

    Supports both predefined color themes
    and user-defined hexadecimal colors.
    """

    if not settings.get("accent_enabled", False):
        if effective_mode(settings) == "white":
            return ("#626B76", "#525B65", "#737D88")
        return ("#787F89", "#59616D", "#939CA8")

    if settings.get("theme") != "custom":
        return ACCENTS.get(
            settings.get("theme", "blue"),
            ACCENTS["blue"]
        )

    accent = accent_color(settings)

    return (
        accent,
        _mix_rgb(
            accent,
            "#000000",
            0.26
        ),
        _mix_rgb(
            accent,
            "#FFFFFF",
            0.19
        )
    )


# ==========================================
# GET USER THEME INTENSITY
# ==========================================

def _intensity(settings):
    """
    Read the color intensity from settings.

    Valid values:
        0 to 100

    Standard value:
        60

    Returns a normalized value:
        0.0 to 1.0
    """

    try:
        return max(
            0,
            min(
                100,
                int(
                    settings.get(
                        "theme_intensity",
                        60
                    )
                )
            )
        ) / 100.0

    except (
        TypeError,
        ValueError,
        OverflowError
    ):
        return 0.6


# ==========================================
# COMPLETE THEME PALETTE
# ==========================================

def theme_palette(settings):
    """
    Returns normalized colors for widgets
    using custom QPainter drawing.

    Useful for:
        checkboxes
        audio sliders
        custom controls
        preview widgets
    """

    mode = effective_mode(settings)

    accent, deep, hover = accent_shades(settings)

    if mode == "white":
        return {
            "mode": "white",
            "accent": accent,
            "accent_deep": deep,
            "accent_hover": hover,
            "window": _tinted_surface_mappings(
                settings, "white"
            )["#15171B"],
            "card": _tinted_surface_mappings(
                settings, "white"
            )["#1D2026"],
            "surface": _tinted_surface_mappings(
                settings, "white"
            )["#282C33"],
            "text": "#202A38",
            "text_muted": "#5B697B",
            "border": _tinted_surface_mappings(
                settings,
                "white"
            )["#353A43"],
            "selection_text": "#FFFFFF",
        }

    return {
        "mode": "black",
        "accent": accent,
        "accent_deep": deep,
        "accent_hover": hover,
        "window": _tinted_surface_mappings(
            settings, "black"
        )["#15171B"],
        "card": _tinted_surface_mappings(
            settings, "black"
        )["#1D2026"],
        "surface": _tinted_surface_mappings(
            settings, "black"
        )["#282C33"],
        "text": "#E9EDF3",
        "text_muted": "#949EAD",
        "border": _tinted_surface_mappings(
            settings,
            "black"
        )["#353A43"],
        "selection_text": "#FFFFFF",
    }


# ==========================================
# FULL-WINDOW ACCENT-TINTED SURFACES
# ==========================================

# The old version recolored only blue
# selected widgets.
#
# Backgrounds, cards, list surfaces, borders,
# scrollbar grooves and neutral buttons
# remained gray.
#
# These colors appear throughout the
# original page styles.
#
# The complete semantic surface palette now
# receives the selected accent in one pass.
#
# Different tint strengths are used for:
#     window backgrounds
#     cards
#     panels
#     buttons
#     borders
#
# Foreground text colors are handled
# separately.

SURFACE_LEVELS = {

    # ======================================
    # DEEP WINDOW SURFACES
    # ======================================

    "#15171B": (0.26, 0.12),
    "#0F1115": (0.26, 0.12),
    "#111317": (0.28, 0.12),
    "#13161B": (0.25, 0.12),
    "#14171C": (0.25, 0.12),
    "#15191F": (0.24, 0.12),
    "#171B22": (0.25, 0.12),
    "#191C22": (0.25, 0.12),
    "#23272F": (0.27, 0.13),

    # ======================================
    # SIDEBAR, CARDS AND PANELS
    # ======================================

    "#1D2026": (0.34, 0.16),
    "#24272D": (0.33, 0.16),
    "#242933": (0.33, 0.16),
    "#282C33": (0.38, 0.19),
    "#292E36": (0.38, 0.19),
    "#2A303A": (0.38, 0.19),
    "#2C313A": (0.39, 0.19),
    "#30353F": (0.43, 0.22),
    "#303640": (0.43, 0.22),
    "#303742": (0.43, 0.22),
    "#343A44": (0.44, 0.22),
    "#343B46": (0.44, 0.22),
    "#343C47": (0.44, 0.22),
    "#22262D": (0.36, 0.18),

    # ======================================
    # BORDERS AND DIVIDERS
    # ======================================

    "#353A43": (0.48, 0.23),
    "#383E47": (0.48, 0.23),
    "#3A424D": (0.48, 0.23),
    "#414956": (0.49, 0.25),
    "#444D5A": (0.50, 0.25),
    "#454C57": (0.50, 0.25),
    "#627084": (0.45, 0.20),
}


# ==========================================
# COLOR BLENDING
# ==========================================

def _mix_rgb(original, accent, factor):
    """
    Blend two six-digit hexadecimal colors.

    The first color acts as the base.
    The second color acts as the tint.

    factor:
        0.0 = base color
        1.0 = selected accent color

    Returns:
        #RRGGBB

    Text colors are not modified here.
    """

    original = original.lstrip("#")
    accent = accent.lstrip("#")

    values = []

    for index in (0, 2, 4):
        base = int(
            original[index:index + 2],
            16,
        )

        tint = int(
            accent[index:index + 2],
            16,
        )

        value = round(
            base * (1.0 - factor)
            + tint * factor
        )

        values.append(value)

    return "#" + "".join(
        f"{number:02X}"
        for number in values
    )


# ==========================================
# GENERATE FULL SURFACE PALETTE
# ==========================================

def _tinted_surface_mappings(settings, mode):
    """
    Generate mappings for all surface colors.

    Each original QSS color receives:
        - dark or light base
        - selected accent
        - intensity appropriate to its role

    Unlike the old engine, neutral surfaces
    are recolored as well.
    """

    accent = accent_color(settings)

    result = {}

    for original, strengths in (
        SURFACE_LEVELS.items()
    ):
        dark_strength, light_strength = strengths

        if mode == "white":
            base = LIGHT_COLORS.get(
                original,
                "#F0F3F7",
            )

            strength = light_strength

        else:
            base = DARK_COLORS.get(
                original,
                original,
            )

            strength = dark_strength

        # Strength is multiplied by the user's
        # intensity, keeping the established
        # 60% setting visually close to the
        # previous release.

        # Accent mode recolors the ENTIRE interface, as in the original app.
        # Appearance mode retains neutral dark or white surfaces.
        if settings.get("accent_enabled", False):
            amount = min(0.90, max(0.0, _intensity(settings) / 100.0))
            strength = strength * (0.50 + amount * 1.15)
            result[original] = _mix_rgb(base, accent, strength)
        else:
            result[original] = base

    return result


# ==========================================
# CACHED COLOR MATCHING
# ==========================================

@lru_cache(maxsize=6)
def _color_pattern(color_keys):
    """
    Compile the color matcher only when
    the color vocabulary changes.

    This avoids unnecessary processing
    during theme changes.
    """

    alternatives = "|".join(
        re.escape(color)
        for color in sorted(
            color_keys,
            key=len,
            reverse=True,
        )
    )

    return re.compile(
        r"(?<![\w#])(?:"
        + alternatives
        + r")(?![\da-fA-F])",
        re.I,
    )


# ==========================================
# TRANSFORM ORIGINAL QSS
# ==========================================

def transform_stylesheet(
    source,
    settings,
    apply_accent=True,
):
    """
    Transforms an ORIGINAL QSS string
    into the selected application theme.

    Important:
        Always pass original QSS.

    Do not transform an already transformed
    stylesheet repeatedly.

    This function never changes widgets
    or window flags by itself.

    Parameters:
        source:
            Original QSS stylesheet.

        settings:
            Dictionary from load_settings().

        apply_accent:
            If False, only transform
            surfaces and font.

            Useful when accent values
            are already inserted directly
            by the calling widget.

    Returns:
        New themed QSS string.
    """

    # ======================================
    # VALIDATE SOURCE
    # ======================================

    if (
        not isinstance(source, str)
        or not source
    ):
        return source

    # ======================================
    # DETERMINE APPEARANCE MODE
    # ======================================

    mode = effective_mode(settings)

    # ======================================
    # BASE LIGHT / DARK PALETTE
    # ======================================

    if mode == "white":
        mappings = dict(LIGHT_COLORS)

    else:
        mappings = dict(DARK_COLORS)

    # ======================================
    # COLOR ALL APPLICATION SURFACES
    # ======================================

    # This is deliberately independent
    # of the apply_accent flag.
    #
    # SettingsPage may insert the accent
    # directly into its own stylesheet,
    # but it still needs tinted backgrounds.
    #
    # The palette changes:
    #     windows
    #     sidebar
    #     cards
    #     controls
    #     lists
    #     neutral buttons
    #     borders

    mappings.update(
        _tinted_surface_mappings(
            settings,
            mode,
        )
    )

    # ======================================
    # REPLACE BLUE ACCENT COLORS
    # ======================================

    if apply_accent:
        shades = accent_shades(settings)

        for original, shade_index in (
            ACCENT_REPLACEMENTS.items()
        ):
            mappings[original] = (
                shades[shade_index]
            )

    # ======================================
    # PREPARE COLOR LOOKUP
    # ======================================

    lookup = {
        key.upper(): color
        for key, color in mappings.items()
    }

    # ======================================
    # REPLACE COLORS IN ONE PASS
    # ======================================

    pattern = _color_pattern(
        tuple(sorted(lookup))
    )

    output = pattern.sub(
        lambda match:
            lookup[
                match.group(0).upper()
            ],
        source,
    )

    # ======================================
    # APPLY FONT
    # ======================================

    font_name = settings.get(
        "font_family",
        "Segoe UI",
    )

    if font_name not in FONTS:
        font_name = "Segoe UI"

    output = output.replace(
        '"Segoe UI"',
        f'"{font_name}"',
    )

    # ======================================
    # LIGHT MODE CONTRAST FIX
    # ======================================

    if (
        mode == "white"
        and apply_accent
    ):
        output += LIGHT_FOREGROUND_FIX

    return output
