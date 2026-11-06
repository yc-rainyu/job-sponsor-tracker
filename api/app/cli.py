import argparse
from datetime import date

from sqlalchemy.orm import Session

from app.db.engine import engine
from app.services.import_applications import RowError, import_applications
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

    applications_parser = commands.add_parser('import-applications')
    applications_parser.add_argument('json')
    applications_parser.add_argument(
        '--user', required=True, help='email of the account'
    )
    applications_parser.add_argument('--dry-run', action='store_true')
    applications_parser.add_argument('--replace', action='store_true')

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
    elif args.command == 'import-applications':
        with Session(engine) as session:
            try:
                result = import_applications(
                    session,
                    args.json,
                    args.user,
                    replace=args.replace,
                    dry_run=args.dry_run,
                )
            except (RowError, LookupError, RuntimeError) as exc:
                parser.exit(1, f'error: {exc}\n')
            if not args.dry_run:
                session.commit()
        verb = 'would import' if args.dry_run else 'imported'
        replacing = f' replacing {result.existing}' if result.existing else ''
        print(f'{verb} {result.total} applications for {args.user}{replacing}')
        print(f'by country {result.by_country}')
        print(f'by status {result.by_status}')
        print(f'sponsors linked {result.linked}  not linked {len(result.unlinked)}')
        for name in result.unlinked:
            print(f'  not linked: {name}')


if __name__ == '__main__':
    main()
