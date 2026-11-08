# SilkJS debug parser stack reproducer

Upstream report: [silkjs#780](https://github.com/julia-script/silkjs/issues/780).

This standalone `Engine<NoHostServices>` uses pristine SilkJS and its default
1 MiB stack budget. It compiles a JavaScript function with 40 `else if` branches.
On macOS arm64 with Silk dev.61, an unoptimized build exits 1 with
`InternalError: stack overflow`; the speed-optimized build exits 0 with
`compile succeeded`. No runtime compatibility patches are involved.

From the runtime repository root, copy the probe into a temporary directory:

```sh
repro_dir=$(mktemp -d)
cp tools/repros/silkjs-debug-stack/main.silk tools/repros/silkjs-debug-stack/silk.toml "$repro_dir/"
git clone https://github.com/julia-script/silkjs "$repro_dir/silkjs"
git -C "$repro_dir/silkjs" checkout c8c320bb4839217d29a45a215c4362da334c6e2f
cd "$repro_dir"
silk build main.silk -o probe-debug --optimization none --debug true
./probe-debug
silk build main.silk -o probe-speed --optimization speed --debug true
./probe-speed
```

On macOS, use a compatible SDK if required by the pinned compiler, for example
`export SDKROOT=/Library/Developer/CommandLineTools/SDKs/MacOSX15.5.sdk`.

The runtime's separate embedding fix gives the main isolate up to 4 MiB, bounded
by the available native stack. This makes ordinary debug REPL startup work; it
does not reduce the engine's parser frames or override explicit worker limits.
