import itertools

from threading import Event


def spin(done: Event) -> None:
    for char in itertools.cycle(r'\|/-'):

        status = f'\r{char}'
        print(status, end='', flush=True)
        if done.wait(.1):
            break

        blanks = ' ' * len(status)
        print(f'\r{blanks}\r', end='')

    blanks: str = ' ' * len(status)
    print(f'\r{blanks}\r', end='', flush=True)
