Usage
=====

Running locally
---------------

Install the project and launch the desktop application:

.. code-block:: bash

   uv sync
   uv run plutus

On first launch, Plutus prompts for the SQLite database file location and
reuses that saved path on later launches.

Building a distributable
------------------------

Build the desktop binary with PyInstaller:

.. code-block:: bash

   uv run pyinstaller plutus.spec

The generated application will be placed under ``dist/`` as ``plutus`` on Linux,
``plutus.exe`` on Windows, or ``Plutus.app`` on macOS.
