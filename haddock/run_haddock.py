import sys
import toml
import json
from datetime import datetime

from haddock.modules.analysis.ana import Ana
from haddock.modules.cns.engine import CNS
from haddock.modules.cns.input import InputGenerator
from haddock.modules.docking.it0 import RigidBody
from haddock.modules.docking.it1 import SemiFlexible
from haddock.modules.docking.itw import WaterRefinement
from haddock.modules.worker.distribution import JobCreator
from haddock.modules.functions import *

etc_folder = get_full_path('haddock', 'etc')
with open(f'{etc_folder}/default.json', 'r') as fh:
    default_recipes = json.load(fh)
fh.close()


def greeting():
    now = datetime.now().replace(second=0, microsecond=0)
    python_version = sys.version
    return (f'''##############################################
#                                            #
#         Starting HADDOCK v3.0beta1         #
#                                            #
#             EXPERIMENTAL BUILD             #
#                                            #
##############################################

Starting HADDOCK on {now}

HADDOCK version: 3.0 beta 1
Python {python_version}
''')


def generate_topology(mol_dic, run_param):
    print('++ Generating topologies')

    recipe_name = run_param['stage']['topology']['recipe']
    if recipe_name == 'default':
        recipe_name = default_recipes['topology']

    recipe = f'topology/template/{recipe_name}'
    if not os.path.isfile(recipe):
        print('+ ERROR: Template recipe for topology not found')

    topo_gen = InputGenerator(recipe_file=recipe,
                              input_folder='topology')

    jobs = JobCreator(job_id='generate',
                      job_folder='topology')

    job_counter = 1
    for mol in mol_dic:
        for input_strc in mol_dic[mol]:
            output_strct = input_strc.split('/')[1].split('.')[0]
            input_f = topo_gen.generate(protonation_dic={},
                                        output_pdb=True,
                                        output_psf=True,
                                        input_pdb=input_strc,
                                        input_psf=None,
                                        output_fname=output_strct)

            jobs.delegate(job_num=job_counter,
                          input_file_str=input_f)

            job_counter += 1

    cns = CNS()
    cns.run(jobs)
    output = retrieve_output(jobs)
    topology_dic = molecularize(output)
    return topology_dic


def run_it0(model_dic, run_param):
    print('\n++ Running it0')
    file_list = []
    supported_modules = []

    recipe_name = run_param['stage']['rigid_body']['recipe']
    if recipe_name == 'default':
        recipe_name = default_recipes['rigid_body']

    recipe = f'rigid_body/template/{recipe_name}'
    if not os.path.isfile(recipe):
        print('+ ERROR: Template recipe for rigid-body not found')

    if '.cns' not in recipe:
        # Its a module, look for it
        if recipe not in supported_modules:
            print(f'+ ERROR: {recipe} not supported.')
            exit()

    else:
        # Its a HADDOCK recipe
        it0 = RigidBody()
        job_dic = it0.init(recipe, model_dic, run_param)
        complex_list = it0.run(job_dic)
        file_list = it0.output(complex_list)

    return file_list


def run_it1(model_list, run_param):
    print('\n++ Running it1')
    file_list = []
    supported_modules = []

    recipe_name = run_param['stage']['semi_flexible']['recipe']
    if recipe_name == 'default':
        recipe_name = default_recipes['semi_flexible']

    recipe = f'semi_flexible/template/{recipe_name}'
    if not os.path.isfile(recipe):
        print('+ ERROR: Template recipe for semi-flexible not found')

    if '.cns' not in recipe:
        # Its a module, look for it
        if recipe not in supported_modules:
            print(f'+ ERROR: {recipe} not supported.')
            exit()

    else:
        # Its a HADDOCK recipe
        it1 = SemiFlexible()
        job_dic = it1.init(recipe, model_list)
        complex_list = it1.run(job_dic)
        file_list = it1.output(complex_list)

    return file_list


def run_itw(model_list, run_param):
    print('\n++ Running itw')
    file_list = []
    supported_modules = []

    recipe_name = run_param['stage']['water_refinement']['recipe']
    if recipe_name == 'default':
        recipe_name = default_recipes['water_refinement']

    recipe = f'water_refinement/template/{recipe_name}'
    if not os.path.isfile(recipe):
        print('+ ERROR: Template recipe for semi-flexible not found')

    if '.cns' not in recipe:
        # Its a module, look for it
        if recipe not in supported_modules:
            print(f'+ ERROR: {recipe} not supported.')
            exit()

    else:
        # Its a HADDOCK recipe
        itw = WaterRefinement()
        job_dic = itw.init(recipe, model_list)
        complex_list = itw.run(job_dic)
        file_list = itw.output(complex_list)

    return file_list


def run_analysis(pdb_l):
    ana = Ana(pdb_l)

    ana.extract_energies()

    ana.calculate_haddock_score()

    ana.cluster(cutoff=0.60, threshold=4)

    # ana.run_fastcontact()
    # ana.run_dfire()
    # ana.run_dockq()

    ana.output()


if __name__ == '__main__':

    print(greeting())

    run_f = 'data/run.toml'
    if not os.path.isfile(run_f):
        print('+ ERROR: data/run.toml not found, make sure you are in the correct folder.')
        exit()
    run_parameters = toml.load(run_f)

    molecules = get_begin_molecules('data/')

    # 1. Generate topologies ==========================================================================================#
    begin_models = generate_topology(molecules, run_parameters)

    # 2. Dock =========================================================================================================#

    # Input:
    #  molecule dictionary, keys=molecule, values=list of tuples containing .psf and .pdb
    #   example:
    # {
    #  'mol1': [('begin/mol1_1.psf', 'begin/mol1_1.pdb')],
    #  'mol2': [('begin/mol2_1.psf', 'begin/mol2_1.pdb'),
    #           ('begin/mol2_2.psf', 'begin/mol2_2.pdb')]
    #  'mol3': [('begin/mol3_1.psf', 'begin/mol3_1.pdb')]
    #   }

    # Output:
    #  List of complexes, SORTED according to ranking!
    #   example:
    # ['complex_42.pdb', 'complex_10.pdb', 'complex_23.pdb']

    # Rigid-body (it0)
    # > Get sampling parameters
    rigid_sampling = run_parameters['stage']['rigid_body']['sampling']

    # > Run rigid-body docking
    rigid_complexes = run_it0(begin_models, run_parameters)
    # rigid_complexes = run_lightdock(begin_models)

    # Semi-flexible (it1)
    semiflex_sampling = run_parameters['stage']['semi_flexible']['sampling']

    if semiflex_sampling > rigid_sampling:
        print(f'+ WARNING: Semi Flexible sampling ({semiflex_sampling}) is higher than Rigid-body sampling ({rigid_sampling})')
        print(f'++ Passing {rigid_sampling} complexes to Semi Flexible stage')

    # > Select top N models
    semi_flexible_input_complexes = rigid_complexes[:semiflex_sampling]

    # > Run semi-flexible refinement
    semi_flexible_complexes = run_it1(semi_flexible_input_complexes, run_parameters)

    # Water refinement (itw)
    waterref_sampling = run_parameters['stage']['water_refinement']['sampling']

    # > Select top N models
    if semiflex_sampling > rigid_sampling:
        print(f'+ WARNING: Water refinement n ({waterref_sampling}) is higher than Semi-flexible sampling {semiflex_sampling}')
        print(f'++ Passing {semiflex_sampling} complexes to Water refinement')

    water_refinement_input_complexes = semi_flexible_complexes[:waterref_sampling]

    water_refinement_complexes = run_itw(water_refinement_input_complexes, run_parameters)

    # 3. Analysis =====================================================================================================#

    run_analysis(water_refinement_complexes)

    # 4. Done! ========================================================================================================#

    print(bye())

    # =================================================================================================================#
