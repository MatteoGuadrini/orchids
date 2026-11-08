#!/usr/bin/env python3
"""Convert the Orchids VS Code themes to a Zed theme family JSON.

This is a Python port of Zed's own `theme_importer` crate
(zed-industries/zed, crates/theme_importer), extended with a few extra
VS Code color mappings that the Rust importer does not cover.

Usage:
    python3 zed/tools/convert_vscode_theme.py

Reads  vscode/themes/orchids-{dark,light}-color-theme.json
Writes zed/themes/orchids.json
"""

import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VSCODE_THEMES = os.path.join(ROOT, "vscode", "themes")
ZED_THEMES_DIR = os.path.join(ROOT, "zed", "themes")

SCHEMA = "https://zed.dev/schema/themes/v0.2.0.json"
AUTHOR = "Matteo Guadrini"

ACCENTS = ["#A9CC7E", "#B79CF5", "#FA8FC5", "#7FD4CB", "#F2C566", "#E8B06A", "#DCA9F2"]

# UI border color per appearance. The VS Code themes use a mossy green
# (#5E7C2B) for panel.border & friends; for Zed we substitute the muted
# orchid lavender used for inactive text instead.
UI_BORDERS = {
    "dark": "#7e6f96ff",
    "light": "#8b7a99ff",
}

# Filled button / selection colors per appearance. The VS Code themes use a
# green button.background; for Zed we substitute deep orchid purple (dark) and
# pale orchid lavender (light), which keep `text` readable on top.
ELEMENT_COLORS = {
    "dark": {
        "background": "#53307aff",
        "active": "#4b3968ff",
        "selection_background": "#53307a80",
    },
    "light": {
        "background": "#e3d3f4ff",
        "active": "#e9e1eeff",
        "selection_background": "#e3d3f4b3",
    },
}

# Accent color used for `icon.accent` per appearance (replaces the green
# progressBar/button accent from the VS Code themes).
ICON_ACCENTS = {
    "dark": "#b79cf5ff",
    "light": "#5e4b70ff",
}


# ---------------------------------------------------------------------------
# Syntax capture mapping (ported from theme_importer/src/vscode/syntax.rs)
# ---------------------------------------------------------------------------

ZED_TOKENS = [
    ("attribute", ["entity.other.attribute-name"], []),
    ("boolean", ["constant.language"], []),
    ("comment", ["comment"], ["comment.doc"]),
    ("comment.doc", ["comment.block.documentation"], ["comment"]),
    ("constant", ["constant", "constant.language", "constant.character"], ["number"]),
    ("constructor", ["entity.name.tag", "entity.name.function.definition.special.constructor"], []),
    ("embedded", ["meta.embedded"], []),
    ("emphasis", ["markup.italic"], []),
    ("emphasis.strong", ["markup.bold", "markup.italic markup.bold", "markup.bold markup.italic"], ["emphasis"]),
    ("enum", ["support.type.enum"], []),
    ("function", ["entity.function", "entity.name.function", "variable.function"], []),
    ("hint", [], []),
    ("keyword", ["keyword", "keyword.other.fn.rust", "keyword.control", "keyword.control.fun",
                 "keyword.control.class", "punctuation.accessor", "entity.name.tag"], []),
    ("label", ["label", "entity.name", "entity.name.import", "entity.name.package"], []),
    ("link_text", ["markup.underline.link", "string.other.link"], []),
    ("link_uri", ["markup.underline.link", "string.other.link"], []),
    ("number", ["constant.numeric", "number"], ["constant"]),
    ("operator", ["operator", "keyword.operator"], []),
    ("predictive", [], []),
    ("preproc", ["preproc", "meta.preprocessor", "punctuation.definition.preprocessor"], []),
    ("primary", [], []),
    ("property", ["variable.member", "support.type.property-name", "variable.object.property",
                  "variable.other.field"], []),
    ("punctuation", ["punctuation", "punctuation.section", "punctuation.accessor",
                     "punctuation.separator", "punctuation.definition.tag"], []),
    ("punctuation.bracket", ["punctuation.bracket", "punctuation.definition.tag.begin",
                              "punctuation.definition.tag.end"], ["punctuation"]),
    ("punctuation.delimiter", ["punctuation.delimiter", "punctuation.separator",
                               "punctuation.terminator"], ["punctuation"]),
    ("punctuation.list_marker", ["markup.list punctuation.definition.list.begin"], ["punctuation"]),
    ("punctuation.special", ["punctuation.special"], ["punctuation"]),
    ("string", ["string"], []),
    ("string.escape", ["string.escape", "constant.character", "constant.other"], ["string"]),
    ("string.regex", ["string.regex"], ["string"]),
    ("string.special", ["string.special", "constant.other.symbol"], ["string"]),
    ("string.special.symbol", ["string.special.symbol", "constant.other.symbol"], ["string"]),
    ("tag", ["tag", "entity.name.tag", "meta.tag.sgml"], []),
    ("text.literal", ["text.literal", "string"], []),
    ("title", ["title", "entity.name"], []),
    ("type", ["entity.name.type", "entity.name.type.primitive", "entity.name.type.numeric",
              "keyword.type", "support.type", "support.type.primitive", "support.class"], []),
    ("variable", ["variable", "variable.language", "variable.member", "variable.parameter",
                  "variable.parameter.function-call"], []),
    ("variable.parameter", ["variable.parameter", "variable.parameter.function-call"], ["variable"]),
    ("variable.special", ["variable.special", "variable.member", "variable.annotation",
                          "variable.language"], ["variable"]),
    ("variant", ["variant"], []),
]

# map zed token name -> index for fallback resolution
TOKEN_INDEX = {name: i for i, (name, _, _) in enumerate(ZED_TOKENS)}


def token_candidate_scopes(token_color):
    scope = token_color.get("scope")
    if scope is None:
        return []
    if isinstance(scope, str):
        scope = [scope]
    out = []
    for s in scope:
        out.extend(part.strip() for part in s.split(","))
    return out


def rank_match(zed_scopes, candidate_scopes):
    matches = 0
    n = len(zed_scopes)
    for ix, scope in enumerate(zed_scopes):
        weight = n - ix
        if scope in candidate_scopes:
            matches += 1 + weight
    return matches


def find_best_token_color(zed_name, token_colors):
    _, scopes, _ = ZED_TOKENS[TOKEN_INDEX[zed_name]]
    best_ix, best_rank = None, 0
    for ix, tc in enumerate(token_colors):
        settings = tc.get("settings", {})
        if not settings.get("foreground"):
            continue
        rank = rank_match(scopes, token_candidate_scopes(tc))
        if rank > best_rank:  # last max wins, like Rust max_by_key
            best_ix, best_rank = ix, rank
    if best_ix is not None:
        return token_colors[best_ix]
    # fallbacks
    for fb_name in ZED_TOKENS[TOKEN_INDEX[zed_name]][2]:
        tc = find_best_token_color(fb_name, token_colors)
        if tc is not None:
            return tc
    return None


def parse_font_style(font_style):
    """Return (font_style, font_weight) like the Rust importer."""
    if not font_style:
        return None, None
    fs, fw = None, None
    if "italic" in font_style:
        fs = "italic"
    elif "oblique" in font_style:
        fs = "oblique"
    if "bold" in font_style:
        fw = 700
    return fs, fw


def convert_syntax(token_colors):
    syntax = {}
    for name, _, _ in ZED_TOKENS:
        tc = find_best_token_color(name, token_colors)
        if tc is None:
            continue
        settings = tc.get("settings", {})
        fs, fw = parse_font_style(settings.get("fontStyle"))
        style = {}
        if settings.get("foreground"):
            style["color"] = normalize_color(settings["foreground"])
        if settings.get("background"):
            style["background_color"] = normalize_color(settings["background"])
        if fs:
            style["font_style"] = fs
        if fw:
            style["font_weight"] = fw
        if style:
            syntax[name] = style
    return syntax


# ---------------------------------------------------------------------------
# UI colors
# ---------------------------------------------------------------------------

def normalize_color(color):
    """Normalize a VS Code color to #RRGGBBAA for Zed."""
    if not color:
        return None
    c = color.strip()
    if re.fullmatch(r"#[0-9a-fA-F]{3}", c):
        c = "#" + "".join(ch * 2 for ch in c[1:])
    if re.fullmatch(r"#[0-9a-fA-F]{6}", c):
        c = c + "ff"
    if re.fullmatch(r"#[0-9a-fA-F]{8}", c):
        return c.lower()
    return color  # e.g. named colors; let Zed deal with it


def first(colors, *keys):
    for k in keys:
        v = colors.get(k)
        if v:
            return normalize_color(v)
    return None


def convert_colors(vscode, appearance):
    c = vscode.get("colors", {})
    token_colors = vscode.get("tokenColors", [])
    ui_border = UI_BORDERS[appearance]

    global_fg = first(c, "foreground")
    if not global_fg:
        for tc in token_colors:
            if tc.get("scope") is None and tc.get("settings", {}).get("foreground"):
                global_fg = normalize_color(tc["settings"]["foreground"])
                break
    if not global_fg:
        global_fg = first(c, "editor.foreground")

    tab_inactive_bg = first(c, "tab.inactiveBackground")

    style = {}

    def put(key, value):
        if value:
            style[key] = value

    # --- status colors (git / diagnostics) ---
    put("conflict", first(c, "gitDecoration.conflictingResourceForeground",
                         "gitDecoration.conflictedResourceForeground"))
    put("created", first(c, "editorGutter.addedBackground",
                         "gitDecoration.addedResourceForeground",
                         "gitDecoration.untrackedResourceForeground"))
    put("deleted", first(c, "editorGutter.deletedBackground",
                         "gitDecoration.deletedResourceForeground"))
    put("modified", first(c, "editorGutter.modifiedBackground",
                          "gitDecoration.modifiedResourceForeground"))
    put("ignored", first(c, "gitDecoration.ignoredResourceForeground"))
    put("error", first(c, "editorError.foreground", "errorForeground"))
    put("warning", first(c, "editorWarning.foreground", "warningForeground"))
    put("info", first(c, "editorInfo.foreground", "infoForeground"))
    put("success", first(c, "editorGutter.addedBackground",
                         "terminal.ansiGreen", "charts.green"))
    put("hidden", first(c, "tab.inactiveForeground"))
    put("hint", first(c, "editorInlayHint.foreground"))
    put("unreachable", first(c, "editorError.foreground", "errorForeground"))

    # Status background/border variants. Zed's tinted buttons and git
    # decorations use these; leaving them unset falls back to Zed's default
    # blue-ish status colors. Derive them from each status color at low alpha,
    # matching the convention used by Zed's own themes.
    for status in ("conflict", "created", "deleted", "error", "hidden", "hint",
                   "ignored", "info", "modified", "success", "unreachable",
                   "warning"):
        fg = style.get(status)
        if not fg:
            continue
        put(f"{status}.background", fg[:7] + "1a")
        put(f"{status}.border", fg)

    # --- general chrome ---
    put("background", first(c, "editor.background"))
    style["background.appearance"] = "opaque"
    for k in ("border", "border.variant", "border.selected", "border.transparent", "border.disabled"):
        put(k, ui_border)
    put("border.focused", first(c, "focusBorder", "editorCursor.foreground",
                                "inputOption.activeBorder", "tab.activeBorder"))
    put("elevated_surface.background", first(c, "dropdown.background", "quickInput.background"))
    put("surface.background", first(c, "panel.background", "sideBar.background"))
    put("panel.background", first(c, "panel.background", "sideBar.background"))
    put("status_bar.background", first(c, "statusBar.background"))
    put("title_bar.background", first(c, "titleBar.activeBackground"))
    put("title_bar.inactive_background", first(c, "titleBar.inactiveBackground"))
    put("toolbar.background", first(c, "breadcrumb.background", "editor.background"))
    put("tab_bar.background", first(c, "editorGroupHeader.tabsBackground"))
    put("tab.active_background", first(c, "tab.activeBackground") or tab_inactive_bg)
    put("tab.inactive_background", tab_inactive_bg)
    put("pane.focused_border", ui_border)
    put("panel.focused_border", ui_border)
    put("search.match_background", first(c, "editor.findMatchBackground",
                                         "editor.findMatchHighlightBackground"))
    put("drop_target.background", first(c, "list.dropBackground",
                                        "list.activeSelectionBackground"))

    # --- elements / text ---
    element = ELEMENT_COLORS[appearance]
    put("element.background", element["background"])
    put("element.active", element["active"])
    put("element.selection_background", element["selection_background"])
    put("element.hover", first(c, "list.hoverBackground", "button.hoverBackground"))
    put("element.selected", first(c, "list.activeSelectionBackground",
                                  "list.focusBackground", "inputOption.activeBackground"))
    put("element.disabled", first(c, "input.disabledBackground", "editorGroupHeader.tabsBackground"))
    put("ghost_element.hover", first(c, "list.hoverBackground"))
    put("ghost_element.selected", first(c, "list.activeSelectionBackground", "list.focusBackground"))
    put("text", global_fg)
    put("text.muted", first(c, "tab.inactiveForeground", "breadcrumb.foreground",
                            "descriptionForeground"))
    put("text.disabled", first(c, "input.disabledForeground", "tab.inactiveForeground"))
    put("text.placeholder", first(c, "input.placeholderForeground", "tab.inactiveForeground"))
    put("text.accent", first(c, "textLink.foreground", "button.foreground", "editorCursor.foreground"))
    put("link_text.hover", first(c, "textLink.activeForeground", "textLink.foreground"))
    put("icon", first(c, "foreground", "editor.foreground"))
    put("icon.accent", ICON_ACCENTS[appearance])
    put("icon.muted", first(c, "descriptionForeground", "tab.inactiveForeground"))
    put("icon.disabled", first(c, "input.disabledForeground"))
    put("icon.placeholder", first(c, "input.placeholderForeground"))

    # --- editor ---
    put("editor.background", first(c, "editor.background"))
    put("editor.foreground", first(c, "editor.foreground") or global_fg)
    put("editor.gutter.background", first(c, "editor.background", "editorGroup.background"))
    put("editor.line_number", first(c, "editorLineNumber.foreground"))
    put("editor.active_line_number", first(c, "editorLineNumber.activeForeground",
                                           "editor.foreground"))
    put("editor.hover_line_number", first(c, "editorLineNumber.activeForeground",
                                          "editor.foreground"))
    put("editor.active_line.background", first(c, "editor.lineHighlightBackground"))
    put("editor.highlighted_line.background", first(c, "editor.lineHighlightBackground",
                                                    "editor.selectionBackground"))
    put("editor.invisible", first(c, "editorWhitespace.foreground"))
    put("editor.wrap_guide", first(c, "editorIndentGuide.background", "panel.border"))
    put("editor.active_wrap_guide", first(c, "editorIndentGuide.activeBackground", "panel.border"))
    put("editor.indent_guide", first(c, "editorIndentGuide.background", "panel.border"))
    put("editor.indent_guide_active", first(c, "editorIndentGuide.activeBackground",
                                            "panel.border"))
    put("editor.document_highlight.bracket_background",
        first(c, "editorBracketMatch.background", "editor.lineHighlightBackground"))
    put("editor.document_highlight.read_background",
        first(c, "editor.wordHighlightBackground", "editor.lineHighlightBackground"))
    put("editor.document_highlight.write_background",
        first(c, "editor.wordHighlightStrongBackground", "editor.lineHighlightBackground"))
    put("editor.subheader.background", first(c, "panelSectionHeader.background",
                                             "sideBarSectionHeader.background"))

    # --- scrollbars ---
    put("scrollbar.thumb.background", first(c, "scrollbarSlider.background"))
    put("scrollbar.thumb.hover_background", first(c, "scrollbarSlider.hoverBackground"))
    put("scrollbar.thumb.border", first(c, "scrollbarSlider.background"))
    put("scrollbar.track.background", first(c, "editor.background"))
    put("scrollbar.track.border", ui_border)

    # --- terminal ---
    put("terminal.background", first(c, "terminal.background", "editor.background"))
    put("terminal.foreground", first(c, "terminal.foreground", "editor.foreground"))
    put("terminal.bright_foreground", first(c, "terminal.ansiBrightWhite"))
    put("terminal.dim_foreground", first(c, "terminal.ansiBrightBlack"))
    ansi_map = {
        "black": "terminal.ansiBlack", "red": "terminal.ansiRed",
        "green": "terminal.ansiGreen", "yellow": "terminal.ansiYellow",
        "blue": "terminal.ansiBlue", "magenta": "terminal.ansiMagenta",
        "cyan": "terminal.ansiCyan", "white": "terminal.ansiWhite",
        "bright_black": "terminal.ansiBrightBlack", "bright_red": "terminal.ansiBrightRed",
        "bright_green": "terminal.ansiBrightGreen", "bright_yellow": "terminal.ansiBrightYellow",
        "bright_blue": "terminal.ansiBrightBlue", "bright_magenta": "terminal.ansiBrightMagenta",
        "bright_cyan": "terminal.ansiBrightCyan", "bright_white": "terminal.ansiBrightWhite",
    }
    for zed_key, vscode_key in ansi_map.items():
        put(f"terminal.ansi.{zed_key}", first(c, vscode_key))

    # --- predictive / suggestions ---
    put("predictive", first(c, "editorSuggestWidget.foreground"))
    put("predictive.background", first(c, "editorSuggestWidget.background"))
    put("predictive.border", ui_border)

    return style


# ---------------------------------------------------------------------------

def convert_theme(vscode_path, name, appearance):
    with open(vscode_path) as f:
        vscode = json.load(f)

    style = convert_colors(vscode, appearance)
    style["syntax"] = convert_syntax(vscode.get("tokenColors", []))

    # players derived from accent colors
    players = []
    for accent in ACCENTS:
        players.append({
            "cursor": normalize_color(accent),
            "background": normalize_color(accent),
            "selection": normalize_color(accent)[:7] + "3d",
        })
    style["players"] = players

    return {
        "name": name,
        "appearance": appearance,
        "style": style,
    }


def main():
    os.makedirs(ZED_THEMES_DIR, exist_ok=True)

    family = {
        "$schema": SCHEMA,
        "name": "Orchids",
        "author": AUTHOR,
        "themes": [
            convert_theme(os.path.join(VSCODE_THEMES, "orchids-dark-color-theme.json"),
                          "Orchids Dark", "dark"),
            convert_theme(os.path.join(VSCODE_THEMES, "orchids-light-color-theme.json"),
                          "Orchids Light", "light"),
        ],
    }

    out = os.path.join(ZED_THEMES_DIR, "orchids.json")
    with open(out, "w") as f:
        json.dump(family, f, indent=2)
        f.write("\n")

    for t in family["themes"]:
        print(f"{t['name']}: {len(t['style']) - 2} style keys, "
              f"{len(t['style']['syntax'])} syntax captures")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
