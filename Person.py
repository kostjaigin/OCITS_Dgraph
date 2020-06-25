import numpy as np

class Person:
    '''
        Represents a Person.

        Instance Attributes:
            TODO describe existing attributes
    '''

    def __init__(self, id):
        self.id = id # internal id
        self.uid = None # dgraph db id
        self.__private_follows = [] # follows
        self.__private_rawfeatures = [] # vector of raw features 0/1
        self.__private_features = [] # list of features it does posses

    def follow(self, id):
        if id not in self.__private_follows:
            self.__private_follows.append(id)

    def add_raw_features(self, features):
        self.__private_rawfeatures.extend(features)

    def hasFeature(self, featurePos) -> bool:
        return self.__private_rawfeatures[featurePos] == 1

    def clear_raw_features(self):
        self.__private_rawfeatures = []

    def add_feature(self, feature):
        if feature not in self.__private_features:
            self.__private_features.append(feature)

    '''
    GETTERS
    '''

    def get_follows(self):
        return self.__private_follows

    def get_features(self):
        return self.__private_features








