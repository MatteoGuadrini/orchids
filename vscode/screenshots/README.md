# Screenshots

This folder should contain screenshots for the VS Code Marketplace listing.

## Required Screenshots

- `dark.png` - Screenshot of Orchids Dark theme (recommended: 1280x800px)
- `light.png` - Screenshot of Orchids Light theme (recommended: 1280x800px)

## How to Create Screenshots

### Method 1: VS Code Built-in Screenshot

1. Open VS Code with the Orchids theme activated
2. Open a code file with good syntax examples
3. Open the Command Palette (Ctrl+Shift+P or Cmd+Shift+P)
4. Type "Developer: Take Screenshot"
5. Save the screenshot to this folder

### Method 2: System Screenshot Tool

1. Activate the Orchids theme in VS Code
2. Open a code file
3. Use your system's screenshot tool:
   - **Windows**: Win+Shift+S (Snipping Tool)
   - **macOS**: Cmd+Shift+4
   - **Linux**: Usually Print Screen or use gnome-screenshot
4. Save to this folder

### Method 3: Using Terminal (Linux)

```bash
# Using gnome-screenshot
gnome-screenshot -a -f screenshots/dark.png

# Using import (ImageMagick)
import screenshots/dark.png
```

## Screenshot Guidelines

- **Size**: 1280x800px or similar (minimum 960x600px)
- **Format**: PNG
- **Content**: Show code with good syntax highlighting examples
- **Window**: Include the editor window with sidebar/status bar visible
- **Dark Mode**: Use a dark background for the Orchids Dark screenshot
- **Light Mode**: Use a light background for the Orchids Light screenshot

## What to Show

Consider showing:
- A code file with various syntax elements (functions, classes, strings, comments)
- File explorer in the sidebar
- Status bar at the bottom
- Good contrast and readability

## After Creating Screenshots

Once you have the screenshots:
1. Verify they're in PNG format
2. Check the dimensions
3. Update `package.json` gallery section if needed
4. The extension is ready for publishing

## Example Code for Screenshots

You can use this sample code for your screenshots:

```javascript
// Orchids Theme Sample
const orchids = {
  species: ['Phalaenopsis', 'Vanda', 'Cattleya', 'Paphiopedilum', 'Oncidium'],
  colors: {
    pink: '#FA8FC5',
    purple: '#B79CF5',
    green: '#A9CC7E',
    gold: '#F2C566'
  },
  
  getTheme() {
    return {
      background: '#1A1322',
      foreground: '#EFE7F6'
    };
  },
  
  *getSpecies() {
    for (const species of this.species) {
      yield species;
    }
  }
};

async function displayOrchids() {
  const theme = orchids.getTheme();
  console.log(theme);
  
  for (const species of orchids.getSpecies()) {
    console.log(species);
  }
}

class OrchidGarden {
  constructor(name) {
    this.name = name;
    this.plants = [];
  }
  
  addPlant(plant) {
    this.plants.push(plant);
  }
  
  getPlantCount() {
    return this.plants.length;
  }
}

// Export
export { orchids, displayOrchids, OrchidGarden };
```
