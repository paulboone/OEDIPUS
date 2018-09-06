
from random import random
import numpy as np
from numpy.random import choice

from scipy.spatial import Delaunay


def perturb_length(x, ms):
    dx = ms * (random() - x)
    return x + dx

# def mutate_box(parent_box, mutation_strength):
#     return ([
#         perturb_length(parent_box[0], mutation_strength),
#         perturb_length(parent_box[1], mutation_strength),
#         perturb_length(parent_box[2], mutation_strength),
#         -1.0, -1.0])

def mutate_box(parent_box, mutation_strength):
    child = [parent_box[0], parent_box[1], parent_box[2], -1.0, -1.0]
    dof = choice([0,1,2])
    child[dof] = perturb_length(child[dof], mutation_strength)
    return child

def choose_parents(num_parents, boxes, convergence_bins=10):
    # calculate convex hull

    box_range = boxes[:,3:5]

    triang = Delaunay(box_range)
    hull_point_indices = np.unique(triang.convex_hull.flatten())

    # choose parents
    point_weights = {i:0 for i in hull_point_indices}
    total_weight = 0
    for edge in triang.convex_hull:
        distance = np.sqrt(np.sum((box_range[edge[0]] - box_range[edge[1]]) ** 2))
        point_weights[edge[0]] += distance
        point_weights[edge[1]] += distance
        total_weight += 2 * distance

    point_weights = {k:point_weights[k] / total_weight for k in point_weights}
    parent_indices = choice(list(point_weights.keys()), num_parents, p=list(point_weights.values()))
    parents = np.array([boxes[i] for i in parent_indices])

    return parents


def new_boxes(gen, children_per_generation, boxes, config={}):
    mutation_strength = config['mutation_strength']
    parents = choose_parents(children_per_generation, boxes, convergence_bins=40)
    children = np.array([mutate_box(p, mutation_strength) for p in parents])
    return children, parents
