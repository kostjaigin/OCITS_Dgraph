from os import listdir
from DgraphRecommendation import Person
from DgraphRecommendation import DataReader
from DgraphRecommendation import DgraphInterface
import time

''' 
Reads twitter data files from here: https://snap.stanford.edu/data/ego-Twitter.html
Sets the matching schema in dgraph instance
Translates into dgraph format and
Stores data locally in RDF files
'''

def main():

    ''' INIT SCHEMA '''
    graphinterface = DgraphInterface()
    print("Dropping all...")
    graphinterface.drop_all()
    print("Setting the schema...")
    graphinterface.set_schema()

    print("Starting the file reading...")

    ''' Read person's files one by one '''

    path = "/Users/Ones-Kostik/Desktop/TwitterData/twitter"
    files = listdir(path)
    reader = DataReader() # contains help functions for data processing
    files.sort()
    all_features = [] # remember features for later
    filesnum = len(files)
    # features contained in the data contain special characters that are not allowed to be contained in dgraph string
    special_characters = "!\"@#$%^&*()[]{};:,./<>?\|`~-=_+"
    random_words = ['alpha', 'beta', 'gamma', 'maxima', 'centavra', 'lorem', 'ipsum', 'quatro', 'hoax', 'grade', 'study', 'key', 'utopian', 'tee', 'search', 'grind']
    random_words += ["angle", "statement", "filthy", "leak", "dogs", "aback", "scrub", "purpose", "discussion", "lizards", "legs", "sample", "swot", "flock", "zinc"]

    for i, file in enumerate(files):
        print(f'{i}/{filesnum} files processed')
        # first part contains id, second part item kind
        parts = file.split('.')
        id = parts[0]
        kind = parts[1]
        filepath = path + '/' + file
        person = reader.getPerson(id)

        # since we go through sorted files they come directly after each other
        # circles -> edges -> egofeat -> feat -> featnames
        if kind == "circles":
            continue # not interested in circles for now
        elif kind == "edges":
            # might contains nodes not mentioned in filenames
            with open(filepath, 'r') as f:
                for line in f:
                    line = line.strip()
                    data = line.split(" ")
                    follower = reader.getPerson(data[0])
                    follows = reader.getPerson(data[1])
                    follower.follow(follows)
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
                for line in f:
                    line = line.strip()
                    # if line's first element's len bigger 1 it is an id
                    data = line.split(" ")
                    first_elem = data[0]
                    if len(first_elem) > 0:
                        target = reader.getPerson(first_elem)
                        data.pop(0)
                    # read raw features for target
                    features = [int(x) for x in data]
                    target.add_raw_features(features)
        elif kind == "featnames":
            with open(filepath, 'r') as f:
                for line in f:
                    line = line.strip() # get rid of /n or space
                    data = line.split(" ")
                    feature_order = int(data[0])
                    feature_name = data[1]
                    # remember features for later...
                    feature_name_contains_special = any(not c.isalnum() for c in feature_name)
                    if feature_name_contains_special:
                        feature_name = feature_name.translate({ord(c): random_words[i] for i, c in enumerate(special_characters)})
                    if feature_name not in features:
                        all_features.append(feature_name)
                    for iter_person in reader.iteration_persons.values():
                        if iter_person.hasFeature(feature_order):
                            iter_person.add_feature(feature_name)
            # featnames is the last file with id
            reader.clearIteration()
    # add edges from combined.txt file
    path = "/Users/Ones-Kostik/Desktop/TwitterData/twitter_combined.txt"
    with open(path, 'r') as f:
        for line in f:
            line = line.strip() # get rid of /n or space
            data = line.split(" ")
            if data[0] in reader.persons and data[1] in reader.persons:
                follower = reader.persons[data[0]]
                follows = reader.persons[data[1]]
                follower.follow(follows)

    testing_person = reader.persons['12831']
    assert len(testing_person.get_follows()) == 244
    assert len(testing_person.get_features()) == 53

    # save data into rdf file
    rdffile = "/Users/Ones-Kostik/dgraph/twitter.rdf"
    lines = []
    all_features = list(set(all_features))

    size = len(all_features)
    for i, feature in enumerate(all_features):
        print(f'{i}/{size} processed features')
        typeline = f'<_:{feature}> <dgraph.type> "Feature" .\n'
        nameline = f'<_:{feature}> <name> "{feature}" .\n'
        lines.append(typeline)
        lines.append(nameline)


    size = len(reader.persons.values())
    for i, person in enumerate(reader.persons.values()):
        print(f'{i}/{size} processed persons')
        typeline = f'<_:{person.id}> <dgraph.type> "Person" .\n'
        idline = f'<_:{person.id}> <id> "{person.id}" .\n'
        lines.append(typeline)
        lines.append(idline)
        for feature in person.get_features():
            line = f'<_:{person.id}> <tracks> <_:{feature}> .\n'
            lines.append(line)

    for i, person in enumerate(reader.persons.values()):
        print(f'{i}/{size} processed persons for following')
        for followed in person.get_follows():
            followline = f'<_:{person.id}> <follows> <_:{followed.id}> .\n'
            lines.append(followline)

    # write lines to the .rdf file
    with open(rdffile, 'a') as f:
        f.writelines(lines)


if __name__ == '__main__':
    main()



