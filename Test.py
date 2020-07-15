import pandas as pd
import numpy as np
import random
import networkx as nx
from tqdm import tqdm
import re
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix

def main():
    nodesfile = "/Users/Ones-Kostik/Desktop/fb-pages-food/fb-pages-food.nodes"
    edgesfile = "/Users/Ones-Kostik/Desktop/fb-pages-food/fb-pages-food.edges"
    # load nodes details
    with open(nodesfile) as f:
        fb_nodes = f.read().splitlines()

        # load edges (or links)
    with open(edgesfile) as f:
        fb_links = f.read().splitlines()

    # capture nodes in 2 separate lists
    node_list_1 = []
    node_list_2 = []

    for i in tqdm(fb_links):
        node_list_1.append(i.split(',')[0])
        node_list_2.append(i.split(',')[1])

    fb_df = pd.DataFrame({'node_1': node_list_1, 'node_2': node_list_2})
    # create graph
    G = nx.from_pandas_edgelist(fb_df, "node_1", "node_2", create_using=nx.Graph())
    initial_node_count = len(G.nodes)

    fb_df_temp = fb_df.copy()

    # empty list to store removable links
    omissible_links_index = []
    G_temp = G.copy()
    deletable_links = []
    for i in tqdm(fb_df.index.values):
        # remove a node pair and build a new graph
        source = fb_df.iat[i, 0]
        dest = fb_df.iat[i, 1]
        G_temp.remove_edge(source, dest)

        # check there is no spliting of graph and number of nodes is same
        if nx.number_connected_components(G_temp) == 1 and len(G_temp.nodes) == initial_node_count:
            omissible_links_index.append(i)
            deletable_links.append(str((source, dest))+"\n")
            fb_df_temp = fb_df_temp.drop(index=i)
        else:
            G_temp.add_edge(source, dest)

    print("omissible:")
    print(len(omissible_links_index))
    print(f"remaining graph edges len: {len(G_temp.edges)}")


if __name__ == '__main__':
    main()