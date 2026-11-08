# SilkJS compatibility

The pinned SilkJS source already targets Silk `0.1.0-dev.61+91f335268900`.
`runtime-compat.patch` preserves the runtime integrations described below;
compiler-version and explicit-lifetime patches are no longer needed.

The patch gives the engine's macOS `kevent` declaration a C forwarding shim.
SilkJS allows the kernel to retain registration data; the standard library
declares a stronger no-capture contract for the same symbol. Separate symbols
avoid the compiler's conflicting-declaration error without strengthening the
engine's contract.

The patch also retains each object's allocation realm, with its GC tracing,
release, and heap-snapshot edge. Upstream's prototype-based replacement loses
the realm for null-prototype objects or after a prototype change, breaking the
existing cross-realm `Error.captureStackTrace` tests. Closure cells cached by
bytecode keep their realm along with the bytecode until they are destroyed.

It preserves syntax-error source coordinates when Node stack hooks are enabled,
so VM compilation can render its source line and caret.

`tools/prepare_silkjs.py` verifies the upstream archive checksum before applying
the patch with zero fuzz. It compares an existing source tree with the freshly
patched archive and rejects unexpected changes. A pristine copy of the same
archive can be upgraded automatically to the patched tree.

Remove the corresponding patch sections when upstream supports compatible native
declarations, allocation-realm stack formatting, and syntax-error coordinates.
