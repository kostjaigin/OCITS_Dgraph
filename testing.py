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

from itertools import islice

def k_shortest_slice(G, source, target, k, weight=None):
    return list(islice(nx.shortest_simple_paths(G, source, target, weight=weight), k))

def k_shortest_gen(G, source, target, k):
    shortests = nx.shortest_simple_paths(G, source, target)
    res = []
    for c, path in enumerate(shortests):
        res.append(path)
        if c == k-1:
            break
    return res

def k_shortest_prediction(G, src, dst, k):
    shortests = nx.shortest_simple_paths(G, src, dst)
    res = 0
    for c, path in enumerate(shortests):
        res += 1/sqrt(len(path))
        if c == k-1:
            break
    return res

def main():

    samples = get_unconnected(10) # get 10 not connected node pairs
    sample = samples[0]
    src = sample[0]
    dst = sample[1]

    interface = DgraphInterface()
    G, _ = download_graph(True, interface)
    k = 4 # to use with [:k]

    #k_shortests_mean = mean(timeit.repeat(lambda: k_shortest_paths(G, src, dst, k), number=1, repeat=100))
    #k_shortests_2_mean = mean(timeit.repeat(lambda: k_shortest_2(G, src, dst, k), number=1, repeat=100))
    #print(k_shortests_mean)
    #print(k_shortests_2_mean)

    k_shortests_mean = mean(timeit.repeat(lambda: k_shortest_prediction(G, src, dst, k), number=1, repeat=100))
    print(k_shortests_mean)
    res = k_shortest_prediction(G, src, dst, k)
    print(f"result: {res}")

    # c_k = sum([len(path) for path in shortest_paths])
    # print(c_k)
    # mean_time = mean(timeit.repeat(lambda : k_predict(edge, 2, interface), number=1, repeat=10))
    # print(mean_time)


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

def get_unconnected(number:int):
    wdir = os.getcwd()
    file = os.path.join(wdir, "non_edges_persons_True.txt")
    edges = []
    with open(file, 'r') as f:
        i = 0
        for line in f:
            i += 1
            content = line.strip().split(" ")
            src = content[0]
            dst = content[1]
            edges.append((src, dst))
            if i == number:
                break
    return edges

def download_graph(predict_persons: bool, interface: DgraphInterface) -> (nx.Graph, nx.Graph):
    ''' DOWNLOAD DGRAPH DATA AND TRANSFORM IT INTO NETWORKX GRAPH '''
    persons = interface.getAllPersons()
    persons = persons['persons']
    features = interface.getAllFeatures()
    features = features['features']
    # prepare data
    G = nx.Graph()  # normal graph
    G_persons = nx.Graph()  # graph only with persons
    for row in tqdm(features):
        feature = row['name']
        G.add_node(feature)
    for row in tqdm(persons):
        person = row['uid']
        G.add_node(person)
        if predict_persons:
            G_persons.add_node(person)
    for row in tqdm(persons):
        person = row['uid']
        if 'tracks' in row:
            tracks = row['tracks']
            for feat in tracks:
                G.add_edge(person, feat['name'])
                # edges can be provided with additional attributes
                G[person][feat['name']]['type'] = 'tracks'
        if 'follows' in row:
            follows = row['follows']
            for pers in follows:
                G.add_edge(person, pers['uid'])
                # edges can be provided with additional attributes
                G[person][pers['uid']]['type'] = 'follows'
                if predict_persons:
                    G_persons.add_edge(person, pers['uid'])
                    G_persons[person][pers['uid']]['type'] = 'follows'

    return (G, G_persons) if predict_persons else (G, G.copy()) # if not predict_persons, complement of whole graph will be calculated



if __name__ == '__main__':
    main()