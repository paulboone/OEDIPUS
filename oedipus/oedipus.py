
import os
from datetime import datetime
import math

import numpy as np

from oedipus.files import load_config_file
from oedipus.figures import delaunay_figure
from oedipus import box_generator

def print_block(string):
    print('{0}\n{1}\n{0}'.format('=' * 80, string))

def run_all_simulations(box_d, structure_function, dofs, config={}):
    if structure_function == "z12":
        return run_simulations_z12(box_d)
    elif structure_function == "norm":
        return run_simulations_norm(box_d)
    elif structure_function == "donut":
        return run_simulations_donut(box_d)
    elif structure_function == "inverse_donut":
        return run_simulations_inverse_donut(box_d)
    elif structure_function == "meanxz":
        return run_simulations_meanxz(box_d, dofs, config)
    else:
        print("config['structure_function'] type not valid.")

def run_simulations_norm(box_d):
    f = lambda x:((math.e**(-((x - 0.01) / math.sqrt(0.001))**2 /2) / math.sqrt(2 * math.pi)) * (1/math.sqrt(0.01))) / 8
    box_r = -1 * np.ones((len(box_d), 2))
    for i, b in enumerate(box_d):
        box_r[i][0] = (b[0] + b[1]) / 2
        box_r[i][1] = f(b[2])
    return box_r

def run_simulations_z12(box_d):
    box_r = -1 * np.ones((len(box_d), 2))
    for i, b in enumerate(box_d):
        box_r[i][0] = (b[0] + b[1]) / 2
        box_r[i][1] = (b[2]) ** 12
    return box_r

def run_simulations_meanxz(box_d, dofs, config):
    xdofs = config['xdofs']
    print(xdofs, dofs, box_d.shape)
    box_r = -1 * np.ones((len(box_d), 2))
    box_r[:,0] = box_d[:,0:xdofs].mean(axis=1)
    box_r[:,1] = box_d[:,xdofs:dofs].mean(axis=1)
    return box_r

def run_simulations_donut(box_d):
    box_r = -1 * np.ones((len(box_d), 2))
    for i, b in enumerate(box_d):
        angle = math.atan2(b[1] - 0.5, b[0] - 0.5)
        r = 0.125 + 0.25 * b[2] ** 12
        box_r[i][0] = math.cos(angle) * r + 0.5
        box_r[i][1] = math.sin(angle) * r + 0.5
    return box_r

def run_simulations_inverse_donut(box_d):
    box_r = -1 * np.ones((len(box_d), 2))
    for i, b in enumerate(box_d):
        angle = math.atan2(b[1] - 0.5, b[0] - 0.5)
        r = 0.375 - 0.25 * b[2] ** 12
        box_r[i][0] = math.cos(angle) * r + 0.5
        box_r[i][1] = math.sin(angle) * r + 0.5
    return box_r


def calc_bin(value, bound_min, bound_max, bins):
    """Find bin in parameter range.
    Args:
        value (float): some value, the result of a simulation.
        bound_min (float): lower limit, defining the parameter-space.
        bound_max (float): upper limit, defining the parameter-space.
        bins (int): number of bins used to subdivide parameter-space.
    Returns:
        Bin(int) corresponding to the input-value.
    """
    step = (bound_max - bound_min) / bins
    assigned_bin = (value - bound_min) // step
    assigned_bin = min(assigned_bin, bins-1)
    assigned_bin = max(assigned_bin, 0)
    return int(assigned_bin)

def calc_bins(box_r, num_bins):
    return [(calc_bin(b[0], 0.0, 1.0, num_bins), calc_bin(b[1], 0.0, 1.0, num_bins)) for b in box_r]

def oedipus(config_path):
    """
    Args:
        run_id (str): identification string for run.

    """

    config = load_config_file(config_path)
    num_bins = config['number_of_convergence_bins']
    run_id = datetime.now().isoformat()

    dofs = config['degrees_of_freedom']
    structure_function = config['structure_function']
    structure_function_config = config[structure_function]

    figure_guides = ""
    if structure_function in ['donut', 'inverse_donut']:
        figure_guides = "donut"

    print('{:%Y-%m-%d %H:%M:%S}'.format(datetime.now()))

    verbose = config['verbose'] if 'verbose' in config else False
    benchmarks = config['benchmarks']
    next_benchmark = benchmarks.pop(0)

    print(config)
    if config['initial_points'] == "random":
        if config['initial_points_random_seed']:
            print("applying random seed to initial points: %d" % config['initial_points_random_seed'])
            np.random.seed(config['initial_points_random_seed'])

        box_d = np.random.rand(config['children_per_generation'], dofs)
        box_r = -1 * np.ones((config['children_per_generation'], 2))
        np.random.seed() # flush the seed so that only the initial points are set, not generated points
    elif config['initial_points'] == "dof_combinations":
        box_d = np.array(itertools.product([0.0,1.0], repeat=dofs))
        box_r = -1 * np.ones((len(box_d), 2))
    else:
        print("config['initial_points'] type not valid.")
        return

    box_r = run_all_simulations(box_d, structure_function, dofs, structure_function_config)

    bins = set(calc_bins(box_r, num_bins))
    print("bins", bins)

    os.makedirs(config['visualization_output_dir'], exist_ok=True)

    for gen in range(1, config['number_of_generations'] + 1):
        if config['generator_type'] == 'random':
            new_box_d = np.random.rand(config['children_per_generation'], dofs)
            parents_d = parents_r = []
        elif config['generator_type'] == 'mutate':
            pass
        elif config['generator_type'] == 'convex_hull':
            new_box_d, parents_d, parents_r = box_generator.convex_hull.new_boxes(gen, config['children_per_generation'],
                        box_d, box_r, config['convex_hull'])
        else:
            print("config['generator_type'] NOT FOUND.")
            break

        # simulate properties
        new_box_r = run_all_simulations(new_box_d, structure_function, dofs, structure_function_config)
        new_bins = set(calc_bins(new_box_r, num_bins)) - bins
        bins = bins.union(new_bins)

        output_path = os.path.join(config['visualization_output_dir'], "triplot_%d.png" % gen)
        delaunay_figure(box_r, num_bins, output_path, children=new_box_r, parents=parents_r,
                        bins=bins, new_bins=new_bins,
                        title="Generation %d: %d/%d (+%d) %5.2f%% (+%5.2f %%)" %
                            (gen, len(bins), num_bins ** 2, len(new_bins),
                            100*float(len(bins)) / num_bins ** 2, 100*float(len(new_bins)) / num_bins ** 2 ),
                        patches=figure_guides)

        box_d = np.append(box_d, new_box_d, axis=0)
        box_r = np.append(box_r, new_box_r, axis=0)

        # evaluate algorithm effectiveness
        bin_count = len(bins)
        bin_fraction_explored = bin_count / num_bins ** 2
        if verbose:
            print('%s GENERATION %s: %5.2f%%' % (run_id, gen, bin_fraction_explored * 100))
        if bin_fraction_explored >= next_benchmark:
            print_block("%s: %5.2f%% exploration accomplished at generation %d" %
                ('{:%Y-%m-%d %H:%M:%S}'.format(datetime.now()), bin_fraction_explored * 100, gen))
            if benchmarks:
                next_benchmark = benchmarks.pop(0)
            else:
                print("Last benchmark reached")
                break
