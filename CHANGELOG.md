# Changelog

What Super3DX+ adds or changes compared with [Re3DX+](NOTICE.md). Longer explanations are in `docs/`.

## Input and menus

- Controller-first menus: full pad and keyboard control on every screen, with rebindable keys, pad buttons and analog axes
- Controller input filtering, deadzone, response and button-steering speed tuning
- Controller vibration (wall hits, expansion joints, tyre slip) with adjustable strength
- Rebuilt main menu flow: PLAY / SETTINGS / EXIT, then car selection, then Solo / Versus / Car settings
- Stock, Full Tune and Hell's Tuning starting points (Hell's Tuning begins the story on Ch. 101)
- Restored AT / MT transmission select screen
- Special color selection for cars
- Restored suspension lowering for tuned cars
- Volume mixer
- Option to skip the intro cutscenes, and restored missing intro cutscenes
- Information screen

## Game modes

- Fixed versus play over LAN or online, with restored route choice at junctions, last-stretch calls, placings and disconnect handling
- Music selection by the host and by each race's winner in versus
- Time attack rankings with car class and level, kept across sessions
- Restored 10 Outrun's special OST and in-game functionality
- Music track and time zone selection in 10 Outrun
- 10 Outrun rival line animation and rival marker
- Restored junction-choice walls and the "Choose a direction" animation

## Graphics and HUD

- Fixed many missing animations (rival markers, etc.)
- Restored original reflection handling, applied to rival cars
- Tire smoke, headlight flares and the missing shift light
- Arcade-style race HUD alongside the touch HUD, with a debug options menu
- Texture sharpness and graphics options (HD textures, wet road, paint reflections, anti-aliasing)
- Minimaps for Osaka, Hakone, Nagoya and Fukuoka

## Platforms and builds

- Export (English) build support and an English language layer
- Raspberry Pi 5 support with composite CRT output (and optional HDMI)
- Windows, Linux and updated Android players
- Windowed / fullscreen mode (F11 or Alt+Enter), remembered between starts
- `build.py` and `tools/pipeline.py` build driver: Python 3.9+ and a C compiler, no WSL
