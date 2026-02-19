import asyncio

from tikorgzo.cli.workflow import main


def run() -> None:
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
