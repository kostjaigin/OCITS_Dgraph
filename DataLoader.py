from os import listdir
from . import Person
from . import DataReader
from . import DgraphInterface
import http.client
import os
import networkx as nx
import easygui

'''
Load data from networkx graph
Stores feauture-names (301, 296 etc.) and persons (0x...) uids as nodes
'''
def upload_from_networkx(G: nx.Graph, interface: DgraphInterface, predict_persons: bool):
    features = [node for node in G.nodes if not node.startswith("0x")] # must be transformed


''' 
Reads facebook data files from here: https://snap.stanford.edu/data/ego-Facebook.html
Sets the matching schema in dgraph instance
Translates into dgraph format and
Stores data locally in RDF files
Uses live loader and curl-http client to intercooperate nodes and edges
'''
def read_and_upload_facebook():

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
    stored_persons, stored_features = download_stored_nodes(graphinterface, location)
    # i can use this information to prepare edges
    follows_file, tracks_file = reader.write_links_to_rdf(stored_persons_loc = stored_persons, stored_features_loc = stored_features)
    os.system(f"gzip -c {follows_file} > {follows_file}.gz")
    os.system(f"gzip -c {tracks_file} > {tracks_file}.gz")
    if reset_schema:
        # load new edges if schema was removed:
        os.system(f"docker exec -it dgraph dgraph live -f {follows_file}.gz")
        os.system(f"docker exec -it dgraph dgraph live -f {tracks_file}.gz")

'''
Download dgraph persons, features with their uids to file in given :attr location
:returns location of persons file, location of features file
'''
def download_stored_nodes(graphinterface: DgraphInterface, location: str = None) -> (str, str):
    if location is None:
        easygui.msgbox("Please, select where to download the dgraph data files to..")
        location = easygui.diropenbox()
    stored_persons = os.path.join(location, "stored_persons")
    stored_features = os.path.join(location, "stored_features")
    conn = http.client.HTTPConnection(graphinterface.http_external)
    headers = {'Content-Type': 'application/graphql+-'}
    query_persons = "$'{ total(func: has(id)) {   id   uid  }}'"
    query_features = "$'{ total(func: has(name)) {   name   uid  }}'"
    conn.request('POST', '/query', query_persons, headers)
    write_to_file(stored_persons, conn.getresponse().read().decode())
    conn.request('POST', '/query', query_features, headers)
    write_to_file(stored_features, conn.getresponse().read().decode())
    conn.close()
    return stored_persons, stored_features

def write_to_file(file: str, content: str):
    if content is not None and content != "":
        with open(file, 'a') as f:
            f.write(content)




