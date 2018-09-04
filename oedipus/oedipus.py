import os
import sys
from math import sqrt
from datetime import datetime
from collections import Counter
import random

import numpy as np
from sqlalchemy.sql import func, or_
from sqlalchemy.orm.exc import FlushError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import text

import oedipus
from oedipus.files import load_config_file
from oedipus.db import engine, session, Box, MutationStrength
from oedipus import simulation
from oedipus import box_generator

def boxes_in_generation(run_id, generation):
    """Count number of materials in a generation.

    Args:
        run_id (str): identification string for run.
        generation (int): iteration in overall bin-mutate-simulate rountine.

    Returns:

    """
    return session.query(Box).filter(
        Box.run_id == run_id,
        Box.generation == generation
    ).count()

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

def run_all_simulations(box, number_of_convergence_bins):
    """
    Args:
        box (sqlalchemy.orm.query.Query): material to be analyzed.

    """
    results = simulation.alpha.run(box)
    box.update_from_dict(results)
    box.alpha_bin = calc_bin(box.alpha, 0., 1., number_of_convergence_bins)

    results = simulation.beta.run(box)
    box.update_from_dict(results)
    box.beta_bin = calc_bin(box.beta, 0., 1., number_of_convergence_bins)

def print_block(string):
    print('{0}\n{1}\n{0}'.format('=' * 80, string))

def evaluate_convergence(run_id, generation, convergence_cutoff_criteria):
    '''Determines convergence by calculating variance of bin-counts.

    Args:
        run_id (str): identification string for run.
        generation (int): iteration in bin-mutate-simulate routine.

    Returns:
        bool: True if variance is less than or equal to cut-off criteria (so
            method will continue running).
    '''
    query_group = [Box.alpha_bin, Box.beta_bin]

    bin_counts = session \
        .query(func.count(Box.id)) \
        .filter(Box.run_id == run_id, Box.generation < generation) \
        .group_by(*query_group).all()
    bin_counts = [i[0] for i in bin_counts]    # convert SQLAlchemy result to list
    variance = sqrt( sum([(i - (sum(bin_counts) / len(bin_counts)))**2 for i in bin_counts]) / len(bin_counts))
    print('\nCONVERGENCE:\t%s\n' % variance)
    sys.stdout.flush()
    return variance <= convergence_cutoff_criteria

def evaluate_bin_spread(run_id):
    bin_counts = session.query(func.count(Box.id)).filter(Box.run_id == run_id). \
        group_by(Box.alpha_bin, Box.beta_bin).all()
    return len(bin_counts)

def oedipus(config_path):
    """
    Args:
        run_id (str): identification string for run.

    """

    config = load_config_file(config_path)
    run_id = datetime.now().isoformat()

    total_bins = int(config['number_of_convergence_bins']) ** 2

    verbose = config['verbose'] if 'verbose' in config else False
    benchmarks = config['benchmarks']
    next_benchmark = benchmarks.pop(0)

    for gen in range(config['number_of_generations']):
        # create boxes, first generation is always random
        if gen == 0 or config['generator_type'] == 'random':
            boxes = box_generator.random.new_boxes(run_id, gen,
                    config['children_per_generation'], {})
        elif config['generator_type'] == 'mutate':
            boxes = box_generator.mutate.new_boxes(run_id, gen,
                    config['children_per_generation'], config['mutate'])
        else:
            print("config['generator_type'] NOT FOUND.")
            break

        # simulate properties
        for box in boxes:
            run_all_simulations(box, config['number_of_convergence_bins'])
            session.add(box)
        session.commit()

        # evaluate algorithm effectiveness
        bin_count = evaluate_bin_spread(run_id)
        bin_fraction_explored = bin_count / total_bins
        if verbose:
            print('%s GENERATION %s: %5.2f%%' % (run_id, gen, bin_fraction_explored * 100))
        if bin_fraction_explored >= next_benchmark:
            print_block("%5.2f%% exploration accomplished at generation %d" % (bin_fraction_explored * 100, gen))
            if benchmarks:
                next_benchmark = benchmarks.pop(0)
            else:
                print("Last benchmark reached")
                break
