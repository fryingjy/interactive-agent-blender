"""Isolated file-based entry point. No sockets or unrestricted code requests."""
import json
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from modeler.runtime import edit, inspect
from modeler.render import render


def main():
    source, request_path, report_path, *outputs = sys.argv[sys.argv.index('--') + 1:]
    report = Path(report_path)
    if report.exists():
        raise ValueError('Report already exists; use a new path')
    request = json.loads(Path(request_path).read_text(encoding='utf-8'))
    mutation = request['action'] not in {'inspect', 'render'}
    output = Path(outputs[0]) if len(outputs) == 1 else None
    if mutation and (output is None or output.exists() or output.suffix != '.blend'):
        raise ValueError('Edits require a new .blend output path')
    if not mutation and outputs:
        raise ValueError('Inspection cannot save a scene')
    if output and output.resolve() == report.resolve():
        raise ValueError('Report and scene paths must differ')
    bpy.ops.wm.open_mainfile(filepath=str(Path(source).resolve()), use_scripts=False)
    if request['action'] == 'inspect':
        if set(request) != {'action', 'object'}:
            raise ValueError('Unexpected inspect fields')
        result = inspect(request['object'])
    elif request['action'] == 'render':
        if Path(request['path']).resolve() == report.resolve():
            raise ValueError('Render and report paths must differ')
        result = render(request)
    else:
        result = edit(request)
    if mutation:
        output.parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(output.resolve()))
    report.parent.mkdir(parents=True, exist_ok=True)
    with report.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)


if __name__ == '__main__':
    main()
