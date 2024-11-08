from federatedml.secureprotol.semi2k.utils import naming
from federatedml.secureprotol.semi2k.utils import NamingService
from federatedml.secureprotol.semi2k.communicator import Communicator
from federatedml.secureprotol.fate_paillier import PaillierKeypair


Q = 293973345475167247070445277780365744413 ** 2

class SEMI2K(object):
    __instance = None

    @classmethod
    def get_instance(cls) -> 'Semi2k':
        return cls.__instance

    @classmethod
    def set_instance(cls, instance):
        prev = cls.__instance
        cls.__instance = instance
        
        return prev

    @classmethod
    def has_instance(cls):
        return cls.__instance is not None
    
    #@TODO-----------------------------

    def __init__(self, name="ss", q_field=None, local_party=None, all_parties=None, use_mix_rand=False, n_length=1024):
        self.name_service = naming.NamingService(name)
        self._prev_name_service = None
        self._pre_instance = None

        self.communicator = Communicator(local_party, all_parties)

        self.party_idx = self.communicator.party_idx
        self.other_parties = self.communicator.other_parties
        if len(self.other_parties) > 1:
            raise EnvironmentError("support 2-party secret share only")
        self.public_key, self.private_key = PaillierKeypair.generate_keypair(n_length=n_length)

        if q_field is None:
            q_field = self.public_key.n

        # self.q_field = self._align_q_field(q_field)

        self.use_mix_rand = use_mix_rand

    def __enter__(self):
        self._prev_name_service = NamingService.set_instance(self.name_service)
        self._pre_instance = self.set_instance(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        NamingService.set_instance(self._pre_instance)
        # self.communicator.clean()

    def __reduce__(self):
        raise PermissionError("it's unsafe to transfer this")

    def partial_rescontruct(self):
        # todo: partial parties gets rescontructed tensor
        pass

    @classmethod
    def dot(cls, left, right, target_name=None):
        return left.dot(right, target_name)

    def set_flowid(self, flowid):
        self.communicator.set_flowid(flowid)

    def _align_q_field(self, q_field):
        self.communicator.remote_q_field(q_field=q_field, party=self.other_parties)
        other_q_field = self.communicator.get_q_field(party=self.other_parties)
        other_q_field.append(q_field)
        max_q_field = max(other_q_field)
        return max_q_field
