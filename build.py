#!/usr/bin/env python3
"""Builds the player. One script for Windows, Linux (also the Raspberry Pi) and macOS: Python 3.9+ and a C compiler, no WSL.

    python build.py doctor                       what is installed, what is missing and how to get it
    python build.py data <arcade root>           gen + convert: the tables, the recompiled physics and the game's data (data/)
    python build.py exe [--target T] [--cc CC]   the player: build/<target>/super3dx[.exe]
    python build.py package [--target T]         build/<target>/ with the player, its libraries, data/ and play.bat/play.sh, to zip up
    python build.py all <arcade root>            data, exe and package in one go

Targets: `windows` (default on Windows), `linux` (default elsewhere; the Raspberry Pi 5 is the same build, made on the Pi or
with --target pi from another machine with a sysroot, see docs/PI.md).

Compilers, in the order tried unless you pass --cc: for windows `zig cc` (one download from ziglang.org, no installer; `python
build.py setup-zig` fetches it into .super3dx/), then mingw-w64's x86_64-w64-mingw32-gcc (MSYS2, or Linux); for linux gcc or clang.
The Windows build also needs the SDL2 development files for mingw (`python build.py setup-sdl2`, or SDL2_DIR=<...>/x86_64-w64-mingw32).
zlib and the OpenGL ES headers are in third_party/ and need nothing installed.
"""
import argparse
import concurrent.futures
import glob
import hashlib
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(ROOT, ".super3dx")  # downloaded toolchain pieces (git-ignored)
SDL_VER = "2.30.9"
ZIG_VER = "0.17.1"
ZIG = {  # (url, sha256) from ziglang.org/download/index.json
    "x86_64-windows": ("https://ziglang.org/download/%s/zig-x86_64-windows-%s.zip" % (ZIG_VER, ZIG_VER), "b03f477a1943673e02aca0f570e8030dffd536ce1f45cbc4d3326ec31159562e"),
    "x86_64-linux": ("https://ziglang.org/download/%s/zig-x86_64-linux-%s.tar.xz" % (ZIG_VER, ZIG_VER), "3581863e3cbcfd0fce0efc682ce7e9e93da96668a977791d356a26d2a7e9b17a"),
    "aarch64-linux": ("https://ziglang.org/download/%s/zig-aarch64-linux-%s.tar.xz" % (ZIG_VER, ZIG_VER), "a1546d5646eb184437918d6635ca6b762a0e889eac09cef720ee7a1ed3fe7795"),
    "x86_64-macos": ("https://ziglang.org/download/%s/zig-x86_64-macos-%s.tar.xz" % (ZIG_VER, ZIG_VER), "9af07b20319fbd0c92ee46ad23e81d6a782b1aaea2cfb8dcbff35f1d2c7ddbb7"),
    "aarch64-macos": ("https://ziglang.org/download/%s/zig-aarch64-macos-%s.tar.xz" % (ZIG_VER, ZIG_VER), "75f1bc7a1e9852f17ec9a0c1895f767c4ec56d46bc8a834920eece1d0359dd8d"),
}
SRCS = ("platform/sdl2/main_sdl.c platform/sdl2/bgm.c platform/sdl2/movie.c src/app.c src/render.c src/hud.c src/car.c src/collide.c src/sound.c "
        "src/anm.c src/menu.c src/bind.c src/lights.c src/spark.c src/haptic.c src/net.c src/vs_host.c src/nat.c src/title.c src/phys/rc_runtime.c").split()
GENERATED = ["src/phys/phys_rc.c", "src/phys/rc_addr.h", "src/cardb.h"]


def say(*a):
    print(*a, flush=True)


def die(msg):
    sys.exit("build.py: " + msg)


def which(*names):
    for n in names:
        p = shutil.which(n)
        if p:
            return p
    return None


# --------------------------------------------------------------------------------------------- downloads (setup-*)
def download(url, dest, sha256=None):
    say("downloading", url)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with urllib.request.urlopen(url, timeout=60) as r, open(dest + ".part", "wb") as f:
        shutil.copyfileobj(r, f)
    if sha256:
        h = hashlib.sha256(open(dest + ".part", "rb").read()).hexdigest()
        if h != sha256:
            os.remove(dest + ".part")
            die("the download's SHA-256 is %s, expected %s" % (h, sha256))
    os.replace(dest + ".part", dest)


def setup_zig():
    arch = {"amd64": "x86_64", "x86_64": "x86_64", "arm64": "aarch64", "aarch64": "aarch64"}.get(platform.machine().lower())
    os_ = {"Windows": "windows", "Linux": "linux", "Darwin": "macos"}.get(platform.system())
    if not arch or not os_ or "%s-%s" % (arch, os_) not in ZIG:
        die("no Zig download for this machine: install a C compiler instead (see docs/BUILDING.md)")
    url, sha = ZIG["%s-%s" % (arch, os_)]
    dest = os.path.join(TOOLS, os.path.basename(url))
    out = os.path.join(TOOLS, "zig")
    if not glob.glob(os.path.join(out, "zig*")):
        download(url, dest, sha)
        tmp = os.path.join(TOOLS, "zig.tmp")
        shutil.rmtree(tmp, ignore_errors=True)
        (zipfile.ZipFile(dest) if dest.endswith(".zip") else tarfile.open(dest)).extractall(tmp)
        inner = os.path.join(tmp, os.listdir(tmp)[0])
        shutil.rmtree(out, ignore_errors=True)
        shutil.move(inner, out)
        shutil.rmtree(tmp, ignore_errors=True)
        os.remove(dest)
    say("zig:", find_zig())


def find_zig():
    exe = "zig.exe" if os.name == "nt" else "zig"
    p = os.path.join(TOOLS, "zig", exe)
    return p if os.path.isfile(p) else which("zig")


def setup_sdl2():
    out = os.path.join(TOOLS, "SDL2-%s" % SDL_VER)
    if not os.path.isdir(out):
        url = "https://github.com/libsdl-org/SDL/releases/download/release-%s/SDL2-devel-%s-mingw.zip" % (SDL_VER, SDL_VER)
        dest = os.path.join(TOOLS, "sdl2-mingw.zip")
        download(url, dest)
        zipfile.ZipFile(dest).extractall(TOOLS)
        os.remove(dest)
    say("SDL2 (mingw):", sdl2_mingw())


def sdl2_mingw():
    if os.environ.get("SDL2_DIR"):
        return os.environ["SDL2_DIR"]
    for pat in (os.path.join(TOOLS, "SDL2-*", "x86_64-w64-mingw32"), "/opt/mt3dx/win/SDL2-*/x86_64-w64-mingw32", "/usr/x86_64-w64-mingw32"):
        m = sorted(glob.glob(pat))
        if m and os.path.isdir(os.path.join(m[-1], "include")):
            return m[-1]
    return None


# ------------------------------------------------------------------------------------------------------- compile
class Toolchain:
    """a compiler command (a list), what it makes for, and the flags that depend on it"""

    def __init__(self, target, cc=None):
        self.target = target
        self.kind = None
        if target == "windows":
            if cc:
                self.cc = cc.split()
            elif find_zig():
                self.cc = [find_zig(), "cc", "-target", "x86_64-windows-gnu"]
            elif which("x86_64-w64-mingw32-gcc-posix", "x86_64-w64-mingw32-gcc"):
                self.cc = [which("x86_64-w64-mingw32-gcc-posix", "x86_64-w64-mingw32-gcc")]
            else:
                die("no compiler for Windows: `python build.py setup-zig` (or install mingw-w64, see docs/BUILDING.md)")
            self.kind = "zig" if "zig" in os.path.basename(self.cc[0]).lower() else "gcc"
        else:
            if cc:
                self.cc = cc.split()
            elif target == "pi" and os.environ.get("SYSROOT"):
                self.cc = [(os.environ.get("CROSS", "aarch64-linux-gnu") + "-gcc")]
            else:
                found = which("gcc", "cc", "clang")
                if not found:
                    die("no C compiler: install gcc or clang (see docs/BUILDING.md)")
                self.cc = [found]
            self.kind = "gcc"


def newer(src, dst):
    return not os.path.exists(dst) or os.path.getmtime(src) > os.path.getmtime(dst)


def run(cmd, **kw):
    r = subprocess.run(cmd, **kw)
    if r.returncode:
        die("failed: " + " ".join(cmd[:3]) + " ... (exit %d)" % r.returncode)


def gl_names():
    """the OpenGL ES functions the game calls: its sources' gl* words that the GLES2 headers declare"""
    declared = set()
    for h in glob.glob(os.path.join(ROOT, "third_party", "khronos", "GLES2", "*.h")):
        declared |= set(re.findall(r"\b(gl[A-Z]\w*)\s*\(", open(h, encoding="utf-8", errors="replace").read()))
    used = set()
    for s in SRCS:
        used |= set(re.findall(r"\b(gl[A-Z]\w*)\b", open(os.path.join(ROOT, s), encoding="utf-8", errors="replace").read()))
    return sorted(used & declared)


def build_exe(target, cc, opt, jobs):
    for f in GENERATED:
        if not os.path.isfile(os.path.join(ROOT, f)):
            die("missing %s: run `python build.py data <arcade root>` first (the tables and the recompiled physics are made from your copy of the game)" % f)
    tc = Toolchain(target, cc)
    win = target == "windows"
    out = os.path.join(ROOT, "build", target)
    obj = os.path.join(out, "obj")
    os.makedirs(obj, exist_ok=True)
    inc = ["-Isrc", "-Isrc/phys", "-Iplatform/sdl2", "-Ithird_party/stb", "-Ithird_party/zlib", "-Ithird_party/khronos"]
    flags = [opt, "-std=gnu99", "-Wall", "-Wno-unused-function", "-ffp-contract=off", "-DRC_FPT=double", "-DWMMT_EGL"]
    link = []
    if win:
        sdl = sdl2_mingw()
        if not sdl:
            die("no SDL2 development files for mingw: `python build.py setup-sdl2` (or set SDL2_DIR)")
        flags += ["-D__USE_MINGW_ANSI_STDIO=1", "-DWMMT_WIN", "-DGL_APICALL=", "-D_POSIX_THREAD_SAFE_FUNCTIONS", "-D_FILE_OFFSET_BITS=64",
                  "-include", "platform/sdl2/winport.h", "-Iplatform/sdl2/winshim", "-I" + os.path.join(sdl, "include", "SDL2")]
        link = ["-L" + os.path.join(sdl, "lib"), "-lmingw32", "-lSDL2main", "-lSDL2", "-lm", "-lws2_32", "-ladvapi32"]
        if tc.kind == "gcc":
            link += ["-static-libgcc", "-Wl,-Bstatic,--whole-archive", "-lwinpthread", "-Wl,--no-whole-archive,-Bdynamic"]
        exe = os.path.join(out, "super3dx.exe")
    else:
        flags += ["-fPIC"]
        if target == "pi":
            flags += ["-mcpu=cortex-a76"] if platform.machine().lower() not in ("aarch64", "arm64") or os.environ.get("SYSROOT") else []
        env = dict(os.environ)
        sysroot = os.environ.get("SYSROOT")
        if sysroot:
            flags += ["--sysroot=" + sysroot]
            env["PKG_CONFIG_SYSROOT_DIR"] = sysroot
            env["PKG_CONFIG_LIBDIR"] = "%s/usr/lib/aarch64-linux-gnu/pkgconfig:%s/usr/share/pkgconfig" % (sysroot, sysroot)
        pkg = which("pkg-config")
        sdlc = sdll = None
        if pkg:
            r = subprocess.run([pkg, "--cflags", "--libs", "sdl2"], capture_output=True, text=True, env=env)
            if r.returncode == 0:
                parts = r.stdout.split()
                sdlc = [p for p in parts if p.startswith(("-I", "-D"))]
                sdll = [p for p in parts if not p.startswith(("-I", "-D"))]
        if sdlc is None and which("sdl2-config"):
            sdlc = subprocess.run(["sdl2-config", "--cflags"], capture_output=True, text=True).stdout.split()
            sdll = subprocess.run(["sdl2-config", "--libs"], capture_output=True, text=True).stdout.split()
        if sdlc is None:
            die("SDL2 development files not found: install libsdl2-dev (and libegl1-mesa-dev, libgles2-mesa-dev), see docs/BUILDING.md")
        flags += sdlc
        link = sdll + ["-lEGL", "-lGLESv2", "-lm", "-lpthread"]
        exe = os.path.join(out, "super3dx")
    cflags = flags + inc
    key = " ".join(tc.cc + cflags)
    kf = os.path.join(out, "cflags.txt")
    if not os.path.exists(kf) or open(kf).read() != key:
        for o in glob.glob(os.path.join(obj, "*.o")):
            os.remove(o)
        open(kf, "w").write(key)

    jobs_list = []  # (source, object, extra flags)
    phys = os.path.join(obj, "phys_rc.o")
    if newer(os.path.join(ROOT, "src/phys/phys_rc.c"), phys) or newer(os.path.join(ROOT, "src/phys/rc_runtime.h"), phys):
        say("compiling the arcade physics (a minute or two)...")
        jobs_list.append(("src/phys/phys_rc.c", phys, ["-w"]))
    objs = [phys]
    hdrs = glob.glob(os.path.join(ROOT, "src", "*.h")) + glob.glob(os.path.join(ROOT, "platform", "sdl2", "*.h")) + glob.glob(os.path.join(ROOT, "src", "phys", "*.h"))
    newest_hdr = max(os.path.getmtime(h) for h in hdrs)
    zl = sorted(glob.glob(os.path.join(ROOT, "third_party", "zlib", "*.c")))
    for s in SRCS + [os.path.relpath(z, ROOT).replace(os.sep, "/") for z in zl]:
        o = os.path.join(obj, s.replace("/", "_") + ".o")
        objs.append(o)
        stale = not os.path.exists(o) or newer(os.path.join(ROOT, s), o) or os.path.getmtime(o) < newest_hdr
        if stale:
            jobs_list.append((s, o, ["-w"] if s.startswith("third_party") else []))

    if win:  # GL: every gl* function the game calls, as a jump through a pointer filled at start (gl_load, after the context)
        names = gl_names()
        tramp, load = os.path.join(out, "gl_tramp.S"), os.path.join(out, "gl_load.c")
        with open(tramp, "w", newline="\n") as f:
            f.write("/* generated by build.py: GL entry points as trampolines */\n.text\n")
            for n in names:
                f.write(".globl %s\n%s:\n\tjmp *p_%s(%%rip)\n" % (n, n, n))
            f.write(".bss\n")
            for n in names:
                f.write(".globl p_%s\np_%s: .quad 0\n" % (n, n))
        with open(load, "w", newline="\n") as f:
            f.write("/* generated by build.py */\n#include <SDL.h>\n")
            for n in names:
                f.write("extern void *p_%s;\n" % n)
            f.write("int gl_load(void) {\n  int missing = 0;\n")
            for n in names:
                f.write('  if (!(p_%s = SDL_GL_GetProcAddress("%s"))) { missing++; if (missing < 6) SDL_Log("GL: no %s"); }\n' % (n, n, n))
            f.write("  return missing;\n}\n")
        jobs_list.append((tramp, os.path.join(obj, "gl_tramp.o"), []))
        jobs_list.append((load, os.path.join(obj, "gl_load.o"), []))
        objs += [os.path.join(obj, "gl_tramp.o"), os.path.join(obj, "gl_load.o")]

    def compile_one(job):
        s, o, extra = job
        src = s if os.path.isabs(s) else os.path.join(ROOT, s)
        cmd = tc.cc + ["-c", src, "-o", o] if src.endswith(".S") else tc.cc + cflags + extra + ["-c", src, "-o", o]  # (an assembly file takes none of the C flags)
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        return s, r

    say("%s: %d files to compile with %s" % (target, len(jobs_list), " ".join(tc.cc)))
    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as ex:
        failed = False
        for s, r in ex.map(compile_one, jobs_list):
            if r.returncode:
                failed = True
                sys.stderr.write("--- %s\n%s%s\n" % (s, r.stdout, r.stderr))
            elif r.stderr.strip() and "-Wall" in " ".join(cflags):
                pass
        if failed:
            die("compile errors above")
    cmd = tc.cc + [o for o in objs] + ["-o", exe] + link
    run(cmd, cwd=ROOT)
    if win:
        shutil.copyfile(os.path.join(sdl2_mingw(), "bin", "SDL2.dll"), os.path.join(out, "SDL2.dll"))
    say("built", exe)
    return exe


# -------------------------------------------------------------------------------------------------------- package
def package(target):
    out = os.path.join(ROOT, "build", target)
    exe = os.path.join(out, "super3dx.exe" if target == "windows" else "super3dx")
    if not os.path.isfile(exe):
        die("no player: python build.py exe --target %s" % target)
    data = os.path.join(ROOT, "data")
    if not os.path.isdir(data):
        die("no data/: python build.py data <arcade root>")
    pk = os.path.join(out, "package")
    shutil.rmtree(pk, ignore_errors=True)
    os.makedirs(pk)
    shutil.copy(exe, pk)
    if target == "windows":
        shutil.copy(os.path.join(out, "SDL2.dll"), pk)
        open(os.path.join(pk, "play.bat"), "w", newline="\r\n").write(
            '@echo off\nrem Optional: super3dx.exe can be double-clicked as it is. This one adds options, e.g. play.bat --size 1600x1200 (the layout is 4:3); saves go to the save folder.\n'
            'cd /d "%~dp0"\nif not exist save mkdir save\nsuper3dx.exe "%~dp0data" --save "%~dp0save" %*\n')
    else:
        p = os.path.join(pk, "play.sh")
        open(p, "w", newline="\n").write('#!/bin/sh\ncd "$(dirname "$0")"\nmkdir -p save\nexec ./super3dx data --save save "$@"\n')
        os.chmod(p, 0o755)
    say("copying data/ (it is large)...")
    shutil.copytree(data, os.path.join(pk, "data"))
    open(os.path.join(pk, "README.txt"), "w").write(
        "Super3DX+ (see the project's README): the player and the game's data, converted from your own copy of the arcade game.\n"
        "For personal use: the data is the arcade's, do not share it.\n")
    say("package:", pk, "(zip this folder to move it)")


# --------------------------------------------------------------------------------------------------------- doctor
def doctor():
    ok = True

    def line(name, found, hint):
        nonlocal ok
        say("  %-26s %s" % (name, found if found else "MISSING - " + hint))
        ok &= bool(found)

    say("python:", sys.version.split()[0], sys.executable)
    for m in ("capstone", "unicorn", "PIL", "numpy"):
        try:
            __import__(m)
            line("python module " + m, "ok", "")
        except ImportError:
            line("python module " + m, None, "pip install -r tools/requirements.txt")
    line("c++filt or cxxfilt", which("c++filt", "llvm-cxxfilt") or ("cxxfilt module" if _has("cxxfilt") else None), "pip install cxxfilt")
    line("ffmpeg (for the sound/movies)", os.environ.get("FFMPEG") or which("ffmpeg"), "a full build with the Bink decoder: winget install Gyan.FFmpeg, apt install ffmpeg")
    say("compilers:")
    line("zig", find_zig(), "python build.py setup-zig")
    line("mingw-w64 gcc", which("x86_64-w64-mingw32-gcc-posix", "x86_64-w64-mingw32-gcc"), "MSYS2 (pacman -S mingw-w64-x86_64-gcc) or apt install gcc-mingw-w64-x86-64-posix")
    line("gcc / clang", which("gcc", "clang", "cc"), "apt install build-essential")
    line("SDL2 for mingw", sdl2_mingw(), "python build.py setup-sdl2")
    line("SDL2 (Linux dev files)", which("sdl2-config") or (which("pkg-config") and subprocess.run([which("pkg-config"), "--exists", "sdl2"]).returncode == 0 and "pkg-config"), "apt install libsdl2-dev libegl1-mesa-dev libgles2-mesa-dev")
    say("Windows needs one of (zig, mingw-w64) plus SDL2 for mingw; Linux needs gcc/clang plus the SDL2 dev files. The rest is for the data.")


def _has(mod):
    try:
        __import__(mod)
        return True
    except ImportError:
        return False


def pipeline(*args):
    run([sys.executable, os.path.join(ROOT, "tools", "pipeline.py")] + list(args), cwd=ROOT)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["doctor", "setup-zig", "setup-sdl2", "data", "exe", "package", "all"])
    ap.add_argument("arcade", nargs="?", help="the arcade dump: a folder with main and data/ (for data and all)")
    ap.add_argument("--target", choices=["windows", "linux", "pi"], default="windows" if os.name == "nt" else "linux")
    ap.add_argument("--cc", help="the C compiler command to use (e.g. 'zig cc -target x86_64-windows-gnu')")
    ap.add_argument("-O", dest="opt", default="-O2", help="the optimisation flag (-O1 compiles quicker)")
    ap.add_argument("-j", dest="jobs", type=int, default=os.cpu_count() or 2, help="compiler processes at once")
    ap.add_argument("--no-media", action="store_true", help="data: skip the sounds, music and movies")
    a = ap.parse_args()
    if a.cmd == "doctor":
        doctor()
    elif a.cmd == "setup-zig":
        setup_zig()
    elif a.cmd == "setup-sdl2":
        setup_sdl2()
    elif a.cmd in ("data", "all"):
        if not a.arcade:
            die("%s needs the arcade dump folder" % a.cmd)
        pipeline("gen", a.arcade, "--phys")
        pipeline("convert", a.arcade, *(["--no-media"] if a.no_media else []))
    if a.cmd in ("exe", "all"):
        build_exe(a.target, a.cc, a.opt, a.jobs)
    if a.cmd in ("package", "all"):
        package(a.target)


if __name__ == "__main__":
    main()
