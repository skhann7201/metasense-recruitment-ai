import time
import random
from abc import ABC, abstractmethod
from typing import Iterable


def random_delay(min_delay: float = 2.0, max_delay: float = 5.0) -> None:
    time.sleep(random.uniform(min_delay, max_delay))


class Scraper(ABC):
    @abstractmethod
    def run(self, *args, **kwargs) -> Iterable[dict]:
        raise NotImplementedError





