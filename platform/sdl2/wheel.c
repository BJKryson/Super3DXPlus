#include "wheel.h"

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "app.h"
#include "bind.h"
#include "ffb.h"

#define MAXDEV 16

static struct {
  wheel_sink sink;
  volatile int rescan;     /* a device came or went (set by the event loop) */
  volatile int instance;   /* the open wheel's instance id, -1 for none */
  int n, index[MAXDEV];    /* the list: the SDL index of each */
  SDL_Joystick *j;
  SDL_Haptic *h;
  char name[128];          /* the open device's name */
  Uint32 caps;             /* SDL_HapticQuery */
  int fx_const, fx_spring, fx_damper, fx_sine;
  SDL_HapticEffect e_const, e_spring, e_damper, e_sine;
  int hat;                 /* the hat's last directions (SDL_HAT_*) */
  /* what was last sent, to send only a change */
  int s_force, s_spring, s_damper, s_vib, s_hz, s_gain;
  int playing;
} W = { .instance = -1, .rescan = 1, .fx_const = -1, .fx_spring = -1, .fx_damper = -1, .fx_sine = -1 };

void wheel_init(const wheel_sink *sink) { W.sink = *sink; }

int wheel_instance(void) { return W.instance; }

/* ---- the list ---- */

static int is_virtual(int index) {
#if SDL_VERSION_ATLEAST(2, 0, 14)
  return SDL_JoystickIsVirtual(index);
#else
  (void)index;
  return 0;
#endif
}

static void relist(void) {
  const char *names[MAXDEV];
  int haptic[MAXDEV];
  W.n = 0;
  const int count = SDL_NumJoysticks();
  for (int i = 0; i < count && W.n < MAXDEV; ++i) {
    if (is_virtual(i) && !getenv("MT3DX_VWHEEL")) continue;
    const char *name = SDL_JoystickNameForIndex(i);
    SDL_Joystick *j = SDL_JoystickOpen(i); /* (to ask; the same device is shared with the pad layer's open one) */
    int hap = j && SDL_JoystickIsHaptic(j) > 0;
    if (j) SDL_JoystickClose(j);
    if (SDL_IsGameController(i) && !hap) continue; /* a plain pad: the pad layer has it */
    names[W.n] = name ? name : "UNKNOWN";
    haptic[W.n] = hap;
    W.index[W.n++] = i;
  }
  ffb_set_devices(W.n, names, haptic);
}

/* ---- the open device ---- */

static void say(const char *fmt, const char *a, int b, int c) {
  char s[160];
  snprintf(s, sizeof s, fmt, a, b, c);
  ffb_set_status(s);
}

static void fx_zero(void) {
  if (!W.h) return;
  SDL_HapticStopAll(W.h);
  W.playing = 0;
  W.s_force = W.s_spring = W.s_damper = W.s_vib = W.s_hz = 0;
}

static void close_wheel(void) {
  if (W.h) {
    SDL_HapticStopAll(W.h);
    if (W.caps & SDL_HAPTIC_AUTOCENTER) SDL_HapticSetAutocenter(W.h, 100); /* (the driver's own centering back) */
    SDL_HapticClose(W.h);
  }
  if (W.j) SDL_JoystickClose(W.j);
  W.h = NULL, W.j = NULL, W.instance = -1, W.name[0] = 0, W.caps = 0;
  W.fx_const = W.fx_spring = W.fx_damper = W.fx_sine = -1;
  W.playing = 0;
}

static void cartesian(SDL_HapticDirection *d) {
  memset(d, 0, sizeof *d);
  d->type = SDL_HAPTIC_CARTESIAN;
  d->dir[0] = 1;
}

static int make(Uint32 caps, Uint32 bit, SDL_HapticEffect *e) {
  if (!(caps & bit)) return -1;
  return SDL_HapticNewEffect(W.h, e);
}

static void open_wheel(int list_i) {
  close_wheel();
  W.j = SDL_JoystickOpen(W.index[list_i]);
  if (!W.j) {
    say("COULD NOT OPEN IT: %s", SDL_GetError(), 0, 0);
    return;
  }
  W.instance = (int)SDL_JoystickInstanceID(W.j);
  snprintf(W.name, sizeof W.name, "%s", ffb_device_name(list_i));
  W.hat = 0;
  /* where every axis rests now (a pedal that is not moved sends nothing: the bindings must not take it for the middle of its throw) */
  const int na = SDL_JoystickNumAxes(W.j);
  for (int a = 0; a < na && a < AXIS_WHEELS; ++a) W.sink.axis(AXIS_W0 + a, SDL_JoystickGetAxis(W.j, a));
  char info[160];
  snprintf(info, sizeof info, "%d AXES, %d BUTTONS", na, SDL_JoystickNumButtons(W.j));
  fprintf(stderr, "wheel: opened %s (%s)\n", W.name, info);
  if (SDL_JoystickIsHaptic(W.j) <= 0) {
    say("%s; NO FORCE FEEDBACK ON IT", info, 0, 0);
    fprintf(stderr, "wheel: SDL_JoystickIsHaptic: no (%s)\n", SDL_GetError());
    return;
  }
  W.h = SDL_HapticOpenFromJoystick(W.j);
  if (!W.h) {
    char err[64];
    snprintf(err, sizeof err, "%s", SDL_GetError()); /* (what SDL says, on the screen: the one thing a report needs) */
    snprintf(info + strlen(info), sizeof info - strlen(info), "; FORCES NOT AVAILABLE (%s)", err);
    say("%s", info, 0, 0);
    fprintf(stderr, "wheel: SDL_HapticOpenFromJoystick: %s\n", SDL_GetError());
    return;
  }
  W.caps = SDL_HapticQuery(W.h);
  if (W.caps & SDL_HAPTIC_GAIN) SDL_HapticSetGain(W.h, 100);
  if (W.caps & SDL_HAPTIC_AUTOCENTER) SDL_HapticSetAutocenter(W.h, 0); /* (the driver's spring would fight the game's) */

  SDL_HapticEffect *e = &W.e_const;
  memset(e, 0, sizeof *e);
  e->type = SDL_HAPTIC_CONSTANT;
  cartesian(&e->constant.direction);
  e->constant.length = SDL_HAPTIC_INFINITY;
  W.fx_const = make(W.caps, SDL_HAPTIC_CONSTANT, e);

  e = &W.e_spring;
  memset(e, 0, sizeof *e);
  e->type = SDL_HAPTIC_SPRING;
  cartesian(&e->condition.direction);
  e->condition.length = SDL_HAPTIC_INFINITY;
  e->condition.right_sat[0] = e->condition.left_sat[0] = 0xFFFF;
  W.fx_spring = make(W.caps, SDL_HAPTIC_SPRING, e);

  e = &W.e_damper;
  memset(e, 0, sizeof *e);
  e->type = SDL_HAPTIC_DAMPER;
  cartesian(&e->condition.direction);
  e->condition.length = SDL_HAPTIC_INFINITY;
  e->condition.right_sat[0] = e->condition.left_sat[0] = 0xFFFF;
  W.fx_damper = make(W.caps, SDL_HAPTIC_DAMPER, e);

  e = &W.e_sine;
  memset(e, 0, sizeof *e);
  e->type = SDL_HAPTIC_SINE;
  cartesian(&e->periodic.direction);
  e->periodic.length = SDL_HAPTIC_INFINITY;
  e->periodic.period = 30;
  W.fx_sine = make(W.caps, SDL_HAPTIC_SINE, e);

  char what[96] = "";
  if (W.fx_const >= 0) strcat(what, "STEERING ");
  if (W.fx_spring >= 0) strcat(what, "SPRING ");
  if (W.fx_damper >= 0) strcat(what, "DAMPER ");
  if (W.fx_sine >= 0) strcat(what, "VIBRATION ");
  if (!what[0]) {
    snprintf(info + strlen(info), sizeof info - strlen(info), "; NO USABLE FORCE TYPES");
    say("%s", info, 0, 0);
    fprintf(stderr, "wheel: no usable effect (caps %08x): %s\n", W.caps, SDL_GetError());
    return;
  }
  char s[200];
  snprintf(s, sizeof s, "%s; FORCES: %s", info, what);
  ffb_set_status(s);
  fprintf(stderr, "wheel: %s (%s)\n", W.name, s);
  for (int i = 0; i < 4; ++i) {
    int id = i == 0 ? W.fx_const : i == 1 ? W.fx_spring : i == 2 ? W.fx_damper : W.fx_sine;
    if (id >= 0) SDL_HapticRunEffect(W.h, id, 1);
  }
  W.playing = 1;
}

/* the settings' device against the open one */
static void sync_device(void) {
  if (W.rescan) {
    W.rescan = 0;
    relist();
    if (W.instance >= 0) { /* (still plugged in? the list says) */
      int there = 0;
      for (int i = 0; i < W.n; ++i) there |= !strcmp(ffb_device_name(i), W.name);
      if (!there) close_wheel();
    }
  }
  const char *want = ffb_selected_name();
  if (!want) {
    if (W.j) close_wheel();
    return;
  }
  if (W.j && !strcmp(want, W.name)) return;
  for (int i = 0; i < W.n; ++i)
    if (!strcmp(ffb_device_name(i), want)) {
      open_wheel(i);
      return;
    }
}

static Sint16 s16(float v) { return (Sint16)(fmaxf(-1.0f, fminf(1.0f, v)) * 32767.0f); }

static void effect_update(int id, SDL_HapticEffect *e) {
  if (id >= 0 && SDL_HapticUpdateEffect(W.h, id, e) != 0) fprintf(stderr, "wheel: update effect: %s\n", SDL_GetError());
}

void wheel_frame(void) {
  sync_device();
  if (!W.h || !W.playing) return;
  ffb_out o;
  app_ffb(&o);
  if (!o.on) {
    if (W.s_force || W.s_spring || W.s_damper || W.s_vib) { /* (switched off: the forces go to nothing, the effects keep running) */
      memset(&o, 0, sizeof o);
      o.gain = 1.0f;
    } else return;
  }
  const int force = (int)(o.force * 32767.0f), spring = (int)(o.spring * 32767.0f), damper = (int)(o.damper * 32767.0f), vib = (int)(o.vib * 32767.0f);
  const int hz = (int)o.vib_hz, gain = (int)(o.gain * 100.0f);
  const int FORCE_STEP = 330; /* 1 %: a change smaller than this is not sent (a wheel's bus is slow) */
  if (gain != W.s_gain && (W.caps & SDL_HAPTIC_GAIN)) SDL_HapticSetGain(W.h, gain < 1 ? 1 : gain), W.s_gain = gain;
  if (abs(force - W.s_force) >= FORCE_STEP || (force == 0) != (W.s_force == 0)) {
    W.e_const.constant.level = s16(o.force);
    effect_update(W.fx_const, &W.e_const);
    W.s_force = force;
  }
  if (abs(spring - W.s_spring) >= FORCE_STEP || (spring == 0) != (W.s_spring == 0)) {
    W.e_spring.condition.right_coeff[0] = W.e_spring.condition.left_coeff[0] = s16(o.spring);
    effect_update(W.fx_spring, &W.e_spring);
    W.s_spring = spring;
  }
  if (abs(damper - W.s_damper) >= FORCE_STEP || (damper == 0) != (W.s_damper == 0)) {
    W.e_damper.condition.right_coeff[0] = W.e_damper.condition.left_coeff[0] = s16(o.damper);
    effect_update(W.fx_damper, &W.e_damper);
    W.s_damper = damper;
  }
  if (abs(vib - W.s_vib) >= FORCE_STEP || hz != W.s_hz || (vib == 0) != (W.s_vib == 0)) {
    W.e_sine.periodic.magnitude = s16(o.vib);
    W.e_sine.periodic.period = (Uint16)(hz > 0 ? 1000 / hz : 30);
    effect_update(W.fx_sine, &W.e_sine);
    W.s_vib = vib, W.s_hz = hz;
  }
}

void wheel_quit(void) { close_wheel(); }

/* ---- events ---- */

void wheel_event(const SDL_Event *e) {
  switch (e->type) {
  case SDL_JOYDEVICEADDED:
  case SDL_JOYDEVICEREMOVED: W.rescan = 1; break;
  case SDL_JOYAXISMOTION:
    if (e->jaxis.which == W.instance && e->jaxis.axis < AXIS_WHEELS) W.sink.axis(AXIS_W0 + e->jaxis.axis, e->jaxis.value);
    break;
  case SDL_JOYBUTTONDOWN:
  case SDL_JOYBUTTONUP:
    if (e->jbutton.which == W.instance && e->jbutton.button < BP_WHEELS) W.sink.button(BP_W0 + e->jbutton.button, e->type == SDL_JOYBUTTONDOWN);
    break;
  case SDL_JOYHATMOTION:
    if (e->jhat.which == W.instance && e->jhat.hat == 0) { /* the first hat: the D-pad */
      static const struct { int dir, code; } H[4] = { { SDL_HAT_UP, BP_DUP }, { SDL_HAT_DOWN, BP_DDOWN }, { SDL_HAT_LEFT, BP_DLEFT }, { SDL_HAT_RIGHT, BP_DRIGHT } };
      for (int i = 0; i < 4; ++i)
        if ((W.hat & H[i].dir) != (e->jhat.value & H[i].dir)) W.sink.button(H[i].code, (e->jhat.value & H[i].dir) != 0);
      W.hat = e->jhat.value;
    }
    break;
  }
}
