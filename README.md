# Signal Viewer

A GUI for working with (biological) signal data.

## Download a prebuilt app

Prebuilt packages for Windows and macOS are attached to each release on the
[Releases page](https://github.com/fred-kr/signal-viewer/releases/latest). They contain everything the app needs;
no Python or uv installation is required.

| File | Platform |
|---|---|
| `SignalViewer-<version>-windows-x64.zip` | Windows 10/11, 64-bit |
| `SignalViewer-<version>-macos-arm64.zip` | macOS 12 or later on Apple Silicon (M1 and newer) |
| `SignalViewer-<version>-macos-x86_64.zip` | macOS 12 or later on Intel |

The packages are not code-signed. Both operating systems warn about this the first time you open the app.

**Windows**: extract the ZIP to a folder of your choice and double-click `SignalViewer.exe` inside the
`SignalViewer` folder. Keep the whole folder together; the executable needs the files next to it. When SmartScreen
shows "Windows protected your PC", click *More info*, then *Run anyway*.

**macOS**: extract the ZIP and move `SignalViewer.app` to your Applications folder. On first launch macOS reports
that the app "cannot be opened because the developer cannot be verified" or that it "is damaged". Open
*System Settings > Privacy & Security*, scroll to the Security section and click *Open Anyway*, then confirm. This
is needed once per download. Alternatively, remove the quarantine flag from a terminal:

```sh
xattr -dr com.apple.quarantine /Applications/SignalViewer.app
```

## Run from source

Download [the source ZIP](https://github.com/fred-kr/signal-viewer/archive/refs/heads/master.zip) and extract it
to a folder of your choice. Running from source requires [uv](https://docs.astral.sh/uv/getting-started/installation/).

**Windows**: double-click `run_sv_windows.cmd` inside the extracted `signal-viewer-master` folder and accept the
warning that pops up. The script installs uv if it is missing, installs the dependencies (a few minutes on the
first run) and starts the app. If nothing happens, open a command prompt in that folder and run `uv run sv`.

**macOS/Linux**: install uv following the instructions linked above, close the terminal, then open a new terminal
in the extracted folder and run:

```sh
uv run sv
```

## Command line flags

| Flag | Effect |
|---|---|
| `--debug` | Verbose logging to the terminal and to `debug.log` in the per-user app data folder (Windows: `%LOCALAPPDATA%\QuackTech\SignalViewer - Debug`, macOS: `~/Library/Application Support/QuackTech/SignalViewer - Debug`). |
| `--no-opengl` | Disable OpenGL rendering of plots. Try this if plots stay blank. |
| `--reset-settings` | Delete stored settings and start with defaults. |
| `--version` | Print the version and exit. |
| `--self-test` | Build the whole GUI off-screen and exit. Used to smoke-test packaged builds. |

## Build the packaged app yourself

Requires the `dev` dependency group (`uv sync --group dev`). From the repo root:

```sh
uv run pyinstaller packaging/signal_viewer.spec --noconfirm --clean
```

The result is `dist/SignalViewer/` (and `dist/SignalViewer.app` on macOS). The build definition lives in
[packaging/signal_viewer.spec](packaging/signal_viewer.spec); the platform icons in `packaging/icons/` are
generated from `signal_viewer/icons/app_icon.png` by `packaging/make_icons.py`.

Release builds run in GitHub Actions ([.github/workflows/build.yml](.github/workflows/build.yml)) on every tag
that starts with `v`, and can be started manually from the Actions tab. Each job builds, runs the packaged
executable with `--self-test`, and uploads a ZIP; a tag build also attaches the ZIPs to the GitHub release.
