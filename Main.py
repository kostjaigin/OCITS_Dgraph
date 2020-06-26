from os import listdir
from DgraphRecommendation import Person
from DgraphRecommendation import DataReader
from DgraphRecommendation import DgraphInterface

''' 
Reads twitter data files from here: https://snap.stanford.edu/data/ego-Twitter.html
Translates into dgraph format and stores it in dgraph instance
TODO Stores it locally in RDF files
'''

def main():

    graphinterface = DgraphInterface()
    print("Dropping all...")
    graphinterface.drop_all()
    # init schema
    print("Setting the schema...")
    graphinterface.set_schema()

    print("Starting the file reading...")

    ''' Read person's files one by one '''

    path = "/Users/Ones-Kostik/Desktop/TwitterData/twitter"
    files = listdir(path)
    reader = DataReader() # contains help functions for data processing
    files.sort()
    filesnum = len(files)

    for i, file in enumerate(files):
        print(f'{i}/{filesnum}')
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

    # go through persons in reader's collection and store in dgraph
    size = len(reader.persons.values())
    for i, person in enumerate(reader.persons.values()):
        print(f'{i}/{size}')
        person_id = graphinterface.storePerson(person)
        for followed in person.get_follows():
            # make sure followed person stored too
            followed_id = graphinterface.storePerson(followed)
            # add follower
            graphinterface.addFollowerTo(followed_id, person_id)






if __name__ == '__main__':
    main()



