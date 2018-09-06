from collections import Counter
import os
# import sys
# from math import sqrt
from datetime import datetime
# from collections import Counter
from random import random

import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import Delaunay
# from sqlalchemy.sql import func, or_
# from sqlalchemy.orm.exc import FlushError
# from sqlalchemy.exc import IntegrityError
# from sqlalchemy.sql import text

import oedipus
from oedipus.files import load_config_file
# from oedipus.db import engine, session, Box, MutationStrength
# from oedipus import simulation
from oedipus import box_generator

def delaunay_figure(boxes, convergence_bins, output_path, triang=None, parents=[]):

    if not triang:
        triang = Delaunay(boxes[:,3:5])

    hull_point_indices = np.unique(triang.convex_hull.flatten())
    hull_points = np.array([boxes[p] for p in hull_point_indices])

    # plot visualization
    fig = plt.figure(figsize=(12,9))
    ax = fig.add_subplot(1, 1, 1)
    ax.set_ylim(0.0, 1.0)
    ax.set_xlim(0.0, 1.0)
    ax.set_xticks(np.array(range(0,convergence_bins + 1))/convergence_bins)
    ax.set_yticks(np.array(range(0,convergence_bins + 1))/convergence_bins)
    ax.grid(linestyle='-', color='0.7', zorder=0)

    # plot all points as triangulation
    ax.triplot(boxes[:,3], boxes[:,4], triang.simplices.copy(), 'b-', lw=1)

    # plot hull and labels
    ax.plot(hull_points[:,3], hull_points[:,4], color='blue', marker='o', linestyle='None', zorder=10)
    # for p in hull_points:
    #     ax.annotate(i, (p[0], p[1] - 0.01), zorder=30, ha="center", va="top", size=9)

    # plot prior generation
    ax.plot(boxes[-100:,3], boxes[-100:,4], color='yellow', marker='o', linestyle='None', zorder=12)

    # plot chosen parents with proportional circles and label
    if len(parents) > 0:
        parent_counter = Counter([tuple(x) for x in parents]) #need tuples because they are hashable
        unique_parents = np.array([[x[3], x[4], num] for x, num in parent_counter.items()])
        ax.scatter(unique_parents[:,0], unique_parents[:,1], s=40*unique_parents[:,2], color='orange', marker='o', linestyle='None', zorder=15)
        for p in unique_parents:
            x, y, parent_count = p
            if parent_count > 5:
                ax.annotate(str(int(parent_count)), (x, y), zorder=30, ha="center", va="center", size=9)

    fig.savefig(output_path)
    plt.close(fig)


def print_block(string):
    print('{0}\n{1}\n{0}'.format('=' * 80, string))

def run_all_simulations(boxes):
    for b in boxes:
        b[3] = (b[0] + b[1]) / 2
        b[4] = b[2] ** 12

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
    print('{:%Y-%m-%d %H:%M:%S}'.format(datetime.now()))

    verbose = config['verbose'] if 'verbose' in config else False
    benchmarks = config['benchmarks']
    next_benchmark = benchmarks.pop(0)

    print(config)
    boxes = np.array([[random(), random(), random(), -1.0, -1.0] for _ in range(config['children_per_generation'])])
    run_all_simulations(boxes)
    bins = set(calc_bins(boxes, num_bins))
    print("bins", bins)

    os.makedirs(config['visualization_output_dir'], exist_ok=True)
    output_path = os.path.join(config['visualization_output_dir'], "triplot_%d.png" % 0)
    delaunay_figure(boxes, num_bins, output_path)

    for gen in range(1, config['number_of_generations'] + 1):
        if config['generator_type'] == 'random':
            new_boxes = [[random(), random(), random(), -1.0, -1.0] for _ in range(config['children_per_generation'])]
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
        run_all_simulations(new_boxes)
        bins = bins.union(calc_bins(new_boxes, num_bins))
        boxes = np.append(boxes, new_boxes, axis=0)

        output_path = os.path.join(config['visualization_output_dir'], "triplot_%d.png" % gen)
        delaunay_figure(boxes, num_bins, output_path, parents=parents)

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
