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


from DgraphRecommendation import DgraphInterface, Feature, Person

def main():

    start = time.time()
    to_plot = False # should some subgraph be plotted?
    random_walk = False # should perform random walk as prediction algorithm?

    ''' DOWNLOAD DGRAPH DATA AND TRANSFORM IT INTO NETWORKX GRAPH '''
    dgraphinterface = DgraphInterface()
    persons = dgraphinterface.getAllPersons()
    persons = persons['persons']
    features = dgraphinterface.getAllFeatures()
    features = features['features']
    # prepare data
    G = nx.Graph()
    for row in tqdm(features):
        feature = row['name']
        G.add_node(feature)
    for row in tqdm(persons):
        person = row['uid']
        G.add_node(person)
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

    # now the graph should have all nodes and edges required
    download_processing_time = time.time()
    print(download_processing_time-start)
    if to_plot:
        # plot subgraph
        plt.figure(figsize=(50, 50))
        pos = nx.random_layout(G, seed=23)
        subgraph = G.subgraph(["0xfffd8d67d9be8980", "0xfffd8d67d9bed7a2", "0xfffd8d67d9befeb0", "104", "165", "53"])
        nx.draw(subgraph, with_labels=True, pos=pos, node_size=20, alpha=0.6, width=0.7)
        plt.show()

    nodes = list(G.nodes)
    edges = list(G.edges)
    initial_node_count = len(nodes)
    # separate edges into two lists to create data frames
    node_list_1 = []
    node_list_2 = []
    for i in tqdm(edges):
        node_list_1.append(i[0])
        node_list_2.append(i[1])
    fb_df = pd.DataFrame({'node_1':node_list_1, 'node_2':node_list_2})

    ''' REMOVE LINKS FROM CONNECTED NODE PAIRS TO CREATE TRAINING SET BASIS '''
    fb_df_train = fb_df.copy()
    # empty list to store removable links
    # omissible_links_index = []
    # for i in tqdm(fb_df.index.values):              # TODO that is too slow
    #     # remove a node pair and build a new graph
    #     G_temp = nx.from_pandas_edgelist(fb_df_train.drop(index=i), "node_1", "node_2", create_using=nx.Graph())
    #     # check there is no spliting of graph and number of nodes is same
    #     if nx.number_connected_components(G_temp) == 1 and len(G_temp.nodes) == initial_node_count:
    #         omissible_links_index.append(i)
    #         fb_df_train = fb_df_train.drop(index=i)
    # print("Ommissible links number:")
    # print(len(omissible_links_index)) # the iteration speed was aroung 2.34 it/sec
    # ----------------------
    G_temp = G.copy()
    omissible_links = []
    for i in tqdm(edges):                           # FIXED that is much faster, iteration speed around 28 it/sec
        # try to remove the node pair
        G_temp.remove_edge(i[0], i[1])
        # check if there is no splitting of graph and number of ndoes is same
        if nx.number_connected_components(G_temp) == 1 and len(G_temp.nodes) == initial_node_count:
            omissible_links.append(i)
            # fb_df_train = fb_df_train.drop(index=i)
        else:
            G_temp.add_edge(i[0], i[1])
    print("Ommissible links number:")
    print(len(omissible_links))





    # deep walk specific calculations
    if random_walk:
        # get unconnected node pairs as negative samples
        G_comp = nx.complement(G)
        unconnected = list(G_comp.edges)
        print("first ten anti edges")
        print(unconnected[:10])



if __name__ == '__main__':
    main()
