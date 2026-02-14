import os
import sys

if not __package__:
    # Make CLI runnable from source tree with
    #    python src/package
    package_source_path = os.path.dirname(os.path.dirname(__file__))  # noqa: PTH120
    print(package_source_path)  # noqa: T201
    sys.path.insert(0, package_source_path)
