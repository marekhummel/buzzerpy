from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit
from werkzeug.utils import redirect

from helper import host_to_json, playerlist_to_json
from model.game import BuzzGame, Host, Player, Stopwatch

app = Flask(__name__)
app.config['SECRET_KEY'] = 'jh324j2p948vn2mv50ü'
socketio = SocketIO(app)
first_request = True

game = BuzzGame()
stopwatch = Stopwatch()


def send_player_update():
    playerjson = playerlist_to_json(game.get_players_ordered())
    socketio.emit('player_update', (playerjson, game.current_player))


def send_host_update():
    hostjson = host_to_json(game.host)
    socketio.emit('host_update', hostjson)


# Force update of js files
# @app.after_request
# def add_header(response):
#     response.headers['Cache-Control'] = 'no-cache, must-revalidate'
#     return response


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
    return render_template('join.html', hostname=game.host.name, playername=playername)


# ----- SOCKET COMMUNICATION -----

@socketio.on('game_joined')
def game_joined(data):
    playername = data['playername']

    if (not game.has_host() or game.get_player(playername) or
            game.host.name == playername or playername == ''):
        emit('disconnect')
        return

    player = Player(playername)
    game.add_player(player)
    send_player_update()


@socketio.on('game_left')
def game_left(data):
    playername = data['playername']
    game.remove_player(playername)
    send_player_update()


@socketio.on('game_hosted')
def game_hosted(data):
    if game.has_host():
        emit('disconnect')
        return

    hostname = data['hostname']
    host = Host(hostname)
    game.set_host(host)

    send_host_update()
    send_player_update()


@socketio.on('game_host_left')
def game_host_left():
    assert game.has_host(), "non-existent host has left"

    game.remove_host()
    send_host_update()
    send_player_update()


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
    # Model change will happen upon the disconnect coming from the kicked user


@socketio.on('buzzer_clicked')
def buzzer_clicked(data):
    playername = data['playername']
    player = game.get_player(playername)

    if not player:
        raise LookupError('Player gone')
    player.buzz(stopwatch.elapsed())
    if game.current_player is None:
        game.current_player = 0

    send_player_update()


@socketio.on('host_buzzer_reset')
def buzzer_reset():
    for p in game.players:
        p.reset_buzzer()
    game.current_player = None

    send_player_update()
    socketio.emit('player_buzzer_reset')


@socketio.on('host_change_score')
def change_score(data):
    action = data['action']
    player = None

    if game.current_player is not None:
        buzzed_players = [p for p in game.players if p.has_buzzed]
        if game.current_player < len(buzzed_players):
            player = game.get_players_ordered()[game.current_player]
   
    if not player and action != 'bonus':
        return

    if action == 'correct':
        player.correct_answers += 1
    elif action == 'wrong':
        player.wrong_answers += 1
        game.current_player += 1
    elif action == 'bonus':
        player_name = data['player_name']
        player = game.get_player(player_name)
        if not player:
            return

        points = data['bonus_points']
        player.bonus_points += points
    elif action == 'skip':
        game.current_player += 1

    send_player_update()


if __name__ == "__main__":
    socketio.run(app, debug=True)
