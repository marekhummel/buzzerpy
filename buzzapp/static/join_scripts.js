// VARIABLES
var closing_timer;
var guesses = 0;
var round_mode = 0;


// ----- SOCKETS -----
function on_game_update(game, host_only) {
    if (host_only) return;

    var new_scoreboard = create_scoreboard(game.players, 'scoreboard', false);
    replace_element('scoreboard', new_scoreboard);

    round_mode = game.round_mode;
    switch (round_mode) {
        case 0:
            var [new_ul, _] = create_player_list(game, 'playerlist');
            replace_element('playerlist', new_ul);
            break;
        case 1:
            var old_guesses = $('#guessing_inputs input');
            var old_focus_idx = old_guesses.toArray().findIndex((input) => input == document.activeElement);
            var new_guessing_input = create_guessing_input(game.guessing_amount, 'guessing_inputs', old_guesses);
            replace_element('guessing_inputs', new_guessing_input);
            restore_focus_guessing_input(old_focus_idx, '#guessing_inputs input');

            guesses = game.guessing_amount;
            break;
    }

    $('#carousel').carousel(round_mode);
}

function on_host_update(host) {
    if (host === undefined) {
        var closing_counter = 30;
        closing_timer = setInterval(function () {
            closing_counter--;
            $('#hostname').text(`Your host has left, game will be closed in ${closing_counter}secs`);
            if (closing_counter == 0) {
                clearInterval(closing_timer);
                window.location.href = '/';
            }
        }, 1000);
    }
    else {
        clearInterval(closing_timer);
        $('#hostname').html(`Hosted by <b>&raquo;${host.name}&laquo;</b>`);
    }
}

function on_next_round() {
    $('#buzzer').prop('disabled', false).text('BUZZ')
                .removeClass('btn-success').addClass('btn-danger');
    $('#guessing_inputs input').prop('disabled', false).val('');
    $('#btn_lock_guess').prop('disabled', false).text('Lock In');
    $('#btn_stopwatch_stop').prop('disabled', false).text('Stop');
}

function on_stopwatch_action(action) {
    switch (action) {
        case 'start':
            stopwatch_start();
            break;
        case 'stop':
            stopwatch_stop();
            break;
        case 'reset':
            stopwatch_reset();
            break;
    };
}

function on_host_confirm_stopwatch_time(player, time) {
    if (player == window.playername)
        $('#btn_stopwatch_stop').text('Stopped at ' + time.toFixed(2) + ' secs');
}

function on_srv_kick_player(kicked) {
    if (kicked == window.playername)
        window.location.href = '/';
}


// ----- DOM UPDATES -----

// GUESSING
function create_guessing_input(cols, id, old_inputs) {
    var div = document.createElement('div');
    div.setAttribute('id', id);

    for (i = 0; i < cols; i++) {
        var input = document.createElement('input');
        input.classList.add('form-control', 'text-center', 'my-1');
        input.setAttribute('id', 'input_guess_' + i);
        input.setAttribute('autocomplete', 'off');
        
        var placeholder = 'Your Guess';
        if (cols > 1) placeholder += ' #' + (i+1);
        input.setAttribute('placeholder', placeholder);
        
        // Keep previous inputs
        if (old_inputs.length > 0) {
            if (i < old_inputs.length) {
                input.value = old_inputs[i].value;
            }
            input.disabled = old_inputs[0].disabled;
        }
        div.appendChild(input);
    }
    return div;
}

function restore_focus_guessing_input(old_focus_idx, new_inputs_selector) {
    console.log('restore_focus');
    if (old_focus_idx == -1)
        return;

    var new_inputs = $(new_inputs_selector).toArray();
    if (new_inputs.length <= old_focus_idx)
        return;

    new_inputs[old_focus_idx].focus();
}