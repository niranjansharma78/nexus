from abc import ABC, abstractmethod

class ReadOnlyConnector(ABC):
    '''Connectors may read and normalize evidence, but never modify external systems.'''
    name: str

    @abstractmethod
    def test_connection(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def read_evidence(self):
        raise NotImplementedError
