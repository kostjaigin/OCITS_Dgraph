from DgraphRecommendation import Person

class DataReader:
    '''
        Help class to read data from files
    '''
    def __init__(self):
        self.persons = dict()
        self.iteration_persons = dict()

    '''
    :returns person with given id
    if person not recorded yet, record it 
    '''
    def getPerson(self, id) -> Person:
        if id not in self.persons:
            person = Person(id)
            self.persons[id] = person
        if id not in self.iteration_persons:
            self.iteration_persons[id] = self.persons[id]
        return self.persons[id]

    '''
    method called when we are done working with one id's files
    '''
    def clearIteration(self):
        for person in self.iteration_persons.values():
            person.clear_raw_features()
        self.iteration_persons = dict()


