
def main():
    path = "/Users/Ones-Kostik/Desktop/TwitterData/twitter/12831.edges"
    list = []
    with open(path, 'r') as f:
        for line in f:
            data = line.strip().split(" ")
            if data[0] not in list:
                list.append(data[0])
            if data[1] not in list:
                list.append(data[1])
    print(len(list))
    path = "/Users/Ones-Kostik/Desktop/TwitterData/twitter_combined.txt"
    anotherlist = []
    with open(path, 'r') as f:
        for i, line in enumerate(f):
            data = line.strip().split(" ")
            if data[0] != '12831':
                continue
            if data[1] not in anotherlist:
                anotherlist.append(data[1])
    print(len(anotherlist))
    difference = [x for x in anotherlist if x not in list]
    print(len(difference))


if __name__ == '__main__':
    main()