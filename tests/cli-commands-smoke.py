#!/usr/bin/env python3
"""Exercise command dispatch, generated diagnostics, and argument ownership in the real runtime."""
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile

runtime = str(Path(sys.argv[1] if len(sys.argv) > 1 else 'build/silkjsruntime').resolve())
environment = dict(os.environ, NODE_OPTIONS='', NODE_REPL_HISTORY='')


def run(arguments, *, cwd, input='', status=0):
    result = subprocess.run([runtime, *arguments], cwd=cwd, env=environment, input=input,
                            text=True, capture_output=True, timeout=30)
    assert result.returncode == status, (arguments, result.returncode, result.stdout, result.stderr)
    return result


with tempfile.TemporaryDirectory(prefix='silk-cli-commands-') as directory:
    cwd = Path(directory)
    help_text = run(['--help'], cwd=cwd).stdout
    assert all(command in help_text for command in ('run', 'eval', 'check', 'repl', 'test'))
    assert run(['help', 'run'], cwd=cwd).stdout == run(['run', '--help'], cwd=cwd).stdout
    assert 'script' in run(['run'], cwd=cwd, status=2).stderr
    assert 'code' in run(['eval'], cwd=cwd, status=2).stderr
    assert 'print' in run(['eval', '--pritn', '1'], cwd=cwd, status=2).stderr
    assert 'input-type' in run(['eval', '--input-type', 'invalid', '1'], cwd=cwd, status=2).stderr
    assert run(['version'], cwd=cwd).stdout == run(['--version'], cwd=cwd).stdout
    assert '--require' in run(['--help-options'], cwd=cwd).stdout

    forwarded = ['--help', '', 'two words', "single'quote", '$HOME; echo injected', 'line\nbreak', 'é']
    (cwd / 'args.cjs').write_text('console.log(JSON.stringify(process.argv.slice(2)));')
    (cwd / 'package.json').write_text(json.dumps({'scripts': {
        'capture': shlex.quote(runtime) + ' args.cjs', 'fail': 'exit 7',
    }}))
    for separator in ([], ['--']):
        output = run(['run', 'capture', *separator, *forwarded], cwd=cwd).stdout
        assert json.loads(output) == forwarded, output
    assert json.loads(run(['--run', 'capture', '--', *forwarded], cwd=cwd).stdout) == forwarded
    assert 'Missing script' in run(['run', 'missing'], cwd=cwd, status=1).stderr
    run(['run', 'fail'], cwd=cwd, status=1)

    assert run(['eval', '--print', '6 * 7'], cwd=cwd).stdout == '42\n'
    assert run(['eval', '--input-type', 'module', 'console.log(await Promise.resolve(42))'], cwd=cwd).stdout == '42\n'
    source = 'console.log(JSON.stringify(process.argv.slice(1)))'
    assert json.loads(run(['eval', source, *forwarded], cwd=cwd).stdout) == forwarded
    assert run(['eval', '--print', '--', '-42'], cwd=cwd).stdout == '-42\n'

    (cwd / 'valid.cjs').write_text('throw new Error("must not execute during syntax checking");')
    run(['check', 'valid.cjs'], cwd=cwd)
    run(['check'], cwd=cwd, input='const valid = 1;')
    (cwd / 'invalid.cjs').write_text('const invalid = ;')
    assert 'SyntaxError' in run(['check', 'invalid.cjs'], cwd=cwd, status=1).stderr
    assert run(['-e', 'console.log(42)'], cwd=cwd).stdout == '42\n'
    assert json.loads(run(['args.cjs', *forwarded], cwd=cwd).stdout) == forwarded
    # A script with a command's name is still reachable through an explicit path or --.
    (cwd / 'run').write_text('console.log("file named run");')
    assert run(['./run'], cwd=cwd).stdout == 'file named run\n'
    assert run(['--', 'run'], cwd=cwd).stdout == 'file named run\n'

    (cwd / 'sample.test.cjs').write_text("require('node:test')('command test', () => {});")
    output = run(['test', '--reporter', 'tap', '--name-pattern', 'command', 'sample.test.cjs'], cwd=cwd).stdout
    assert 'command test' in output and '# fail 0' in output, output
    (cwd / 'fail.test.cjs').write_text("require('node:test')('failure', () => { throw new Error('expected'); });")
    run(['test', 'fail.test.cjs'], cwd=cwd, status=1)

print('CLI commands, diagnostics, forwarding, legacy forms, and execution modes passed')
