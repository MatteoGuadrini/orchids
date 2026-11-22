# Orchids for IntelliJ

A light & dark theme for IntelliJ-based IDEs — every hue sampled from five
living orchid species.

This is the IntelliJ port of the
[Orchids VS Code theme](https://github.com/MatteoGuadrini/orchids/tree/main/vscode).
It includes both editor color schemes and full UI themes for JetBrains' New UI
and Islands UI.

## Install the full theme plugin (recommended)

1. Download `dist/Orchids-IntelliJ-Plugin.zip`.
2. In IntelliJ IDEA (or another JetBrains IDE), open
   **Settings → Plugins**.
3. Click the gear icon and choose **Install Plugin from Disk**.
4. Select the ZIP file and restart the IDE.
5. Open **Settings → Appearance & Behavior → Appearance → Theme** and pick:
   - **Orchids Dark** / **Orchids Light** for the New UI
   - **Orchids Islands Dark** / **Orchids Islands Light** for the Islands UI
     (IntelliJ 2025.3+)

The plugin bundles the matching editor color schemes, so selecting a UI theme
also installs **Orchids Dark** or **Orchids Light** under
**Settings → Editor → Color Scheme**.

## Install editor schemes only

1. Download `themes/Orchids-Dark.icls` or `themes/Orchids-Light.icls`.
2. Open **Settings → Editor → Color Scheme**.
3. Click the gear icon and choose **Import Scheme**.
4. Select the `.icls` file.

Editor schemes cover syntax highlighting, caret/selection, line numbers,
indent guides, diff/file-status colors, breadcrumbs, search results, and
console output colors. They can be used on top of any UI theme, including the
Classic UI.

## Themes

| Theme | UI variant | Files |
| --- | --- | --- |
| Orchids Dark | New UI | `themes/Orchids-Dark.theme.json` |
| Orchids Light | New UI | `themes/Orchids-Light.theme.json` |
| Orchids Islands Dark | Islands UI | `themes/Orchids-Islands-Dark.theme.json` |
| Orchids Islands Light | Islands UI | `themes/Orchids-Islands-Light.theme.json` |
| Orchids Dark / Light editor schemes | any | `themes/Orchids-{Dark,Light}.icls` |

## Files

- `themes/Orchids-Dark.icls`, `themes/Orchids-Light.icls` — generated editor
  color schemes for manual import.
- `themes/*.theme.json` — JetBrains UI theme descriptors used by the plugin.
- `plugin/` — unpacked JetBrains theme plugin (`META-INF/plugin.xml` plus
  theme resources).
- `dist/Orchids-IntelliJ-Plugin.zip` — installable plugin archive.
- `tools/convert_vscode_theme.py` — converts the VS Code theme JSON to
  IntelliJ `.icls`, `.theme.json`, plugin, and ZIP outputs. Re-run it after
  editing the VS Code themes:

  ```sh
  python3 intellij/tools/convert_vscode_theme.py
  ```

## Notes

- `.icls` files are editor color schemes; `.theme.json` files are IntelliJ UI
  theme descriptors. Only the plugin path applies Orchids colors to menus,
  dialogs, tool windows, tabs, and other IDE chrome.
- The New UI variants inherit from JetBrains' `ExperimentalDark` /
  `ExperimentalLight` themes; the Islands variants inherit from `Islands Dark`
  / `Islands Light`. Keys not overridden fall back to those parent themes.
- On Classic UI, install the plugin for the editor schemes or import the
  `.icls` files directly; the Classic UI chrome itself is not themed here.
