import os

dgraph_settings = dict(
    number_persons = 4039,
    number_features = 1283,
    number_connections_persons = 176468, # should be even
    number_connections_persons_features = 37257,
    host = "192.168.178.27"
)

dgraph_root_folder = "/Users/Ones-Kostik/dgraph"

results_file = os.path.join(os.getcwd(), "results.txt") # where to store results of measurements
resulst_file_k = os.path.join(os.getcwd(), "results_k.txt") # where to store results of k paths prediction