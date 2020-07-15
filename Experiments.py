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

    ''' SETTINGS '''
    to_plot = False # should some subgraph be plotted?
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
    G = nx.Graph()
    G_persons = nx.Graph() # only persons
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
    if to_plot:
        # plot subgraph
        plt.figure(figsize=(50, 50))
        pos = nx.random_layout(G, seed=23)
        subgraph = G.subgraph(["0xfffd8d67d9be8980", "0xfffd8d67d9bed7a2", "0xfffd8d67d9befeb0", "104", "165", "53"])
        nx.draw(subgraph, with_labels=True, pos=pos, node_size=20, alpha=0.6, width=0.7)
        plt.show()

    initial_node_count = len(G.nodes)
    # separate edges into two lists to create data frames
    fb_df = form_data_frame_with_label(list(G.edges))

    ''' FIND UNLINKED NODES TO FORM NEGATIVE SAMPLES '''
    print('Working on unconnected node pairs...')
    non_edges = get_unconnected(G)
    non_edges_persons = get_unconnected(G_persons)
    print('Unconnected calculated...')
    data = form_data_frame_with_label(non_edges, 'link', 0)

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
    G_train_persons = G_persons.copy()
    G_train.remove_edges_from(omissible_links)
    G_train_persons.remove_edges_from(omissible_links)

    possible_persons_edges = non_edges_persons + omissible_links
    print('possible edges calculated')
    # for idx, edge in tqdm(enumerate(possible_persons_edges)):           # TODO THAT IS TOO SLOW! take complement graph only from persons
    #     if not edge[0].startswith("0x") or not edge[1].startswith("0x"):
    #         # both nodes should be persons
    #         possible_persons_edges.pop(idx)

    ''' FORM POSITIVE SAMPLES FROM REMOVABLE EDGES '''
    # print("Prepare samples")
    # data = data.append(form_data_frame_with_label(omissible_links, 'link', 1), ignore_index=True)
    # print(data['link'].value_counts())

    ''' PERFORM LINK PREDICTION USING NETWORKX ALGORITHMS '''
    # each of following lists consists of tuples in form (u, v, p)
    # where u, v represent nodes and p probability of forming a new edge
    jaccard_coef_predictions = nx.jaccard_coefficient(G_train, possible_persons_edges)
    # adamic_index_predictions = nx.adamic_adar_index(G_train, possible_persons_edges)
    # community_res_all_predictions = nx.ra_index_soundarajan_hopcroft(G_train) todo does not work yet
    tuples = list(jaccard_coef_predictions)



    ''' EVALUATE USING AVERAGE PRECISION SCORE '''
    #jaccard_scored = average_precision_score(y_true, y_jaccard)
    #adamic_scored = average_precision_score(y_true, y_adamic)





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

if __name__ == '__main__':
    main()
