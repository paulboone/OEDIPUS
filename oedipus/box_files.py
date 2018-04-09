# standard library imports
import sys
import os
from random import choice, random, randrange, uniform
import shutil
from uuid import uuid4

# related third party imports
import numpy as np
import yaml

# local application/library specific imports
from oedipus.db import session, Box

def perturb_length(x, ms):
    dx = ms * (random() - x)
    return x + dx

def generate_box(run_id):
    """
    
    Args:
        run_id (str): identification string for run.

    Returns:
 
    """
    box = Box(run_id)
    box.generation  = 0
    [box.x, box.y, box.z] = [random(), random(), random()]

    return box

def mutate_box(parent_box, mutation_strength, generation):
    """    
    Args:

    Returns:

    """
    ########################################################################
    # create box
    child_box = Box(parent_box.run_id)
    child_box.parent_id = parent_box.id
    child_box.generation = generation

    ########################################################################
    # perturb side lengths
    child_box.x = perturb_length(parent_box.x, mutation_strength)
    child_box.y = perturb_length(parent_box.y, mutation_strength)
    child_box.z = perturb_length(parent_box.z, mutation_strength)

    return child_box
