# Icon Files

This folder contains the icon files for the VS Code extension.

## Required Files

The VS Code marketplace requires the following icon files:

- `icon.png` - 128x128 pixel PNG file (main extension icon)
- `icon.svg` - SVG version (for documentation and other uses)

## Current Status

- ✅ `icon.svg` - Created (orchid flower design)
- ⏳ `icon.png` - Needs to be generated from the SVG

## How to Generate icon.png

You can convert the SVG to PNG using one of these methods:

### Method 1: Using ImageMagick
```bash
cd icons
convert icon.svg -resize 128x128 icon.png
```

### Method 2: Using Node.js with sharp
```bash
npm install sharp
node -e "const sharp = require('sharp'); sharp('icon.svg').resize(128, 128).png().toFile('icon.png')"
```

### Method 3: Online Tool
1. Open [SVG to PNG converter](https://cloudconvert.com/svg-to-png)
2. Upload `icon.svg`
3. Set size to 128x128
4. Download as `icon.png`

### Method 4: Using Inkscape
```bash
inkscape icon.svg --export-type=png --export-filename=icon.png --export-width=128 --export-height=128
```

## Icon Design

The icon features:
- A stylized **Phalaenopsis amabilis** (Moon Orchid) - the same design from the website
- Characteristic petals in pink and magenta gradients
- Distinctive lip/labellum with golden center
- Green stem
- Colors matching the theme palette:
  - Petals: Gradients from #FFC1DD to #FA8FC5 (light pink to pink)
  - Center lip: Gradient from #FA8FC5 to #B0256B (pink to magenta)
  - Lip center: Gradient from #F5C566 to #F2C566 (gold)
  - Stem: Gradient from #5E7C2B to #A9CC7E (green)
- Dark background: #1A1322 (from Orchids Dark theme)
- Rounded corners for a modern look

## After Creating icon.png

Once you have generated the `icon.png` file, make sure:
1. It's exactly 128x128 pixels
2. It's in PNG format
3. It's located in this `icons/` folder
4. The `package.json` references it correctly

The extension is now ready for packaging and publishing to the VS Code marketplace.
