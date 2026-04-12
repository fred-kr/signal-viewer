# How to run Signal Viewer

Download the [ZIP archive](https://github.com/fred-kr/signal-viewer/archive/refs/heads/master.zip) and extract it to a folder of your choice.

Inside the folder is a `run_sv_<operating_system>` file. Double-click it install the necessary dependencies and run the Signal Viewer application.

If this doesn't work, see below.

## Requirements

For now, `uv` is the easiest method to run the Signal Viewer application.
Install it using one of the following commands, depending on your platform:

*Windows*
```sh
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

## Download ZIP Archive

Download the [ZIP archive](https://github.com/fred-kr/signal-viewer/archive/refs/heads/master.zip) and extract it to a folder of your choice.

## Run Signal Viewer

Open a terminal and navigate to the Signal Viewer folder. Run the following command:
```sh
uv run sv
```

After a few seconds, the Signal Viewer application should open.