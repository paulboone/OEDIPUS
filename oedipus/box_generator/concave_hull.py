
from collections import Counter
import os
from random import random

import matplotlib.pyplot as plt
import matplotlib.tri as tri
import numpy as np
from numpy.random import choice

from scipy.spatial import Delaunay


# box_keys = np.array([(0.6485246735270979, 0.047782203598175005), (0.2830489990985138, 0.12628689741104848), (0.6622976554913607, 0.44610223255199655), (0.5238467971302323, 2.0533664462484873e-05), (0.3363640771542708, 1.2847925496806057e-30), (0.28712548363927487, 3.528392685014887e-11), (0.45652906379983543, 2.7798641594090283e-13), (0.48815798593189064, 7.062050673750976e-08), (0.18620093298510088, 9.666854814957154e-08), (0.4764566629828143, 5.068721994522233e-09), (0.5991196747235934, 0.0009092578044809015), (0.4298307144463124, 0.18472498437168233), (0.20657842564581563, 4.0673759305763774e-05), (0.6090707757024826, 0.01818684956404001), (0.29483365600006345, 0.002495450518303365), (0.2164134741571252, 7.484475991665586e-05), (0.5027908087948297, 1.314358070863552e-22), (0.601130603334519, 0.04661927529860887), (0.3101410174803297, 0.00604831618859075), (0.47668417517994255, 2.05144488480981e-19), (0.2144810065907078, 1.4807752133690835e-05)])


#

def perturb_length(x, ms):
    dx = ms * (random() - x)
    return x + dx

def mutate_box(parent_box, mutation_strength):
    return ([
        perturb_length(parent_box[0], mutation_strength),
        perturb_length(parent_box[1], mutation_strength),
        perturb_length(parent_box[2], mutation_strength),
        -1.0, -1.0])

def choose_parents(num_parents, boxes, output_path=None):
    # calculate convex hull

    box_keys = boxes[:,3:5]

    triang = Delaunay(box_keys)
    hull_point_indices = np.unique(triang.convex_hull.flatten())
    hull_points = np.array([box_keys[p] for p in hull_point_indices])
    print("hull_point_indices", len(hull_point_indices))
    # choose parents
    point_weights = {i:0 for i in hull_point_indices}
    total_weight = 0
    for edge in triang.convex_hull:
        distance = np.sqrt(np.sum((box_keys[edge[0]] - box_keys[edge[1]]) ** 2))
        point_weights[edge[0]] += distance
        point_weights[edge[1]] += distance
        total_weight += 2 * distance

    point_weights = {k:point_weights[k] / total_weight for k in point_weights}
    parent_indices = choice(list(point_weights.keys()), num_parents, p=list(point_weights.values()))

    if output_path:
        # plot visualization
        fig = plt.figure(figsize=(12,9))
        ax = fig.add_subplot(1, 1, 1)
        ax.set_ylim(0.0, 1.0)
        ax.set_xlim(0.0, 1.0)
        ax.set_xticks(np.array(range(0,11))/10)
        ax.set_yticks(np.array(range(0,11))/10)
        ax.grid(linestyle='-', color='0.7', zorder=0)

        # plot all points as triangulation
        ax.triplot(box_keys[:,0], box_keys[:,1], triang.simplices.copy(), 'b-', lw=1)

        # plot hull and labels
        ax.plot(hull_points[:,0], hull_points[:,1], color='blue', marker='o', linestyle='None', zorder=10)
        for i in hull_point_indices:
            ax.annotate(i, (box_keys[i,0], box_keys[i,1] - 0.01), zorder=30, ha="center", va="top", size=9)

        # plot prior generation
        ax.plot(box_keys[-100:,0], box_keys[-100:,1], color='yellow', marker='o', linestyle='None', zorder=12)

        # plot chosen parents with proportional circles and label
        parent_counts = Counter(parent_indices)
        unique_parent_indices = np.unique(parent_indices)
        unique_parent_points = np.array([(box_keys[i,0],box_keys[i,1], parent_counts[i]) for i in unique_parent_indices])
        ax.scatter(unique_parent_points[:,0], unique_parent_points[:,1], s=40*unique_parent_points[:,2], color='orange', marker='o', linestyle='None', zorder=15)
        for i in parent_counts:
            if parent_counts[i] > 5:
                ax.annotate(parent_counts[i], (box_keys[i,0], box_keys[i,1]), zorder=30, ha="center", va="center", size=9)

        fig.savefig(output_path)
        plt.close(fig)

    return np.array([boxes[i] for i in parent_indices])


def new_boxes(gen, children_per_generation, boxes, config={}):
    os.makedirs(config['output_dir'], exist_ok=True)

    # if starting_boxes:
    #     all_boxes = starting_boxes

    mutation_strength = config['mutation_strength']
    parents_graph_path = None
    if 'output_dir' in config:
        parents_graph_path = os.path.join(config['output_dir'], "triplot_%d.png" % gen)

    parents = choose_parents(children_per_generation, boxes, output_path=parents_graph_path)
    children = np.array([mutate_box(p, mutation_strength) for p in parents])
    return children
