#!/usr/bin/env python3
"""Regenerate css/main.min.css from css/main.css using Python's standard library.

Put this file in the project's tools directory. Run:
    python3 tools/minify_css.py
    python3 tools/minify_css.py --check

This conservative helper reduces whitespace only. It preserves comments,
strings, CSS escapes, selector order and property values. It does not perform
structural optimisations or replace a CSS validator.
"""

import argparse
from pathlib import Path
import re
import sys
import tempfile


TOKENS = re.compile(
    r'''/\*[\s\S]*?\*/|"(?:\\[\s\S]|[^"\\])*"|'(?:\\[\s\S]|[^'\\])*'|\\(?:[0-9a-fA-F]{1,6}(?:\r\n|[ \t\r\n\f])?|[^\r\n\f])|\s+|[^\s"']'''
)


def minify(source):
    tokens = TOKENS.findall(source)
    if ''.join(tokens) != source:
        raise ValueError('Unclosed quoted string or unsupported input; no output written.')
    result = []
    for i, token in enumerate(tokens):
        if not token.isspace():
            result.append(token)
            continue
        previous = tokens[i - 1] if i else ''
        following = tokens[i + 1] if i + 1 < len(tokens) else ''
        if not previous or not following:
            continue
        if previous in ('{', '}', ';', ',', ':') or following in ('{', '}', ';', ','):
            continue
        result.append(' ')
    output = ''.join(result) + '\n'
    # Guard against accidentally changing tokens or their order.
    original_tokens = [t for t in tokens if not t.isspace()]
    output_tokens = [t for t in TOKENS.findall(output) if not t.isspace()]
    if original_tokens != output_tokens:
        raise ValueError('Token verification failed; no output written.')
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Check freshness without writing files.')
    args = parser.parse_args()
    project = Path(__file__).resolve().parent.parent
    source_path = project / 'css' / 'main.css'
    output_path = project / 'css' / 'main.min.css'
    try:
        source = source_path.read_text(encoding='utf-8')
        output = minify(source)
        if args.check:
            if not output_path.exists() or output_path.read_bytes() != output.encode('utf-8'):
                print('main.min.css is missing or out of date. Run python3 tools/minify_css.py')
                return 1
            print('main.min.css matches main.css.')
            return 0
        # Replace the output only after the entire generated file is ready.
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='\n',
                    dir=output_path.parent, prefix='.main-min-', delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(output)
            temporary.chmod(0o644)
            temporary.replace(output_path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        original_size = len(source.encode('utf-8'))
        final_size = len(output.encode('utf-8'))
        print(f'Wrote css/main.min.css: {original_size:,} -> {final_size:,} bytes '
              f'({original_size-final_size:,} bytes saved).')
        print('css/main.css was not changed.')
        return 0
    except (OSError, ValueError) as error:
        print(f'Could not generate stylesheet: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
