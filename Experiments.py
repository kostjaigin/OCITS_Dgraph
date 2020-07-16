'''
Here i will conduct the experiments with link prediction algorithms
'''
import networkx as nx
import time
import pandas as pd
import json
import matplotlib.pyplot as plt
from sklearn.metrics import classification_report, roc_auc_score, average_precision_score
from sklearn.model_selection import train_test_split
from tqdm import tqdm
import random
import numpy as np


from DgraphRecommendation import DgraphInterface, Feature, Person

def main():

    ''' SETTINGS '''
    to_calculate_removable = False # should removable edges be recalculated
    removable_links_file = "/Users/Ones-Kostik/desktop/DeepLearningCamp/DgraphRecommendation/removable_links.txt"
    prediction_mode = "connections" # write "features" otherwise todo feautures mode not implemented yet

    start = time.time()

    ''' DOWNLOAD DGRAPH DATA AND TRANSFORM IT INTO NETWORKX GRAPH '''
    dgraphinterface = DgraphInterface()
    persons = dgraphinterface.getAllPersons()
    persons = persons['persons']
    features = dgraphinterface.getAllFeatures()
    features = features['features']
    # prepare data
    G = nx.Graph() # normal graph
    G_persons = nx.Graph() # graph only with persons
    for row in tqdm(features):
        feature = row['name']
        G.add_node(feature)
    for row in tqdm(persons):
        person = row['uid']
        G.add_node(person)
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
                G_persons.add_edge(person, pers['uid'])
                # edges can be provided with additional attributes
                G[person][pers['uid']]['type'] = 'follows'
                G_persons[person][pers['uid']]['type'] = 'follows'

    # now the graph should have all nodes and edges required
    download_processing_time = time.time()
    print(f"{download_processing_time-start} seconds required to process dgraph into networkx structure...")

    initial_node_count = len(G.nodes)
    # separate edges into two lists to create data frames
    fb_df = form_data_frame_with_label(list(G.edges))

    ''' FIND UNLINKED NODES TO FORM NEGATIVE SAMPLES '''
    print('Working on unconnected node pairs...')
    # non_edges = get_unconnected(G)
    non_edges_persons = get_unconnected(G_persons)
    print('Unconnected calculated...')
    # data = form_data_frame_with_label(non_edges, 'link', 0)

    ''' REMOVE LINKS FROM CONNECTED NODE PAIRS TO CREATE TRAINING SET BASIS '''
    print("Working on removable edges in graph...")
    omissible_links = [] # contains removable edges
    if to_calculate_removable:
        G_temp = G.copy()
        for e in tqdm(G.edges):
            src = e[0]
            dst = e[1]
            if not filter_removable(src, dst, prediction_mode):
                continue
            # remove nodes pair
            G_temp.remove_edge(src, dst)
            # check if there is no splitting of graph and number of nodes is same
            if nx.number_connected_components(G_temp) == 1 and len(G_temp.nodes) == initial_node_count:
                # prepare as a line
                omissible_links.append(src + " " + dst + "\n")
            else:
                G_temp.add_edge(src, dst)

        # save removable links to some file
        with open(removable_links_file, "a") as f:
            f.writelines(omissible_links)
    else:
        # read removables from file
        with open(removable_links_file, 'r') as f:
            for line in tqdm(f):
                edge = line.strip().split(" ")
                src, dst = edge[0], edge[1]
                if filter_removable(src, dst, prediction_mode):
                    omissible_links.append((src, dst))
    print("Removable edges calculated...")
    G_train = G.copy()


    # TODO Try with different amount of disposable links
    # TODO store calculation times and precision scores for different values

    ''' Remove 5, 10, 25, 50, 75, 100% of removables links '''
    intervals = [5, 10, 25, 50, 75, 100]
    y_precision_jaccard = []
    y_precision_adamic = []
    y_precision_resall = []
    y_time_jaccard = []
    y_time_adamic = []
    y_time_resall = []

    for x in tqdm(intervals):
        x_removable = take_random_percent(omissible_links, x) # get x percent of random omissible_links
        G_train.remove_edges_from(x_removable) # remove x percent of random edges

        possible_persons_edges = non_edges_persons + x_removable # edges to predict on
        y_true = list(np.zeros(len(non_edges_persons))) + list(np.ones(len(x_removable))) # labels, 0 for non existent, 1's for removed
        print('Possible edges calculated...')

        ''' FORM POSITIVE SAMPLES FROM REMOVABLE EDGES (not required here...) '''
        # print("Prepare samples")
        # data = data.append(form_data_frame_with_label(omissible_links, 'link', 1), ignore_index=True)
        # print(data['link'].value_counts())

        ''' PERFORM LINK PREDICTION USING NETWORKX ALGORITHMS '''
        # each of following lists consists of tuples in form (u, v, p)
        # where u, v represent nodes and p probability score of forming a new edge
        start = time.time()
        jaccard_coef_predictions = nx.jaccard_coefficient(G_train, possible_persons_edges)
        tuples_jaccard = list(jaccard_coef_predictions)
        end = time.time()
        y_time_jaccard.append(end-start)

        start = time.time()
        adamic_index_predictions = nx.adamic_adar_index(G_train, possible_persons_edges)
        tuples_adamic = list(adamic_index_predictions)
        end = time.time()
        y_time_adamic.append(end-start)

        start = time.time()
        res_all_index_predictions = nx.resource_allocation_index(G_train, possible_persons_edges)
        tuples_resalloc = list(res_all_index_predictions)
        end = time.time()
        y_time_resall.append(end-start)
        # community_res_all_predictions = nx.ra_index_soundarajan_hopcroft(G_train) todo does not work yet
        print("Tuples for predictions calculated...")

        _, _, y_jaccard_scores = zip(*tuples_jaccard)
        _, _, y_adamic_scores = zip(*tuples_adamic)
        _, _, y_resalloc_scores = zip(*tuples_resalloc)

        print("Scores collected from tuples...")

        ''' EVALUATE USING AVERAGE PRECISION SCORE '''
        print("Calculate scores for predictions")
        jaccard_scored = average_precision_score(y_true, y_jaccard_scores)
        adamic_scored = average_precision_score(y_true, y_adamic_scores)
        resalloc_scored = average_precision_score(y_true, y_resalloc_scores)
        y_precision_jaccard.append(jaccard_scored)
        y_precision_adamic.append(adamic_scored)
        y_precision_resall.append(resalloc_scored)

    print(f"Jaccard precision scores: {y_precision_jaccard}")
    print(f"Adamic precision scores: {y_precision_adamic}")
    print(f"Ressource Allocation precision scores: {y_precision_resall}")
    print(f"Jaccard time scores: {y_time_jaccard}")
    print(f"Adamic time scores: {y_time_adamic}")
    print(f"Ressource Allocation precision scores: {y_time_resall}")

    plt.figure(figsize=(12, 6))
    plt.plot(x, y_precision_jaccard, label='Jaccard Coefficient')
    plt.plot(x, y_precision_adamic, label='Adamic Adar Index')
    plt.plot(x, y_precision_resall, label='Resource Allocation Index')
    plt.ylim(0, 1)
    plt.legend(loc='upper right', fontsize=15)
    plt.xlabel('% of removed links', fontsize=15)
    plt.ylabel("avg. precision score", fontsize=15)
    plt.grid(True)
    plt.title("Precision scores", fontsize=20)
    plt.show()

    plt.figure(figsize=(12, 6))
    plt.plot(x, y_time_jaccard, label='Jaccard Coefficient')
    plt.plot(x, y_time_adamic, label='Adamic Adar Index')
    plt.plot(x, y_time_resall, label='Resource Allocation Index')
    plt.legend(loc='upper right', fontsize=15)
    plt.xlabel('% of removed links', fontsize=15)
    plt.ylabel("time [s]", fontsize=15)
    plt.grid(True)
    plt.title("Calculation time", fontsize=20)
    plt.show()






def filter_removable(src: str, dst: str, prediction_mode: str) -> bool:
    return prediction_mode == "connections" and src.startswith("0x") and dst.startswith("0x")


''' Return graph's complement's edges '''
def get_unconnected(G: nx.Graph) -> list:
    G_compl = nx.complement(G)
    return list(G_compl.edges)

''' Form pandas data frame from given edges '''
def form_data_frame_with_label(edges: list, label: str = None, value: int = None) -> pd.DataFrame:
    node_list_1 = [i[0] for i in edges]
    node_list_2 = [i[1] for i in edges]
    data = pd.DataFrame({'node_1': node_list_1,
                         'node_2': node_list_2})
    # add label and value for pos/neg sampling (0, 1)
    data[label] = value
    return data

def take_random_percent(list: list, percent: int) -> list:
    sample_len = int(round(len(list)/100*percent))
    result = random.sample(list, sample_len)
    return result


if __name__ == '__main__':
    main()
