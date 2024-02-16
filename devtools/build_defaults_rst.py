"""
Create restructured text pages for module's default parameters.

These pages are then appended to the module's documentation page. See the
`.. include::` statement in the module's `.rst` file in the `docs/` folder.
The created files are save to `docs/modules/*/params/*.rst` files.

The pages generated by this script are not stagged to github. They are used
temporary just to create the HTML files for the documentation.
"""
import os
from collections.abc import Mapping
from pathlib import Path
import shutil

from haddock import haddock3_repository_path, haddock3_source_path
from haddock.core.typing import ParamMap
from haddock.libs.libio import read_from_yaml

MODULE_TITLE_DICT = {
    "topoaa": "All-atom topology module",
    "rigidbody": "Rigid body docking sampling module",
    "lightdock": "LightDock sampling module",
    "gdock": "Gdock sampling module",
    "flexref": "Flexible refinement module",
    "mdref": "Water refinement module",
    "emref": "Energy Minimization refinement module",
    "mdscoring": "Molecular Dynamics scoring module",
    "emscoring": "Energy Minimization scoring module",
    "clustfcc": "FCC Clustering module",
    "caprieval": "CAPRI Evaluation module",
    "contactmap": "Contact Map module",
    "clustrmsd": "RMSD Clustering module",
    "rmsdmatrix": "RMSD Matrix calculation module",
    "seletop": "Selection of top models module",
    "seletopclusts": "Selection of top clusters module",
    "alascan": "Alanine Scanning module",
    "ilrmsdmatrix": "Interface Ligand RMSD Matrix calculation module",
    "exit": "Exit module",
}

CATEGORY_TITLE_DICT = {
    "analysis": "Analysis Modules",
    "extras": "Extra Modules",
    "refinement": "Model Refinement Modules",
    "sampling": "Sampling Modules",
    "scoring": "Scoring Modules",
    "topology": "Topology Modules",
}

REFERENCE_TITLE_DICT = {
    "core": "Core Reference",
    "gear": "Gear Reference",
    "libs": "Libs Reference",
    "gear.clean_steps": "Clean output from step folders",
    "gear.config": "Configuration file I/O",
    "gear.expandable_parameters": "Expandable parameters",
    "gear.extend_run": "Start from copy",
    "gear.greetings": "Greetings messages",
    "gear.haddockmodel": "HADDOCK models",
    "gear.parameters": "Parameters helper",
    "gear.prepare_run": "Prepare run",
    "gear.preprocessing": "PDB preprocessing",
    "gear.restart_run": "Restart run",
    "gear.validations": "Validations",
    "gear.yaml2cfg": "YAML configs",
    "gear.zerofill": "Zero fill prefix",
    "libs.libalign": "libalign: sequence and structural alignments",
    "libs.libcli": "libcli: functions helping clients",
    "libs.libclust": "libclust: functions related to clustering",
    "libs.libcns": "libcns: creating CNS files",
    "libs.libfunc": "libfunc: functional-programming helping tools",
    "libs.libhpc": "libhpc: HPC execution functions",
    "libs.libinteractive": "libinteractive: functions related to interactive tasks",
    "libs.libio": "libio: I/O helping functions",
    "libs.liblog": "liblog: Logging helping functions",
    "libs.libmath": "libmath: Math helping functions",
    "libs.libmpi": "libmpi: MPI execution functions",
    "libs.libontology": "libontology: module communication",
    "libs.libparallel": "libparallel: multiprocessing helping functions",
    "libs.libpdb": "libpdb: PDB helping functions",
    "libs.libplots": "libplots: plotting functionalities",
    "libs.librestraints": "librestraints: functions related to restraints",
    "libs.libstructure": "libstructure: functions related to structures",
    "libs.libsubprocess": "libsubprocess: subprocess execution functions",
    "libs.libtimer": "libtimer: timing functions",
    "libs.libutil": "libutil: utility functions",
    "libs.libworkflow": "libworkflow: workflow functions",
    "core.cns_paths": "CNS paths definitions",
    "core.defaults": "Defaults definitions",
    "core.exceptions": "Exceptions",
    "core.supported_molecules": "Supported molecules",
    "core.typing": "typing",
    "mandatory_parameters.rst": "Mandatory Parameters",
}


class HeadingController:
    """
    Control headings.

    reStructured text headings are defined by punctuation characters.

    In HADDOCK3 docs we use the order: '=', '-', '`', '~', '*'.

    The first heading tags is taken by the main docs. Therefore,
    `HeadingController` manages only from the second ('-') onward.

    Read more at: https://thomas-cokelaer.info/tutorials/sphinx/rest_syntax.html#headings
    """  # noqa: E501

    def __init__(self) -> None:
        self.title_headings = ['-', '`', '~', '*']
        self._idx = 0

    @property
    def next(self) -> str:
        """Give the next heading char."""
        return self.title_headings[self._idx + 1]

    @property
    def current(self) -> str:
        """Give the current heading char."""
        return self.title_headings[self._idx]

    def reset(self) -> None:
        """Reset to the first heading."""
        self._idx = 0

    def increase(self) -> None:
        """Increase current heading."""
        self._idx += 1


HEADING = HeadingController()


def change_title(rst_file: Path, title: str) -> None:
    """
    Change the title of the rst file.
    
    Parameters
    ----------
    rst_file : Path
        Path to the rst file.
    title : str
        New title.
    """
    with open(rst_file, 'r') as fin:
        lines = fin.readlines()
    with open(rst_file, 'w') as fout:
        for ln, line in enumerate(lines):
            if ln == 0:
                line = title + os.linesep
            else:
                line = line
            fout.write(line)

def process_category_file(category: str) -> None:
    """
    Process the category file.

    Parameters
    ----------
    category : str
        Category name.
    """
    category_rst = Path(
                haddock3_repository_path,
                'docs',
                f"haddock.modules.{category}.rst"
                )
    target_rst = Path(
        haddock3_repository_path,
        'docs',
        'modules',
        f"{category}",
        "index.rst"
        )
    shutil.move(category_rst, target_rst)
    # change title
    if category in CATEGORY_TITLE_DICT:
        title = CATEGORY_TITLE_DICT[category]
        change_title(target_rst, title)


def process_module_file(category: str, module_name: str) -> None:
    """
    Process the module file.

    Parameters
    ----------
    category : str
        Category name.
    module_name : str
        Module name.
    """
    module_rst = Path(
        haddock3_repository_path,
        'docs',
        f"haddock.modules.{category}.{module_name}.rst"
        )
    target_rst = Path(
        haddock3_repository_path,
        'docs',
        'modules',
        category,
        module_rst.name
        )
    shutil.move(module_rst, target_rst)
    # does the submodule exist?
    submodule_gen = Path(haddock3_repository_path, 'docs').glob(f"haddock.modules.{category}.{module_name}.*.rst")
    submodule_list = list(submodule_gen)
    if len(submodule_list) != 0:
        
        submodule_name = submodule_list[0]
    
        submodule_rst = Path(
            haddock3_repository_path,
            'docs',
            submodule_name
        )
    
        submodule_target_rst = Path(
            haddock3_repository_path,
            'docs',
            'modules',
            category,
            submodule_rst.name
            )
        shutil.move(submodule_rst, submodule_target_rst)
    
    with open(target_rst, 'a') as fout:
        fout.write(
            f"{os.linesep}Default Parameters{os.linesep}"
            f"---------------{os.linesep}"
            f'.. include:: params/{module_name}.rst'
            + os.linesep
            + os.linesep
            )
    # change title
    if module_name in MODULE_TITLE_DICT:
        title = MODULE_TITLE_DICT[module_name]
        change_title(target_rst, title)


# prepare YAML markdown files
def main() -> None:
    """
    Prepare restructured text files from YAML default configs in modules.

    These files are written to the 'docs/' folder but not stagged to
    github. Instead, they are used only by Sphinx to generate the HTML
    documentation pages.
    """
    # uses this pattern instead of importing:
    # from haddock.modules import modules_category
    # to avoid importing dependencies of the haddock modules packages
    pattern = Path('modules', '*', '*', '*.yaml')
    configs = haddock3_source_path.glob(str(pattern))

    processed_categories = []
    # create RST pages for all modules' configuration files.
    for config in configs:
        if "_template" in str(config):
            continue

        module_name = config.parents[0].name
        category = config.parents[1].name
        params = read_from_yaml(config)

        # ignore empty modules - currently topocg for example
        if len(params) == 0:
            continue

        # if the category has not been processed yet, copy the category file
        if category not in processed_categories:

            process_category_file(category)
            
            processed_categories.append(category)

        HEADING.reset()
        HEADING.increase()
        text = build_rst(params)

        params_folder = Path(
            haddock3_repository_path,
            'docs',
            'modules',
            category,
            'params',
            )
        params_folder.mkdir(exist_ok=True)

        with open(Path(params_folder, f'{module_name}.rst'), 'w') as fout:
            fout.write(text)

        # copy the RST file to the new_docs/source/params folder
        process_module_file(category, module_name)

    # Generate general default parameters RST page
    HEADING.reset()
    HEADING.increase()
    general_defaults = Path(haddock3_source_path, 'modules', 'defaults.yaml')
    general_params = read_from_yaml(general_defaults)
    text = build_rst(general_params)
    params_file = Path(
        haddock3_repository_path,
        'docs',
        'modules',
        'general_module_params.rst',
        )

    with open(params_file, 'w') as fout:
        fout.write(text)

    # Generate mandatory parameters RST page
    HEADING.reset()
    mandatory_defaults = Path(haddock3_source_path, 'core', 'mandatory.yaml')
    mandatory_params = read_from_yaml(mandatory_defaults)

    for param in mandatory_params:
        mandatory_params[param]["default"] = \
            "No default assigned, this parameter is mandatory"

    text = build_rst(mandatory_params)
    params_file = Path(
        haddock3_repository_path,
        'docs',
        'reference',
        'core',
        'mandatory_parameters.rst',
        )

    with open(params_file, 'w') as fout:
        fout.write('Mandatory Parameters' + os.linesep)
        fout.write('====================' + os.linesep)
        fout.write(text)

    # now libs, gear and core
    for folder in ("libs", "gear", "core"):
        rst_files = Path(haddock3_repository_path, 'docs').glob(f"haddock.{folder}.*rst")
        for rst_file in rst_files:
            target_rst = Path(
                haddock3_repository_path,
                'docs',
                'reference',
                folder,
                rst_file.name
                )
            shutil.move(rst_file, target_rst)
            title_key = ".".join(rst_file.name.split(".")[1:-1])
            if title_key in REFERENCE_TITLE_DICT:
                title = REFERENCE_TITLE_DICT[title_key]
                change_title(target_rst, title)


def do_text(name: str, param: ParamMap, level: str) -> str:
    """Create text from parameter dictionary."""
    text = [
        f'{name}',
        f'{level * len(name)}',
        '',
        f'| *default*: {param["default"]!r}',
        f'| *type*: {param["type"]}',
        f'| *title*: {param["title"]}',
        f'| *short description*: {param["short"]}',
        f'| *long description*: {param["long"]}',
        f'| *group*: {param.get("group", "No group assigned")}',
        f'| *explevel*: {param["explevel"]}',
        '',
        ]

    return os.linesep.join(text)


def loop_params(config: ParamMap, easy: list[str], expert: list[str],
                guru: list[str]) -> tuple[list[str], list[str], list[str]]:
    """
    Treat parameters for module.

    *Important:* considers that some configuration files can have
    dictionaries with subparameters. However, there should NOT be more
    than one level of nesting in the configuration parameter files.
    """
    # sort parameters by name
    sorted_ = sorted(
        ((k, v) for k, v in config.items()),
        key=lambda x: x[0],
        )

    for name, data in sorted_:

        # case for nested parameters like `mol1` in topoaa
        if isinstance(data, Mapping) and "default" not in data:

            explevel = data["explevel"]
            new_title = [name, HEADING.current * len(name), '']

            if explevel == 'easy':
                easy.extend(new_title)
                sublist = easy
            elif explevel == 'expert':
                expert.extend(new_title)
                sublist = expert
            elif explevel == 'guru':
                guru.extend(new_title)
                sublist = guru
            elif explevel == 'hidden':
                continue
            else:
                emsg = f'explevel {explevel!r} is not expected'
                raise AssertionError(emsg)

            data_text = (
                f'| *title*: {data["title"]}',
                f'| *short description*: {data["short"]}',
                f'| *long description*: {data["long"]}',
                f'| *group*: {data["group"]}',
                f'| *explevel*: {explevel}',
                '',
                )
            sublist.append(os.linesep.join(data_text))

            # create subparameters RST sorted by name
            data_sorted = sorted(
                ((k, v) for k, v in data.items()),
                key=lambda x: x[0],
                )
            for name2, param2 in data_sorted:
                if isinstance(param2, Mapping):
                    text = do_text(
                        f'{name}.{name2}',
                        param2,
                        level=HEADING.next,
                        )
                    sublist.append(text)

        # case for normal parameter
        elif isinstance(data, Mapping):

            explevel = data["explevel"]
            text = do_text(name, data, level=HEADING.current)

            if explevel == 'easy':
                easy.append(text)
            elif explevel == 'expert':
                expert.append(text)
            elif explevel == 'guru':
                guru.append(text)
            elif explevel == 'hidden':
                continue
            else:
                emsg = f'explevel {explevel!r} is not expected'
                raise AssertionError(emsg)
        else:
            emsg = f'Unexpected parameter behaviour: {name!r}'
            raise AssertionError(emsg)

    easy.append('')
    expert.append('')
    guru.append('')

    return easy, expert, guru


def build_rst(module_params: ParamMap) -> str:
    """Build .rst text."""
    easy = ['Easy', HEADING.current * 4, '']
    expert = ["Expert", HEADING.current * 6, '']
    guru = ['Guru', HEADING.current * 4, '']

    HEADING.increase()
    easy, expert, guru = loop_params(module_params, easy, expert, guru)

    doc: list[str] = []
    for list_ in (easy, expert, guru):
        if len(list_) > 4:
            doc.extend(list_)

    text = os.linesep + os.linesep + os.linesep.join(doc)
    return text


if __name__ == "__main__":
    main()
