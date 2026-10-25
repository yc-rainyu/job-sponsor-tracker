import argparse
from datetime import date

from sqlalchemy.orm import Session

from app.db.engine import engine
from app.services.sponsors.import_aliases import import_aliases
from app.services.sponsors.import_register import import_register


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='cmd', required=True)

    import_register_p = sub.add_parser('import-register')
    import_register_p.add_argument('csv')
    import_register_p.add_argument('--published', required=True)

    import_aliases_p = sub.add_parser('import-aliases')
    import_aliases_p.add_argument('csv')

    args = parser.parse_args()
    if args.cmd == 'import-register':
        with Session(engine) as session:
            result = import_register(
                session, args.csv, date.fromisoformat(args.published)
            )
            session.commit()
        print(f'added {result.added}  removed {result.removed}  total {result.total}')
    elif args.cmd == 'import-aliases':
        with Session(engine) as session:
            result = import_aliases(session, args.csv)
            session.commit()
        print(f'added {result.added}  total {result.total}')


if __name__ == '__main__':
    main()
