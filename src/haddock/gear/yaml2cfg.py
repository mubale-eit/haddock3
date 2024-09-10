"""
Parse data from HADDOCK3 to YAML and YAML to HADDOCK3 and related.

Accross this file you will see references to "yaml" as variables and
function names. In these cases, we always mean the HADDOCK3 YAML
configuration files which have specific keys.
"""

import os
from pathlib import Path
from haddock import config_expert_levels, _hidden_level
from haddock.libs.libio import read_from_yaml
from haddock.core.exceptions import ConfigurationError
from haddock.core.typing import (
    Union,
    ParamDict,
    ParamMap,
    Mapping,
    )


def yaml2cfg_text(
        ymlcfg: dict, module: str, explevel: str, details: bool = False
        ) -> str:
    """
    Convert HADDOCK3 YAML config to HADDOCK3 user config text.

    Adds commentaries with help strings.

    Parameters
    ----------
    ymlcfg : dict
        The dictionary representing the HADDOCK3 config file.

    module : str
        The module to which the config belongs to.

    explevel : str
        The expert level to consider. Provides all parameters for that
        level and those of inferior hierarchy. If you give "all", all
        parameters will be considered.

    details : bool
        Whether to add the 'long' description of each parameter.
    """
    new_config: list[str] = []
    if module is not None:
        new_config.append(f"[{module}]")

    new_config.append(
        _yaml2cfg_text(
            ymlcfg,
            module,
            explevel,
            details=details,
            )
        )

    return os.linesep.join(new_config) + os.linesep


def _yaml2cfg_text(
        ymlcfg: dict, module: str, explevel: str, details: bool = False
        ) -> str:
    """
    Convert HADDOCK3 YAML config to HADDOCK3 user config text.

    Does not consider expert levels.
    See :func:`yaml2cfg_text_with_explevels` instead.

    Parameters
    ----------
    ymlcfg : dict
        The dictionary representing the HADDOCK3 YAML configuration.
        This configuration should NOT have the expertise levels. It
        expectes the first level of keys to be the parameter name.

    module : str
        The module to which the config belongs to.

    explevel : str
        The expert level to consider. Provides all parameters for that
        level and those of inferior hierarchy. If you give "all", all
        parameters will be considered.

    details : bool
        Whether to add the 'long' description of each parameter.
    """
    params: list[str] = []
    exp_levels = {
        _el: i for i, _el in enumerate(
            config_expert_levels + ("all", _hidden_level)
            )
        }
    exp_level_idx = exp_levels[explevel]

    # define set of undesired parameter keys
    undesired = ("default", "explevel", "type")
    if not details:
        undesired = undesired + ("long",)  # type: ignore

    for param_name, param in ymlcfg.items():
        # treats parameters that are subdictionaries of parameters
        if isinstance(param, Mapping) and "default" not in param:
            params.append("")  # give extra space
            if module is not None:
                curr_module = f"{module}.{param_name}"
            else:
                curr_module = param_name
            params.append(f"[{curr_module}]")
            _ = _yaml2cfg_text(
                param,  # type: ignore
                module=curr_module,
                explevel=explevel,
                details=details,
                )
            params.append(_)

        # treats normal parameters
        elif isinstance(param, Mapping):
            if exp_levels[param["explevel"]] > exp_level_idx:
                # ignore this parameter because is of an expert level
                # superior to the one request:
                continue

            comment: list[str] = []
            for _comment, cvalue in param.items():
                if _comment in undesired:
                    continue

                if cvalue == "":
                    continue

                comment.append(f"${_comment} {cvalue}")

            default_value = param["default"]

            # boolean values have to be lower for compatibility with toml cfg
            if isinstance(default_value, bool):
                default_value = str(default_value).lower()
                param_line = "{} = {}  # {}"
            else:
                param_line = "{} = {!r}  # {}"

            params.append(
                param_line.format(
                    param_name,
                    default_value,
                    " / ".join(comment),
                    )
                )

            if param["type"] == "list":
                params.append(os.linesep)

        else:
            # ignore some other parameters that are defined for sections.
            continue

    return os.linesep.join(params)


def read_from_yaml_config(
        cfg_file: Union[Path, str], default_only: bool = True
        ) -> dict:
    """Read config from yaml by collapsing the expert levels.

    Parameters
    ----------
    cfg_file :
        Path to a .yaml configuration file
    default_only : bool
        Set the return value of this function; if True (default value), only
        returns default values, else return the fully loaded configuration file

    Return
    ------
    ycfg : dict
        The full default configuration file as a dict
    OR
    cfg : dict
        A dictionary containing only the default parameters values
    """
    ycfg = read_from_yaml(cfg_file)
    if default_only:
        # there's no need to make a deep copy here, a shallow copy suffices.
        cfg = {}
        cfg.update(flat_yaml_cfg(ycfg))
        return cfg
    return ycfg


def flat_yaml_cfg(cfg: ParamMap) -> ParamDict:
    """Flat a yaml config."""
    new: ParamDict = {}
    for param, values in cfg.items():
        try:
            new_value = values["default"]
        except KeyError:
            new_value = flat_yaml_cfg(values)
        except TypeError:
            # happens when values is a string for example,
            # addresses `explevel` in `mol*` topoaa.
            continue
        else:
            # coordinates with tests.
            # users should not edit yaml files. So this error triggers
            # only during development
            if "explevel" not in values:
                emsg = f"`explevel` not defined for: {param!r}"
                raise ConfigurationError(emsg)

        new[param] = new_value

    return new


def find_incompatible_parameters(yaml_file: Path) -> dict[str, ParamDict]:
    """
    Reads a YAML configuration file and identifies nodes containing the 'incompatible' key.

    This function takes the path to a YAML file, reads its contents, and searches for nodes
    that include an 'incompatible' key. It returns a dictionary where each key is a node name
    and each value is another dictionary representing the 'incompatible' parameters for that node.

    Parameters
    ----------
    yaml_file : Path
        The path to the YAML file to be read.

    Return
    ------
    incompatible_parameters : dict[str, dict[str, str]]
        A dictionary with node names as keys and their corresponding
        'incompatible' parameters as values.
    """
    config = read_from_yaml(yaml_file=yaml_file)

    # Go over each node and see which contains the `incompatible` key
    incompatible_parameters = {}
    for node, values in config.items():
        if "incompatible" in values:
            incompatible_parameters[node] = values["incompatible"]
    return incompatible_parameters
