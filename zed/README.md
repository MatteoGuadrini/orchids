# Orchids for Zed

A light & dark color theme for [Zed](https://zed.dev) — every hue sampled
from five living orchid species.

This is the Zed port of the
[Orchids VS Code theme](https://github.com/MatteoGuadrini/orchids/tree/main/vscode).

## Install

Search for **Orchids** in Zed's extension registry (`zed: extensions` from the
command palette) and install it, or add the theme files manually to
`~/.config/zed/themes/`.

## Themes

- **Orchids Dark**
- **Orchids Light**

## Files

- `themes/orchids.json` — Zed theme family (generated)
- `tools/convert_vscode_theme.py` — converts the VS Code theme JSON to Zed
  format. Re-run it after editing the VS Code themes:

  ```sh
  python3 zed/tools/convert_vscode_theme.py
  ```

## Publishing

See [PUBLISHING.md](PUBLISHING.md) for how to submit this extension to the
Zed extension registry.
