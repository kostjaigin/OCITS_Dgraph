import itertools
import time
from functools import reduce
from math import sqrt
import multiprocessing as mp

from DgraphRecommendation import DgraphInterface

'''
    Methods to perform k-shortest-predictions on dgraph using mapreduce paradigm on parallelization. Did not work out for me...    
'''

'''
    Performs the prediction: returns k-shortest_idxs for edges in the same order and calculation time accumulated
'''
def predict_k_shortest(edges, k) -> (list, int):
    coresnumber = mp.cpu_count()
    pool = mp.Pool(coresnumber)
    # chunks are sorted: chunkify([10], 5) -> [[0, 1], [2, 3], [4, 5], [6, 7], [8, 9, 10]]
    data_chunks = chunkify(edges, 10, k) # APPEND k TO CHUNKS
    mapped = pool.map(chunks_mapper, data_chunks) # problem todo those wont become sorted on themselfs...
    reduced_rates, reduced_time = reduce(reducer, mapped)
    return reduced_rates, reduced_time

''' reunites calculation results '''
def reducer(p: (list, int), c: (list, int)) -> (list, int):
    p_rates, p_time = p
    c_rates, c_time = c
    return p_rates+c_rates, p_time+c_time

def chunkify(seq, chunks, k):
    avg = len(seq) / float(chunks)
    out = []
    last = 0.0

    while last < len(seq):
        out.append((seq[int(last):int(last + avg)], k))
        last += avg

    return out

''' performs prediction calculation for given edges, acts as a MAPPER '''
def k_shortest_prediction(edge, k) -> (list, int):
    interface = DgraphInterface()
    time_k = 0
    rates = []
    src = edge[0]  # should both be uid
    dst = edge[1]
    ppl, latency = interface.get_k_shortest_pathes(k, src, dst)
    start_delta = int(latency.total_ns) * (10**(-9))  # to secs
    time_k += start_delta
    start = time.time()
    s_k = sum([1 / sqrt(int(item["_weight_"])) for item in ppl["_path_"]])
    end = time.time()
    rates.append(s_k)
    time_k += end - start
    return rates, time_k

def chunks_mapper(chunk):
    datachunk, k = chunk
    mapped_chunk = map(k_shortest_prediction, datachunk, itertools.repeat(k, len(datachunk)))  # map performs function on all elements in chunk
    return reduce(reducer, mapped_chunk)