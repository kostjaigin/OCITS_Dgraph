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
from sklearn.metrics import roc_auc_score, average_precision_score
from DgraphRecommendation.DataLoader import download_stored_nodes, read_and_upload_facebook

from itertools import islice

def k_shortest_predictions(G, src, dst) -> (float, float, float, float):
    shortests = nx.shortest_simple_paths(G, src, dst)
    res = 0
    for c, path in enumerate(shortests):
        res += 1/sqrt(len(path))
        if c == 0:
            res_1 = res
        if c == 3:
            res_4 = res
        if c == 7:
            res_8 = res
        if c == 15:
            res_16 = res
            break
    return res_1, res_4, res_8, res_16

def k_shortest_prediction(G, src, dst, k):
    shortests = nx.shortest_simple_paths(G, src, dst)
    res = 0
    for c, path in enumerate(shortests):
        res += 1/sqrt(len(path))
        if c == k-1:
            break
    return res

def write_to_results(lines: list):
    wdir = os.path.join(os.getcwd(), "DataOutput")
    file = os.path.join(wdir, "results.txt")
    with open(file, 'a') as f:
        f.writelines(lines)

def main():

    interface = DgraphInterface()

    ''' SETTINGS '''
    numbers = [1000, 5000, 10000, 25000, 50000, 80000] # how many nodes to take for both labels (balanced sets)
    predict_persons = True

    interface = DgraphInterface()
    G, _ = download_graph(predict_persons, interface)

    for number in numbers:

        lines = [] # result lines
        lines.append(f"CALCULATION FOR NUMBER OF LABELS = {number}\n")

        samples = get_unconnected(number, predict_persons)  # get not connected node pairs
        y_true = [0] * number
        samples += get_connected(number, predict_persons)  # get connected node pairs
        y_true += [1] * number

        G_train = G.copy()
        G_train.remove_edges_from(samples)

        ''' PREDICT USING K-SHORTEST PATHS '''
        scores = { 1:[], 4:[], 8:[], 16:[] }
        times = dict()

        for k in scores:
            print(f"Calculating shortests paths for k={k} and number of samples of each label = {number}")
            start = time.time()
            for sample in tqdm(samples):
                src = sample[0]
                dst = sample[1]
                score = k_shortest_prediction(G_train, src, dst, k)
                scores[k].append(score)
            end = time.time()
            times[k] = end-start
            print("...done!")

        assert len(scores[1]) == len(scores[4]) == len(scores[8]) == len(scores[16]) == len(samples)

        # write results down
        print("Calculating average precision scores for results...")
        for k in scores:
            kavg = average_precision_score(y_true, scores[k])
            ktime = times[k]
            lines.append(f"Average Precision Score for k-path-prediction with k value of {k} is {kavg}\n")
            lines.append(f"Time for k-path-prediction with k value of {k} is {ktime}\n")

        print("Calculating Jaccard Coefficients...")
        start = time.time()
        jaccard = list(nx.jaccard_coefficient(G_train, samples))
        end = time.time()
        _, _, jaccard_scores = zip(*jaccard)
        jaccard_avg = average_precision_score(y_true, jaccard_scores)
        lines.append(f"Average precision Score for Jaccard Coefficient prediction is {jaccard_avg}\n")
        lines.append(f"Time for Jaccard Coefficient prediction is {end-start}\n")

        print("Calculating preferential attachment index...")
        start = time.time()
        pref_attach = list(nx.preferential_attachment(G_train, samples))
        end = time.time()
        _, _, pref_attach_scores = zip(*pref_attach)
        pref_attach_avg = average_precision_score(y_true, pref_attach_scores)
        lines.append(f"Average precision Score for Prefferential Attachment prediction is {pref_attach_avg}\n")
        lines.append(f"Time for Prefferential Attachment prediction is {end-start}\n")

        print("Calculating adamic index...")
        start = time.time()
        adamic = list(nx.adamic_adar_index(G_train, samples))
        end = time.time()
        _, _, adamic_scores = zip(*adamic)
        adamic_avg = average_precision_score(y_true, adamic_scores)
        lines.append(f"Average precision Score for Adamic Adar Index prediction is {adamic_avg}\n")
        lines.append(f"Time for Adamic Adar Index prediction is {end-start}\n")

        print("Calculating Resource Allocation index...")
        start = time.time()
        resall = list(nx.resource_allocation_index(G_train, samples))
        end = time.time()
        _, _, resall_scores = zip(*resall)
        resall_avg = average_precision_score(y_true, resall_scores)
        lines.append(f"Average precision Score for Resource Allocation index prediction is {resall_avg}\n")
        lines.append(f"Time for Resource Allocation Index prediction is {end-start}\n")

        write_to_results(lines) # send results to results and continue with next number


def get_unconnected(number:int, predict_persons:bool):
    wdir = os.getcwd()
    file = os.path.join(wdir, f"non_edges_persons_{predict_persons}.txt")
    edges = []
    with open(file, 'r') as f:
        i = 0
        for line in f:
            content = line.strip().split(" ")
            src = content[0]
            dst = content[1]
            if not is_removable(src, dst, predict_persons):
                continue
            i += 1
            edges.append((src, dst))
            if i == number:
                break
    return edges

def get_connected(number:int, predict_persons:bool):
    wdir = os.getcwd()
    file = os.path.join(wdir, f"removable_links_persons_{predict_persons}.txt")
    edges = []
    with open(file, 'r') as f:
        i = 0
        for line in f:
            content = line.strip().split(" ")
            src = content[0]
            dst = content[1]
            if not is_removable(src, dst, predict_persons):
                continue
            i += 1
            edges.append((src, dst))
            if i == number:
                break
    return edges

def is_removable(src: str, dst: str, predict_persons) -> bool:
    if predict_persons:
        return src.startswith("0x") and dst.startswith("0x") # BOTH PERSONS
    else:
        return src[:2] != dst[:2] and (src.startswith("0x") or dst.startswith("0x")) # ONE PERSON, ANOTHER ONE FEATURE

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