

def main():
    print("main")
    scores = { "1":[], "4":[], "8":[], "16":[] }
    for value in scores:
        print(value)
    #k_shortests_mean = mean(timeit.repeat(lambda: k_shortest_paths(G, src, dst, k), number=1, repeat=100))
    #k_shortests_2_mean = mean(timeit.repeat(lambda: k_shortest_2(G, src, dst, k), number=1, repeat=100))
    #print(k_shortests_mean)
    #print(k_shortests_2_mean)

    # k_shortests_mean = mean(timeit.repeat(lambda: k_shortest_prediction(G, src, dst, k), number=1, repeat=10))
    # print(k_shortests_mean)
    # res = k_shortest_prediction(G, src, dst, k)
    # print(f"result: {res}")

    # c_k = sum([len(path) for path in shortest_paths])
    # print(c_k)
    # mean_time = mean(timeit.repeat(lambda : k_predict(edge, 2, interface), number=1, repeat=10))
    # print(mean_time)


def plot_results(intervals, y_precision_jaccard, y_precision_adamic, y_precision_resall, y_time_jaccard, y_time_adamic, y_time_resall):
    ''' PLOT THE RESULTS '''
    plt.figure(figsize=(12, 6))
    plt.plot(intervals, y_precision_jaccard, label='Jaccard Coefficient')
    plt.plot(intervals, y_precision_adamic, label='Adamic Adar Index')
    plt.plot(intervals, y_precision_resall, label='Resource Allocation Index')
    plt.ylim(0, 1)
    plt.legend(loc='upper right', fontsize=15)
    plt.xlabel('% of removed links', fontsize=15)
    plt.ylabel("avg. precision score", fontsize=15)
    plt.grid(True)
    plt.title("Precision scores", fontsize=20)
    plt.show()

    plt.figure(figsize=(12, 6))
    plt.plot(intervals, y_time_jaccard, label='Jaccard Coefficient')
    plt.plot(intervals, y_time_adamic, label='Adamic Adar Index')
    plt.plot(intervals, y_time_resall, label='Resource Allocation Index')
    plt.legend(loc='upper right', fontsize=15)
    plt.xlabel('% of removed links', fontsize=15)
    plt.ylabel("time [s]", fontsize=15)
    plt.grid(True)
    plt.title("Calculation time", fontsize=20)
    plt.show()

if __name__ == '__main__':
    main()