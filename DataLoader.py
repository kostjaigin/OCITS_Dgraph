from os import listdir
from DgraphRecommendation import Person, DataReader
from DgraphRecommendation.DgraphInterface import DgraphInterface
import http.client
import os
import networkx as nx
import easygui

'''
Load data from networkx graph
'''
def upload_from_networkx(G: nx.Graph, graphinterface: DgraphInterface):
    # load networkx data to rdf files:
    reader = DataReader.DataReader()
    location = os.getcwd()
    rdf_nodes, rdf_edges = reader.write_graph_to_rdf(G, graphinterface, location)
    # reset schema
    graphinterface.drop_all()
    graphinterface.set_schema()
    # load with live loader from .rdf
    upload_with_live_loader(rdf_nodes)
    upload_with_live_loader(rdf_edges)

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
    reader = DataReader.DataReader()
    reader.read_from_facebook()

    persons_file, features_file = reader.write_data_to_rdf()
    # try to create .gz archives from .rdf data:
    if reset_schema:
        # load data new if schema was removed:
        upload_with_live_loader(persons_file)
        upload_with_live_loader(features_file)
    # now i require stored persons, features files to proceed (because of uids in there)
    location = os.path.split(persons_file)[0] # store uids infos in the same folder
    stored_persons, stored_features = download_stored_nodes(graphinterface, location)
    # i can use this information to prepare edges
    follows_file, tracks_file = reader.write_links_to_rdf(stored_persons_loc = stored_persons, stored_features_loc = stored_features)
    if reset_schema:
        # load new edges if schema was removed:
        upload_with_live_loader(follows_file)
        upload_with_live_loader(tracks_file)
    assert graphinterface.getNumbers() == (4039, 1283, 176648, 37257) # TODO to remove

def upload_with_live_loader(rdf: str):
    os.system(f"gzip -c {rdf} > {rdf}.gz")
    os.system(f"docker exec -it dgraph dgraph live -f {rdf}.gz")

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
    if os.path.exists(stored_persons):
        os.remove(stored_persons)
    if os.path.exists(stored_features):
        os.remove(stored_features)
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




