function create_player_list(game, id) {
    function new_list() {
        var list = document.createElement('ul');
        list.classList.add('list-group', 'mx-auto');
        list.classList.add('gap-1');
        list.style = 'width: 55%;';
        return list;
    }

    function new_list_item() {
        var item = document.createElement('li');
        item.classList.add('list-group-item');
        item.classList.add('border', 'rounded', 'buzzer_list_item');
        return item;
    }

    function new_content() {
        var content = document.createElement('span');
        content.classList.add('d-flex', 'justify-content-center');
        content.style = 'font-size: 110%;';
        return content;
    }


    if (game.players.length == 0) {
        var list = new_list();

        var item = new_list_item();
        item.classList.add('list-group-item-secondary');
        var content = new_content();
        content.classList.add('fw-bold');
        content.innerText = 'No players joined yet';
        item.appendChild(content);

        list.appendChild(item);

        var div = document.createElement('div');
        div.setAttribute('id', id);
        div.appendChild(list);
        return div;
    }


    var buzz_list = new_list();
    var non_buzz_list = new_list();
    var current_guesser_idx = -1;
    for (var i = 0; i < game.players.length; i++) {
        var player = game.players[i];
        var item = new_list_item();

        var content = new_content();
        item.appendChild(content);

        if (player.has_buzzed) {
            // Name
            var name = document.createElement('span');
            name.innerText = player.name;
            content.appendChild(name);

            // Coloring
            if (player.round_has_answered) {
                if (player.round_correct_answer) {
                    // Correct answer
                    item.classList.add('list-group-item-success', 'buzzer_list_item_correct');
                }
                else if (player.round_correct_answer === false) {
                    // Wrong answer
                    item.classList.add('list-group-item-danger', 'buzzer_list_item_wrong');
                }
                else {
                    // Skipped answer
                    item.classList.add('list-group-item-warning', 'buzzer_list_item_wait');
                }
            }
            else {
                // Not answered yet
                if (current_guesser_idx === -1) {
                    // Current guesser
                    content.classList.add('fw-bold');
                    item.classList.add('border-3', 'my-2');
                    content.style = 'font-size: 200%;';
                    current_guesser_idx = i;
                }

                item.classList.add('list-group-item-warning', 'buzzer_list_item_wait');
            }

            
            // Add bagde for stopwatch
            if (player.buzz_time_sw) {
                var sw = document.createElement('span');
                sw.className = 'badge bg-secondary mt-1 buzz_time_badge';
                sw.innerText = player.buzz_time_sw;
                item.appendChild(sw);
            }

            buzz_list.appendChild(item);
        }
        else {
            content.innerText = `${player.name}`;
            item.classList.add('list-group-item-secondary', 'buzzer_list_item_stale');
            non_buzz_list.appendChild(item);
        }    

        if (current_guesser_idx !== i) {
            item.classList.add('mx-5');
        }
    }

    // create entire div
    var div = document.createElement('div');
    div.className = 'd-grid col-12 mx-auto gap-5';
    div.setAttribute('id', id);

    if (buzz_list.childNodes.length > 0)
        div.appendChild(buzz_list);
    if (non_buzz_list.childNodes.length > 0)
        div.appendChild(non_buzz_list);
    return div;
}

function create_scoreboard(players, id, is_host) {
    console.log(is_host);

    function create_kick_button(player) {
        var btn = document.createElement('button');
        btn.className = 'btn btn-sm btn-danger ms-4 kick_button';
        btn.innerText = 'Kick';
        const kicked_name = player;
        btn.onclick = function () { socket.emit('host_kick_player', { playername: kicked_name }); };
        return btn;
    }


    if (players.length == 0) {
        var tbody = document.createElement('tbody');
        tbody.setAttribute('id', id);

        var tr = document.createElement('tr');

        var td = document.createElement('td');
        td.className = 'text-center pt-2 pb-4';
        td.setAttribute('colspan', 6);
        td.innerText = 'No players joined yet';

        tr.appendChild(td);
        tbody.appendChild(tr);
        return tbody;
    }

    // Sort by pts, correct, wrong, bonus, name
    var cmp_func = function (a, b) { return -(a.pts - b.pts) || -(a.correct_answers - b.correct_answers) };
    players.sort(cmp_func);

    var tbody = document.createElement('tbody');
    tbody.setAttribute('id', id);
    for (var i = 0; i < players.length; i++) {
        var row = document.createElement('tr');

        var th_nr = document.createElement('th');
        th_nr.setAttribute('scope', 'row');
        if (i == 0 || cmp_func(players[i-1], players[i]) != 0)
            th_nr.innerHTML = i+1;
        row.appendChild(th_nr);

        var td_name = document.createElement('td');
        td_name.innerHTML = players[i].name;
        row.appendChild(td_name);

        var td_correct = document.createElement('td');
        td_correct.innerHTML = players[i].correct_answers;
        row.appendChild(td_correct);

        var td_wrong = document.createElement('td');
        td_wrong.innerHTML = players[i].wrong_answers;
        row.appendChild(td_wrong);

        var td_bonus = document.createElement('td');
        td_bonus.innerHTML = players[i].bonus_points;
        row.appendChild(td_bonus);

        var td_pts = document.createElement('td');
        td_pts.className = 'fw-bold';
        td_pts.innerHTML = players[i].pts;
        row.appendChild(td_pts);

        if (is_host) {
            var td_kick = document.createElement('td');
            td_kick.appendChild(create_kick_button(players[i].name));
            row.appendChild(td_kick);
        }

        tbody.appendChild(row);
    }

    return tbody;
}

function create_dropdown(players, id) {
    players.sort(function (a, b) { return a.name.localeCompare(b.name); });

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

    players.forEach(p => {
        var option = document.createElement('option');
        option.value = p.name;
        option.innerText = p.name;

        select.appendChild(option);
    });

    return select;
}


function toggle_answer_button_status(players) {
    var guesser_left = false;
    for (i = 0; i < players.length; i++) {
        if (players[i].has_buzzed && !players[i].round_has_answered)
            guesser_left = true;
    }

    document.getElementById('correct_button').disabled = !guesser_left;
    document.getElementById('wrong_button').disabled = !guesser_left;
    document.getElementById('skip_button').disabled = !guesser_left;
}


function create_guess_overview(players, id) {
    if (players.length == 0) {
        var tbody = document.createElement('tbody');
        tbody.setAttribute('id', id);

        var tr = document.createElement('tr');

        var td = document.createElement('td');
        td.className = 'text-center pt-2 pb-4';
        td.setAttribute('colspan', 2);
        td.innerText = 'No players joined yet';

        tr.appendChild(td);
        tbody.appendChild(tr);
        return tbody;
    }

    // Sort by pts, correct, wrong, bonus, name
    players.sort(function (a, b) { return a.name.localeCompare(b.name); });

    var tbody = document.createElement('tbody');
    tbody.setAttribute('id', id);
    for (var i = 0; i < players.length; i++) {
        var row = document.createElement('tr');

        var td_name = document.createElement('td');
        td_name.innerHTML = players[i].name;
        row.appendChild(td_name);

        var td_guess = document.createElement('td');
        td_guess.innerHTML = players[i].round_guess ?? '';
        row.appendChild(td_guess);

        tbody.appendChild(row);
    }

    return tbody;
}