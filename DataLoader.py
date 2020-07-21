from os import listdir
from DgraphRecommendation import Person
from DgraphRecommendation import DataReader
from DgraphRecommendation import DgraphInterface
import time
import json
from DgraphRecommendation import Feature
import random
import os

''' 
Reads facebook data files from here: https://snap.stanford.edu/data/ego-Facebook.html
Sets the matching schema in dgraph instance
Translates into dgraph format and
Stores data locally in RDF files
Uses live loader and curl-http client to intercooperate nodes and edges
'''

def main():

    reset_schema = False # set to True to reload db completely

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

    persons_file, features_file = reader.write_data_to_rdf()
    # try to create .gz archives from .rdf data:
    os.system(f"gzip -c {persons_file} > {persons_file}.gz")
    os.system(f"gzip -c {features_file} > {features_file}.gz")
    if reset_schema:
        # load data new if schema was removed:
        os.system(f"docker exec -it dgraph dgraph live -f {persons_file}.gz")
        os.system(f"docker exec -it dgraph dgraph live -f {features_file}.gz")
    # now i require stored persons, features files to proceed (because of uids in there)
    location = os.path.split(persons_file)[0] # store uids infos in the same folder
    stored_persons = os.path.join(location, "stored_persons")
    stored_features = os.path.join(location, "stored_features")
    command = f"curl -H \"Content-Type: application/graphql+-\" \"{graphinterface.http_external}/query\" -XPOST -d $"
    query_persons = "'{ total(func: has(id)) {   id   uid  }}' > "
    query_features = "'{ total(func: has(name)) {   name   uid  }}' > "
    os.system(command+query_persons+stored_persons)
    os.system(command+query_features+stored_features)
    # i can use this information to prepare edges
    follows_file, tracks_file = reader.write_links_to_rdf(stored_persons_loc = stored_persons, stored_features_loc = stored_features)
    os.system(f"gzip -c {follows_file} > {follows_file}.gz")
    os.system(f"gzip -c {tracks_file} > {tracks_file}.gz")
    if reset_schema:
        # load new edges if schema was removed:
        os.system(f"docker exec -it dgraph dgraph live -f {follows_file}.gz")
        os.system(f"docker exec -it dgraph dgraph live -f {tracks_file}.gz")



if __name__ == '__main__':
    main()



