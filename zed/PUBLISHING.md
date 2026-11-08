# Publishing the Orchids theme to Zed

Zed extensions are published by opening a pull request against the
[`zed-industries/extensions`](https://github.com/zed-industries/extensions)
repository. There is no CLI publish command — the registry is built from git
submodules.

## Prerequisites

1. **Public GitHub repository** containing this `zed/` directory (this repo:
   <https://github.com/MatteoGuadrini/orchids>).
2. **`extension.toml`** at `zed/extension.toml` with `id`, `name`, `version`,
   `schema_version`, `authors`, and `repository` filled in.
3. **Theme files** in `zed/themes/*.json` conforming to
   <https://zed.dev/schema/themes/v0.2.0.json>.

## Publishing steps

### 1. Commit and push

```sh
git add zed
git commit -m "Add Zed theme extension"
git push
```

Note the commit SHA — the registry pins a specific commit of your repo.

### 2. Fork and clone the extensions registry

```sh
git clone https://github.com/zed-industries/extensions.git
cd extensions
```

(Or fork it on GitHub and clone your fork.)

### 3. Add this repo as a submodule

Because the extension lives in the `zed/` subdirectory of this repository,
add the submodule and use the `path` field:

```sh
git submodule add https://github.com/MatteoGuadrini/orchids.git extensions/orchids
git add extensions/orchids
```

Then check out the commit you want to publish inside the submodule:

```sh
cd extensions/orchids
git checkout <commit-sha>
cd ../..
```

### 4. Register the extension

Add an entry to the top-level `extensions.toml` (keep it sorted):

```toml
[orchids]
submodule = "extensions/orchids"
path = "zed"
version = "0.1.0"
```

The `version` **must** match `version` in `zed/extension.toml` at the pinned
commit.

### 5. Sort and open a PR

```sh
pnpm install
pnpm sort-extensions
git add extensions.toml .gitmodules
git commit -m "Add orchids theme extension"
git push origin <your-branch>
```

Then open a pull request against `zed-industries/extensions`.

## PR rules

- Each PR must add or update exactly one extension.
- At most three open PRs at a time.
- Respond to maintainer feedback within 3 weeks.

## Updating the theme

1. Edit `vscode/themes/*.json` (or `zed/themes/orchids.json` directly).
2. If you edited the VS Code themes, regenerate:

   ```sh
   python3 zed/tools/convert_vscode_theme.py
   ```

3. Bump `version` in both `zed/extension.toml` and `vscode/package.json` if needed.
4. Commit, push, then update the submodule pointer and `version` in
   `extensions.toml` in a new PR to the registry.

## Local preview

Copy the theme file into Zed's user themes directory to try it before
publishing:

```sh
mkdir -p ~/.config/zed/themes
cp zed/themes/orchids.json ~/.config/zed/themes/
```

Then pick **Orchids Dark** or **Orchids Light** via `theme selector: toggle`.
