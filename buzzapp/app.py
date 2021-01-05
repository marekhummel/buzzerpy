from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit
from werkzeug.utils import redirect

from helper import host_to_json, playerlist_to_json
from model.game import BuzzGame, Host, Player, Stopwatch

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
startup = True

game: BuzzGame = BuzzGame()
sw: Stopwatch = Stopwatch()


def send_player_update():
    playerjson = playerlist_to_json(game.players)
    socketio.emit('player_update', playerjson)


def send_host_update():
    hostjson = host_to_json(game.host)
    print(hostjson)
    socketio.emit('host_update', hostjson)


# ----- APP ROUTES -----

@app.route('/')
def main():
    global startup
    if startup:
        session.clear()
        startup = False
    errors = session.get('index_errors')
    return render_template('index.html', errors=errors)


@app.route('/host')
def host():
    if game.has_host():
        session['index_errors'] = 'GAME ALREADY HOSTED'
        return redirect('/')

    hostname = request.args.get('name')
    session.pop('index_errors', None)
    return render_template('host.html', hostname=hostname)


@app.route('/join')
def join():
    playername = request.args.get('name')

    if not game.has_host():
        session['index_errors'] = 'GAME NOT HOSTED YET'
        return redirect('/')

    if game.get_player(playername):
        session['index_errors'] = 'NAME ALREADY CHOSEN'
        return redirect('/')

    session.pop('index_errors', None)
    return render_template('join.html', hostname=game.host.name, playername=playername)


# ----- SOCKET COMMUNICATION -----

@socketio.on('game_joined')
def game_joined(data):
    playername = data['playername']

    if not game.has_host() or game.get_player(playername):
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
    print("HAS LEFT")
    send_host_update()
    send_player_update()


@socketio.on('host_stopwatch_action')
def host_start_stopwatch(data):
    action = data['action']

    if action == 'start':
        sw.start()
    elif action == 'stop':
        sw.stop()
    elif action == 'reset':
        sw.reset()

    socketio.emit('stopwatch_action', action)


@socketio.on('buzzer_clicked')
def buzzer_clicked(data):
    playername = data['playername']
    player = game.get_player(playername)

    if not player:
        raise LookupError('Player gone')
    player.buzz(sw.elapsed())

    send_player_update()


@socketio.on('host_buzzer_reset')
def buzzer_reset():
    for p in game.players:
        p.reset()

    send_player_update()
    socketio.emit('player_buzzer_reset')


if __name__ == "__main__":
    socketio.run(app, debug=True)

