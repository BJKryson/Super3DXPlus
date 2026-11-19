# ANGLE (libEGL.dll, libGLESv2.dll)

The Windows player starts on the graphics driver's own OpenGL ES. On a PC whose driver has none (a virtual machine, remote desktop, a very old or
generic driver) it falls back to these two files, Google's ANGLE, which runs OpenGL ES on top of Direct3D 11. They sit next to `super3dx.exe`
and are not used when the driver has OpenGL ES.

- Version 2.1.28066 (git bfdad9d663f7), 64-bit Windows. ANGLE needs `d3dcompiler_47.dll`, which Windows 10 and 11 have.
- Google's repository (https://github.com/google/angle, https://chromium.googlesource.com/angle/angle) publishes source only, no binaries. These are the two files from the official
  Electron release **v43.8.12** (`electron-v43.8.12-win32-x64.zip` from https://github.com/electron/electron/releases/tag/v43.8.12, whose SHA-256 `5af2194e6b86fcad6d9f66d0a9c2158fecceaf1bd9518f43e68bd629dd3f6b9d` matches the release's `SHASUMS256.txt`), unchanged.
- sha256: `libEGL.dll` 9c944cf72e4e557a1eecdc69b9a478235ae80e6b1ea7652b4ba9c655bb9aa053, `libGLESv2.dll` 26d1a2adbf3d66be28604b245469ed58a69587a4ed51354a2bf380216df8163a
- License: BSD 3-clause, Copyright 2018 The ANGLE Project Authors (the Chromium licenses are in that zip's `LICENSES.chromium.html`).

To update, take both files from a newer Electron release that still ships them (Electron 44 and later build ANGLE into the program) and fix the numbers above.
