from typing import Dict

from flask import Flask, render_template, request
from flask_socketio import SocketIO, join_room, leave_room

from helper import playerlist_to_json
from model.game import BuzzGame, Player, Stopwatch


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

hosted_games: Dict[int, BuzzGame] = {}
sw: Stopwatch = Stopwatch()


@app.route('/')
def main():
    return render_template('index.html')


@app.route('/host')
def host():
    bg = BuzzGame(list(hosted_games.keys()))
    hosted_games[bg.id] = bg
    return render_template('host.html', gameid=bg.id)


@app.route('/join')
def join():
    gameid = int(request.args.get('gameid'))
    playername = request.args.get('playername')

    if gameid not in hosted_games.keys():
        return render_template('index.html', errors="GAME NOT EXISTENT")

    if hosted_games[gameid].get_player(playername):
        return render_template('index.html', errors="NAME ALREADY CHOSEN")

    return render_template('join.html', gameid=gameid, playername=playername)


@socketio.on('join_game')
def join_game(data):
    gameid = data['gameid']
    playername = data['playername']

    if gameid not in hosted_games.keys():
        return

    player = Player(playername)
    game = hosted_games[gameid]
    game.add_player(player)

    join_room(gameid)
    playerjson = playerlist_to_json(game.players)
    socketio.emit('game_update', playerjson, room=gameid)


@socketio.on('join_game_host')
def join_game_host(data):
    gameid = data['gameid']
    if gameid not in hosted_games.keys():
        return

    join_room(gameid)


@socketio.on('host_stopwatch_action')
def host_start_stopwatch(data):
    gameid = data['gameid']
    action = data['action']
    if gameid not in hosted_games.keys():
        return

    if action == 'start':
        sw.start()
    elif action == 'stop':
        sw.stop()
    elif action == 'reset':
        sw.reset()

    socketio.emit('stopwatch_action', action, room=gameid)


@socketio.on('click_buzzer')
def buzzer_clicked(data):
    gameid = data['gameid']
    playername = data['playername']

    game = hosted_games[gameid]
    player = game.get_player(playername)

    if not player:
        raise LookupError('Player gone')
    player.buzz(sw.elapsed())

    playerjson = playerlist_to_json(game.players)
    socketio.emit('game_update', playerjson, room=gameid)


@socketio.on('reset_buzzers') 
def buzzer_clicked(data):
    gameid = data['gameid']
    if gameid not in hosted_games.keys():
        return

    game = hosted_games[gameid]
    for p in game.players:
        p.reset()

    playerjson = playerlist_to_json(game.players)
    socketio.emit('game_update', playerjson, room=gameid)
    socketio.emit('buzzer_reset', room=gameid)


if __name__ == "__main__":
    socketio.run(app, debug=True)
