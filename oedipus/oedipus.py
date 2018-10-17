
import os
from datetime import datetime
import math
from random import random, seed

import numpy as np

import oedipus
from oedipus.files import load_config_file
from oedipus.figures import delaunay_figure
from oedipus import box_generator

def print_block(string):
    print('{0}\n{1}\n{0}'.format('=' * 80, string))

def run_all_simulations(boxes, structure_function):
    if structure_function == "z12":
        run_simulations_z12(boxes)
    elif structure_function == "donut":
        run_simulations_donut(boxes)
    elif structure_function == "inverse_donut":
        run_simulations_inverse_donut(boxes)
    else:
        print("config['structure_function'] type not valid.")

def run_simulations_z12(boxes):
    for b in boxes:
        b[3] = (b[0] + b[1]) / 2
        b[4] = b[2] ** 12

def run_simulations_donut(boxes):
    for b in boxes:
        angle = math.atan2(b[1] - 0.5, b[0] - 0.5)
        r = 0.125 + 0.25 * b[2] ** 12
        b[3] = math.cos(angle) * r + 0.5
        b[4] = math.sin(angle) * r + 0.5

def run_simulations_inverse_donut(boxes):
    for b in boxes:
        angle = math.atan2(b[1] - 0.5, b[0] - 0.5)
        r = 0.375 - 0.25 * b[2] ** 12
        b[3] = math.cos(angle) * r + 0.5
        b[4] = math.sin(angle) * r + 0.5


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

def calc_bins(boxes, num_bins):
    return [(calc_bin(b[3], 0.0, 1.0, num_bins), calc_bin(b[4], 0.0, 1.0, num_bins)) for b in boxes]

def oedipus(config_path):
    """
    Args:
        run_id (str): identification string for run.

    """

    config = load_config_file(config_path)
    num_bins = config['number_of_convergence_bins']
    run_id = datetime.now().isoformat()
    structure_function = config['structure_function']
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
            seed(config['initial_points_random_seed'])
        boxes = np.array([[random(), random(), random(), -1.0, -1.0] for _ in range(config['children_per_generation'])])
        seed() # flush the seed so that only the initial points are set, not generated points
    elif config['initial_points'] == "dof_combinations":
        boxes = np.array([[0.0, 0.0, 0.0, -1.0, -1.0], [0.0, 0.0, 1.0, -1.0, -1.0],
                [0.0, 1.0, 0.0, -1.0, -1.0], [1.0, 0.0, 0.0, -1.0, -1.0], [0.0, 1.0, 1.0, -1.0, -1.0],
                [1.0, 0.0, 1.0, -1.0, -1.0], [1.0, 1.0, 0.0, -1.0, -1.0], [1.0, 1.0, 1.0, -1.0, -1.0]])
    else:
        print("config['initial_points'] type not valid.")
        return

    run_all_simulations(boxes, structure_function)

    bins = set(calc_bins(boxes, num_bins))
    print("bins", bins)

    os.makedirs(config['visualization_output_dir'], exist_ok=True)

    for gen in range(1, config['number_of_generations'] + 1):
        if config['generator_type'] == 'random':
            new_boxes = np.array([[random(), random(), random(), -1.0, -1.0] for _ in range(config['children_per_generation'])])
            parents = []
        elif config['generator_type'] == 'mutate':
            pass
        elif config['generator_type'] == 'convex_hull':
            new_boxes, parents = box_generator.convex_hull.new_boxes(gen, config['children_per_generation'],
                        boxes, config['convex_hull'])
        else:
            print("config['generator_type'] NOT FOUND.")
            break

        # simulate properties
        run_all_simulations(new_boxes, structure_function)
        new_bins = set(calc_bins(new_boxes, num_bins)) - bins
        bins = bins.union(new_bins)


        output_path = os.path.join(config['visualization_output_dir'], "triplot_%d.png" % gen)
        delaunay_figure(boxes, num_bins, output_path, children=new_boxes, parents=parents,
                        bins=bins, new_bins=new_bins,
                        title="Generation %d: %d/%d (+%d) %5.2f%% (+%5.2f %%)" %
                            (gen, len(bins), num_bins ** 2, len(new_bins),
                            100*float(len(bins)) / num_bins ** 2, 100*float(len(new_bins)) / num_bins ** 2 ),
                        patches=figure_guides)



        boxes = np.append(boxes, new_boxes, axis=0)

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
