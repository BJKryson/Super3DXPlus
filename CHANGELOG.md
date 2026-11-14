# Changelog

Everything added or changed on top of [Re3DX+](NOTICE.md) (the static recompilation of Wangan Midnight Maximum Tune 3DX+; MIT).
The short hashes below point at commits of the project's earlier development history, which this repository does not carry (it starts
fresh, with the sources as of the date of its first commit). `docs/` (BUILDING.md, BUILDS.md, ARCHITECTURE.md, INPUT.md, PI.md, VERSUS.md) has the
longer explanations. No game data is in the repository.

Builds: **Export** (English), **JP** (Japan). Targets: Windows SDL2 player, Raspberry Pi 5 (CRT, optionally HDMI), Android, Linux.

---

## Latest (2026-11-14)

- **Controller vibration**: wall hits, expansion joints and tyre slip on the pad's two motors, each with its own strength under GAME OPTIONS > VIBRATION (`docs/INPUT.md`).
- **Sharp fullscreen**: the Windows player is per-monitor DPI aware, so a scaled screen (125 %, 150 %, 200 %) gets the real pixels instead of a stretched bitmap; the default window is scaled to match.
- **Window mode**: GAME OPTIONS > WINDOW MODE (and F11 / Alt+Enter) for windowed or fullscreen, remembered between starts.
- **Screens**: the Information, Debug options and Vibration screens have their own title bars; the Information screen carries the credits and the notice. The default vibration is overall 80 %, wall hits and joints 100 %, tyre slip 50 %.
- **Desktop defaults**: `super3dx.exe` starts by double-click (`data/` and `save/` beside it, 1280x960, the high-quality effects on).
- Fix: the steering filter's settings are saved again (the options file wrote `filter` and read `filter3`).

## 2026-11-13

- **Versus as the real machine shows it**: Please wait! screens over the votes, the black loading screen before the VS cutscene (with the engine rev and
  brake), cars drawn over the discs; the route choice with the leader deciding (the destination boards, "Choose a direction", the junction walls
  standing across the road); the last-stretch call (distance, "Keep going!" / "Don't get caught!", the alarm); each player's real place at the end, TIME UP
  handling, the car sound muted at the finish; disconnects (the car vanishes with a notice, two players end the round, the host leaving ends the game).
- **Versus music**: the race's song plays from the soundtrack of whoever picks it: the host first, then the last race's winner, for everyone.
- **Ranking**: the time attack plates show the car's class letters (A, B, C, S) with its level.
- **Game options**: an INFORMATION button (a placeholder screen for now).
- **Pi**: `tools/pi/install.sh --hdmi` and `prep_boot.ps1 -Hdmi` for an HDMI screen instead of composite (untested on hardware).
- **Tyre marks** are darker than the road.
- **Build**: `build.py` and `tools/pipeline.py` replace the shell scripts: Python 3.9+ and a C compiler (Zig or MinGW-w64 on Windows), no WSL; zlib and the
  GLES2 headers are in `third_party/`.


---

## Platforms and build

- **Initial import** (f368774): the Re3DX+ core, the Android layer and the arcade-physics recompiler tools reorganised into a modular layout
  (docs/ARCHITECTURE.md); an SDL2 player for Linux and a native Windows build (mingw-w64: GL ES context from WGL, GL functions loaded at start, LAN
  stubbed out); streaming Ogg Vorbis music (stb_vorbis), audio buffer and gain settings, keyboard driving keys, an exit watchdog; test hooks
  (`MT3DX_AUTOSTART`, `AUTOQUIT`, `AUDIO_DUMP`, `LOG`); phone-quality extras (MSAA, bloom, 16x aniso) off by default on the desktop.
- **Export (English) build support** (f368774, 0146161, d619956): per-build address tables (`tools/addrs`), region-aware converters, loud failure on
  empty inputs, Japan-vs-Export physics comparison (identical). The arcade's sprite table is sorted by name, so the two builds' ids differ:
  `tools/sprids.py` generates `src/spriteids.h` and the code's `JID(n)` macros map a Japan id to the build's (`tools/jpids.json`); the Export build's
  sprite table length is its own (8,109 vs 8,091); a leading maker with no car data (Gemballa) is left out of the Export list (`CARDB_MAKER0`).
- **Language layer** (d619956, 1f1f28d, 475a7dd): what the port writes itself is English in the Export build (card titles, HP and class suffixes, default
  rankings, race plate, START RAMP, wheel part messages, taxi colour names), picked by the arcade's own region columns (`wmmtaddr.lang()`,
  `WMMT_LANG_EN`); English titles break at '/'; 32-bit text offsets in `titledb` (titles past id ~3600 read wrong).
- **Windows player** (919cdf0, 8ff50ba, 042c084): draws at the window's size with the wide-screen layout, resizable, mouse mapped to the layout; frame
  pacing from the display's refresh (swap interval, precise 60 Hz hold, 120 Hz: 2); displays faster than 60 Hz run 60 arcade steps a second through an
  accumulator (a 120 Hz phone ran at double speed).
- **Raspberry Pi 5** (3923269): arm64 cross build, KMS/DRM composite 480i with a CRT pass (safe area, flicker filter), boot service, setup tools,
  docs/PI.md. Tested on a CRT: 60 fps locked, 53 C, pad, USB audio and LAN versus.
- **Android** (8580268, 44442fb, e5a5f0d, 6f35c56): pad input, touch controls auto/on/off (`controls.txt`, START+SELECT), the screen-environment blit,
  shader table kept up to date, music through `bgm.c` (decoded whole, gapless loop, crossfaded next loop) instead of MediaPlayer, `PKG`/`LABEL` to build
  the Export APK beside the Japan one (checked on a Retroid).
- **Test tooling**: `MT3DX_SHOT`, `MT3DX_TAP`, `MT3DX_SCRIPT` (steps by screen: taps and menu actions, `{NAME}` typing a car's name, `@PAUSE`),
  `MT3DX_AUTODRIVE`, `MT3DX_VPAD` (a virtual pad through the real pad code), HUD scripts kept in `tools/test` (cb36874), card-page test hooks.

## Input

- **Controller-first menus** (3a838e0, 09900d0, ed382e2, 7319f56; docs/INPUT.md): the arcade's seven actions (steering, gas, brake, shifter, view) from
  keyboard and pad beside mouse and touch; every screen reads one `menu_in` intent and the pointer is an adapter (`menu_pointer`); SDL game
  controllers (d-pad, stick with repeat, A/B/Y, triggers, bumpers, Start); the save, name, setting, dress-up and pause screens take the actions.
- **Rebindable controls** (4c774b7, a4fb89c): `bind.c`, a KEY BINDINGS screen, bindable analog steering/gas/brake axes, an input readout.
- **Held pedals** after pause, race keys and axes tracked as held (9f83bf9).

## Menus, screens and flow

- **Main flow** (5327da4, 78f1f8d–4c17557, 69e1039–7d07a5d): a main menu (PLAY, SETTINGS, EXIT), a settings selector (GAME, CONTROLS, SOUND), and a
  new car's starting point (Stock, Full Tune, Hell's Tuning) as discs with descriptions on a translucent band, pulsing arrows, fades, baked
  headline titles; rotating disc rims; text-only discs.
- **Hell's Tuning** (87364b2, 858f749, 6f758f5+): a fully tuned car starts on the story's second loop (Ch. 101) with the first loop's bonuses (SPECIAL
  meter, Maximum Tune and Wangan Midnight R soundtracks); its description reads "Story mode starts on Ch. 101."
- **Car select / garage** (2f42435, d0ae345–9831c63, 18697c2…): one card with named cars, tiles ordered by last use with level, title and model
  badges, horsepower, class pills, a red pulsing cursor with the menus' own chevrons, a "Register a new car" tile first, page tabs, no wrap at the
  ends, the delete bin on the select (the separate garage screen was dropped); tuned-parts screens keep the colour cycling with up/down.
- **Several cards of one model** (9f83bf9): per-card slots (car + 12 x dup, up to 8 of a model) with their own parts, tune and results; save lines
  carry ` #n`; the garage is written through a `.tmp`, with a `.bak` of what was loaded and `.fewer` when a write holds fewer cars.
- **Special car colours** (d5daa97, 5fe3d36): a COLOR key on the card screen, unlocked by plays (all ten with ALL PARTS), shown on the car in its parts.
- **Name entry** (ad6ed4f, 6f758f5, 9dc6eb2): the car's name asked before the starting point; the keyboard moved up so the characters sit between the
  dividers, the katakana / hiragana / upper / lower / enter tabs in the bottom row, a tighter ring and a centred tab ring, the cursor on the first
  letter from the start without touch controls, English opens on upper case.
- **Select transmission** (new): a new car asks AT or MT right before its card is confirmed (after the starting point), on the arcade's own screen - the AT and MT discs with the car behind, Select transmission on the bar, no cancel key. The choice carries to the card's transmission setting; it can also be changed later from the Car / Settings discs (below).
- **Mode select after the car's card** (new): once the car is confirmed, three text discs - **SOLO** (the game select: story, 10 out run, time
  attack, now the arcade's three-disc layout), **VERSUS / BATTLE** (the Bluetooth / LAN / server versus screen, moved here out of the game
  select) and **CAR / SETTINGS** (four discs: **TRANSMISSION**, the AT / MT screen; **DRESS-UP / PARTS**, "Select the part to exchange";
  **METER & BGM**, the card's settings; **DELETE CAR**, a KEEP / DELETE question that removes the car with its tune, parts and results).
  Back goes one level up through all of them (the mode discs go back to the card). The touch bin (garage, car list) and the card's dress-up
  wheel key are gone: DELETE CAR is on these discs, and CUSTOMIZE opens a two-disc menu: DRESS-UP PARTS and PAINT COLOR (the special colours the car has won).
  The card's own COLOR and METER / BGM keys, its dress-up key (and Up), and the bin on the car list and garage (button, view key, touch)
  are removed with them: those screens are only reached from the discs now.
- **Card data confirmed** now has seven pages, "(n/7)": the two settings pages (transmission / meter, BGM) are gone, as the discs cover them.
- **Touch on the disc menus** (fix): a tap on a disc chooses that disc (a second tap on the one that is on decides it) and a tap between discs does nothing.
  Before, the two-disc selects (STOCK / FULL TUNED, AT / MT, KEEP / DELETE, CUSTOMIZE) used the three-disc places, so a tap on the other disc decided the one that was on.
- **Options trimmed**: the bloom, the screen-space ambient occlusion, the baked ambient occlusion and the FSR sharpening are gone (always off); the Game options
  screen no longer has the KEY BINDINGS and VOLUME keys (the SETTINGS discs open them) and keeps HUD OPTIONS and the bridge reflection. The **reset car** control is removed
  (keyboard, pad and the touch key; an old bindings file's line for it is ignored).
- **Key bindings** (fix and tidy): two pad buttons per action (was three), the arcade's top bar (also the Volume, Meter & BGM and HUD options screens), and no more
  soft-lock: waiting for an input gives up after 8 s, any input of the wrong kind (a pad button for a key cell, a key for a pad cell) ends the wait, and a menu action always
  keeps one key and one pad button (binding the OK pad button to another menu action swaps instead of leaving a pad with no OK).
- **Textures** (HUD OPTIONS): SOFT / NORMAL / SHARP / SHARPER, the mip bias the road and scenery are drawn with (the default is SHARP, one level sharper than before); acts at once.
- **10 out run**: the rival's line now slides (the model's own two-key animation, 1.3 s); the rival mark pops in each time it comes over the car (it ran down unseen
  before); a beep as you come up to the line, quicker the nearer (the arcade's approach5; off in HUD OPTIONS, "10 OUT RUN BEEP").
- **Tyre smoke** from a sliding or spinning wheel (the tyre marks' strength drives it; tiresmoke.tga is lights.wpk's last texture; WMMT_NO_SMOKE turns it off).
- **Suspension kit**: a tuned car (handling level 6 and over) sits lower on its tyres in the menus and the race, by the arcade's own car_height.lua (a few centimetres;
  src/partdb.h CAR_HEIGHT, PART_SUSP_*; `susp 0` in save_dir/graphics leaves it up).
- **Card data confirmed**: a Special Vehicle's Body color row showed the Title line again ("B3 Class /Wangan Beginner" under a full-tuned Corolla's): its colour name's sprite
  id ran into the class rows'; the class rows moved clear of it (menu_extra.bin).
- **Time attack ranking**: a kept run shows the class its car had (C9 .. SSS), saved with the ranking ("rank2" lines; older lines read as class N).
- **Default master volume 50%** for a new save (an existing save keeps its level). Test runs with a menu script, shots or auto quit are silent unless MT3DX_AUDIO is set.
- **10 out run time zone and music** (new): after the level select the time zone and BGM select (the time attack's) opens, starting on the level's
  own time zone and soundtrack. Its list is the 10 out run's own: RANDOM, Just Flat Out, Midnight Sanctuary, Nip And Tuck Race, Highway Obsession,
  Adrenaline Blowouts The Fear, NO BGM (the pick plays through the race; the 32-man level keeps the card's songs); back returns to the level select.
- **Everything open from the start**: every meter (Normal, For Racing, Special) and every soundtrack source (3 / 3DX / 3DX+, Maximum Tune & 2,
  Wangan Midnight R) is open on every car, STOCK or FULL TUNED; and every dress-up part and special colour is, too (a car of an older save as well).
- **Rivals' windows reflect the screen** (new): the rivals' and the traffic's glass now takes the screen as its environment map as the player's
  does (the arcade gives every car the same EnvMapTexture). Not seen in a race yet.
- **Axis sensitivity** (new): the AXES list of the key bindings has a SENS. column (50-200 %, the response curve: below 100 softer about the middle, above sharper, the full throw unchanged) beside DEADZONE
  (now 0-40 % in finer steps), saved with the bindings (older files read as 100 %).
- Fix: the stray "0" in a box on the race loading screen (Export build): the soundtrack logo's sprite ids were the Japan build's, not
  mapped; the three logos now show.
- Fix: the dress-up screens' top bars and pictures read the Japan build's sprite ids in the Export build ("[Gull wing]" above the neons, locks
  and NEW tags missing): the layout table's ids are mapped.
- **Brand select** (e5a78ab, 353dab7, c89f1b9, cfa9b31): a **Special Vehicles** button at the row's right end (a generated "?" logo, left panel and
  name plate), the row centred (Export: moved half a step; JP with Gemballa: scaled to fit), the arrows kept on both sides of Toyota, the old
  bottom-bar key retired; the Special Vehicles caption.
- **Card check, nine pages** (21d23d7, ad6ed4f, 6f758f5, 0adaa50): from the arcade's own layouts through `menu_extra.bin` — 1 machine registration
  (Mileage password and Card life rows removed), 2 story mode (cut-out rival pictures and ramp names from the arcade's story-index table, tuner story
  included), 3 ghost battle, 4 its record, 5 10 out run, 6 versus, 7 time attack (a list that scrolls by itself with the glowing stop knob), 8 and
  9 the settings (meter, transmission; sound source only on page 9); BGM volume and password-printing rows removed; the bottom bar's key glyphs animate.
- **Fixes**: the second car of a model no longer stocks the first (1667a7d); a new car's name no longer lands on the car already driven (6141ab0, the
  garage save stored it while the name was typed); back from the game select no longer skips pages after KEEP; no touch settings or back key on the top bar
  without touch controls (4c2cec4); touch-only keys hidden in the arcade HUD style (454f114, 37a9f8d); a skip of the boot with a press (a3fa037).
- **Menu text and fonts**: the game's own font for the port's text (1db2b12), race plate names in the arcade's white font 1 from `menu_extra.bin`
  (a32d224), headline titles in the arcade's red-glow style (1ec43d6–5cde354), card-select titles in white.
- **`menu_extra.bin`** (69e1039+; docs/BUILDS.md): an optional pack whose sprites override `menu.bin`'s and which carries its own animations; built by
  `tools/extrapack.py` (discs, titles, labels, the arcade's fonts 1, 2 and 5 as ASCII glyphs, the card pages' animations, the story pictures and ramps, the
  "?" logo).

## Gameplay, sound and HUD

- **Race HUD** (fc398bd, 917d15c, a85327b): an arcade style at the cabinet's size and places (no touch keys) with the touch layout as its own style;
  scanline bars pixel-exact; a HUD options submenu (input readout, fps counter, back mirror).
- **Shift light** (eb58316, f3562c2): the rev lamp over the meters when the rev rate passes 0.86, blinking 3 frames of every 5.
- **Time attack** (9f83bf9, 703fc01): a machine-wide persistent ranking shown on the ranking screen, a result place and RECORD TIME, records kept with
  traffic on, the back/music/after-race flow; export ranking screen digits and cars fixed.
- **Story**: story races pick their city's map in the Export build (6cbaeeb); rival fixes: Shima in Export, a rival keeps its model when the car select
  lacks its type, wheel textures with red and blue exchanged corrected.
- **10-in-a-row soundtrack** (7127660, 582fa21, 8af2fdf): `ten_*` loops by level and rivals beaten, started at once with a 0.6 s crossfade, crossfaded at
  the cutscene flash, car sound muted (turbo blow-off and turn chimes too), 16 one-shot voices.
- **Movies** (36aab47): the attract loop's `intro`, `playdemo` and `tutorial` in the SDL2 player (JPEG frames over an Ogg soundtrack; made by
  `tools/media/prepare_movie_sdl.sh`); the English build keeps the prologue's first part, Japan both (e7153c3).
- **Minimaps** (9f83bf9): `navi_<city>.bin` for Osaka, Hakone, Nagoya and Fukuoka.
- **Volume mixer** (a3fa037); graphics options: texture filtering (aniso, LOD bias), exhaust and roll cage toggles; defaults set (axis readout, FSR, AO,
  bloom and wet road off; 2x AA) (793f4e6).

## Cars and rendering

- **Reflections** (b50e64f, 6726825, b1c0153, e76bd36, 82b76f1, 5fb7a73): the car paint and glass sample the last frame as the arcade's `car.cg` does,
  menu cars have their own env map and lighting (`look.txt` to tune), glass layered by normal facing, no vertex colour on glass batches.
- **Tuned parts** (eb58316, 4d56949): the exhaust and roll cage a tune shows (IsTuned thresholds read from the arcade), the Celsior's gold emblem, clear
  tail lamps, smoked glass and Mach sticker; aero kit paints (`wpk_paint`, `wpk_share_sync`) in menus, race and versus; gold Impreza wheels.
- **Headlights** (b6719e5): the streak and glow flares of `car_frontlight.igb` at each car's HL_NULL nodes, camera facing, scaled by distance and faded by
  the angle to the car's axis; story rivals have them too.
- **Textures and conversion**: compressed images of pixel order 100 hold red and blue exchanged and are decoded right once in `tex.py` (course arrows,
  goal line, neons, auras, wheels, traffic, car icon) (6bf148b); map vertex colours stored R G B A (the Wangan tunnels' orange light) (40effb3).
- **Skies and light banding** (c9684e6, 6c01337, 21485fa, 31b3614, 97e41fa, e742824, fb7245d, f1623f9, fe92211, d3b4aeb): Hakone's morning sky drawn opaque
  and dithered; all sky packs dithered; then, after dithering and baking made planes and boxes round beams, the soft alphas (light beams, building,
  bridge and goal glows, light panels, headlight pool and flares) are stored at 8 bits (`WPK_RGBA8`, wpk format 16) so the arcade's own blend
  shows without banding. Street lights have one flare under the housing; light files per city (Osaka, Nagoya, Fukuoka); `WPK_HIDE_TEX` test hook.
  Binaries older than this cannot read format 16: the Pi and Android need the new binary together with the new night maps and lights.

## Research notes (docs/)

FEASIBILITY.md (what a port to other hardware takes), PLAN.md, PI.md, RESEARCH-ten-ghost-event.md, BUILDS.md (builds, languages, extras, card pages, lights).

## Known gaps

- Chapter 6's ramp name differs from the real card's in one case, and two ramps in episodes 17 and 18 read differently from hardware captures.
- Page 9's bottom bar still shows an unneeded "Select items" glyph.
- The JP build compiles and was driven through the menus lightly; the Export build is the main test target.
- Pi and Android builds of the latest changes are not deployed yet.
