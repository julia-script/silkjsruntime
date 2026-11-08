#!/usr/bin/env python3
"""Debug startup needs parser headroom; recursion must still stop before the OS guard."""
import pathlib
import resource
import subprocess
import sys

executable = str(pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'build/silkjsruntime').resolve())


def run(source, stack_limit=None):
    def restrict_stack():
        _, hard = resource.getrlimit(resource.RLIMIT_STACK)
        resource.setrlimit(resource.RLIMIT_STACK, (stack_limit, hard))

    result = subprocess.run([executable, '-e', source], text=True, capture_output=True,
                            timeout=30, preexec_fn=restrict_stack if stack_limit else None)
    assert result.returncode == 0, (result.returncode, result.stdout, result.stderr)
    assert result.stdout.strip() == 'ok', (result.stdout, result.stderr)


# This is the original failure, without needing a terminal: module compilation
# exhausted the inherited 1 MiB engine budget before a REPL could be constructed.
run("require('node:repl'); console.log('ok')")
run("""
const branches = Array.from({length: 40}, (_, i) =>
  `${i ? 'else ' : ''}if(x===${i})return ${i};`).join('');
const f = new Function('x', branches);
if (f(39) !== 39) throw new Error('compiled function failed');
console.log('ok');
""")

# Reflect.apply forces native interpreter reentry. It must throw a catchable
# stack exception, including when the OS stack is only as large as our 4 MiB cap.
overflow = """
let caught = false;
function recurse() { return Reflect.apply(recurse, null, []); }
try { recurse(); } catch (error) { caught = /stack/i.test(error.message); }
if (!caught || new Function('return 42')() !== 42)
  throw new Error('stack overflow did not recover');
console.log('ok');
"""
run(overflow)
run(overflow, 4 * 1024 * 1024)
print('Stack budget: REPL compilation, parser headroom and overflow recovery passed')
