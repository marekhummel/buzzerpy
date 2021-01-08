from time import monotonic
from typing import List, Optional


class Host():
    name: str

    def __init__(self, name: str):
        self.name = name


class Player():
    name: str
    has_buzzed: bool
    buzz_time: Optional[float]
    buzz_time_sw: Optional[str]

    def __init__(self, name: str):
        self.name = name
        self.reset()

    def buzz(self, clock: Optional[float]):
        self.has_buzzed = True
        self.buzz_time = monotonic()
        self.buzz_time_sw = f'{clock:05.2F} secs' if clock else None

    def reset(self):
        self.has_buzzed = False
        self.buzz_time = None
        self.buzz_time_sw = None


class BuzzGame():
    host: Host
    players: List[Player]

    def __init__(self):
        self.host = None
        self.players = []

    def set_host(self, host: Host):
        self.host = host

    def remove_host(self):
        self.host = None

    def has_host(self) -> bool:
        return self.host is not None

    def add_player(self, player: Player):
        self.players.append(player)

    def get_player(self, name) -> Optional[Player]:
        for p in self.players:
            if p.name == name:
                return p
        return None

    def remove_player(self, name):
        self.players = [p for p in self.players if p.name != name]


class Stopwatch():
    _running: bool
    _start: float
    _elapsed_intervals: List[float]

    def __init__(self):
        self._running = False
        self._elapsed_intervals = []

    def start(self):
        if not self._running:
            self._start = monotonic()
            self._running = True

    def stop(self):
        if self._running:
            self._elapsed_intervals.append(monotonic() - self._start)
            self._running = False

    def reset(self):
        if not self._running:
            self._elapsed_intervals = []

    def elapsed(self) -> Optional[float]:
        if len(self._elapsed_intervals) == 0 and not self._running:
            return None

        total = sum(self._elapsed_intervals)
        if self._running:
            total += monotonic() - self._start
        return total
