from enum import IntEnum
from time import monotonic


class RoundMode(IntEnum):
    Buzzer = 0
    Guessing = 1
    Stopwatch = 2


class Host:
    name: str

    def __init__(self, name: str):
        self.name = name

    def to_json(self):
        return self.__dict__


class Player:
    name: str
    buzzer_has_buzzed: bool
    buzzer_guesser_time: float | None
    stopwatch_time: float | None
    guessing_list: list[str] | None
    round_has_received_pts: bool
    round_correct_answer: bool | None
    correct_answers: int
    wrong_answers: int
    bonus_points: int
    answer_streak: int

    # ** Init

    def __init__(self, name: str):
        self.name = name
        self.correct_answers = 0
        self.wrong_answers = 0
        self.bonus_points = 0
        self.answer_streak = 0
        self.next_round()

    # ** Player interaction

    def buzz(self):
        self.buzzer_has_buzzed = True
        self.buzzer_guesser_time = monotonic()

    def set_guesses(self, guesses: list[str]):
        self.guessing_list = guesses
        self.buzzer_guesser_time = monotonic()

    def stop_stopwatch(self, clock: float | None):
        self.stopwatch_time = clock if clock else 0

    # ** Scores

    def correct_answer(self):
        self.correct_answers += 1
        self.round_has_received_pts = True
        self.round_correct_answer = True
        self.answer_streak += 1

    def wrong_answer(self):
        self.wrong_answers += 1
        self.round_has_received_pts = True
        self.round_correct_answer = False
        self.answer_streak = 0

    # ** Misc

    def next_round(self):
        self.buzzer_has_buzzed = False
        self.buzzer_guesser_time = None
        self.stopwatch_time = None
        self.guessing_list = None
        self.round_has_received_pts = False
        self.round_correct_answer = None

    def get_points(self):
        net = self.correct_answers * 10 - self.wrong_answers * 5
        return net + self.bonus_points

    def to_json(self):
        return dict(self.__dict__, pts=self.get_points())


class BuzzGame:
    host: Host | None
    players: list[Player]
    round_mode: RoundMode
    round_in_progress: bool
    guessing_amount: int

    def __init__(self):
        self.host = None
        self.players = []
        self.round_mode = RoundMode.Buzzer
        self.round_in_progress = False
        self.guessing_amount = 1

    def set_host(self, host: Host):
        self.host = host

    def remove_host(self):
        self.host = None

    def has_host(self) -> bool:
        return self.host is not None

    def add_player(self, player: Player):
        self.players.append(player)

    def get_player(self, name) -> Player | None:
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

    def to_json(self):
        return {
            "host": self.host.to_json() if self.host else None,
            "players": [p.to_json() for p in self.players],
            "round_mode": self.round_mode,
            "round_in_progress": self.round_in_progress,
            "guessing_amount": self.guessing_amount,
        }


class Stopwatch:
    _running: bool
    _start: float
    _elapsed_intervals: list[float]

    def __init__(self):
        self._running = False
        self._elapsed_intervals = []

    def start(self) -> bool:
        if self._running:
            return False

        self._start = monotonic()
        self._running = True
        return True

    def stop(self) -> bool:
        if not self._running:
            return False

        self._elapsed_intervals.append(monotonic() - self._start)
        self._running = False
        return True

    def reset(self) -> bool:
        if self._running:
            return False

        self._elapsed_intervals = []
        return True

    @property
    def is_running(self) -> bool:
        return self._running

    def elapsed(self) -> float | None:
        if len(self._elapsed_intervals) == 0 and not self._running:
            return None

        total = sum(self._elapsed_intervals)
        if self._running:
            total += monotonic() - self._start
        return total
