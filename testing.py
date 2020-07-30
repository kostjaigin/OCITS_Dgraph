import os
import matplotlib.pyplot as plt
import networkx as nx
import time

from DgraphRecommendation import DgraphInterface

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
            i += 1
            edges.append((src, dst))
            if i == number:
                break
    return edges

def k_shortest_prediction(G, src, dst, k):
    shortests = nx.shortest_simple_paths(G, src, dst)
    paths = []
    for c, path in enumerate(shortests):
        paths += path
        if c == k-1:
            break
    return paths

def main():

    graphinterface = DgraphInterface()

    G, _ = download_graph(True, graphinterface)
    edges = get_unconnected(10)
    ks = [1, 4, 8, 16]

    dgraph_mean_times = []
    nx_mean_times = []

    for k in ks:
        k_mean_dgraph = 0
        k_mean_nx = 0
        for edge in edges:
            src = edge[0]
            dst = edge[1]
            ppl, latency = graphinterface.get_k_shortest_pathes(k, src, dst)
            k_mean_dgraph += latency.processing_ns*(10**(-9))
            start = time.time()
            shortests = k_shortest_prediction(G, src, dst, k)
            end = time.time()
            k_mean_nx += (end-start)
        k_mean_dgraph = k_mean_dgraph/len(edges)
        k_mean_nx = k_mean_nx/len(edges)
        dgraph_mean_times.append(k_mean_dgraph)
        nx_mean_times.append(k_mean_nx)

    print(dgraph_mean_times)
    print(nx_mean_times)





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

def plot_precisions(intervals, precisions: dict):
    ''' PLOT THE RESULTS '''
    plt.figure(figsize=(12, 6))
    for precision in precisions:
        plt.plot(intervals, precisions[precision], label=precision)
    plt.ylim(0, 1)
    plt.legend(loc='lower right', fontsize=15)
    plt.xlabel('# samples', fontsize=15)
    plt.ylabel("avg. precision score", fontsize=15)
    plt.grid(True)
    plt.title("Precision scores", fontsize=20)
    plt.show()

def plot_times(intervals, times: dict):
    plt.figure(figsize=(12, 6))
    for t in times:
        plt.plot(intervals, times[t], label=t)
    plt.legend(loc='upper left', fontsize=15)
    plt.xlabel('# samples', fontsize=15)
    plt.ylabel("time [s]", fontsize=15)
    plt.grid(True)
    plt.title("Calculation time", fontsize=20)
    plt.show()

if __name__ == '__main__':
    main()