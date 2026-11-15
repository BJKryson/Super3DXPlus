# Super3DX+

This an accessibility-focused native port of *Wangan Midnight Maximum Tune 3DX+* built for non-wheel controllers, with a console-style frontend. It is based on the static recompilation work of [Re3DX+](https://github.com/Allannn-sudo), but the player was rebuilt on SDL2 alongside the Android player. It supports both the Japan and Export (English) versions of the game, and runs on:

- PC (Windows / Linux)
- Android
- Raspberry Pi

Showcase video: https://www.youtube.com/watch?v=WwAjkctDoF4

## Copyright disclaimer

This repository does **NOT** contain any copyrighted content from the original game or from Bandai Namco Entertainment, Inc. or its affiliates, and nothing generated from it. It contains only free, open-source (MIT) tools for building the conversion from **your own legally obtained game data**. See [Quick start](#quick-start).

*Wangan Midnight Maximum Tune* is a trademark of Bandai Namco Entertainment, Inc. This is an UNOFFICIAL, strictly NON-COMMERCIAL fan project and is not affiliated with them in any way, shape or form, written or implied.

**Where can I get the APK / EXE?** 
You can't. Any pre-built binaries you see online are unauthorized distributions of copyrighted content, and are not affiliated with this project or its developers. Running unsigned executables from strangers is a bad idea anyway. 

## Quick start

**You need your own copy of the game:** a folder with a file called `main` and a folder called `data` inside (from the Japan or Export version of 3DX+; `docs/BUILDS.md` lists the versions known to work). Nothing from the game is included or downloaded. You also need about 15 GB of free disk space, an internet connection for the first run, and an hour or more of waiting.

**Windows**

1. On this page, click the green **Code** button, then **Download ZIP**, and unzip it somewhere (not inside a protected folder like Program Files).
2. Double-click **`setup.bat`**.
3. Follow the prompts. It installs what it needs (it will offer to install Python and ffmpeg if you don't have them), asks you to pick your game folder, and builds everything.
4. When it says it's done, it tells you which folder your game is in. Open it and double-click **`super3dx.exe`**.

**Linux / Raspberry Pi / macOS**

Download the code, open a terminal in its folder and run `./setup.sh`. It installs the Python packages by itself, and tells you the one `apt install` command to run if a compiler or SDL2 is missing.

**If something goes wrong:** the setup stops with a plain-language explanation of what probably happened and what to do, and saves a full log in `build/logs/` (named `setup-<date>.txt`). If you are stuck, open an issue and attach that file. `docs/BUILDING.md` has a list of common problems and their fixes.

**Prefer to do it by hand, or build for something else?** `docs/BUILDING.md` has the complete manual steps for Windows and Linux (no installer), the individual build commands, and the Raspberry Pi and Android builds (also `docs/PI.md`). Controls and remapping are in `docs/INPUT.md`. To build both the Japan and Export versions, run the setup again and pick the other game folder.

## Layout

```
build.py        build driver (Windows, Linux, macOS)
src/            the game (platform-neutral C)
platform/       per-target code: sdl2/ (PC, Pi), android/, pi/
tools/          data pipeline (Python): converters, generators, packers, per-build address tables
test/           desktop tests in C
third_party/    stb, zlib, Khronos GLES2 headers (each with its own notice)
docs/           building, testing, Pi, versus, input, builds, architecture
```

## What makes this "native"?

This is not an emulator wrapper. The arcade's car physics are statically recompiled from the game's own executable, and everything else (rendering, menus, sound, netcode) is a ground-up reconstruction. The game code runs on bare metal and "just works" without emulator setup, and most of the work goes into quality-of-life improvements for all sorts of control schemes.

## What's different from Re3DX+

Re3DX+ was touch-only, Japan-only, and basic in functionality. Super3DX+ adds:

- Controller support, with vibration and input filtering
- Support for both Export and Japan versions
- Menus and flow reworked for a non-arcade setting, as authentic as possible
- A rebuilt car save/load system, like a modern Banapass-style garage
- The original race UI restored, with touch controls optional
- Restored features: 10 Outrun music, story-mode visual upgrades (roll cages, exhaust, Gatchan's Celsior parts), body color customization, and more
- Many bug fixes, such as broken texture conversions and missing tuning parts

This only scratches the surface; see `CHANGELOG.md`.

## Why the Pi?

The Raspberry Pi build turns a Pi into an appliance that boots straight into the game over composite video: "what if WMMT3 had a home-console port?" Flash the card, put it in the Pi, play (`docs/PI.md`).

See: https://www.youtube.com/watch?v=vMuYHEGcGEk

- **Pi 5:** solder a composite video jack onto the J7 pads for composite video, and use a USB sound card for analog audio.
- **Pi 4 and below:** use a TRRS-to-composite (camcorder style) cable in the headphone jack.
- **HDMI:** install with `tools/pi/install.sh --hdmi` (or `prep_boot.ps1 -Hdmi`). Untested on real hardware.

Only tested on a Raspberry Pi 5 (8 GB). Other models should work with simple config tweaks, but I don't have the hardware to test.

## Status

Time attack, story mode, 10 Outrun, the garage, dress-up and card screens, and versus for up to four machines (`docs/VERSUS.md`) work in both builds.

- **Not implemented:** ghost VS battle, the post-race mileage screen, the 10 Outrun post-race rewards / progress screen.
- **Known bugs:** menu slide/select animations aren't smooth; story rival headlight flare positions are inaccurate (no position data seems to be stored for them); gamepad detection for vibration is a little finicky (basic SDL2 compatibility).
- **Limitations:** no racing wheel or force feedback support, and classic iOS support was dropped (no equipment to test either).
- **Cautions:** story mode hasn't been played all the way through. The Japan build is tested much less than Export, since I can't read Japanese; if the text is messed up, please submit an issue.
- **Maybe later:** rollback netcode for online versus (big undertaking, noticeable performance cost), wheel support.



## Licence and credits

MIT (`LICENSE`), keeping Re3DX+'s copyright. Game content is not covered and not included. See `NOTICE.md`.

- **Super3DX+**: developed by [smolderyguest](https://github.com/smolderyguest).
- **[Re3DX+](https://github.com/Allannn-sudo)** by Allannn-sudo: the original conversion effort, including the static recompilation of the physics and the first rewrite of rendering, menus, HUD, sound and data converters (MIT).
- **libretro / Lakka-LibreELEC**: reference for the Pi's composite output and filtering method.
