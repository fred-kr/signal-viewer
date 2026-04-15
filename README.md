# Installation



## Windows

Download [Signal Viewer](https://github.com/fred-kr/signal-viewer/archive/refs/heads/master.zip) and extract the ZIP archive to a folder of your choice.

Navigate to the `signal-viewer-master` folder and open the `run_sv_windows.cmd` file by double-clicking on it (the `.cmd` part may not be visible, depending on your settings).

Confirm the warning message that pops up, and then wait until the required dependencies have been installed. 
This can take a few minutes when starting the application for the first time, but subsequent runs should be much quicker.

If everything worked, the Signal Viewer application should open. If not, try manually installing the required dependencies (see below).

## MacOS (possibly Linux, not tested)

[uv](https://docs.astral.sh/uv/getting-started/installation/) is required to run the Signal Viewer application. To install uv, run the following command in a command prompt or terminal window:

*Windows*
```bat
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

*macOS and Linux*
```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

or, if `curl` isn't available:

```sh
wget -qO- https://astral.sh/uv/install.sh | sh
```

Wait until the installation has finished, then close the terminal window and go to the next step.

## Download ZIP Archive

If you haven't already, download [Signal Viewer](https://github.com/fred-kr/signal-viewer/archive/refs/heads/master.zip) and extract the ZIP archive to a folder of your choice.

## Run Signal Viewer

Open a terminal (on Windows: press the Windows key + R, then type "cmd" and press enter) and navigate to the `signal-viewer-master` folder.

If you didn't change the defaults, the folder should be located at `C:\Users\%USERNAME%\Downloads\signal-viewer-master\signal-viewer-master` on Windows.

Navigate there using `cd` (on Windows: `cd C:\Users\%USERNAME%\Downloads\signal-viewer-master\signal-viewer-master`), and then run the following command:
```sh
uv run sv
```

The first time you run the application, it will take a few minutes to install the required dependencies. Once this is done, the Signal Viewer application should open.