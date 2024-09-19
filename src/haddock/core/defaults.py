"""All default parameters used by the framework."""

import importlib.resources
import os
import string
import sys
from pathlib import Path

import yaml
from pkg_resources import resource_filename

import haddock
from haddock import core_path, log


BINARY_DIR = Path(importlib.resources.files(haddock) / "bin")  # type: ignore

cns_exec = Path(resource_filename("haddock", "bin/cns_"))
if not cns_exec.exists():
    log.warning("CNS executable not found at %s", cns_exec)
    _cns_exec = os.environ.get("CNS_EXEC")
    if _cns_exec is None:
        log.error(
            "Please define the location the CNS binary by setting a CNS_EXEC system variable"
        )
        sys.exit(1)
    else:
        cns_exec = Path(_cns_exec)

CONTACT_FCC_EXEC = Path(resource_filename("haddock", "bin/contact_fcc"))
FAST_RMSDMATRIX_EXEC = Path(resource_filename("haddock", "bin/fast-rmsdmatrix"))

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
