"""HADDOCK3 rigid-body docking module"""
import logging
from os import linesep
from pathlib import Path
from haddock.modules import BaseHaddockModule
from haddock.cns.engine import CNSJob, CNSEngine
from haddock.cns.util import generate_default_header, load_ambig
from haddock.cns.util import load_workflow_params, prepare_multiple_input
from haddock.ontology import Format, ModuleIO, PDBFile

logger = logging.getLogger(__name__)


def generate_flexref(identifier, input_file, step_path, recipe_str, defaults, ambig=None):
    """Generate the .inp file that will run the docking."""
    # prepare the CNS header that will read the input

    # read the default parameters
    default_params = load_workflow_params(defaults)
    param, top, link, topology_protonation, \
        trans_vec, tensor, scatter, \
        axis, water_box = generate_default_header()

    # for element in input_files:
    pdb = Path(input_file.path, input_file.file_name)
    psf_list = []
    for psf in input_file.topology:
        psf_list.append(Path(psf.path, psf.file_name))

    # pdb_list.append(str(pdb))
    # psf_list.append(str(psf))

    input_str = prepare_multiple_input([pdb], psf_list)

    if ambig:
        ambig_str = load_ambig(ambig)
    else:
        ambig_str = ""

    output_pdb_filename = step_path / f'flexref_{identifier}.pdb'
    output = f"{linesep}! Output structure{linesep}"
    output += (f"eval ($output_pdb_filename="
               f" \"{output_pdb_filename}\"){linesep}")
    inp = default_params + param + top + input_str + output \
        + topology_protonation + ambig_str + recipe_str

    inp_file = step_path / f'flexref_{identifier}.inp'
    with open(inp_file, 'w') as fh:
        fh.write(inp)

    return inp_file


class HaddockModule(BaseHaddockModule):

    def __init__(self, order, path, *ignore, **everything):
        recipe_path = Path(__file__).resolve().parent.absolute()
        cns_script = recipe_path / "cns" / "flexref.cns"
        defaults = recipe_path / "cns" / "flexref.toml"
        super().__init__(order, path, cns_script, defaults)

    def run(self, **params):
        logger.info("Running [flexref] module")

        # Pool of jobs to be executed by the CNS engine
        jobs = []

        # Get the models generated in previous step
        models_to_refine = [p for p in self.previous_io.output if p.file_type == Format.PDB]

        first_model = models_to_refine[0]
        topologies = first_model.topology

        refined_structure_list = []
        for idx, model in enumerate(models_to_refine):
            inp_file = generate_flexref(
                idx,
                model,
                self.path,
                self.recipe_str,
                self.defaults,
                ambig=params.get('ambig', None),
                )

            out_file = self.path / f"flexref_{idx}.out"
            structure_file = self.path / f"flexref_{idx}.pdb"
            refined_structure_list.append(structure_file)

            job = CNSJob(inp_file, out_file, cns_folder=self.cns_folder_path)

            jobs.append(job)

        # Run CNS engine
        logger.info(f"Running CNS engine with {len(jobs)} jobs")
        engine = CNSEngine(jobs)
        engine.run()
        logger.info("CNS engine has finished")

        # Check for generated output, fail it not all expected files are found
        expected = []
        not_found = []
        for model in refined_structure_list:
            if not model.exists():
                not_found.append(model.name)
            pdb = PDBFile(model, path=self.path)
            pdb.topology = topologies
            expected.append(pdb)
        if not_found:
            self.finish_with_error("Several files were not generated:"
                                   f" {not_found}")

        # Save module information
        io = ModuleIO()
        io.add(refined_structure_list)
        io.add(expected, "o")
        io.save(self.path)
