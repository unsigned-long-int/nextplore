import itertools
import queue

from threading import Event


def spin(progress_queue: queue.Queue[str], done: Event) -> None:
    for char in itertools.cycle(r'\|/-'):
        try:
            progress_step = progress_queue.get_nowait()
        except queue.Empty:
            pass

        status = f'\r{char} {progress_step}'
        print(status, end='', flush=True)
        if done.wait(.1):
            break

        blanks = ' ' * len(status)
        print(f'\r{blanks}\r', end='')

    blanks: str = ' ' * len(status)
    print(f'\r{blanks}\r', end='', flush=True)
