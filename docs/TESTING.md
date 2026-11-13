# Testing

## Test hooks of the player

Set as environment variables (they do nothing unset, and silence the sound unless `MT3DX_AUDIO` is set):

| Variable | What it does |
|---|---|
| `MT3DX_LOG=1` | log to stderr as the player runs (frame lines, the versus' events) |
| `MT3DX_AUTOSTART=n` | press START each second from n seconds on |
| `MT3DX_GOTO=n` | after START go straight to menu screen n (the `MENU_` enum in `src/menu.h`; 36 is the versus' lobby) |
| `MT3DX_SCRIPT="screen:step;..."` | steps by screen: `@OK`, `@DOWN`, `@LEFT`..., or a tap `x,y`; a `+` repeats until the screen changes (`platform/sdl2/main_sdl.c`) |
| `MT3DX_SHOT=s,s` `MT3DX_SHOT_DIR=dir` | the frame as `shot_<s>.ppm` at those seconds |
| `MT3DX_AUTOQUIT=s` | leave after s seconds |
| `MT3DX_AUTODRIVE=1` `MT3DX_AUTODRIVE_KMH=n` | hold the accelerator in a race (below n km/h) |
| `MT3DX_VSAUTO=host[:n]\|join` | host a LAN game and start it once n machines are in, or join the first found |
| `MT3DX_VSKM=n` | a versus race of n km (short, to test the flow) |
| `MT3DX_NETLOG=1`, `MT3DX_NET_LAG=ms` | the netcode's measurements; an artificial lag on received packets |

## Versus on one PC

`tools/test/vs2.ps1` starts two or three players on this PC (a host and clients that drive themselves), logs and screenshots in
`build/test-runs/<name>-<role>`:

```powershell
powershell -File tools\test\vs2.ps1 -Players 2 -Km 1 -Quit 150 -Shots '60,90'
```

Per-player variables go in `-Host_` / `-Client` / `-Client2` (`'MT3DX_AUTODRIVE_KMH=120;MT3DX_AUTOQUIT=60'` to have one slow down or leave).
`-Players 1 -Expect 2` waits for a second machine (another PC or a Pi) to join. Do not rebuild the player while a test runs (the file is in use).

## The C tests (`test/`)

Desktop programs that exercise the physics and the story's start without a window: `physics_sweep.c` (every car on three courses),
`story_start_test.c`, `story_rival_race.c`, `rival_test.c`, `ten_test.c`, `vs_test.c`, and `hudshot.c` / `menushot.c` (screenshots through a stub GL).
They are built by hand against `src/` (see the head of each file) and need the generated sources.
