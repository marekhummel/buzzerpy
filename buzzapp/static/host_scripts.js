// GENERAL

function create_dropdown(players, id) {
    var sorted_players = players.slice().sort((a, b) => a.name.localeCompare(b.name));

    var select = document.createElement('select');
    select.setAttribute('id', id);
    select.className = 'form-select form-select-sm';
    select.required = true;

    var default_opt = document.createElement('option');
    default_opt.value = '';
    default_opt.disabled = true;
    default_opt.selected = true;
    default_opt.hidden = true;
    default_opt.innerText = 'Select Player';
    select.append(default_opt);

    sorted_players.forEach(p => {
        var option = document.createElement('option');
        option.value = p.name;
        option.innerText = p.name;

        select.appendChild(option);
    });

    return select;
}

function create_scorebuttons(players, id) {
    function create_button(text, btn_class, title, disabled, onclick) {
        var btn = document.createElement('button');
        btn.classList.add('btn', btn_class);
        btn.type = 'button';
        btn.title = title;
        btn.innerHTML = text;
        btn.disabled = disabled;
        btn.onclick = onclick;
        return btn;
    }

    var scorebuttons = document.createElement('div');
    scorebuttons.setAttribute('id', id);
    scorebuttons.classList.add('mt-auto');

    if (players.length == 0) {
        var row = document.createElement('div');
        row.classList.add('row');
        scorebuttons.appendChild(row);

        var form_group = document.createElement('div');
        form_group.classList.add('form-group', 'col-3', 'mx-auto');
        row.appendChild(form_group);

        var input_group = document.createElement('div');
        input_group.classList.add('input-group', 'my-1');
        form_group.appendChild(input_group);

        var name = document.createElement('input');
        name.type = "text";
        name.classList.add('form-control', 'text-center');
        name.value = 'No players have joined yet';
        name.disabled = true;
        input_group.appendChild(name);
    }


    var form = document.createElement('form');
    form.classList.add('form-inline');
    form.action = null;
    scorebuttons.appendChild(form);

    var row = document.createElement('div');
    row.classList.add('row');
    form.appendChild(row);

    // Sort by name
    var sorted_players = players.slice().sort((a, b) => a.name.localeCompare(b.name));
    for (var i = 0; i < sorted_players.length; i++) {
        var player = sorted_players[i];
        const player_name = player.name;

        var form_group = document.createElement('div');
        form_group.classList.add('form-group', 'col-4');
        row.appendChild(form_group);

        var input_group = document.createElement('div');
        input_group.classList.add('input-group', 'my-1');
        form_group.appendChild(input_group);

        var name = document.createElement('input');
        name.type = "text";
        name.classList.add('form-control');
        name.value = player_name;
        name.disabled = true;
        if (player.round_has_received_pts) {
            if (player.round_correct_answer)
                name.style = 'background: #d1e7dd;'; 
            else if (player.round_correct_answer === false)
                name.style = 'background: #f8d7da;'; 
            else
                name.style = 'background: #fff3cd;'; 
        }
        input_group.appendChild(name);

        console.log(player.guessing_list);
        var disabled = player.round_has_received_pts || (!player.buzzer_has_buzzed && !player.guessing_list && player.stopwatch_time === null);
        var btn_correct = create_button('&check;', 'btn-success', 'Correct answer', disabled, () => host_correct_answer(player_name));
        var btn_wrong = create_button('&cross;', 'btn-danger', 'Wrong answer', disabled, () => host_wrong_answer(player_name));
        var btn_skip = create_button('&#9711;', 'btn-secondary', 'Skip player', disabled, () => host_skip_player(player_name));
        input_group.appendChild(btn_correct);
        input_group.appendChild(btn_wrong);
        input_group.appendChild(btn_skip);       
    }

    return scorebuttons;
}

// GUESSING ROUND
function create_guess_overview(players, cols, id) {
    if (players.length == 0) {
        var tbody = document.createElement('tbody');
        tbody.setAttribute('id', id);

        var tr = document.createElement('tr');

        var td = document.createElement('td');
        td.className = 'text-center pt-2 pb-4';
        td.style = "white-space: normal !important; wor -wrap: break-word;";
        td.setAttribute('colspan', cols+1);
        td.innerText = 'No players have joined yet';

        tr.appendChild(td);
        tbody.appendChild(tr);
        return tbody;
    }

    // Sort by name
    var sorted_players = players.slice().sort((a, b) => a.name.localeCompare(b.name));

    var tbody = document.createElement('tbody');
    tbody.setAttribute('id', id);
    for (var i = 0; i < sorted_players.length; i++) {
        var row = document.createElement('tr');

        var td_name = document.createElement('td');
        td_name.innerHTML = sorted_players[i].name;
        row.appendChild(td_name);

        for (j = 0; j < cols; j++) {
            var td_guess = document.createElement('td');
            td_guess.innerHTML = sorted_players[i].guessing_list?.[j] ?? '';
            row.appendChild(td_guess);
        }


        tbody.appendChild(row);
    }

    return tbody;
}

function create_guess_overview_head(cols, id) {
    var thead = document.createElement('thead');
    thead.setAttribute('id', id);

    var tr = document.createElement('tr');
    thead.appendChild(tr);

    var namecol = document.createElement('th');
    namecol.setAttribute('scope', 'col');
    namecol.style = 'width: 25%;';
    namecol.innerText = 'Name';
    tr.appendChild(namecol);

    for (i = 0; i < cols; i++) {
        var guesscol = document.createElement('th');
        guesscol.setAttribute('scope', 'col');
        guesscol.innerText = 'Guess';
        if (cols > 1) guesscol.innerText += ' #' + (i+1);
        tr.appendChild(guesscol);
    }    

    return thead;
}

// STOPWATCH ROUND
function create_stopwatch_overview(players, id) {
    if (players.length == 0) {
        var tbody = document.createElement('tbody');
        tbody.setAttribute('id', id);

        var tr = document.createElement('tr');

        var td = document.createElement('td');
        td.className = 'text-center pt-2 pb-4';
        td.setAttribute('colspan', 2);
        td.innerText = 'No players have joined yet';

        tr.appendChild(td);
        tbody.appendChild(tr);
        return tbody;
    }

    // Sort by stopwatch time
    pressed_players = players.filter(p => p.stopwatch_time != null);
    pressed_players.sort((a, b) => a.stopwatch_time - b.stopwatch_time);
    other_players = players.filter(p => !pressed_players.includes(p));
    players = pressed_players.concat(other_players);

    var tbody = document.createElement('tbody');
    tbody.setAttribute('id', id);

    for (var i = 0; i < players.length; i++) {
        var row = document.createElement('tr');

        var td_name = document.createElement('td');
        td_name.innerHTML = players[i].name;
        row.appendChild(td_name);

        var td_guess = document.createElement('td');
        if (players[i].stopwatch_time != null)
            td_guess.innerHTML = players[i].stopwatch_time.toFixed(2) + ' secs';
        row.appendChild(td_guess);

        tbody.appendChild(row);
    }


    return tbody;
}


// MISC
function host_correct_answer(player) {
    socket.emit('host_change_score', { player_name: player, action: 'correct' });
};

function host_wrong_answer(player) {
    socket.emit('host_change_score', { player_name: player, action: 'wrong' });
};

function host_skip_player(player) {
    socket.emit('host_change_score', { player_name: player, action: 'skip' });
};

function host_bonus_points() {
    player = document.getElementById('player_dropdown').value;
    if (player === "") return;

    bonus_points = parseInt(document.getElementById('bonus_points').value);
    socket.emit('host_change_score', { player_name: player, action: 'bonus', bonus_points: bonus_points });

    document.getElementById('player_dropdown').selectedIndex = 1;
    document.getElementById('bonus_points').value = '';
};

function host_next_round() {
    socket.emit('host_next_round');
};

function host_change_roundmode_buzzer() {
    socket.emit('host_change_roundmode', { gamemode: 'buzzer' });
    $('#carousel').carousel(0);
}

function host_change_roundmode_guessing() {
    socket.emit('host_change_roundmode', { gamemode: 'guessing' });
    $('#carousel').carousel(1);
}

function host_change_roundmode_stopwatch() {
    socket.emit('host_change_roundmode', { gamemode: 'stopwatch' });
    $('#carousel').carousel(2);
}

function host_add_guess_column() {
    socket.emit('host_guess_column_change', { action: 'add' });
}

function host_remove_guess_column() {
    socket.emit('host_guess_column_change', { action: 'remove' });
}

function host_start_stopwatch() {
    socket.emit('host_stopwatch_action', { action: 'start' });
    stopwatch_start();
};

function host_stop_stopwatch() {
    socket.emit('host_stopwatch_action', { action: 'stop' });
    stopwatch_stop();
};

function host_reset_stopwatch() {
    socket.emit('host_stopwatch_action', { action: 'reset' });
    stopwatch_reset();
};