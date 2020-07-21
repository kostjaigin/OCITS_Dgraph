from os import listdir
from DgraphRecommendation import Person
from DgraphRecommendation import DataReader
from DgraphRecommendation import DgraphInterface
import time
import json
from DgraphRecommendation import Feature
import random

''' 
Reads facebook data files from here: https://snap.stanford.edu/data/ego-Facebook.html
Sets the matching schema in dgraph instance
Translates into dgraph format and
Stores data locally in RDF files
The Script works in two phases:
    - Phase 1: load main data [load_main_data set to True]
    -- Creates files features_facebook.rdf and persons_facebook.rdf without relations (edges)
    
    After phase 1 i downloaded .rdf files with persons and features uids using the command line tool curl:
    curl -H "Content-Type: application/graphql+-" "localhost:8080/query" -XPOST -d $'{ total(func: has(name)) {   name   uid  }}' > stored_features
    curl -H "Content-Type: application/graphql+-" "localhost:8080/query" -XPOST -d $'{ total(func: has(id)) {   id   uid  }}' > stored_persons
    
    - Phase 2: connect loaded data [load_main_data set to False]
    -- Creates follows_facebook.rdf and tracks_facebook.rdf containing information about edges in the graph structure
'''

def main():

    load_main_data = False # set to True to reload features and persons to corresponding .rdf files
    reset_schema = False # set to True to reload db completely
    load_uids_manually = False # set to True if you are trying to get uids of stored objects using dgraph client

    graphinterface = DgraphInterface()
    if reset_schema:
        print('Removing old schema and data')
        graphinterface.drop_all()
        print('Setting db schema')
        graphinterface.set_schema()

    print("Starting the file reading...")

    ''' Read person's files one by one '''

    reader = DataReader()
    reader.read_from_facebook()

    testing_person = reader.persons['3980']
    assert len(testing_person.get_follows()) == 59

    collectedpersons = list(reader.persons.values())
    # random selection for check
    for i in range(1, 4):
        testing_person = random.choice(collectedpersons)
        print(f'testing person {i} with id {testing_person.id}')
        print(f'person tracks {len(testing_person.get_features())}')
        print(f'person follows {len(testing_person.get_follows())}')
        print("-"*10)

    if load_main_data:
        # save data into rdf file
        rdffile = "/Users/Ones-Kostik/dgraph/features_facebook.rdf"
        lines = []
        all_features = list(set(reader.all_features))

        # WRITE FEATURES
        size = len(all_features)
        for i, feature in enumerate(all_features):
            print(f'{i}/{size} processed features')
            typeline = f'<_:{feature}> <dgraph.type> "Feature" .\n'
            nameline = f'<_:{feature}> <name> "{feature}" .\n'
            lines.append(typeline)
            lines.append(nameline)
        with open(rdffile, 'a') as f:
            f.writelines(lines)

        lines = []
        rdffile = "/Users/Ones-Kostik/dgraph/persons_facebook.rdf"

        # WRITE PERSONS
        size = len(reader.persons.values())
        for i, person in enumerate(reader.persons.values()):
            print(f'{i}/{size} processed persons')
            typeline = f'<_:{person.id}> <dgraph.type> "Person" .\n'
            idline = f'<_:{person.id}> <id> "{person.id}" .\n'
            lines.append(typeline)
            lines.append(idline)
        with open(rdffile, 'a') as f:
            f.writelines(lines)
    elif load_uids_manually:
        # IS TOO SLOW
        # save relations
        follows_lines = []
        follows_rdffile = "/Users/Ones-Kostik/dgraph/follows_facebook.rdf"
        tracks_lines = []
        tracks_rdffile = "/Users/Ones-Kostik/dgraph/tracks_facebook.rdf"
        size = len(reader.persons.values())
        for i, person in enumerate(reader.persons.values()):
            person_uid = graphinterface.find_by_id(person.id)
            if person_uid is None:
                print("Person not stored in dgraph: " + person.id)
                print("Exiting...")
                return
            for followed in person.get_follows():
                target_uid = graphinterface.find_by_id(follower.id)
                if target_uid is None:
                    print("Person not stored in dgraph: " + followed.id)
                    print("Exiting...")
                    return
                followline = f'<{person_uid}> <follows> <{target_uid}> .\n'
                follows_lines.append(followline)
            for feature in person.get_features():
                feature_uid = graphinterface.find_feature_by_name(feature)
                if feature_uid is None:
                    print("Feature not stored in dgraph: " + feature)
                    print("Exiting...")
                    return
                tracksline = f'<{person_uid}> <tracks> <{feature_uid}> .\n'
                tracks_lines.append(tracksline)
            print(f'{i}/{size} processed persons')
        # write lines to the .rdf files
        with open(follows_rdffile, 'a') as f:
            f.writelines(follows_lines)
        with open(tracks_rdffile, 'a') as f:
            f.writelines(tracks_lines)
    else:
        # load uids from stored files and create relations .rdf files manually
        stored_persons = ''
        file = '/Users/Ones-Kostik/dgraph/stored_persons'
        with open(file, 'r') as f:
            data = json.load(f)
            data = data['data']['total']
        size = len(data)
        for i, row in enumerate(data):
            print(f'Processing {i}/{size} row in collected persons data')
            row_id = row['id']
            reader.persons[row_id].uid = row['uid']
        file = '/Users/Ones-Kostik/dgraph/stored_features'
        with open(file, 'r') as f:
            data = json.load(f)
            data = data['data']['total']
        size = len(data)
        all_features = dict()
        for i, row in enumerate(data):
            print(f'Processing {i}/{size} row in collected features data')
            row_name = row['name']
            row_uid = row['uid']
            feature = Feature(row_name, row_uid)
            all_features[row_name] = feature
        # save relations
        follows_lines = []
        follows_rdffile = "/Users/Ones-Kostik/dgraph/follows_facebook.rdf"
        tracks_lines = []
        tracks_rdffile = "/Users/Ones-Kostik/dgraph/tracks_facebook.rdf"
        size = len(reader.persons.values())
        for i, person in enumerate(reader.persons.values()):
            person_uid = person.uid
            if person_uid is None:
                print("Person not stored in dgraph: " + person.id)
                print("Exiting...")
                return
            for followed in person.get_follows():
                target_uid = reader.persons[followed.id].uid
                if target_uid is None:
                    print("Person not stored in dgraph: " + followed.id)
                    print("Exiting...")
                    return
                followline = f'<{person_uid}> <follows> <{target_uid}> .\n'
                follows_lines.append(followline)
            for feature in person.get_features():
                feature_uid = all_features[feature].uid
                if feature_uid is None:
                    print("Feature not stored in dgraph: " + feature)
                    print("Exiting...")
                    return
                tracksline = f'<{person_uid}> <tracks> <{feature_uid}> .\n'
                tracks_lines.append(tracksline)
            print(f'{i}/{size} processed persons')
        # write lines to the .rdf files
        with open(follows_rdffile, 'a') as f:
            f.writelines(follows_lines)
        with open(tracks_rdffile, 'a') as f:
            f.writelines(tracks_lines)

    print('Final persons size:')
    print(len(reader.persons.values()))
    print("Final features size:")
    print(len(all_features.values()))

if __name__ == '__main__':
    main()



