import os

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
first_request = True

game = BuzzGame()
stopwatch = Stopwatch()
host_sid: str | None = None
player_sids: dict[str, str] = {}


def send_game_update(host_only=False):
    socketio.emit("srv_game_update", (game.toJson(), host_only))


def send_host_update():
    socketio.emit("srv_host_update", game.host.toJson() if game.host else None)


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


# Force update of js files
@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store"
    return response


# ----- APP ROUTES -----


@app.route("/")
def index():
    global first_request  # Not preferred, but works for now
    if first_request:
        session.clear()
        first_request = False
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
    hostname = request.args.get("name")

    if game.has_host():
        session["index_errors"] = "GAME ALREADY HOSTED"
        return redirect("/")

    if game.get_player(hostname):
        session["index_errors"] = "NAME ALREADY CHOSEN"
        return redirect("/")

    session.pop("index_errors", None)
    return render_template("host.html", hostname=hostname)


@app.route("/join")
def join():
    playername = request.args.get("name")
    host = game.host

    if host is None:
        session["index_errors"] = "GAME NOT HOSTED YET"
        return redirect("/")

    if game.get_player(playername) or host.name == playername:
        session["index_errors"] = "NAME ALREADY CHOSEN"
        return redirect("/")

    if playername == "":
        session["index_errors"] = "ENTER A NAME"
        return redirect("/")

    session.pop("index_errors", None)
    return render_template("join.html", hostname=host.name, playername=playername)


# ----- SOCKET COMMUNICATION -----


# -- Connect / disconnect --


@socketio.on("player_game_joined")
def game_joined(data):
    playername = data["playername"]
    host = game.host

    if (
        host is None
        or game.get_player(playername)
        or host.name == playername
        or playername == ""
    ):
        emit("srv_abort_connect")
        return

    player = Player(playername)
    game.add_player(player)
    player_sids[socket_id()] = playername
    send_game_update()


@socketio.on("player_game_left")
def game_left(data):
    playername = player_sids.pop(socket_id(), None)
    if playername and game.get_player(playername):
        game.remove_player(playername)
        send_game_update()


@socketio.on("game_hosted")
def game_hosted(data):
    global host_sid

    print("game_hosted" + str(data))
    if game.has_host():
        emit("srv_abort_connect")
        return

    hostname = data["hostname"]
    host = Host(hostname)
    game.set_host(host)
    host_sid = socket_id()

    send_host_update()
    send_game_update()


@socketio.on("game_host_left")
def game_host_left():
    global host_sid

    if not is_host():
        return

    game.remove_host()
    host_sid = None
    send_host_update()
    send_game_update()


@socketio.on("disconnect")
def disconnected():
    global host_sid

    if is_host():
        game.remove_host()
        host_sid = None
        send_host_update()
        send_game_update()
        return

    playername = player_sids.pop(socket_id(), None)
    if playername and game.get_player(playername):
        game.remove_player(playername)
        send_game_update()


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
    if not is_host():
        return

    gm = data["gamemode"]
    if gm == "buzzer":
        game.round_mode = RoundMode.Buzzer
    elif gm == "guessing":
        game.round_mode = RoundMode.Guessing
    elif gm == "stopwatch":
        game.round_mode = RoundMode.Stopwatch
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

    player_name = data["player_name"]
    player = game.get_player(player_name)
    if not player:
        return

    action = data["action"]
    if action == "correct":
        player.correct_answer()
    elif action == "wrong":
        player.wrong_answer()
    elif action == "skip":
        player.round_has_received_pts = True
    elif action == "bonus":
        points = data["bonus_points"]
        player.bonus_points += points

    send_game_update()


@socketio.on("host_stopwatch_action")
def host_start_stopwatch(data):
    if not is_host():
        return

    action = data["action"]

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
    if not is_host():
        return

    action = data["action"]

    if action == "add":
        game.guessing_amount += 1
    elif action == "remove":
        game.guessing_amount -= 1

    send_game_update()


# -- Player Actions --


@socketio.on("player_buzzer_click")
def buzzer_clicked(data):
    player = current_player()

    if not player:
        return

    player.buzz()
    game.round_in_progress = True
    send_game_update()


@socketio.on("player_guess_lockin")
def player_guess_lockin(data):
    player = current_player()

    if not player:
        return

    if not player.guessing_list:
        player.set_guesses(data["guesses"])
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
