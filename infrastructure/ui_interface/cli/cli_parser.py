import argparse
import queue

from tabulate import tabulate

from sqlalchemy.orm import sessionmaker
from sqlalchemy import Engine
from threading import Event, Thread
from dataclasses import dataclass

from infrastructure.event_orchestration_service.event_orchestrator import EventOrchestrator
from core.orm_factory import AIORMFactory

from .loading_spinner import spin
from .stdin_streamer import read_stdin_stream


@dataclass
class CLIParser:
    ai_orm_factory: AIORMFactory
    prog_name: str
    description: str
    engine: Engine

    def process_query(self, event_orchestrator: EventOrchestrator) -> None:
        parser = self._setup_parser()
        args = parser.parse_args()
        user_query = args.query

        if not args.query:
            user_query = read_stdin_stream()

        progress_queue = queue.Queue()
        progress_queue.put('providing response...')

        done = Event()
        spinner = Thread(target=spin, args=(progress_queue, done))
        spinner.start()

        orm_model = self.ai_orm_factory.retrieve_orm_model(
            progress_queue=progress_queue,
            query=user_query
        )

        progress_queue.put('requesting data from orm model...')
        Session = sessionmaker(bind=self.engine)
        session = Session()
        sample = session.query(orm_model).all()
        if sample:
            headers = sample[0].__table__.columns.keys()
            table_data = [[getattr(row, column)
                           for column in headers] for row in sample]
            print(f'\n {tabulate(table_data, headers=headers, tablefmt="grid")}')

        done.set()
        spinner.join()

    def _setup_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            prog=self.prog_name,
            description=self.description,
            formatter_class=argparse.MetavarTypeHelpFormatter
        )

        parser.add_argument(
            '-q',
            '--query',
            type=str,
            help='You generic query to request data from server.'
        )

        return parser
