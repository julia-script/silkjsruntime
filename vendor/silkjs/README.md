# SilkJS compatibility

The pinned SilkJS source already targets Silk `0.1.0-dev.61+91f335268900`.
`runtime-compat.patch` preserves the runtime integrations described below;
compiler-version and explicit-lifetime patches are no longer needed.

These patches are unresolved upstream blockers for the dependency-upgrade PR,
not the intended build arrangement. Do not add further engine compatibility
patches here: report the limitation upstream, use its supported API or fix, and
pin the upstream revision. Remove these hunks before merging the upgrade once
their regression tests pass against unmodified dependencies.

| Requirement | Upstream report | Removal check |
| --- | --- | --- |
| Compatible Darwin event declarations | [silkjs#783](https://github.com/julia-script/silkjs/issues/783) | SilkJS events and Silk's Reactor compile together without a C forwarding shim. |
| Stable allocation-realm information | [silkjs#784](https://github.com/julia-script/silkjs/issues/784) | Cross-realm stack tests pass for null/replaced prototypes and retained contexts using a supported API. |
| Syntax origin with Node stack hooks | [silkjs#785](https://github.com/julia-script/silkjs/issues/785) | VM syntax-error filename, source line and caret tests pass. |

The separate debug parser stack limitation is tracked in
[silkjs#780](https://github.com/julia-script/silkjs/issues/780); it does not add an
engine patch. This repository does not patch the Silk compiler or standard library.

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
