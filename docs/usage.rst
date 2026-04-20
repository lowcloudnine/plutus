Usage
=====

Running locally
---------------

Install the project and launch the desktop application:

.. code-block:: bash

   python -m pip install -e .
   plutus

Building a distributable
------------------------

Build the desktop binary with PyInstaller:

.. code-block:: bash

   pyinstaller plutus.spec

The generated application will be placed under ``dist/``.
