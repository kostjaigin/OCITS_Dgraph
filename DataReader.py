from DgraphRecommendation import Person
import easygui
from os import listdir
from os import path
from tqdm import tqdm

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
    Read facebook (or twitter) files content into persons and all_features
    '''
    def read_from_facebook(self):
        easygui.msgbox("Please, select the data folder ('facebook') using the file dialog")
        data_dir = easygui.diropenbox() # where to take files from
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




