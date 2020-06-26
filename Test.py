
def main():
    special_characters = "!\"@#$%^&*()[]{};:,./<>?\|`~-=_+"
    random_words = ['alpha', 'beta', 'gamma', 'maxima', 'centavra', 'lorem', 'ipsum', 'quatro', 'hoax', 'grade',
                    'study', 'key', 'utopian', 'tee', 'search', 'grind']
    random_words += ["angle", "statement", "filthy", "leak", "dogs", "aback", "scrub", "purpose", "discussion",
                     "lizards", "legs", "sample", "swot", "flock", "zinc"]
    feature_name = "fuzzy#tante@krazi@dot."
    feature_name = feature_name.translate({ord(c): random_words[i] for i, c in enumerate(special_characters)})
    print(feature_name)

if __name__ == '__main__':
    main()