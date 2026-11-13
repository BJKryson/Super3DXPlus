"""What the tools need from the system that is not a Python package, found the same way on Windows, Linux and macOS:
a C++ demangler (c++filt, or the `cxxfilt` package) and fonts (any of a list of file names in the usual font folders, or in
the folders named by MT3DX_FONT_DIRS, `;` or `:` separated)."""
import glob
import os
import shutil
import subprocess


def demangle_many(names):
    """the demangled names, as `c++filt -n` gives them (the same count and order); needs c++filt (binutils, on PATH) or `pip install cxxfilt`"""
    names = list(names)
    exe = shutil.which("c++filt") or shutil.which("llvm-cxxfilt")
    if exe:
        out = subprocess.run([exe, "-n"], input="\n".join(names), capture_output=True, text=True).stdout.split("\n")
        return out[:len(names)]
    try:
        import cxxfilt
    except ImportError:
        raise SystemExit("no c++filt on PATH (binutils) and no cxxfilt module: `pip install cxxfilt` (tools/requirements.txt)")
    out = []
    for n in names:
        try:
            out.append(cxxfilt.demangle(n))
        except Exception:
            out.append(n)
    return out


def _font_dirs():
    dirs = [p for p in os.environ.get("MT3DX_FONT_DIRS", "").replace(";", os.pathsep).split(os.pathsep) if p]
    if os.name == "nt":
        dirs += [os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts"), os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Fonts")]
    dirs += ["/usr/share/fonts", "/usr/local/share/fonts", os.path.expanduser("~/.fonts"), os.path.expanduser("~/.local/share/fonts"),
             "/Library/Fonts", "/System/Library/Fonts", "/System/Library/Fonts/Supplemental", os.path.expanduser("~/Library/Fonts")]
    return dirs


def find_font(*names):
    """the first existing font file among `names` (file names, case-insensitive, or absolute paths), searched in the font folders"""
    for n in names:
        if os.path.isabs(n) and os.path.exists(n):
            return n
    for d in _font_dirs():
        for n in names:
            if os.path.isabs(n):
                continue
            for p in glob.glob(os.path.join(d, "**", n), recursive=True) + glob.glob(os.path.join(d, "**", n.lower()), recursive=True):
                return p
    raise SystemExit("no font found: tried %s (put one in a folder named by MT3DX_FONT_DIRS)" % ", ".join(names))
