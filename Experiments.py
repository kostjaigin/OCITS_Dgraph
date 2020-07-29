'''
Here i will conduct the experiments with link prediction algorithms
'''
import networkx as nx
import time
from math import sqrt
from sklearn.metrics import roc_auc_score, average_precision_score
from tqdm import tqdm
import os
import random
import numpy as np


from DgraphRecommendation import DgraphInterface, Feature, Person
from DgraphRecommendation import config
from DgraphRecommendation.DataLoader import read_and_upload_facebook, prepare_predictable


def main():

    interface = DgraphInterface()

    ''' SETTINGS '''
    # check if dgraph reinitialization required
    load_dgraph = interface.getNumbers() != (config.dgraph_settings['number_persons'], config.dgraph_settings['number_features'],
                                                     config.dgraph_settings['number_connections_persons'], config.dgraph_settings[
                                                         'number_connections_persons_features']) # if to reload data into dgraph: set to True to force reload
    predict_persons = False  # to predict [a] connections between persons, otherwise [b] predict new features of persons
    use_nx = True # to calculate values/times using networkx provided algorithms
    use_k_shortest = False # to calculate values/times using k-shortest-path implementation

    cwd = os.getcwd()
    non_edges_file = os.path.join(cwd, f"non_edges_persons_{predict_persons}.txt")
    removable_links_file = os.path.join(cwd, f"removable_links_persons_{predict_persons}.txt")

    if load_dgraph:
        read_and_upload_facebook() # if required reload dgraph
        if os.path.exists(removable_links_file):
            os.remove(removable_links_file) # these are useless now
        if os.path.exists(non_edges_file):
            os.remove(non_edges_file) # these are useless now

    to_calculate_removable = not os.path.exists(removable_links_file)  # should removable edges be recalculated
    to_calculate_non_edges = not os.path.exists(non_edges_file)  # should non-edges (complement graph) be recalculated
    separator = " " # what sign to use as separator when writing results down to files

    start = time.time()
    ''' DOWNLOAD DGRAPH DATA AND TRANSFORM IT INTO NETWORKX GRAPH '''
    # G_inv contains [a] only connections between persons [b] normal graph
    G, G_inv = download_graph(predict_persons, interface)
    # now the graph should have all nodes and edges required
    download_processing_time = time.time()
    print(f"{download_processing_time-start} seconds required to process dgraph into networkx structure...")

    initial_node_count = len(G.nodes)

    ''' FIND UNLINKED NODES TO FORM NEGATIVE SAMPLES '''
    print('Working on unconnected node pairs in inv graph...')
    non_edges_inv = []
    if to_calculate_non_edges:
        non_edges_inv = get_unconnected(G_inv)
        write_links_down_to(non_edges_inv, non_edges_file, separator)
    else:
        # read non edges from file
        with open(non_edges_file, 'r') as f:
            for line in tqdm(f):
                edge = line.strip().split(separator)
                src, dst = edge[0], edge[1]
                if is_removable(src, dst, predict_persons):
                    non_edges_inv.append((src, dst))
    print('Unconnected calculated...')

    ''' REMOVE LINKS FROM CONNECTED NODE PAIRS TO CREATE TRAINING SET BASIS '''
    print("Working on removable edges in graph...")
    omissible_links = [] # contains removable edges
    if to_calculate_removable:
        G_temp = G.copy()
        for e in tqdm(G.edges):
            src = e[0]
            dst = e[1]
            if not is_removable(src, dst, predict_persons):
                continue
            # remove nodes pair
            G_temp.remove_edge(src, dst)
            # check if there is no splitting of graph and number of nodes is same
            if nx.number_connected_components(G_temp) == 1 and len(G_temp.nodes) == initial_node_count:
                # prepare as a line
                omissible_links.append((src, dst))
            else:
                G_temp.add_edge(src, dst)
        write_links_down_to(omissible_links, removable_links_file, separator)
    else:
        # read removables from file
        with open(removable_links_file, 'r') as f:
            for line in tqdm(f):
                edge = line.strip().split(separator)
                src, dst = edge[0], edge[1]
                if is_removable(src, dst, predict_persons):
                    omissible_links.append((src, dst))
    print("Removable edges calculated...")

    print(f"length of non-edges persons: {len(non_edges_inv)}")
    print(f"length of omissible: {len(omissible_links)}")

    ''' REMOVE 5, 10, 25, 50, 75, 100% OF REMOVABLE LINKS '''
    intervals = [5, 10, 25, 50, 75, 100]
    y_precision_jaccard = []
    y_precision_adamic = []
    y_precision_resall = []
    y_precision_top_1 = []
    y_precision_top_4 = []
    y_precision_top_16 = []
    y_time_jaccard = []
    y_time_adamic = []
    y_time_resall = []
    y_time_top_1 = []
    y_time_top_4 = []
    y_time_top_16 = []

    for x in tqdm(intervals):
        G_train = G.copy()
        x_removable = take_random_percent(omissible_links, x) # get x percent of random omissible_links
        G_train.remove_edges_from(x_removable) # remove x percent of random edges

        possible_persons_edges = non_edges_inv + x_removable # edges to predict on
        y_true = list(np.zeros(len(non_edges_inv))) + list(np.ones(len(x_removable))) # labels, 0 for non existent, 1's for removed
        print('Possible edges calculated...')

        if use_k_shortest:
            # mark remaining edges as "predictable"
            predictable_file = prepare_predictable(G_train)
            # load predictables into dgraph
            interface.addPredictableEdges(predictable_file)
            # perform prediction:
            k_1_rates, calctime = k_shortest_prediction(possible_persons_edges, 1)
            y_time_top_1.append(calctime)
            k_1_score = average_precision_score(y_true, k_1_rates)
            y_precision_top_1.append(k_1_score)

            k_4_rates, calctime = k_shortest_prediction(possible_persons_edges, 4)
            y_time_top_4.append(calctime)
            k_4_score = average_precision_score(y_true, k_4_rates)
            y_precision_top_4.append(k_4_score)

            k_16_rates, calctime = k_shortest_prediction(possible_persons_edges, 16)
            y_time_top_16.append(calctime)
            k_16_score = average_precision_score(y_true, k_16_rates)
            y_precision_top_16.append(k_16_score)

            # remove these edges from dgraph
            interface.remove_predictable(predictable_file)



        if use_nx:
            ''' PERFORM LINK PREDICTION USING NETWORKX ALGORITHMS '''
            # each of following lists consists of tuples in form (u, v, p)
            # where u, v represent nodes and p (probability) score of forming a new edge
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

    if use_nx: # todo do check if k_shortest too
        lines = []
        # todo lines append k_shortest results and times
        lines.append(f"Jaccard precision scores: {y_precision_jaccard}\n")
        lines.append(f"Adamic precision scores: {y_precision_adamic}\n")
        lines.append(f"Ressource Allocation precision scores: {y_precision_resall}\n")
        lines.append(f"Jaccard time scores: {y_time_jaccard}\n")
        lines.append(f"Adamic time scores: {y_time_adamic}\n")
        lines.append(f"Ressource Allocation precision scores: {y_time_resall}\n")
        print(lines)
        with open(config.results_file, 'a') as f:
            f.writelines(lines)



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

def is_removable(src: str, dst: str, predict_persons) -> bool:
    if predict_persons:
        return src.startswith("0x") and dst.startswith("0x") # BOTH PERSONS
    else:
        return src[:2] != dst[:2] and (src.startswith("0x") or dst.startswith("0x")) # ONE PERSON, ANOTHER ONE FEATURE

''' Return graph's complement's edges '''
def get_unconnected(G: nx.Graph) -> list:
    G_compl = nx.complement(G)
    return list(G_compl.edges)

def take_random_percent(list: list, percent: int) -> list:
    sample_len = int(round(len(list)/100*percent))
    result = random.sample(list, sample_len)
    return result

def write_links_down_to(links: list, file: str, separator: str):
    for link in links:
        with open(file, "a") as f:
            line = link[0] + separator + link[1] + '\n'
            f.write(line)

def k_shortest_prediction(edges, k) -> (list, int):
    interface = DgraphInterface()
    time_k = 0
    rates = []
    for edge in edges:
        src = edge[0]  # should both be uid
        dst = edge[1]
        ppl, latency = interface.get_k_shortest_pathes(k, src, dst)
        start_delta = int(latency.total_ns) * (10**(-9))  # to secs
        time_k += start_delta
        start = time.time()
        s_k = sum([1 / sqrt(int(item["_weight_"])) for item in ppl["_path_"]])
        end = time.time()
        rates.append(s_k)
        time_k += end - start
    return rates, time_k


if __name__ == '__main__':
    main()
