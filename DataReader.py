import networkx as nx

from DgraphRecommendation import Person, DgraphInterface
from DgraphRecommendation.DataLoader import download_stored_nodes
from DgraphRecommendation.Feature import Feature
import easygui
from os import listdir
from os import path
import os
from tqdm import tqdm
import json


class DataReader:
    '''
    Help class to read data from files
    '''

    def __init__(self):
        self.persons = dict()
        self.all_features = []
        self.iteration_persons = dict()

    '''
    :returns person with given id
    if person not recorded yet, record it 
    '''

    def getPerson(self, id) -> Person:
        if id not in self.persons:
            person = Person(id)
            self.persons[id] = person
        if id not in self.iteration_persons:
            self.iteration_persons[id] = self.persons[id]
        return self.persons[id]

    '''
    method called when we are done working with one id's files
    '''

    def clearIteration(self):
        for person in self.iteration_persons.values():
            person.clear_raw_features()
        self.iteration_persons = dict()

    ''' 
    Reads facebook (or twitter) files content into persons and all_features
    '''

    def read_from_facebook(self):
        easygui.msgbox("Please, select the data folder ('facebook') using the file dialog")
        data_dir = easygui.diropenbox()  # where to take files from
        if data_dir is None:
            return
        files = listdir(data_dir)
        files.sort()

        for file in tqdm(files):
            # first part contains id, second part item kind
            parts = file.split('.')
            id = parts[0]
            kind = parts[1]
            filepath = path.join(data_dir, file)
            person = self.getPerson(id)
            # since we go through sorted files they come directly after each other
            # circles -> edges -> egofeat -> feat -> featnames
            if kind == "circles":
                continue  # not interested in circles for now
            elif kind == "edges":
                # might contains nodes not mentioned in filenames
                with open(filepath, 'r') as f:
                    for line in f:
                        line = line.strip()
                        data = line.split(" ")
                        follower = self.getPerson(data[0])
                        follows = self.getPerson(data[1])
                        # facebook data is undirected
                        follower.follow(follows)
                        follows.follow(follower)
            elif kind == "egofeat":
                # read raw features (0 & 1)
                with open(filepath, 'r') as f:
                    for line in f:
                        line = line.strip()
                        features = [int(x) for x in line.split(" ")]
                        person.add_raw_features(features)
            elif kind == "feat":
                # read raw features in ego-space
                with open(filepath, 'r') as f:
                    # read raw features for target
                    target = person
                    # each line contains features for one node id
                    for line in f:
                        line = line.strip()
                        data = line.split(" ")
                        target = self.getPerson(data[0])
                        data.pop(0)
                        features = [int(x) for x in data]
                        target.add_raw_features(features)
            elif kind == "featnames":
                with open(filepath, 'r') as f:
                    for line in f:
                        line = line.strip()  # get rid of /n or space
                        data = line.split(" ")
                        feature_order = int(data[0])
                        feature_name = data[-1]
                        if feature_name not in self.all_features:
                            self.all_features.append(feature_name)
                        for iter_person in self.iteration_persons.values():
                            if iter_person.hasFeature(feature_order):
                                iter_person.add_feature(feature_name)
                # featnames is the last file with id
                self.clearIteration()

        easygui.msgbox("Files processed. Please select the combined file ('*_combined.txt') for further processing..")
        filepath = easygui.fileopenbox()
        if filepath is None:
            return
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                data = line.split(" ")
                if data[0] in self.persons and data[1] in self.persons:
                    follower = self.persons[data[0]]
                    follows = self.persons[data[1]]
                    follower.follow(follows)
                    follows.follow(follower)

    '''
    Writes (outputs) persons, all_feautures to .rdf files (no links)
    :returns persons_file adress + features_file adress
    '''
    def write_data_to_rdf(self):
        # check if required files exist already, if so return them
        filedir = os.getcwd()
        features_file = path.join(filedir, "features_facebook.rdf")
        persons_file = path.join(filedir, "persons_facebook.rdf")
        if os.path.exists(features_file) and len(open(features_file).readlines()) > 0 \
            and os.path.exists(persons_file) and len(open(persons_file).read()) > 0:
            return persons_file, features_file
        if len(self.persons) == 0 or len(self.all_features) == 0:
            easygui.msgbox("Please, perform data reading first")
            return

        if path.exists(features_file):
            os.remove(features_file)  # remove old file

        lines = []
        all_features = list(set(self.all_features))
        # WRITE FEATURES
        for feature in tqdm(all_features):
            typeline = f'<_:{feature}> <dgraph.type> "Feature" .\n'
            nameline = f'<_:{feature}> <name> "{feature}" .\n'
            lines.append(typeline)
            lines.append(nameline)
        with open(features_file, 'a') as f:
            f.writelines(lines)

        if path.exists(persons_file):
            os.remove(persons_file)  # remove old file

        # WRITE PERSONS
        lines = []
        for person in tqdm(self.persons.values()):
            typeline = f'<_:{person.id}> <dgraph.type> "Person" .\n'
            idline = f'<_:{person.id}> <id> "{person.id}" .\n'
            lines.append(typeline)
            lines.append(idline)
        with open(persons_file, 'a') as f:
            f.writelines(lines)

        return persons_file, features_file

    '''
    Writes links between persons and features to .rdf files
    :arg stored_persons_loc where stored persons file can be found
    :arg stored_features_loc where stored features file can be found
    '''

    def write_links_to_rdf(self, stored_persons_loc: str, stored_features_loc: str):
        file = stored_persons_loc
        with open(file, 'r') as f:
            data = json.load(f)
            data = data['data']['total']
        for row in tqdm(data):
            row_id = row['id']
            self.persons[row_id].uid = row['uid']

        file = stored_features_loc
        with open(file, 'r') as f:
            data = json.load(f)
            data = data['data']['total']
        all_features = dict()
        for row in tqdm(data):
            row_name = row['name']
            row_uid = row['uid']
            feature = Feature(row_name, row_uid)
            all_features[row_name] = feature

        # save relations
        wdir = os.getcwd()
        follows_lines = []
        follows_rdffile = path.join(wdir, "follows_facebook.rdf")
        if path.exists(follows_rdffile):
            os.remove(follows_rdffile)  # remove old file
        tracks_lines = []
        tracks_rdffile = path.join(wdir, "tracks_facebook.rdf")
        if path.exists(tracks_rdffile):
            os.remove(tracks_rdffile)  # remove old file

        for person in tqdm(self.persons.values()):
            person_uid = person.uid
            if person_uid is None:
                # todo change to log, throw an error
                easygui.msgbox("Person not stored in dgraph: " + person.id + ", exiting...")
                print("Exiting...")
                return
            for followed in person.get_follows():
                target_uid = self.persons[followed.id].uid
                if target_uid is None:
                    easygui.msgbox("Person not stored in dgraph: " + followed.id + ", exiting..")
                    print("Exiting...")
                    return
                followline = f'<{person_uid}> <follows> <{target_uid}> .\n'
                follows_lines.append(followline)
            for feature in person.get_features():
                feature_uid = all_features[feature].uid
                if feature_uid is None:
                    easygui.msgbox("Feature not stored in dgraph: " + feature + ", exiting...")
                    print("Exiting...")
                    return
                tracksline = f'<{person_uid}> <tracks> <{feature_uid}> .\n'
                tracks_lines.append(tracksline)
            # write lines to the .rdf files
        with open(follows_rdffile, 'a') as f:
            f.writelines(follows_lines)
        with open(tracks_rdffile, 'a') as f:
            f.writelines(tracks_lines)

        return follows_rdffile, tracks_rdffile

    '''
    Parse stored_* files and store information from there in forms of dictionaries
    persons dict with keys of ids and values of uids
    features dict with keys of names and values of uids
    '''
    def read_from_stored_to_dic(self, stored_persons: str, stored_features: str) -> (dict, dict):
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

    '''
    Write nodes from networkx graph to .rdf file
    '''
    def write_graph_to_rdf(self, G: nx.Graph, graphinterface: DgraphInterface, location: str) -> (str, str):
        stored_persons, stored_feats = download_stored_nodes(graphinterface, location)
        _, all_feats = self.read_from_stored_to_dic(stored_persons, stored_feats)
        lines = []
        for node in G.nodes:
            if node.startswith("0x"): # person
                typeline = f'<{node}> <dgraph.type> "Person"\n'
            else: # feature
                typeline = f'<{all_feats[node]}> <dgraph.type> "Feature"\n'
            lines.add(typeline)
        # save in nodes file
        rdffile_nodes = path.join(location, "graph_nodes.rdf")
        with open(rdffile_nodes, 'a') as f:
            f.writelines(lines)
        # do edges
        lines = []
        for node in G.nodes:
            if not node.startswith("0x"): # if not a person
                continue
            adjs = G[node]
            for adj in adjs:
                if adj.startswith("0x"): # if a person
                    followsline = f'<{node}> <follows> <{adj}>\n'
                    lines.append(followsline)
                else:
                    tracksline = f'{node} <tracks> <{all_feats[adj]}>\n'
                    lines.append(tracksline)
        # save in edges file
        rdffile_edges = path.join(location, "graph_edges.rdf")
        with open(rdffile_edges, 'a') as f:
            f.writelines(lines)

        return rdffile_nodes, rdffile_edges




