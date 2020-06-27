
def main():
    list_of_strings = ['abc', 'python', 'dima']
    list_of_strings *= 1000
    # step 1: compute lens of strings
    list_of_string_lens = [len(s) for s in list_of_strings]
    list_of_string_lens = zip(list_of_strings, list_of_string_lens)
    # step 2: compute max value
    max_len = max(list_of_string_lens, key=lambda t: t[1])
    print(max_len)



if __name__ == '__main__':
    main()