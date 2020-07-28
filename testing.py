import itertools
import timeit
from functools import reduce
from statistics import mean

import easygui
from os import path
import os
import shutil
import http.client
import time
import json
from tqdm import tqdm
import networkx as nx
import sys
from math import sqrt
from pathlib import Path
import matplotlib.pyplot as plt
import multiprocessing as mp

from DgraphRecommendation import DgraphInterface
from DgraphRecommendation import config
from DgraphRecommendation.DataLoader import download_stored_nodes, read_and_upload_facebook


def main():
    file = "/Users/Ones-Kostik/desktop/non_edges_persons_True.txt"
    edges = []
    with open(file, 'r') as f:
        i = 0
        for line in f:
            i += 1
            content = line.strip().split(" ")
            src = content[0]
            dst = content[1]
            edges.append((src, dst))
            if i == 5:
                break
    edge = edges[0]
    interface = DgraphInterface()
    mean_time = mean(timeit.repeat(lambda : k_predict(edge, 2, interface), number=1, repeat=10))
    print(mean_time)


def plot_results(intervals, y_precision_jaccard, y_precision_adamic, y_precision_resall, y_time_jaccard, y_time_adamic, y_time_resall):
    ''' PLOT THE RESULTS '''
    plt.figure(figsize=(12, 6))
    plt.plot(intervals, y_precision_jaccard, label='Jaccard Coefficient')
    plt.plot(intervals, y_precision_adamic, label='Adamic Adar Index')
    plt.plot(intervals, y_precision_resall, label='Resource Allocation Index')
    plt.ylim(0, 1)
    plt.legend(loc='upper right', fontsize=15)
    plt.xlabel('% of removed links', fontsize=15)
    plt.ylabel("avg. precision score", fontsize=15)
    plt.grid(True)
    plt.title("Precision scores", fontsize=20)
    plt.show()

    plt.figure(figsize=(12, 6))
    plt.plot(intervals, y_time_jaccard, label='Jaccard Coefficient')
    plt.plot(intervals, y_time_adamic, label='Adamic Adar Index')
    plt.plot(intervals, y_time_resall, label='Resource Allocation Index')
    plt.legend(loc='upper right', fontsize=15)
    plt.xlabel('% of removed links', fontsize=15)
    plt.ylabel("time [s]", fontsize=15)
    plt.grid(True)
    plt.title("Calculation time", fontsize=20)
    plt.show()

def k_predict(edge, k, interface: DgraphInterface) -> float:
    time_k = 0
    src = edge[0]  # should both be uid
    dst = edge[1]
    ppl, latency = interface.get_k_shortest_pathes(k, src, dst)
    # start_delta = int(latency.total_ns) * (10 ** (-9))  # to secs
    # time_k += start_delta
    # start = time.time()
    # s_k = sum([1/(int(item["_weight_"])) for item in ppl["_path_"]])
    # end = time.time()
    # time_k += end - start
    return ppl



def k_shortest_prediction(edges, k) -> (list, int):
    interface = DgraphInterface()
    time_k = 0
    rates = []
    for edge in tqdm(edges):
        idx, tme = k_predict(edge, k, interface)
        rates.append(idx)
        time_k += tme
    return rates, time_k

if __name__ == '__main__':
    main()