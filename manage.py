#!/usr/bin/env python
import importlib

import os
import sys
import django
from django.conf import settings


# Force settings to run so that the python path is modified
# settings.INSTALLED_APPS  # pylint: disable=pointless-statement


def run():
    """
    Executed during django startup

    NOTE: DO **NOT** add additional code to this method or this file! The Platform Team
          is moving all startup code to more standard locations using Django best practices.
    """

    django.setup()


if __name__ == "__main__":

    run()

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)



