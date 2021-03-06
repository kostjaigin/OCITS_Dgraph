import pydgraph
import datetime
import json
from DgraphRecommendation import Person, config


class DgraphInterface:

    def __init__(self):
        # pygraph works on grpc which can read options for channels it covers
        opts = [('grpc.max_receive_message_length', 16*1024*1024)]
        # grpc external port
        grpc_e = config.dgraph_settings["host"]+":9080"
        http_e = config.dgraph_settings["host"]+":8080"
        self.grpc_external = grpc_e
        # http external port
        self.http_external = http_e
        self.client_stub = pydgraph.DgraphClientStub(grpc_e, options=opts)
        self.client = pydgraph.DgraphClient(self.client_stub)

    ''' Set dgraph schema, do execute once or after test execution '''
    def set_schema(self):
        schema = """
        id: string @index(exact) .
        name: string @index(exact) .
        follows: [uid] .
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

    def deleteNode(self, uid: str):
        res = ''
        txn = self.client.txn()
        try:
            p = {
                'uid': f'{uid}'
            }
            response = txn.mutate(del_obj=p)
            txn.commit()
            res = response
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

    def getAllPersons(self) -> str:
        query = """
                query {
                    persons(func: has(id)) {
                        id
                        uid
                        tracks {
                            name
                            uid
                        }
                        follows {
                            id
                            uid
                        }
                    }
                }
                """
        res = self.client.txn(read_only=True).query(query)
        ppl = json.loads(res.json)
        return ppl

    def getAllFeatures(self) -> str:
        query = """
                        query {
                            features(func: has(name)) {
                                name
                                uid
                            }
                        }
                        """
        res = self.client.txn(read_only=True).query(query)
        ppl = json.loads(res.json)
        return ppl

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

    '''
        Add predictable edges to graph
    '''
    def addPredictableEdges(self, srcfile: str):
        txn = self.client.txn()
        try:
            muts = [] # mutations
            with open(srcfile, 'r') as f:
                for line in f:
                    content = line.strip()
                    mutation = txn.create_mutation(set_nquads=content)
                    muts.append(mutation)
            request = txn.create_request(mutations=muts, commit_now=True)
            txn.do_request(request)
        finally:
            txn.discard()

    '''
        Remove all "predictable" edges from graph
    '''
    def remove_predictable(self, srcfile: str):
        txn = self.client.txn()
        try:
            muts = [] # mutations
            with open(srcfile, 'r') as f:
                for line in f:
                    content = line.strip()
                    mutation = txn.create_mutation(del_nquads=content)
                    muts.append(mutation)
            request = txn.create_request(mutations=muts, commit_now=True)
            txn.do_request(request)
        finally:
            txn.discard()




    ''' Get numbers of nodes and edges in the graph: #persons, #features, #interpersons_connections, #feature_connections '''
    def getNumbers(self) -> (int, int, int, int):
        txn = self.client.txn()
        query = """ query
                {
                      amount_of_persons(func: type(Person)) {
                        number: count(uid)
                      }
                      amount_of_features(func: type(Feature)) {
                        number: count(uid)
                      }
                      var(func: has(follows)) {
                        u as count(follows)
                      }
                      amount_of_persons_connections() {
                        number: sum(val(u))
                      }
                      var(func: has(tracks)) {
                        v as count(tracks)
                      }
                      amount_of_feature_connections() {
                        number: sum(val(v))
                      }
                }
                """
        res = self.client.txn(read_only=True).query(query)
        ppl = json.loads(res.json)
        return int(ppl["amount_of_persons"][0]["number"]), int(ppl["amount_of_features"][0]["number"]), int(ppl["amount_of_persons_connections"][0]["number"]), int(ppl["amount_of_feature_connections"][0]["number"])


    ''' 
        Find k shortest pathes in dgraph between @arg str and @arg dst
    '''
    def get_k_shortest_pathes(self, k: int, src: str, dst: str):
        query = """query all($src: string, $dst: string, $k: int) {
                        source as var(func: uid($src))
                        destination as var(func: uid($dst))
                        shortest(from: uid(source), to: uid(destination), numpaths: $k) {
                            follows
                        }
                    }
                """
        variables = {'$src': src, '$dst': dst, '$k': str(k)}
        res = self.client.txn(read_only=True).query(query, variables=variables)
        ppl = json.loads(res.json)
        latency = res.latency
        return ppl, latency
