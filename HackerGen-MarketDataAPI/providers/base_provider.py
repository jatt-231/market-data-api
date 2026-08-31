from abc import ABC, abstractmethod

class BaseProvider(ABC):
    """
    Ye ek 'blueprint' hai. Har naya data provider (Quotex, ya future
    mein koi aur) is blueprint ko follow karega. Isse hamara core
    system kisi bhi provider ke sath kaam kar sakta hai, bina
    apna code badle.
    """

    @abstractmethod
    async def connect(self):
        pass

    @abstractmethod
    async def get_latest_candles(self, symbol: str, count: int):
        pass

    @abstractmethod
    async def get_provider_status(self):
        pass