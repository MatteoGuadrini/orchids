# Publishing Guide

This guide will help you publish the Orchids theme to the VS Code Marketplace.

## Prerequisites

1. **VS Code Account**: Create an account at [Visual Studio Marketplace](https://marketplace.visualstudio.com/vscode)
2. **Personal Access Token (PAT)**:
   - Go to [Azure DevOps](https://dev.azure.com/)
   - Sign in with your VS Code account
   - Navigate to User Settings → Personal Access Tokens
   - Create a new token with "Marketplace" scope
   - Save the token securely

3. **Node.js**: Ensure Node.js is installed (already available)

4. **vsce (VS Code Extension Manager)**:
   ```bash
   npm install -g @vscode/vsce
   ```

## Before Publishing

### 1. Update package.json

Edit `package.json` and update the following fields:

```json
{
  "publisher": "your-publisher-name",  // Your VS Code publisher name
  "repository": {
    "type": "git",
    "url": "https://github.com/your-username/orchids-vscode"
  },
  "bugs": {
    "url": "https://github.com/your-username/orchids-vscode/issues"
  },
  "homepage": "https://github.com/your-username/orchids-vscode#readme"
}
```

### 2. Create Screenshots

Create screenshots in the `screenshots/` folder:

```bash
mkdir -p screenshots
```

**For Orchids Dark:**
1. Open VS Code with Orchids Dark theme
2. Open a code file
3. Take a screenshot (or use VS Code's built-in screenshot feature)
4. Save as `screenshots/dark.png` (recommended size: 1280x800 or similar)

**For Orchids Light:**
1. Open VS Code with Orchids Light theme
2. Open a code file
3. Take a screenshot
4. Save as `screenshots/light.png`

### 3. Verify Icon

Ensure `icons/icon.png` exists and is 128x128 pixels:
```bash
cd icons
file icon.png
# Should show: icon.png: PNG image data, 128 x 128
```

### 4. Create GitHub Repository

1. Create a new repository on GitHub: `orchids-vscode`
2. Initialize git in the vscode folder:
   ```bash
   cd /home/gu/Documents/Projects/orchids/vscode
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/your-username/orchids-vscode.git
   git push -u origin main
   ```

## Publishing Steps

### Step 1: Login to vsce

```bash
cd /home/gu/Documents/Projects/orchids/vscode
vsce login your-publisher-name
```

You'll be prompted to enter your Personal Access Token.

### Step 2: Package the Extension

```bash
vsce package
```

This will create a `.vsix` file (e.g., `orchids-theme-1.0.0.vsix`).

### Step 3: Test Locally (Optional)

Before publishing, test the extension locally:

```bash
code --install-extension orchids-theme-1.0.0.vsix
```

Then activate the theme in VS Code to verify everything works.

### Step 4: Publish to Marketplace

```bash
vsce publish
```

The extension will be published to the VS Code Marketplace. It may take a few minutes to appear.

### Step 5: Verify

1. Go to [Visual Studio Marketplace](https://marketplace.visualstudio.com/vscode)
2. Search for "Orchids"
3. Verify your extension appears with correct screenshots and description

## Updating the Extension

### Make Changes

Edit the theme files or add new features.

### Update Version

Increment the version in `package.json`:

```json
{
  "version": "1.0.1"
}
```

### Update Changelog

Add an entry to `CHANGELOG.md`:

```markdown
## [1.0.1] - 2024-01-XX

### Fixed
- Fixed color contrast for strings in dark theme
```

### Commit and Push

```bash
git add .
git commit -m "Version 1.0.1"
git push
```

### Publish

```bash
vsce publish
```

## Troubleshooting

### "Publisher not found"

Ensure you've created a publisher name in your VS Code Marketplace account settings.

### "Invalid token"

Generate a new Personal Access Token and try logging in again.

### "File not found"

Check that all referenced files exist:
- `icons/icon.png`
- `themes/orchids-dark-color-theme.json`
- `themes/orchids-light-color-theme.json`
- Screenshots (if referenced in package.json)

### "Version already exists"

Increment the version number in `package.json` before publishing again.

## Tips

- **Version Numbers**: Follow semantic versioning (MAJOR.MINOR.PATCH)
- **Screenshots**: Use high-quality screenshots showing various languages
- **Description**: Keep the description clear and concise
- **Keywords**: Use relevant keywords to help users find your theme
- **Categories**: Use "Themes" as the category
- **License**: Include a LICENSE file (MIT is recommended for themes)

## Additional Resources

- [VS Code Extension API](https://code.visualstudio.com/api)
- [vsce Documentation](https://github.com/microsoft/vscode-vsce)
- [Marketplace Publishing](https://code.visualstudio.com/api/working-with-extensions/publishing-extension)
- [Theme Color Reference](https://code.visualstudio.com/api/references/theme-color)

## Support

If you encounter issues during publishing:
1. Check the [vsce GitHub issues](https://github.com/microsoft/vscode-vsce/issues)
2. Review the [VS Code documentation](https://code.visualstudio.com/docs)
3. Ask for help in the [VS Code Discord](https://discord.gg/VSCode)
