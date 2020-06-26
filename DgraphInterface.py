import pydgraph
import datetime
import json
from DgraphRecommendation import Person


class DgraphInterface:

    def __init__(self):
        self.client_stub = pydgraph.DgraphClientStub('localhost:9080')
        self.client = pydgraph.DgraphClient(self.client_stub)

    ''' Set dgraph schema, do execute once or after test execution '''
    def set_schema(self):
        schema = """
        id: string @index(exact) .
        name: string @index(exact) .
        follows: [uid] @reverse .
        tracks: [uid] @reverse .
        
        type Person {
            id
            follows
            tracks
        }
        type Feature {
            name
        }
        """
        return self.client.alter(pydgraph.Operation(schema=schema))

    ''' Drop whole DB, use only for test purposes '''
    def drop_all(self):
        return self.client.alter(pydgraph.Operation(drop_all=True))

    ''' Simply add feature to dgraph @:returns uid '''
    def addFeature(self, feature: str) -> str:
        res = ''
        txn = self.client.txn()
        try:
            # create data
            p = {
                'uid': '_:newfeature',
                'dgraph.type': 'Feature',
                'name': feature
            }
            # Run mutation.
            response = txn.mutate(set_obj=p)
            # Commit transaction.
            txn.commit()
            res = response.uids['newfeature']
        finally:
            txn.discard()
        return res

    ''' Simply add person to dgraph @:returns uid '''
    def addPerson(self, person: Person) -> str:
        res = ''
        txn = self.client.txn()
        try:
            # create data
            p = {
                'uid': '_:newperson',
                'dgraph.type': 'Person',
                'id': f'{person.id}',
            }
            # Run mutation.
            response = txn.mutate(set_obj=p)
            # Commit transaction.
            txn.commit()
            res = response.uids['newperson']
        finally:
            txn.discard()
        return res

    ''' Query to find feature by name @:returns uid of target or empty string '''
    def find_feature_by_name(self, name: str) -> str:
        query = """query all($a: string) {
                        find_feature(func: eq(name, $a)) {
                            uid
                        }
                    }"""
        variables = {'$a': name}
        res = self.client.txn(read_only=True).query(query, variables=variables)
        ppl = json.loads(res.json)
        if len(ppl['find_feature']) == 0:
            return None
        return ppl['find_feature'][0]['uid']

    ''' Query to find person by id @:returns uid of target '''
    def find_by_id(self, id: str) -> str:
        query = """query all($a: string) {
                find_person(func: eq(id, $a)) {
                    uid
                }
            }"""
        variables = { '$a': id }
        res = self.client.txn(read_only=True).query(query, variables=variables)
        ppl = json.loads(res.json)
        if len(ppl['find_person']) == 0:
            return None
        return ppl['find_person'][0]['uid']

    ''' Add follower to the person @:params person's and follower's uids '''
    def addFollowerTo(self, person: str, follower: str):
        txn = self.client.txn()
        try:
            setstatement = '<%s> <follows> <%s> .' % (follower, person)
            mutation = txn.create_mutation(set_nquads=setstatement)
            request = txn.create_request(mutations=[mutation], commit_now=True)
            txn.do_request(request)
        finally:
            txn.discard()

    ''' Add feature to the user @:params person's and feature's uids '''
    def addTracksTo(self, person: str, feature: str):
        txn = self.client.txn()
        try:
            setstatement = '<%s> <tracks> <%s> .' % (person, feature)
            mutation = txn.create_mutation(set_nquads=setstatement)
            request = txn.create_request(mutations=[mutation], commit_now=True)
            txn.do_request(request)
        finally:
            txn.discard()
