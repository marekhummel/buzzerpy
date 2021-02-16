from time import monotonic
from typing import List, Optional


class Host():
    name: str

    def __init__(self, name: str):
        self.name = name

    def toJson(self):
        return self.__dict__


class Player():
    name: str
    has_buzzed: bool
    buzz_time: Optional[float]
    buzz_time_sw: Optional[str]
    correct_answers: int
    wrong_answers: int
    bonus_points: int
    round_correct_answer: bool

    def __init__(self, name: str):
        self.name = name
        self.correct_answers = 0
        self.wrong_answers = 0
        self.bonus_points = 0
        self.next_round()

    def buzz(self, clock: Optional[float]):
        self.has_buzzed = True
        self.buzz_time = monotonic()
        self.buzz_time_sw = f'{clock:05.2F} secs' if clock else None

    def correct_answer(self):
        self.correct_answers += 1
        self.round_has_answered = True
        self.round_correct_answer = True

    def wrong_answer(self):
        self.wrong_answers += 1
        self.round_has_answered = True
        self.round_correct_answer = False

    def next_round(self):
        self.has_buzzed = False
        self.buzz_time = None
        self.buzz_time_sw = None
        self.round_has_answered = False
        self.round_correct_answer = None

    def get_points(self):
        net = self.correct_answers * 10 - self.wrong_answers * 5
        return net + self.bonus_points

    def toJson(self):
        return dict(self.__dict__, pts=self.get_points())


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

    def get_round_player(self):
        for p in self.get_players_ordered():
            if p.has_buzzed and not p.round_has_answered:
                return p
        return None

    def remove_player(self, name):
        self.players = [p for p in self.players if p.name != name]

    def next_round(self):
        for p in self.players:
            p.next_round()

    def get_players_ordered(self):
        def sort_key(p): return (not p.has_buzzed, p.buzz_time)
        return sorted(self.players, key=sort_key)

    def toJson(self):
        def optional(obj): return obj.toJson() if obj else None
        return {'host': optional(self.host),
                'players': [p.toJson() for p in self.get_players_ordered()]}


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
