# Research: 10-in-a-row music, Ghost Battle, VS event modes

Read from the Export dump's `main` (the Japan build has the same files and tables) on Nov 4. Addresses are the Export build's.

## 1. The 10-in-a-row soundtrack: it is all there

`data/sound/bgm/maxi3/ten_a1..a9, b1..b8, c1..c8, d1..d6, e1..e7.wav` (37 loops, 1.5 to 3 MB each) are in both dumps. `main`'s BGM
table (12 bytes a track: path, volume 2.5, title; indexed by `emBgmType`) has them at 55..92, and each letter's title is the track you named:

| set | tracks | title (from the table) |
|---|---|---|
| a | ten_a1..a9 (55..63) | Nip And Tuck Race (Maxi 2) |
| b | ten_b1..b8 (64..71) | Highway Obsession (Maxi 2) |
| c | ten_c1..c8 (72..79) | Adrenaline Blowouts The Fear (Maxi 2) |
| d | ten_d1..d6 (80..85) | Just Flat Out (Maxi 3) |
| e | ten_e1..e7 (86..92) | Midnight Sanctuary (Maxi 3) |

(The titles are the table's first letters N, H, A, J, M; the full names are your list, in that order.)

The loop played is `getTenRoundBgm10(level, round)` (0x857ed60): table at 0x9335240, 10 ints a level, `round` the rivals beaten so far (0..9).
The race calls it with round 0 as it starts (`setRaceBgm`), then after each beaten rival `SNDStreamSetNextBgm(getTenRoundBgm10(level, beaten))`
(race thread, 0x8910460): the next loop is queued and starts when the current one ends (the engine's "seamless play list"); a row that
repeats a loop (d2, d2) just goes on with it. Levels 1..10:

| level | set | loop by rivals beaten 0..9 |
|---|---|---|
| 1, 6 | d | d1 d2 d2 d3 d3 d4 d4 d5 d5 d6 |
| 2, 7 | e | e1 e2 e2 e3 e3 e4 e4 e5 e6 e7 |
| 3, 8 | a | a1 a2 a3 a4 a5 a6 a7 a8 a8 a9 |
| 4, 9 | b | b1 b2 b3 b4 b5 b6 b6 b7 b7 b8 |
| 5, 10 | c | c1 c2 c3 c4 c5 c6 c6 c7 c7 c8 |

The 32-man level (`getTenRoundBgmExtend`, 0x857ed7c) does not use them: by rivals beaten (groups 0-1, 2-4, 5-7, ... 31) it takes a pair of
songs from the card's BGM list (3DX+ / Maxi 2 / R source), the second one when a check on the clWorkSpace comes out true. After the last
rival the race music stops (the port already does that).

Done (Nov 4): the loops are in `tools/pipeline.py` (step bgm) and encoded into both data folders (ogg and m4a); `app_bgm` gives the level's first loop and `app_bgm_next` the one of the rivals beaten, which the SDL player (`bgm_next`, decoded ahead and crossfaded in over 0.6 s from its start as the rival goes) plays. The Android player does not queue yet (it plays the first loop only). Checked: a 10-in-a-row race played ten_d1, then ten_d2 after the first rival.

## 2. Ghost Battle (分身対戦, "bunshin taisen")

What the dump has, all offline-usable:

- **The opponents.** `data/target/{jp,us}/*.target.gz` (189 files, 55 MB): text headers (a profile: name characters, class, title,
  total wins) then 8 "areas", each a car, its dress-up and tune (`area0_car_ = 82`, `tune_power_ 17`, `tune_handling_ 16`, `ramp_`, `route_`,
  `class_`) and a recorded run, `area0_trail_size_ = 161516` bytes, binary after the text, with a checksum `trail_sum_`. These are the
  fresh machine's "extracted opponents" (`clTargetDataManager`, `getDefaultCrown`); the real game fills the list from the network.
- **The replay code.** `yt::CGhost` (`Init(int, SGhostSettingSet const&, char const*)`, `Drive`, `SetFirst`, `GetInfoCarDisp`,
  `GetInfoCarCamera`, `GetInfoCarEffect`, `End`), `yt::CGhostSetting::GetSettingPt` and `yt::CSampler` (`Load`, `Save`, `GetSample`,
  `InterFromOdo_Dual`, `SSampleInfo070426`) are in the recompiled physics already (`phys_rc.c`), as are `CSeq::pGhostAry`,
  `fGhostInterAry` and `pGhostSettingAry`. The port's `car.c` does not set a ghost up.
- **The menus.** Layouts and pictures: `menu_layout_ta_ghost(_ring)`, `menu_p_ta_ghost_*`, `menu_p_ghost_title(2)`, `menu_p_pre_decide_your_ghost`,
  the crowns (`menu_g_crown_*`, `menu_layout_crown_get_a/b`, `crown_saikyo`), `menu_g_finish_vs`, the challenger mail (`menu_layout_challenge_*`).
- **The flow** (main's debug screen outline, a local dev script (not kept here)): 6-3 the time attack's ghost setting (a ghost to race in a time attack),
  4-14 "your alter ego was made" (the run kept as your ghost), 8-1 how to pick the opponent, 8-2 level, 8-3 area, 8-9/8-10 the opponent and
  its data, 8-11 load, 8-13 the race, 8-15 the result (time up / win / lose), 8-16..18 dress-up parts won, 8-19 crown, 8-20 area conquered,
  8-22 the tutorial race (against a bundled opponent), 4-13 revenge. The picks by friends, strongest players, battle history and card
  name search, and the crown ranking, need the server; the "extracted" opponents and the tutorial do not.

Feasibility: **good for an offline Ghost Battle**: (1) a converter for the target files' trails into whatever `CSampler::Load` reads (the
format is the part I have not decoded: the trail is binary, with a size and checksum per area), (2) `car_start` setting up `CGhost` with
the opponent's car and tune (`CGhostSetting`) and drawing it as a rival (the port's rival draw does most), (3) the menu flow 8-1..8-15 with
the arcade's layouts (8-1's server methods left out), the crowns and the winnings kept in the card, (4) your own runs saved as ghosts
(`CSampler::Save`, 4-14; also the TA "ghost setting"). Rough size: the converter and a first race against a bundled ghost a few days, the
menu flow and rewards a week more. The game-mode slot the VS took stays as it is: Ghost Battle can be a second key on the game select.

## 3. VS special events

Pieces that exist: `clWorkSpace::isEventMode`, `EvOnEventModeSetting` / `EvOffEventModeSetting` / `EvGetEventMode` (a cabinet setting from
the operator's test mode: `clTestModeEventModeThread`), `clV386CardData::isEventModePlayable`, the boot's "CHECK EVENT MODE SETTING"
(every linked cabinet must have it on, and the count must match the linked count), `clEventTitleThread` (3-1A: the event title screen,
`atract_p_event_title_bg`), the entry screens 18-3-3..6 (`menu_layout_event_entry_*`: entry accepted, cancelled, no opponent found, wait),
`menu_layout_event_gas_skip`, `notConnect`, `readError`, a race screen 9-8 "(event mode)", book-keeping `addEventOpen`, `addModeEvent`,
`addTuneEvent`; and in the VS: `addVersusNoHandicap` with `menu_g_vs_ex_handi` (the handicap), `menu_layout_pre_vs_serious` and the
`omakase` icons (let the machine choose), debug course labels "V337 / V363 route, special course, normal course" in the join sequence.
All of it rides on the cabinets' network (entries, matching, no intrusion), so it belongs with the VS work for later: what is there to
reuse is the layouts, strings and the settings' names; the event's rules (what is open, who may enter) are in sequence code I have not read.
