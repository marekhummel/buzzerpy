import os
import secrets

from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit
from model.game import BuzzGame, Host, Player, RoundMode, Stopwatch
from werkzeug.utils import redirect

app = Flask(__name__)
secret_key = os.environ.get("SECRET_KEY")
if "PORT" in os.environ and not secret_key:
    raise RuntimeError("SECRET_KEY must be set when running in production")

app.config["SECRET_KEY"] = secret_key or "local-development-only"
socketio = SocketIO(app)

game = BuzzGame()
stopwatch = Stopwatch()
host_sid: str | None = None
host_token: str | None = None
player_sids: dict[str, str] = {}
player_tokens: dict[str, str] = {}

MAX_NAME_LENGTH = 32
DISCONNECT_GRACE_SECONDS = 10


def send_game_update(host_only=False):
    socketio.emit("srv_game_update", (game.to_json(), host_only))


def send_host_update():
    socketio.emit("srv_host_update", game.host.to_json() if game.host else None)


def is_host() -> bool:
    return socket_id() == host_sid


def socket_id() -> str:
    sid = getattr(request, "sid", None)
    if not isinstance(sid, str):
        raise TypeError("Socket.IO event received without a socket ID")
    return sid


def current_player() -> Player | None:
    playername = player_sids.get(socket_id())
    return game.get_player(playername) if playername else None


def session_identity(role: str) -> tuple[str, str] | None:
    name = session.get("participant_name")
    token = session.get("participant_token")
    if (
        session.get("participant_role") != role
        or not isinstance(name, str)
        or not isinstance(token, str)
    ):
        return None
    return name, token


def set_session_identity(role: str, name: str) -> None:
    session["participant_role"] = role
    session["participant_name"] = name
    session["participant_token"] = secrets.token_urlsafe(32)


def valid_name(name: object) -> bool:
    return isinstance(name, str) and bool(name) and len(name) <= MAX_NAME_LENGTH


def remove_disconnected_host(sid: str) -> None:
    global host_sid, host_token

    socketio.sleep(DISCONNECT_GRACE_SECONDS)
    if host_sid != sid:
        return

    game.remove_host()
    host_sid = None
    host_token = None
    send_host_update()
    send_game_update()


def remove_disconnected_player(sid: str, playername: str) -> None:
    socketio.sleep(DISCONNECT_GRACE_SECONDS)
    if player_sids.get(sid) != playername:
        return

    del player_sids[sid]
    if game.get_player(playername):
        game.remove_player(playername)
        player_tokens.pop(playername, None)
        send_game_update()


# Force update of js files
@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store"
    return response


# ----- APP ROUTES -----


@app.route("/")
def index():
    errors = session.get("index_errors")
    return render_template("index.html", errors=errors)


@app.route("/ping")
def ping():
    print("Host pinged.")
    return ""


@app.route("/health")
def health():
    return {"status": "ok"}


@app.route("/host")
def host():
    hostname = request.args.get("name", "").strip()

    if not valid_name(hostname):
        session["index_errors"] = "ENTER A NAME"
        return redirect("/")

    if game.has_host():
        session["index_errors"] = "GAME ALREADY HOSTED"
        return redirect("/")

    if game.get_player(hostname):
        session["index_errors"] = "NAME ALREADY CHOSEN"
        return redirect("/")

    session.pop("index_errors", None)
    set_session_identity("host", hostname)
    return render_template("host.html", hostname=hostname)


@app.route("/join")
def join():
    playername = request.args.get("name", "").strip()
    host = game.host

    if host is None:
        session["index_errors"] = "GAME NOT HOSTED YET"
        return redirect("/")

    if game.get_player(playername) or host.name == playername:
        session["index_errors"] = "NAME ALREADY CHOSEN"
        return redirect("/")

    if not valid_name(playername):
        session["index_errors"] = "ENTER A NAME"
        return redirect("/")

    session.pop("index_errors", None)
    set_session_identity("player", playername)
    return render_template("join.html", hostname=host.name, playername=playername)


# ----- SOCKET COMMUNICATION -----


# -- Connect / disconnect --


@socketio.on("player_game_joined")
def game_joined(data):
    identity = session_identity("player")
    if identity is None:
        emit("srv_abort_connect")
        return

    playername, token = identity
    host = game.host

    if host is None or host.name == playername:
        emit("srv_abort_connect")
        return

    existing_player = game.get_player(playername)
    if existing_player:
        if player_tokens.get(playername) != token:
            emit("srv_abort_connect")
            return
        for sid, name in list(player_sids.items()):
            if name == playername:
                del player_sids[sid]
    else:
        player = Player(playername)
        game.add_player(player)
        player_tokens[playername] = token

    player_sids[socket_id()] = playername
    send_game_update()


@socketio.on("game_hosted")
def game_hosted(data):
    global host_sid, host_token

    identity = session_identity("host")
    if identity is None:
        emit("srv_abort_connect")
        return

    hostname, token = identity
    host = game.host
    if host:
        if host.name != hostname or host_token != token:
            emit("srv_abort_connect")
            return
    else:
        game.set_host(Host(hostname))
        host_token = token

    host_sid = socket_id()

    send_host_update()
    send_game_update()


@socketio.on("disconnect")
def disconnected():
    if is_host():
        socketio.start_background_task(remove_disconnected_host, socket_id())
        return

    sid = socket_id()
    playername = player_sids.get(sid)
    if playername and game.get_player(playername):
        socketio.start_background_task(remove_disconnected_player, sid, playername)


# -- Host Actions --


@socketio.on("host_kick_player")
def host_kick_player(data):
    if not is_host():
        return

    playername = data["playername"]
    socketio.emit("srv_kick_player", playername)
    if game.get_player(playername):
        game.remove_player(playername)
        for sid, name in list(player_sids.items()):
            if name == playername:
                del player_sids[sid]
        send_game_update()


@socketio.on("host_change_roundmode")
def host_change_roundmode(data):
    if not is_host() or game.round_in_progress or stopwatch.is_running:
        return

    if not isinstance(data, dict):
        return

    gm = data.get("gamemode")
    if gm == "buzzer":
        game.round_mode = RoundMode.Buzzer
    elif gm == "guessing":
        game.round_mode = RoundMode.Guessing
    elif gm == "stopwatch":
        game.round_mode = RoundMode.Stopwatch
    else:
        return

    send_game_update()


@socketio.on("host_next_round")
def host_next_round():
    if not is_host():
        return

    game.next_round()
    send_game_update()
    socketio.emit("srv_next_round")


@socketio.on("host_change_score")
def host_change_score(data):
    if not is_host():
        return

    if not isinstance(data, dict):
        return

    player_name = data.get("player_name")
    player = game.get_player(player_name)
    if not player:
        return

    action = data.get("action")
    if action in {"correct", "wrong", "skip"} and player.round_has_received_pts:
        return

    if action == "correct":
        player.correct_answer()
    elif action == "wrong":
        player.wrong_answer()
    elif action == "skip":
        player.round_has_received_pts = True
    elif action == "bonus":
        points = data.get("bonus_points")
        if type(points) is not int:
            return
        player.bonus_points += points
    else:
        return

    send_game_update()


@socketio.on("host_stopwatch_action")
def host_start_stopwatch(data):
    if not is_host() or game.round_mode != RoundMode.Stopwatch:
        return

    if not isinstance(data, dict):
        return

    action = data.get("action")

    if action == "start":
        changed = stopwatch.start()
    elif action == "stop":
        changed = stopwatch.stop()
    elif action == "reset":
        changed = stopwatch.reset()
    else:
        return

    if changed:
        socketio.emit("srv_stopwatch_action", action)


@socketio.on("host_guess_column_change")
def host_guess_column_change(data):
    if not is_host() or game.round_mode != RoundMode.Guessing or game.round_in_progress:
        return

    if not isinstance(data, dict):
        return

    action = data.get("action")

    if action == "add" and game.guessing_amount < 10:
        game.guessing_amount += 1
    elif action == "remove" and game.guessing_amount > 1:
        game.guessing_amount -= 1
    else:
        return

    send_game_update()


# -- Player Actions --


@socketio.on("player_buzzer_click")
def buzzer_clicked(data):
    player = current_player()

    if not player or game.round_mode != RoundMode.Buzzer:
        return

    player.buzz()
    game.round_in_progress = True
    send_game_update()


@socketio.on("player_guess_lockin")
def player_guess_lockin(data):
    player = current_player()

    if not player or game.round_mode != RoundMode.Guessing:
        return

    if not isinstance(data, dict):
        return

    guesses = data.get("guesses")
    if (
        not player.guessing_list
        and isinstance(guesses, list)
        and len(guesses) == game.guessing_amount
        and all(isinstance(guess, str) for guess in guesses)
    ):
        player.set_guesses(guesses)
        game.round_in_progress = True
        send_game_update(True)


@socketio.on("player_stopwatch_stop")
def player_stopwatch_stop(data):
    player = current_player()

    if (
        not player
        or game.round_mode != RoundMode.Stopwatch
        or not stopwatch.is_running
        or player.stopwatch_time is not None
    ):
        return

    elapsed = stopwatch.elapsed()
    if elapsed is None:
        return

    player.stop_stopwatch(elapsed)
    game.round_in_progress = True
    send_game_update()

    confirm_data = (player.name, player.stopwatch_time)
    socketio.emit("srv_confirm_stopwatch_time", confirm_data)


# ------ MAIN --------

if __name__ == "__main__":
    if "PORT" in os.environ:
        # Hosting platforms provide PORT for publicly reachable web services.
        port = int(os.environ["PORT"])
        socketio.run(app, host="0.0.0.0", port=port)
    else:
        # local
        socketio.run(app, debug=True)
