import os
from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit
from werkzeug.utils import redirect

from model.game import BuzzGame, Host, Player, Stopwatch, RoundMode

app = Flask(__name__)
app.config['SECRET_KEY'] = 'jh324j2p948vn2mv50ü'
socketio = SocketIO(app)
first_request = True

game = BuzzGame()
stopwatch = Stopwatch()


def send_game_update(host_only=False):
    socketio.emit('srv_game_update', (game.toJson(), host_only))


def send_host_update():
    socketio.emit('srv_host_update', game.host.toJson() if game.host else None)


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

@socketio.on('player_game_joined')
def game_joined(data):
    playername = data['playername']

    if (not game.has_host() or game.get_player(playername) or
            game.host.name == playername or playername == ''):
        emit('srv_abort_connect')
        return

    player = Player(playername)
    game.add_player(player)
    send_game_update()


@socketio.on('player_game_left')
def game_left(data):
    playername = data['playername']
    if game.get_player(playername):
        game.remove_player(playername)
        send_game_update()


@socketio.on('game_hosted')
def game_hosted(data):
    print('game_hosted' + str(data))
    if game.has_host():
        emit('srv_abort_connect')
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


# -- Host Actions --


@socketio.on('host_kick_player')
def host_kick_player(data):
    playername = data['playername']
    socketio.emit('srv_kick_player', playername)
    if game.get_player(playername):
        game.remove_player(playername)
        send_game_update()


@socketio.on('host_change_roundmode')
def host_change_roundmode(data):
    gm = data['gamemode']
    if gm == 'buzzer':
        game.round_mode = RoundMode.Buzzer
    elif gm == 'guessing':
        game.round_mode = RoundMode.Guessing
    elif gm == 'stopwatch':
        game.round_mode = RoundMode.Stopwatch
    send_game_update()


@socketio.on('host_next_round')
def host_next_round():
    game.next_round()
    send_game_update()
    socketio.emit('srv_next_round')


@socketio.on('host_change_score')
def host_change_score(data):
    player_name = data['player_name']
    player = game.get_player(player_name)
    if not player:
        return

    action = data['action']
    if action == 'correct':
        player.correct_answer()
    elif action == 'wrong':
        player.wrong_answer()
    elif action == 'skip':
        player.round_has_received_pts = True
    elif action == 'bonus':
        points = data['bonus_points']
        player.bonus_points += points

    send_game_update()


@socketio.on('host_stopwatch_action')
def host_start_stopwatch(data):
    action = data['action']

    if action == 'start':
        stopwatch.start()
    elif action == 'stop':
        stopwatch.stop()
    elif action == 'reset':
        stopwatch.reset()

    socketio.emit('srv_stopwatch_action', action)


@socketio.on('host_guess_column_change')
def host_guess_column_change(data):
    action = data['action']

    if action == 'add':
        game.guessing_amount += 1
    elif action == 'remove':
        game.guessing_amount -= 1

    send_game_update()


# -- Player Actions --

@socketio.on('player_buzzer_click')
def buzzer_clicked(data):
    playername = data['playername']
    player = game.get_player(playername)

    if not player:
        raise LookupError('Player gone')

    player.buzz()
    game.round_in_progress = True
    send_game_update()


@socketio.on('player_guess_lockin')
def player_guess_lockin(data):
    playername = data['playername']
    player = game.get_player(playername)

    if not player:
        raise LookupError('Player gone')

    if not player.guessing_list:
        player.set_guesses(data['guesses'])
        game.round_in_progress = True
        send_game_update(True)


@socketio.on('player_stopwatch_stop')
def player_stopwatch_stop(data):
    playername = data['playername']
    player = game.get_player(playername)

    if not player:
        raise LookupError('Player gone')

    player.stop_stopwatch(stopwatch.elapsed())
    game.round_in_progress = True
    send_game_update()

    confirm_data = (playername, player.stopwatch_time)
    socketio.emit('srv_confirm_stopwatch_time', confirm_data)


# ------ MAIN --------

if __name__ == "__main__":
    if 'PORT' in os.environ:
        # heroku run
        port = int(os.environ['PORT'])
        socketio.run(app, host='0.0.0.0', port=port)
    else:
        # local
        socketio.run(app, debug=True)

    
    
