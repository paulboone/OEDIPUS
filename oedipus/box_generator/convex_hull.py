
from collections import Counter
import os
from random import random

import matplotlib.pyplot as plt
import matplotlib.tri as tri
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

def output_figure(triang, boxes, hull_points, parents, convergence_bins, output_path):

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
    ax.plot(hull_points[:,0], hull_points[:,1], color='blue', marker='o', linestyle='None', zorder=10)
    # for p in hull_points:
    #     ax.annotate(i, (p[0], p[1] - 0.01), zorder=30, ha="center", va="top", size=9)

    # plot prior generation
    ax.plot(boxes[-100:,3], boxes[-100:,4], color='yellow', marker='o', linestyle='None', zorder=12)

    # plot chosen parents with proportional circles and label
    parent_counter = Counter([tuple(x) for x in parents]) #need tuples because they are hashable
    unique_parents = np.array([[x[3], x[4], num] for x, num in parent_counter.items()])
    ax.scatter(unique_parents[:,0], unique_parents[:,1], s=40*unique_parents[:,2], color='orange', marker='o', linestyle='None', zorder=15)
    for p in unique_parents:
        x, y, parent_count = p
        if parent_count > 5:
            ax.annotate(str(int(parent_count)), (x, y), zorder=30, ha="center", va="center", size=9)

    fig.savefig(output_path)
    plt.close(fig)

def choose_parents(num_parents, boxes, output_path=None, convergence_bins=10):
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
    if output_path:
        hull_points = np.array([box_range[p] for p in hull_point_indices])
        output_figure(triang, boxes, hull_points, parents, convergence_bins, output_path)

    return parents


def new_boxes(gen, children_per_generation, boxes, config={}):
    os.makedirs(config['output_dir'], exist_ok=True)

    mutation_strength = config['mutation_strength']
    parents_graph_path = None
    if 'output_dir' in config:
        parents_graph_path = os.path.join(config['output_dir'], "triplot_%d.png" % gen)

    parents = choose_parents(children_per_generation, boxes, output_path=parents_graph_path, convergence_bins=40)
    children = np.array([mutate_box(p, mutation_strength) for p in parents])
    return children
