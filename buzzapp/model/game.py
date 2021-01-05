from random import randint
from time import time
from typing import List


class Player():
    name: str
    has_buzzed: bool
    buzz_time: float
    buzz_time_sw: float

    def __init__(self, name: str):
        self.name = name
        self.reset()

    def buzz(self, clock):
        self.has_buzzed = True
        self.buzz_time = time()
        self.buzz_time_sw = clock

    def reset(self):
        self.has_buzzed = False
        self.buzz_time = None
        self.buzz_time_sw = None


class BuzzGame():
    id: int
    players: List[Player]

    def __init__(self, assigned_ids):
        gid = 123456  # randint(100000, 999999)
        while gid in assigned_ids:
            gid = randint(100000, 999999)

        self.id = gid
        self.players = []

    def add_player(self, player: Player):
        self.players.append(player)

    def get_player(self, name) -> Player:
        for p in self.players:
            if p.name == name:
                return p

        return None



class Stopwatch():
    _running: bool
    _start: float
    _elapsed_intervals: List[float]

    def __init__(self):
        self._running = False
        self._elapsed_intervals = []

    def start(self):
        if not self._running:
            self._start = time()
            self._running = True

    def stop(self):
        if self._running:
            self._elapsed_intervals.append(time() - self._start)
            self._running = False

    def reset(self):
        if not self._running:
            self._elapsed_intervals = []

    def elapsed(self):
        total = sum(self._elapsed_intervals)
        if self._running:
            total += time() - self._start
        return total