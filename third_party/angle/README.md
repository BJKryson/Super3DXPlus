# ANGLE (libEGL.dll, libGLESv2.dll)

The Windows player starts on the graphics driver's own OpenGL ES. On a PC whose driver has none (a virtual machine, remote desktop, a very old or
generic driver) it falls back to these two files, Google's ANGLE, which runs OpenGL ES on top of Direct3D 11. They sit next to `super3dx.exe`
and are not used when the driver has OpenGL ES.

- Version 2.1.27997 (git 1a32f60bea08), 64-bit Windows, taken from a current Chromium/Electron application build. ANGLE needs `d3dcompiler_47.dll`, which Windows 10 and 11 have.
- sha256: `libEGL.dll` c26b0134d9fcceeecb60f64fb3cd7c3dadccc5034d7d4587ed09c265987efa99, `libGLESv2.dll` 1a57fe92349a92e57601589b5fe0ff94b12ad857e8534ef37b20cc7c82c6e2a9
- Source and license: https://chromium.googlesource.com/angle/angle (BSD 3-clause, Copyright 2018 The ANGLE Project Authors).

To update, replace both files with the same version of another build of ANGLE and fix the numbers above.
