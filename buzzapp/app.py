from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit
from werkzeug.utils import redirect

from model.game import BuzzGame, Host, Player, Stopwatch

app = Flask(__name__)
app.config['SECRET_KEY'] = 'jh324j2p948vn2mv50ü'
socketio = SocketIO(app)
first_request = True

game = BuzzGame()
stopwatch = Stopwatch()


def send_game_update():
    socketio.emit('game_update', game.toJson())


def send_host_update():
    socketio.emit('host_update', game.host.__dict__ if game.host else None)


# Force update of js files
@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store'
    return response


# ----- APP ROUTES -----

@app.route('/')
def index():
    global first_request  # Not preferred, but works for now
    if first_request:
        session.clear()
        first_request = False
    errors = session.get('index_errors')
    return render_template('index.html', errors=errors)


@app.route('/host')
def host():
    hostname = request.args.get('name')

    if game.has_host():
        session['index_errors'] = 'GAME ALREADY HOSTED'
        return redirect('/')

    if game.get_player(hostname):
        session['index_errors'] = 'NAME ALREADY CHOSEN'
        return redirect('/')

    session.pop('index_errors', None)
    return render_template('host.html', hostname=hostname)


@app.route('/join')
def join():
    playername = request.args.get('name')

    if not game.has_host():
        session['index_errors'] = 'GAME NOT HOSTED YET'
        return redirect('/')

    if game.get_player(playername) or game.host.name == playername:
        session['index_errors'] = 'NAME ALREADY CHOSEN'
        return redirect('/')

    if playername == '':
        session['index_errors'] = 'ENTER A NAME'
        return redirect('/')

    session.pop('index_errors', None)
    hname = game.host.name
    return render_template('join.html', hostname=hname, playername=playername)


# ----- SOCKET COMMUNICATION -----


# -- Connect / disconnect --

@socketio.on('game_joined')
def game_joined(data):
    playername = data['playername']

    if (not game.has_host() or game.get_player(playername) or
            game.host.name == playername or playername == ''):
        emit('disconnect')
        return

    player = Player(playername)
    game.add_player(player)
    send_game_update()


@socketio.on('game_left')
def game_left(data):
    playername = data['playername']
    if game.get_player(playername):
        game.remove_player(playername)
        send_game_update()


@socketio.on('game_hosted')
def game_hosted(data):
    if game.has_host():
        emit('disconnect')
        return

    hostname = data['hostname']
    host = Host(hostname)
    game.set_host(host)

    send_host_update()
    send_game_update()


@socketio.on('game_host_left')
def game_host_left():
    assert game.has_host(), "non-existent host has left"

    game.remove_host()
    send_host_update()
    send_game_update()


# -- Stopwatch --

@socketio.on('host_stopwatch_action')
def host_start_stopwatch(data):
    action = data['action']

    if action == 'start':
        stopwatch.start()
    elif action == 'stop':
        stopwatch.stop()
    elif action == 'reset':
        stopwatch.reset()

    socketio.emit('stopwatch_action', action)


@socketio.on('host_kick_player')
def host_kick_player(data):
    playername = data['playername']
    socketio.emit('player_kicked', playername)
    if game.get_player(playername):
        game.remove_player(playername)
        send_game_update()


@socketio.on('buzzer_clicked')
def buzzer_clicked(data):
    playername = data['playername']
    player = game.get_player(playername)

    if not player:
        raise LookupError('Player gone')
    player.buzz(stopwatch.elapsed())

    send_game_update()


# -- Misc --

@socketio.on('guess_locked_in')
def guess_locked_in(data):
    playername = data['playername']
    player = game.get_player(playername)

    if not player:
        raise LookupError('Player gone')

    if not player.round_guess:
        player.round_guess = data['guess']
        send_game_update()


@socketio.on('host_next_round')
def next_round():
    game.next_round()
    send_game_update()
    socketio.emit('player_next_round')


@socketio.on('host_change_score')
def change_score(data):
    action = data['action']
    player = game.get_round_player()

    if player:
        if action == 'correct':
            player.correct_answer()
        elif action == 'wrong':
            player.wrong_answer()
        elif action == 'skip':
            player.round_has_answered = True

    else:
        player_name = data['player_name']
        player = game.get_player(player_name)
        if not player:
            return

        if action == 'correct':
            player.correct_answer()
        elif action == 'bonus':
            points = data['bonus_points']
            player.bonus_points += points

    send_game_update()


if __name__ == "__main__":
    socketio.run(app, debug=True)
