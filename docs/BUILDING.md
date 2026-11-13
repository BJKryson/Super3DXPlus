# Building

Everything is driven by `build.py` (the player) and `tools/pipeline.py` (the data); both are plain Python 3.9+, the same on Windows,
Linux and macOS. `python build.py doctor` shows what is installed and what is missing, with the command to get it.

Nothing from the arcade game is in this repository. Two things are made from **your own dump** of the game (a folder with `main` and
`data/`, e.g. from your cabinet's drive): the *data* the player reads (`data/`, a few GB) and the *generated sources* (tables, and the
physics recompiled from `main`; `src/phys/phys_rc.c` is about 18 MB). Both stay out of git (`.gitignore`). Never upload them.

## 1. Get the tools

| You need | Windows | Linux / macOS |
|---|---|---|
| Python 3.9+ and the packages | python.org, then `pip install -r tools/requirements.txt` | the same (`python3`) |
| a C compiler | **Zig** (`python build.py setup-zig`, no installer) or MinGW-w64 (MSYS2: `pacman -S mingw-w64-x86_64-gcc`) | gcc or clang (`apt install build-essential`) |
| SDL2 development files | `python build.py setup-sdl2` (the mingw package, from libsdl.org's release) | `apt install libsdl2-dev libegl1-mesa-dev libgles2-mesa-dev` |
| ffmpeg with the Bink decoder (sound, movies) | a full build: `winget install Gyan.FFmpeg`, or set `FFMPEG` | `apt install ffmpeg` |
| a C++ demangler | installed by the `cxxfilt` package in `tools/requirements.txt` | `c++filt` (binutils) |
| fonts for a few menu pictures | Arial (already there); the converter looks in `C:\Windows\Fonts` | Nimbus Sans / DejaVu (`apt install fonts-urw-base35 fonts-dejavu fonts-noto-cjk`) |

The converters draw a few pictures' text (the versus selector's discs, the "?" of the special vehicles button, the save screen's
Chinese info page) with whatever of those fonts they find, in the folders named by `MT3DX_FONT_DIRS` and the system's. A different font
gives a slightly different look in those pictures only.

## 2. Make the data (once per game build)

```sh
python build.py data /path/to/dump          # = tools/pipeline.py gen --phys, then convert
```

- `gen` reads `main` and writes the tables (`src/*db.h`, `src/spriteids.h`, `tools/*.json`) and, with `--phys`, the recompiled physics
  (`src/phys/phys_rc.c`, `src/phys/rc_addr.h`) and `data/phys.img`. A few minutes.
- `convert` writes `data/`: the maps, cars, HUD, menus, sounds, music and movies. It takes an hour or more (the menu pictures are
  the long step), and every step logs to `build/logs/<step>.log`. `python tools/pipeline.py steps` lists the steps; `--only <step>` runs
  one, `--no-media` skips the sound, music and movies (the ones that need ffmpeg), `--keep-going` collects all the failures.
- The dump may be the Japan or the Export build (`docs/BUILDS.md`); the region's art folders (`sprite` / `sprite-us`, ...) are handled.
  The dump is only read.

## 3. Build the player

```sh
python build.py exe                         # Windows: build/windows/super3dx.exe;  Linux: build/linux/super3dx
python build.py exe --cc "zig cc -target x86_64-windows-gnu"     # pick the compiler yourself
python build.py exe -O -O1 -j 8             # quicker to compile; eight compiler processes
python build.py package                     # build/<target>/package/: the player, its DLL, data/, play.bat or play.sh
```

The first build compiles the physics (`phys_rc.c`, a minute or two); later ones only what changed. `play.bat` starts the game with its
data and saves next to it (`play.bat --size 1280x960` for a bigger window; the layout is 4:3).

Run it: double-click `super3dx.exe` (it takes `data/` and `save/` from beside itself, opens at 1280x960 and has the high-quality effects on; `play.bat` is optional), or from a shell: `build\windows\super3dx.exe [data] [--save save] [--size WxH] [--fullscreen]`. `MT3DX_HQ=0` turns the effects off (a slow GPU). Controls and remapping: `docs/INPUT.md`.

## Raspberry Pi 5

On the Pi itself: install the dependencies as for Linux, then `python3 build.py data ...` is not needed there: build the data on a PC and copy
`data/` over (`tools/pi/install.sh` does it), and build the player on the Pi with `python3 build.py exe --target pi` (a few minutes).
From another machine: `tools/pi/sysroot.sh` makes an arm64 sysroot, then `SYSROOT=/opt/pi-sysroot python3 build.py exe --target pi`.
Preparing the card, the service and the composite (or HDMI) output: `docs/PI.md`.

## Android

`platform/android/build.sh` builds the APK (needs the Android SDK and NDK: `tools/dev/setup_wsl.sh --android` on Ubuntu installs them) after
`python tools/pipeline.py gen <dump> --phys`; `platform/android/deploy.ps1` installs it on a phone over USB. See the comments in both.

## Problems

- `missing src/phys/phys_rc.c`: run the data step first; the player cannot be built without the generated sources.
- `no SDL2 development files for mingw`: `python build.py setup-sdl2`, or point `SDL2_DIR` at `<...>/x86_64-w64-mingw32`.
- A converter step fails: read `build/logs/<step>.log`; `--only <step>` re-runs it after you fix the cause. A step that fails for a missing
  font or ffmpeg says so.
- Windows: if linking a mingw build complains about `winpthread`, use Zig or the `posix` thread model of MinGW (`x86_64-w64-mingw32-gcc-posix`).
