"""All default parameters used by the framework."""

import importlib.resources
import string
from pathlib import Path

import yaml

import haddock
from haddock import core_path


BINARY_DIR = Path(importlib.resources.files(haddock) / "bin")  # type: ignore

cns_exec = Path(BINARY_DIR, "cns")
if not cns_exec.exists():
    # This means the CNS binary is not in the default location
    #  and should be set manually in the configuration file
    cns_exec = None


MODULE_PATH_NAME = "step_"
"""
Module input and generated data will be stored in folder starting by
this prefix"""

MODULE_IO_FILE = "io.json"
"""Default name for exchange module information file"""

MAX_NUM_MODULES = 10000
"""Temptative number of max allowed number of modules to execute"""

valid_run_dir_chars = string.ascii_letters + string.digits + "._-/\\"

RUNDIR = "run_dir"
"""Default run directory name."""

INTERACTIVE_RE_SUFFIX = "interactive"
"""Suffix added to interactive haddock3-re runs."""

MODULE_DEFAULT_YAML = "defaults.yaml"
"""Default name of the yaml default parameters file."""

CNS_MODULES = ["rigidbody", "flexref", "emscoring", "mdscoring", "mdref", "emref"]
"""List of CNS modules available in HADDOCK3."""


with open(Path(core_path, "mandatory.yaml"), "r") as fin:
    _ycfg = yaml.safe_load(fin)
max_molecules_allowed = _ycfg["molecules"]["maxitems"]
del _ycfg
