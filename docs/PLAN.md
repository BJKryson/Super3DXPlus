# WMMT 3DX+ on Raspberry Pi 5 (480i composite) - project plan

Goal: a home-console-style port of Wangan Midnight Maximum Tune 3DX+ (Export build, English) that
boots from a flashed SD card on a Raspberry Pi 5 and outputs 480i composite to a CRT.
Built as a fork of Re3DX+ (MIT, by Allannn-sudo / 高橋涼介のFC): credit it everywhere.
The repo ships tools only; users bring their own game data. No game data or assets are published.

## Decisions
- Content: full 3DX+ single player, including 10-in-a-row (10 Outrun). No online/versus for now (LAN maybe later).
- Base: native Linux/arm64 fork of Re3DX+ (not an emulator). Physics is the statically recompiled arcade code.
- Video: GLES via Mesa (v3d), KMS/DRM + EGL, no desktop. 640x480 render at 60 fps, 480i NTSC composite is the focus.
  Each field takes alternate lines of the newest frame. HDMI is a separate build script. PAL is dropped.
- Accuracy over "enhancement": drop Re3DX+'s HD upscaling / extra shaders.
- Input: SDL2 GameController, hotplug, remap wizard, Bluetooth pairing screen, wheel (evdev) as a stretch.
- Audio: USB DAC first (user's Ugreen DAC is the test case), HDMI fallback, fixed rate/period size, audio setup screen.
- Saves: simple profile slots on the SD card or an external FAT32/exFAT drive, selectable.
  Stretch: standalone PC editor; importer for YACardEmu card.bin and Re3DX+ saves.
- Boot menu (launcher) before the game: controllers, audio, video, saves/storage. Also reachable in game by a button combo.
- Image: Buildroot (prototype first on Raspberry Pi OS Lite). One command on a PC takes the user's game folder
  and produces a .img to flash with Raspberry Pi Imager. Image expands to the card (32 GB card to start).
- Language: English first (Export `-us` assets), Japanese later.

## Environment (all on E:)
- Developed on Windows with a WSL2 Ubuntu 24.04 distro kept on the E: drive (`wsl --install Ubuntu-24.04 --location E:\WSL\...`);
  `tools/dev/setup_wsl.sh [--android]` reproduces its packages, Python environment and Android SDK.
- Windows `adb` (platform-tools, on E:) talks to the phone on USB; `platform/android/deploy.ps1` installs and pushes data.
  Test device: Retroid Pocket 5, Android 13.

## Findings
- Export and Japan 3DX+ have near-identical data trees. Only config.lua differs in shared files (JAMMA flag).
  Region folders differ (sprite vs sprite-us, anime vs anime-us, movie vs movie-us).
- Export `main` is a different build (24.93 MB vs 24.86 MB, ~21.9M bytes differ), so all binary-address-keyed tooling needs re-pointing.
- Re3DX+ docs omit these Linux needs: numpy, fonts-urw-base35, fonts-noto-cjk, ffmpeg AAC instead of macOS afconvert,
  build-tools >= 35 for zipalign -P. `adb push <folder>` crashed (bad_alloc) on this setup: use a tarball.
- Re3DX+ Android flow never creates data/cutin/jp/*.txt (the story's in-race lines; only iOS build.sh copies them from
  the arcade data and the README table omits them). Without them EVERY story start aborts: rc_dispatch "indirect call 0"
  in Cut::clCutIn::Init (backtrace: story_cut_start -> car_cutin_start -> f_85b16a4). The Android log.txt does not keep
  the abort message (stderr is lost on abort): make log writes unbuffered/flushed. Fixed by copying data/cutin/jp (112 files).
  The Export data has cutin/us (and LocationTest_*); the Export build should read those.
- Re3DX+ already implements 10-in-a-row (tendb.py, pack_tenline.py, ten_test.c). Generator warns:
  "no chara pack for 10 CHARA_NIS_BCNR33_YUJI".

## Regional differences (confirmed by the user, from TCRF)
- The three empty Export car folders are the Gemballa cars (3.8 RS, RSR, Avalanche), Japan-only (Porsche licensing).
  Their wheels/stickers are Japan-only too. Keep the table entries (ids stay in step with the binary) but never list them.
- Story rivals are substituted in Export: Shima's Blackbird = black Fairlady Z S (Z33) with NISMO S-Tune GT kit (aero C);
  Ishida = Subaru Alcyone SVX; Masaki starts with a Mazda Eunos Cosmo. Tables are read from the Export main, so verify
  no story rival still points at a Gemballa pack.
- Export-only: Toyota Aristo/Celsior "Japanese-model" disclaimer (Lexus GS/LS abroad) when highlighted: the menu rework must show it.
- Japanese and Export cards are not interchangeable (a Gemballa car on an imported card needs a defined fallback).
- Everything else (courses incl. Fukuoka, other cars, dress-up, BGM, 100 story stages) is shared.

## Verification of the project folder (2026-11-03)
From clean copies of this repository (no leftovers from the scratch folders):
- `tools/dev/compare_builds.sh <Japan> <Export> --rivals`: generate + physics recompile 19 s / 18 s, both with 0 problems;
  156 car samples vs 156, 0 differing once names are ignored; 100 story races per build with no crash or hang:
  61 identical, 39 with a substituted rival car, 0 with the same rivals and a different result. RESULT: SAME.
- Android: `tools/gen_from_original.sh <Japan> --phys` then `platform/android/build.sh` builds the APK from scratch
  (6,185,540 bytes; the earlier hand-built one was 6,185,538, the difference being the signing key's name).
Not run from the new folder: `tools/convert_all.sh` end to end (its steps are the ones that were run by hand and
shown to work on the Japan data) and `platform/android/deploy.ps1` (same logic as the tarball push that worked).

## Status
- [x] WSL + toolchain
- [x] Re3DX+ generator + physics recompile on Japan data (0 problems)
- [x] Full asset conversion (Japan) and Android build; verified working on the Retroid Pocket 5 (sound, per-car models)
- [x] Project folder created (this repository, `Super3DX+`): Export-aware sources merged, platform code under
  platform/android, iOS-only files dropped (Re3DX+ stays outside as reference), portable scripts (tools/convert_all.sh,
  tools/dev/*), .gitignore/.gitattributes keep game-derived files out. Verified from a clean copy: see "Verification" below.
- [x] Python generator + physics recompile re-pointed at the Export main:
  tools/addrmap.py (symbol-anchored Japan->Export address translation, checked against bytes),
  tools/mkaddrmap.py (writes the shipped table tools/addrs/export.json; keyed by md5 of main), tools/wmmtaddr.py (A()).
  Whole generator runs; physics recompile = 668 functions, 0 problems (same as Japan).
  Export quirks found: gearbox ids shifted (ranked, not hard-coded); 3 car folders ship empty in the Export data
  (gem_964_38RS, gem_964_RSR, gem_997_AVA); roots.txt holds bare Japan addresses (now translated).
- [x] C side made build-independent (work/export-gen only): tools/recomp/mkrcaddr.py writes src/phys/rc_addr.h
  (RCA(98028e4) game-state macros, f_<japan> -> f_<build> aliases, image/heap/stack layout derived from the image end);
  car.c wraps its 23 address lines in RCA(); title.c and rc_runtime.h use the derived layout.
  Only ~45 real address uses (most of the ~278 literals in menu.c/hud.c are comments).
- [x] Export physics vs Japan (a local dev script, test/car_test.c, every course AT+MT): 144 lines each, IDENTICAL.
  Broader sweep (a local dev script, not kept here): 40 distinct ECarTypes (52 cars, Gemballa excluded) x 3 courses,
  900 frames each, 156 samples: 0 differences once names are ignored. Only regional names differ
  (Aristo/Celsior "Taxi" vs 個タク仕様, ROADSTER = MX-5, Mazdaspeed Atenza = Mazdaspeed6).
  Story rival races (a local dev script + cmp_rival_race.sh; rivals built from each build's RIVALDB as app.c does,
  1200 frames, all 100 episodes, no aborts or hangs): 61 identical, 0 same-rivals-different-result, 39 with a
  substituted rival car and nothing else (same series, same rival count): Gemballa 3.8RS -> Z33 (36x), Avalanche -> SVX
  (3x), RSR -> Eunos Cosmo (1x), and once 3.8RS -> RX-8 (SE3P) which TCRF's notes don't mention (check which episode).
  (The old test/rival_test.c puts SERIES into `losses` and runs series 0, which never ends: don't use it for story races.)
- [~] Export asset pipeline (English -us assets): first full pass done, see docs/BUILDS.md. Everything but the menu step
  passes; the menu step is re-running with the banner-string fix. Still to do: look at the English menu pictures, and run
  the game on the Export data.
- [~] SDL2 platform (platform/sdl2, milestone 1): builds and runs on the Japan data: window, GLES context, audio, mouse as
  touch, Enter as the start button. No BGM, movies or gamepad yet. WSL notes: Mesa's Direct3D 12 GPU path (GPU=1) FREEZES
  the player at the first Start press (the game thread waits forever on a GPU fence inside the driver; with the loader
  thread on, it deadlocks against that thread too), so the default is the software renderer, which works. The loader
  thread is opt-in (--loader-thread). A watchdog makes the window closable even when the game thread hangs.
- [x] Linux/Pi platform layer (KMS/EGL, 480i, SDL audio/input): the SDL2 player cross-built for arm64 on Raspberry Pi OS Lite, KMS/DRM on the
  Pi 5 composite connector, a CRT pass (safe area, flicker filter), boots into the game as a service (docs/PI.md). First run 2026-11-05:
  60 fps locked, 53 C at most, LAN versus worked. Left: clean shutdown/power path, pad mapping on other pads, read-only root
- [ ] Accuracy pass (remove enhancements)
- [ ] Launcher/boot menu + console-style game menus + profile saves
- [ ] Buildroot image builder
- [ ] Stretch: save editor, card importer, JP language, LAN
