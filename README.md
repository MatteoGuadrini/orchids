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

## License

MIT — see [`vscode/LICENSE`](vscode/LICENSE).
