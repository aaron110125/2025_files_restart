"""
Helper script used by test_startup.py to load app.py with a mocked boto3 client
and print the resolved module-level variables.

Usage:
    python _helper_print_app_vars.py <app_path> <var_name>

The script patches boto3.client so no real AWS connection is attempted.
"""

import importlib.util
import os
import sys
import unittest.mock

app_path = sys.argv[1]
var_name = sys.argv[2]

with unittest.mock.patch("boto3.client"):
    spec = importlib.util.spec_from_file_location("app", app_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    print(getattr(mod, var_name))
