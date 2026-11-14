# Super3DX+

A console-style port of the arcade racing game *Wangan Midnight Maximum Tune 3DX+*: controller first, a menu flow built for a
couch instead of a touch screen, and a Raspberry Pi 5 that boots straight into the game and outputs 480i composite video to a
CRT (or, optionally, HDMI). It runs on Windows, Linux, the Pi and Android.

It is a fork of [Re3DX+](https://github.com/Allannn-sudo) (MIT): the car physics are statically recompiled from the arcade's own
executable, and the rendering, menus and sound are rewritten. See `NOTICE.md` for credit, and for what is not here:
**no game content**. You bring your own copy of the game and build the data from it; nothing taken from the game is in this
repository, and nothing generated from it either.

## What works

- Time attack, story mode (all episodes, the in-race dialogue), the 10-in-a-row, the garage, dress-up and the card screens, in the
  Japan and Export (English) builds of 3DX+.
- Versus over a LAN or through a relay: up to four machines (tested with two and three, PC and Pi), the route choice at a junction with the
  leader deciding, the last-stretch call, places, disconnect handling, the winner's choice of music. See `docs/VERSUS.md`.
- Controller (and keyboard) input with remapping, controller vibration (wall hits, expansion joints, tyre slip), the arcade HUD or a touch HUD, the arcade's sound.
- A Raspberry Pi 5 image path: the game starts at boot on a CRT at 60 fps (`docs/PI.md`).

Not done yet, or not tested: controller vibration on pads other than the one it was tried with, the Pi's HDMI output on real hardware, the Buildroot image, some of the story
extras. `CHANGELOG.md` has the history; `docs/PLAN.md` the plan.

## Quick start

You need a dump of the game (a folder with `main` and `data/`; `docs/BUILDS.md` lists the builds that are known to work), Python 3.9
or newer, and a C compiler. There is no WSL requirement: Windows builds with Zig (one download) or MinGW-w64.

```sh
pip install -r tools/requirements.txt
python build.py doctor                      # what you have and what is missing
python build.py all /path/to/the/dump       # tables, physics, data (long: an hour or more), the player, a folder to zip
```

Steps, the options and the other targets (Linux, the Pi, Android) are in `docs/BUILDING.md`. Run the result by double-clicking `super3dx.exe` in the folder, or with
`build/windows/package/play.bat` (or `play.sh`); the data and the saves live next to it.

## Layout

```
build.py        the build driver (Windows, Linux, macOS)
src/            the game (platform-neutral C): the physics glue, the race, menus, HUD, render, sound, netcode
platform/       one folder per target: sdl2/ (PC, Pi), android/, pi/ (the service files)
tools/          the data pipeline (Python): pipeline.py, the generators, converters and packers; addrs/ the per-build address tables
test/           desktop tests in C (physics sweep, story start, rival checks)
third_party/    stb, zlib, the Khronos GLES2 headers (all permissively licensed, each with its own notice)
docs/           building, testing, the Pi, versus, input, the arcade builds, architecture
```

## Licence

MIT (`LICENSE`), keeping Re3DX+'s copyright line. Game content is not covered by it and is not here.

## Credits

- **[Re3DX+](https://github.com/Allannn-sudo)** by Allannn-sudo (高橋涼介のFC): the static recompilation of the arcade's physics, and
  the first rewrite of the rendering, menus, HUD, sound and the data converters. Super3DX+ is built on that work (MIT).
- **Super3DX+**: the console-style menu flow and controls, the Raspberry Pi 5 / CRT path, the versus netcode, the multi-build support
  and the build tooling, by [smolderyguest](https://github.com/smolderyguest).
- The in-game INFORMATION screen (game options) carries the same credits.

*Wangan Midnight Maximum Tune* is a trademark of Bandai Namco; this is an unofficial fan project and is not affiliated with them.
