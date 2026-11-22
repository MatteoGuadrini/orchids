# Orchids

A light & dark code color theme for **VS Code**, **Zed**, and
**IntelliJ-based IDEs** — every hue sampled from five living orchid species.

![Orchids](https://img.shields.io/badge/Orchids-light%20%26%20dark-pink?style=for-the-badge)

## The palette

Orchids is a meticulously crafted color theme drawn from the natural beauty
of five orchid species:

- **Phalaenopsis** — delicate pinks and magentas
- **Vanda** — rich purples and violets
- **Cattleya** — vibrant fuchsias
- **Paphiopedilum** — earthy greens and browns
- **Oncidium** — golden yellows and oranges

Each color in the theme is sampled from these flowers, creating a harmonious,
natural coding environment that's easy on the eyes during long sessions.

## Themes

Two variants in each editor:

- **Orchids Dark**
- **Orchids Light**

## Repository layout

```
.
├── index.html            # Showcase site: palette, previews, and theme downloads
├── vscode/               # VS Code extension (themes, icons, screenshots)
│   └── themes/           # orchids-{dark,light}-color-theme.json
├── zed/                  # Zed extension
│   ├── themes/orchids.json   # Generated Zed theme family
│   └── tools/                # VS Code → Zed theme converter
└── intellij/             # IntelliJ themes
    ├── themes/           # .icls editor schemes + .theme.json UI descriptors
    ├── plugin/           # Generated JetBrains theme plugin package
    ├── dist/             # Installable plugin ZIP
    └── tools/            # VS Code → IntelliJ theme converter
```

## Installation

Each editor folder ships its own installable theme. Pick yours:

### VS Code — `vscode/`

1. Open VS Code and go to **Extensions** (`Ctrl+Shift+X`).
2. Search for **Orchids** and click **Install** — or download a release
   `.vsix` and use **Install from VSIX...**.
3. Open the Command Palette (`Ctrl+Shift+P`) → **Preferences: Color Theme**
   and choose **Orchids Dark** or **Orchids Light**.

Manual alternative: copy `vscode/themes/orchids-{dark,light}-color-theme.json`
into your VS Code user themes directory and select the theme as above.
Full details: [`vscode/README.md`](vscode/README.md).

### Zed — `zed/`

1. Open the command palette and run `zed: extensions`.
2. Search for **Orchids** and install it — or copy
   `zed/themes/orchids.json` into `~/.config/zed/themes/`.
3. Pick **Orchids Dark** or **Orchids Light** from the theme selector.

Full details: [`zed/README.md`](zed/README.md).

### IntelliJ-based IDEs — `intellij/`

1. Build the plugin archive if needed:

   ```sh
   python3 intellij/tools/convert_vscode_theme.py
   ```

   This produces `intellij/dist/Orchids-IntelliJ-Plugin.zip`.
2. In IntelliJ IDEA (or another JetBrains IDE), open
   **Settings → Plugins**, click the gear icon, and choose
   **Install Plugin from Disk**. Select the ZIP and restart the IDE.
3. Open **Settings → Appearance & Behavior → Appearance → Theme** and pick
   **Orchids Dark** / **Orchids Light** (New UI) or **Orchids Islands
   Dark** / **Orchids Islands Light** (Islands UI).

Editor schemes only: import `intellij/themes/Orchids-{Dark,Light}.icls` via
**Settings → Editor → Color Scheme → ⚙ → Import Scheme**. Full details:
[`intellij/README.md`](intellij/README.md).

## VS Code

See [`vscode/README.md`](vscode/README.md) for installation, customization,
and publishing instructions. The VS Code themes are the source of truth —
edit them first.

## Zed

See [`zed/README.md`](zed/README.md). The Zed theme is generated from the
VS Code themes. After editing `vscode/themes/`, regenerate it with:

```sh
python3 zed/tools/convert_vscode_theme.py
```

See [`zed/PUBLISHING.md`](zed/PUBLISHING.md) for how to submit the extension
to the Zed registry.

## IntelliJ

See [`intellij/README.md`](intellij/README.md). The IntelliJ port includes
generated editor color schemes (`.icls`) plus full UI theme descriptors
(`.theme.json`) for JetBrains' New UI and Islands UI, packaged as an
installable plugin in `intellij/dist/`. After editing `vscode/themes/`,
regenerate everything with:

```sh
python3 intellij/tools/convert_vscode_theme.py
```

## Showcase site

`index.html` is a self-contained page (no build step) that presents the
theme: the species behind each color, syntax previews, and ready-to-download
theme files for VS Code, Zed, IntelliJ, iTerm2, Alacritty, Ghostty, Kitty,
and Windows Terminal — all generated client-side from the color tokens
embedded in the page. Open it directly in a browser.

## Open source
_Orchids_ is an open source project. Any contribute, It's welcome.

**A great thanks**.

For donations, press this

For me

[![paypal](https://www.paypalobjects.com/en_US/i/btn/btn_donateCC_LG.gif)](https://www.paypal.me/guos)

For [Telethon](http://www.telethon.it/)

The Telethon Foundation is a non-profit organization recognized by the Ministry of University and Scientific and Technological Research.
They were born in 1990 to respond to the appeal of patients suffering from rare diseases.
Come today, we are organized to dare to listen to them and answers, every day of the year.

[Adopt the future](https://www.ioadottoilfuturo.it/)