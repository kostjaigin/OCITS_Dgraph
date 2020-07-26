import easygui
from os import path
import os
import shutil
import http.client
import time
import json
from tqdm import tqdm
import networkx as nx
import sys
from pathlib import Path

from DgraphRecommendation import DgraphInterface
from DgraphRecommendation import config
from DgraphRecommendation.DataLoader import download_stored_nodes, read_and_upload_facebook


def main():
    tuple = (config.dgraph_settings['number_persons'], config.dgraph_settings['number_features'],
     config.dgraph_settings['number_connections_persons'], config.dgraph_settings[
         'number_connections_persons_features'])  # if to reload data into dgraph: set to True to force reload
    print(tuple)

if __name__ == '__main__':
    main()