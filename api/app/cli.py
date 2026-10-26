import argparse
from datetime import date

from sqlalchemy.orm import Session

from app.db.engine import engine
from app.services.sponsors.import_aliases import import_aliases
from app.services.sponsors.import_register import import_register


def main() -> None:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest='command', required=True)

    register_parser = commands.add_parser('import-register')
    register_parser.add_argument('csv')
    register_parser.add_argument('--published', required=True)

    aliases_parser = commands.add_parser('import-aliases')
    aliases_parser.add_argument('csv')

    args = parser.parse_args()
    if args.command == 'import-register':
        with Session(engine) as session:
            result = import_register(
                session, args.csv, date.fromisoformat(args.published)
            )
            session.commit()
        print(f'added {result.added}  removed {result.removed}  total {result.total}')
    elif args.command == 'import-aliases':
        with Session(engine) as session:
            result = import_aliases(session, args.csv)
            session.commit()
        print(f'added {result.added}  total {result.total}')


if __name__ == '__main__':
    main()
