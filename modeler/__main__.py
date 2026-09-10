"""Launch one inspected decision in an isolated Blender process."""
import argparse
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--blender', required=True, type=Path)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--request', required=True, type=Path)
    parser.add_argument('--report', required=True, type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    for path in (args.blender, args.input, args.request):
        if not path.is_file():
            parser.error(f'File not found: {path}')
    command = [str(args.blender.resolve()), '-b', '--factory-startup',
               '--disable-autoexec', '--python-exit-code', '1', '--python',
               str(Path(__file__).with_name('worker.py')), '--',
               str(args.input.resolve()), str(args.request.resolve()),
               str(args.report.resolve())]
    if args.output:
        command.append(str(args.output.resolve()))
    raise SystemExit(subprocess.run(command, timeout=180, check=False).returncode)


if __name__ == '__main__':
    main()
