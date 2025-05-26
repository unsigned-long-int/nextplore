from typing import List


def read_stdin_stream() -> str:
    print('enter your query (Press Enter on an empty line to finish):')
    print('you can enter multiple lines. press Enter on an empty line when done.\n')

    lines: List[str] = []

    while True:
        line = input('>>> ')
        if not line:
            break
        lines.append(line)

    stream = '\n'.join(lines)
    return stream
