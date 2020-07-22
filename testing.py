import easygui
from os import path
import os
import http.client
import networkx as nx


def main():
    G = nx.Graph()
    G.add_edges_from([(1, 2), (1, 3), (1, 4), (3, 4), (4, 5)])
    for edge in G.edges:
        print(edge)
    # # now i require stored persons, features files to proceed (because of uids in there)
    # location = easygui.diropenbox()  # store uids infos in the same folder
    # stored_persons = path.join(location, "stored_persons")
    # stored_features = path.join(location, "stored_features")
    # command = f"curl -H \"Content-Type: application/graphql+-\" \"{graphinterface.http_external}/query\" -XPOST -d $"
    # query_persons = "'{ total(func: has(id)) {   id   uid  }}' > "
    # query_features = "'{ total(func: has(name)) {   name   uid  }}' > "
    # os.system(command + query_persons + stored_persons)
    # os.system(command + query_features + stored_features)

if __name__ == '__main__':
    main()