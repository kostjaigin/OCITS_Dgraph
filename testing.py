import easygui
from os import path
import os
import http.client
import time
import json
from tqdm import tqdm
import networkx as nx

from DgraphRecommendation import DgraphInterface
from DgraphRecommendation.DataLoader import download_stored_nodes, read_and_upload_facebook


def main():
    # graphinterface = DgraphInterface()
    # location = "/Users/Ones-Kostik/Desktop/example"
    # stored_persons, stored_features = download_stored_nodes(graphinterface, location)
    # all_persons, all_features = read_from_stored_to_dic(stored_persons, stored_features)
    # print(all_persons)
    G = nx.Graph()
    G.add_edges_from([(1, 2), (1, 3), (1, 4), (3, 4), (4, 5)])
    for x in G.nodes:
        print(x)

'''
Parse stored_* files and store information from there in forms of dictionaries
persons dict with keys of ids and values of uids
features dict with keys of names and values of uids
'''
# todo test it
def read_from_stored_to_dic(stored_persons: str, stored_features: str) -> (dict, dict):
    file = stored_persons
    with open(file, 'r') as f:
        data = json.load(f)
        data = data['data']['total']
    all_persons = dict()
    for row in tqdm(data):
        row_id = row['id']
        row_uid = row['uid']
        all_persons[row_id] = row_uid

    file = stored_features
    with open(file, 'r') as f:
        data = json.load(f)
        data = data['data']['total']
    all_features = dict()
    for row in tqdm(data):
        row_name = row['name']
        row_uid = row['uid']
        all_features[row_name] = row_uid

    return all_persons, all_features

if __name__ == '__main__':
    main()