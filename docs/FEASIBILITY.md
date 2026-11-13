# Feasibility: car-aware input filtering, force feedback and rumble

Written Nov 4 from the recompiled physics (`src/phys/phys_rc.c`, symbols as comments) and `src/car.c`. Nothing here is built.
TeknoParrot with the Export data (controller only) is the reference to compare against.

## What the port has today

`car_update` (car.c) writes the arcade's `clGameInput` (`P.gin`: +0 wheel -1..1, +4 throttle, +8 brake, +0x14 gear lever) and calls the arcade
frame (`f_8983f64`, `yt::CIO::Drive` among it). It reads back the body matrix, rpm, tyre postures, effects and the sound request. The
arcade's own steering shaping (`yt::CIOBase::MakeLooseness`, `CPotential::GetSteer`) runs inside the sim. The port adds a smoother on
the pad's value (`c->steer`, 12 /s for an analog stick, 3 / 8 /s for keys) before it.

## (a) Input filtering from the car's state

**Feasible, and cheap.** What a filter wants is in the sim's memory every frame:

- the body's velocity and yaw: already derived in `car_update` (`lateral` sideways speed, `c->speed`, yaw from the body matrix); slip
  angle = atan2(lateral, forward), and yaw rate from the last two yaws;
- per-tyre slip: `yt::CTire::GetTireInput` (slip angle, slip ratio, load) and `CTire::GetForce` are recompiled; their outputs sit in the
  `CMachine` tyre structs (the offsets need to be found by watching the writes of those functions; `CSus::GetForce` gives the load);
- speed-sensitive lock: the arcade's cabinet has a real wheel, so the port's pad needs the equivalent: a max steering angle falling with
  speed, and a filter pulling towards the angle that matches the car's slip (counter-steer assist: the steer that zeroes the slip angle,
  blended by how far the car is past the grip limit).

Plan: add `car_dynamics` (speed, slip angle, yaw rate, front / rear slip) to `car_state`, then a filter stage in `car_update` before
`WF(P.gin, ...)`: (1) a speed-dependent range, (2) a rate limit that gets smaller as the slip grows, (3) optional counter-steer assist
with a strength setting. Verification against TeknoParrot: log the wheel value a pad produces on both for the same corner. Effort: about a
day for 1-2, a few more for 3 with tuning. Risk: the sim already expects a wheel, so over-assist changes lap times; keep it a setting.

## (b) Force feedback in, as a filter input

**Feasible, but the arcade's FFB is not in the recompiled part, so it is rebuilt from the sim.** The recompiled code has no FFB output
symbols (the cabinet's wheel motor is driven by the I/O board code, outside `yt::`). What it does have is the physics that causes the
force: `CMachine::WallReaction`, `HitReaction`, `CTire::GetForce` (lateral force, hence the self-aligning torque), `Stroke2WheelAlignment`.
The "wheel pulls the car back from the wall" is the cabinet's wheel turning (a motor) so the driver's hands steer it; the sim receives the
wheel angle as input only. Without FFB the pad's stick stays where it is and the car rams the wall.

So an FFB equivalent is a computed torque on the pad's steering value: torque ~ lateral tyre force (front axle) x trail, plus a wall-hit
impulse from `WallReaction` / the velocity change `car_hits` already measures. The filter then moves the commanded wheel by that torque
(a virtual wheel with inertia and the driver's hold: `steer += (hold_k * (stick - steer) + torque) * dt`), so a wall hit turns the wheel
away like the real one and the stick has to fight it. Effort: a few days (finding the tyre-force fields; tuning the virtual wheel).
Compare with TeknoParrot's wheel value (a pad on it has the same virtual wheel: the arcade's own `CIO` shaping is in both).

## (c) Force feedback as gamepad rumble

**Feasible.** SDL2's `SDL_GameControllerRumble` is available in the SDL player, and Android has `Vibrator`. The signal to use: road and bump
shake from the suspension (`CSus::GetForce` per tyre: take the high-passed sum, so a steady load does nothing and an expansion joint, a
bump or a road-surface change gives a pulse), kerb / rumble-strip texture from `c->slip` and the tyre's surface, wall hits from
`c->impact`. The signal the user calls "sawhorses" is not in the recompiled code under any name I could find (the cabinet's shaker is the
I/O board's), so the road-joint shake is derived from the suspension as above. A gamepad has a low-frequency (large) and a high-frequency
(small) motor: map road joints / bumps to the large one as short pulses, tyre slip and surface to the small one. SDL rumble takes 0..0xFFFF
per motor and a duration, so it is one call per frame with 50 ms durations. Effort: about a day, with a rumble strength setting (off / low /
normal / strong) in the options file next to `graphics`.

## Order of work I would take

1. `car_dynamics` in `car_state` (slip angle, yaw rate, tyre loads): enables everything.
2. Rumble (c): smallest, no effect on the sim.
3. Speed-sensitive range and slip-aware rate limit (a).
4. The virtual wheel with computed torque (b), compared against TeknoParrot's wheel value.
