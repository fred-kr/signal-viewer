# Getting started

Download [Signal Viewer](https://github.com/fred-kr/signal-viewer/archive/refs/heads/master.zip) and extract the ZIP archive to a folder of your choice.

Running *Signal Viewer* requires *uv* to be installed on your system.

## Installation

**Windows**:
If you are on a windows machine, you can run the `run_sv_windows.cmd` file located inside the downloaded `signal-viewer-master` folder by double-clicking it and accepting the warning that pops up.

The script will first download *uv*, and then use *uv* to install the dependencies required for *Signal Viewer*. This might take a few minutes when running for the first time.

Once everything is installed, the Signal Viewer application should open automatically.

Running the script with *uv* already installed skips the installation and immediately opens *Signal Viewer*.

**macOS/Linux**:
If you are on a macOS/Linux machine, you will need to download *uv* yourself by following the instructions on their website: [Install *uv*](https://docs.astral.sh/uv/getting-started/installation/)

Wait until the installation has finished, then close the terminal window and go to the next step.

## Run Signal Viewer

**Windows**:
On windows, just double-click the `run_sv_windows.cmd` file inside the downloaded folder, and the app should start after a few seconds.

If it doesn't, open a command prompt (Press `Windows key + R`, then type `cmd` and hit enter), then navigate to the downloaded `signal-viewer-master` folder by typing `cd C:\path\to\signal-viewer-master` and hitting enter (replace the drive letter and path with the actual path to the downloaded folder).

Then, type `uv run sv` and press enter. The app should start after a few seconds.

**macOS/Linux**:
Open a terminal at the downloaded `signal-viewer-master` folder and type `uv run sv`, then press enter. The app should start after a few seconds.
