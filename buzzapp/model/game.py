from time import monotonic
from typing import List, Optional
from enum import IntEnum


class RoundMode(IntEnum):
    Buzzer = 0
    Guessing = 1
    Stopwatch = 2


class Host():
    name: str

    def __init__(self, name: str):
        self.name = name

    def toJson(self):
        return self.__dict__


class Player():
    name: str
    buzzer_has_buzzed: bool
    buzzer_time: Optional[float]
    stopwatch_time: Optional[float]
    guessing_text: Optional[str]
    round_has_received_pts: bool
    round_correct_answer: bool
    correct_answers: int
    wrong_answers: int
    bonus_points: int

    # ** Init

    def __init__(self, name: str):
        self.name = name
        self.correct_answers = 0
        self.wrong_answers = 0
        self.bonus_points = 0
        self.next_round()

    # ** Player interaction

    def buzz(self):
        self.buzzer_has_buzzed = True
        self.buzzer_time = monotonic()

    def stop_stopwatch(self, clock: Optional[float]):
        self.stopwatch_time = clock if clock else 0

    def set_guess(self, guess: str):
        self.guessing_text = guess

    # ** Scores

    def correct_answer(self):
        self.correct_answers += 1
        self.round_has_received_pts = True
        self.round_correct_answer = True

    def wrong_answer(self):
        self.wrong_answers += 1
        self.round_has_received_pts = True
        self.round_correct_answer = False

    # ** Misc

    def next_round(self):
        self.buzzer_has_buzzed = False
        self.buzzer_time = None
        self.stopwatch_time = None
        self.guessing_text = None
        self.round_has_received_pts = False
        self.round_correct_answer = None

    def get_points(self):
        net = self.correct_answers * 10 - self.wrong_answers * 5
        return net + self.bonus_points

    def toJson(self):
        return dict(self.__dict__, pts=self.get_points())


class BuzzGame():
    host: Host
    players: List[Player]
    round_mode: RoundMode
    round_in_progress: bool

    def __init__(self):
        self.host = None
        self.players = []
        self.round_mode = RoundMode.Buzzer
        self.round_in_progress = False

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

    def next_round(self):
        self.round_in_progress = False
        for p in self.players:
            p.next_round()

    def get_players_ordered(self):
        def sort_key(p): return (not p.buzzer_has_buzzed, p.buzzer_time)
        return sorted(self.players, key=sort_key)

    def toJson(self):
        return {'host': self.host.toJson() if self.host else None,
                'players': [p.toJson() for p in self.get_players_ordered()],
                'round_mode': self.round_mode,
                'round_in_progress': self.round_in_progress}


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
