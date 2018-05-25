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
import yaml

import oedipus
from oedipus.files import load_config_file
from oedipus.db import engine, session, Box, MutationStrength, Convergence
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

def rebin_generations(no_gens, bins):
    k, m = divmod(no_gens, len(bins))
    return list((i + 1) * k + min(i + 1, m) for i in range(len(bins) - 1))

def get_number_of_bins(gen, no_gens, bins):
    index = 0
    for i in rebin_generations(no_gens, bins):
        if gen >= i:
            index += 1
    return bins[index]

def calc_bin(value, bound_min, bound_max, gen, config):
    """Find bin in parameter range.

    Args:
        value (float): some value, the result of a simulation.
        bound_min (float): lower limit, defining the parameter-space.
        bound_max (float): upper limit, defining the parameter-space.
        bins (int): number of bins used to subdivide parameter-space.

    Returns:
        Bin(int) corresponding to the input-value.

    """
    if config['mutate']['mutation_scheme'] in ['adaptive_binning', 'hybrid_adaptive_binning']:
        bins = get_number_of_bins(gen, config['number_of_generations'], config['number_of_convergence_bins'])
    else:
        bins = config['number_of_convergence_bins']
    step = (bound_max - bound_min) / bins
    assigned_bin = (value - bound_min) // step
    assigned_bin = min(assigned_bin, bins-1)
    assigned_bin = max(assigned_bin, 0)
    return int(assigned_bin)

def run_all_simulations(box, gen, config):
    """
    Args:
        box (sqlalchemy.orm.query.Query): material to be analyzed.

    """
    results = simulation.alpha.run(box)
    box.update_from_dict(results)
    box.alpha_bin = calc_bin(box.alpha, 0., 1., gen, config)

    results = simulation.beta.run(box)
    box.update_from_dict(results)
    box.beta_bin = calc_bin(box.beta, 0., 1., gen, config)

def print_block(string):
    print('{0}\n{1}\n{0}'.format('=' * 80, string))

def evaluate_convergence(run_id, generation, convergence_cutoff_criteria):
    '''Determines convergence by calculating variance of bin-counts.
    
    Args:
        run_id (str): identification string for run.
        generation (int): iteration in bin-mutate-simulate routine.

    Returns:
        bool: True if variance is less than or equal to cutt-off criteria (so
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

def oedipus(config_path):
    """
    Args:
        run_id (str): identification string for run.

    """

    config = load_config_file(config_path)
    run_id = datetime.now().isoformat()

    for gen in range(config['number_of_generations']):
        print_block('{} GENERATION {}'.format(run_id, gen))
        
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
            run_all_simulations(box, gen, config)
            session.add(box)
        session.commit()

        # rebin all materials
        if config['mutate']['mutation_scheme'] in ['adaptive_binning', 'hybrid_adaptive_binning']:
            if gen in rebin_generations(config['number_of_generations'], config['number_of_convergence_bins']):
                box_ids = [e[0] for e in session.query(Box.id).filter(Box.run_id==run_id).all()]
                for box_id in box_ids:
                    print('Re-binning box : {}'.format(box_id))
                    box = session.query(Box).get(box_id)
                    box.alpha_bin = calc_bin(box.alpha, 0., 1., gen, config)
                    box.beta_bin = calc_bin(box.beta, 0., 1., gen, config)
                session.commit()

        # store empty-bin convergence
        if config['mutate']['mutation_scheme'] in ['adaptive_binning', 'hybrid_adaptive_binning']:
            no_bins = get_number_of_bins(gen, config['number_of_generations'],
                                    config['number_of_convergence_bins'])
        else:
            no_bins = config['number_of_convergence_bins']
        convergence_score = (no_bins ** 2 - len(session.query(Box.alpha_bin, Box.beta_bin) \
                .distinct().filter(Box.run_id==run_id).all())) / no_bins ** 2
        convergence = Convergence(run_id, gen, convergence_score)
        session.add(convergence)
        session.commit()
