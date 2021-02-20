// SCOREBOARD
function create_scoreboard(players, id, is_host) {  
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
        td.setAttribute('colspan', 7);
        td.innerText = 'No players have joined yet';

        tr.appendChild(td);
        tbody.appendChild(tr);
        return tbody;
    }

    // Sort by pts, correct, wrong, bonus, name
    var pts_cmp_func = (a, b) => -(a.pts - b.pts);
    var cmp_fnc = (a, b) => pts_cmp_func(a, b) || -(a.correct_answers - b.correct_answers) || a.name.localeCompare(b.name);
    var sorted_players = players.slice().sort(cmp_fnc);

    var tbody = document.createElement('tbody');
    tbody.setAttribute('id', id);
    for (var i = 0; i < sorted_players.length; i++) {
        var player = sorted_players[i];
        var row = document.createElement('tr');

        var th_nr = document.createElement('th');
        th_nr.setAttribute('scope', 'row');
        if (i == 0 || pts_cmp_func(sorted_players[i-1], player) != 0)
            th_nr.innerHTML = i+1;
        row.appendChild(th_nr);

        var td_name = document.createElement('td');
        td_name.innerHTML = player.name;
        row.appendChild(td_name);

        var td_correct = document.createElement('td');
        td_correct.innerHTML = player.correct_answers;
        row.appendChild(td_correct);

        var td_wrong = document.createElement('td');
        td_wrong.innerHTML = player.wrong_answers;
        row.appendChild(td_wrong);

        var td_bonus = document.createElement('td');
        td_bonus.innerHTML = player.bonus_points;
        row.appendChild(td_bonus);

        var td_pts = document.createElement('td');
        td_pts.className = 'fw-bold';
        td_pts.innerHTML = player.pts;
        row.appendChild(td_pts);

        if (is_host) {
            var td_kick = document.createElement('td');
            td_kick.appendChild(create_kick_button(player.name));
            row.appendChild(td_kick);
        }

        tbody.appendChild(row);
    }

    return tbody;
}

// PLAYER LIST
function create_player_list(game, id) {
    function new_list() {
        var list = document.createElement('ul');
        list.classList.add('list-group', 'mx-auto');
        list.classList.add('gap-1');
        list.style = 'width: 100%;';
        return list;
    }

    function new_list_item() {
        var item = document.createElement('li');
        item.classList.add('list-group-item');
        item.classList.add('border', 'rounded', 'buzzer_list_item');

        var content = document.createElement('span');
        content.classList.add('d-flex', 'justify-content-center');
        content.style = 'font-size: 110%;';
        item.appendChild(content);

        return [item, content];
    }

    if (game.players.length == 0) {
        var list = new_list();

        var [item, content] = new_list_item();
        item.classList.add('list-group-item-secondary');
        content.classList.add('fw-bold');
        content.innerText = 'No players have joined yet';


        list.appendChild(item);

        var div = document.createElement('div');
        div.setAttribute('id', id);
        div.appendChild(list);
        return div;
    }

    var sorted_players = game.players.slice().sort((a, b) => a.buzzer_time - b.buzzer_time);
    var buzz_list = new_list();
    var non_buzz_list = new_list();
    var current_guesser_idx = -1;
    for (var i = 0; i < sorted_players.length; i++) {
        var player = sorted_players[i];
        var [item, content] = new_list_item();

        if (player.buzzer_has_buzzed) {
            // Name
            var name = document.createElement('span');
            name.classList.add('noselect');
            name.innerText = player.name;
            content.appendChild(name);

            // Coloring
            if (player.round_has_received_pts) {
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
                    item.style = 'width: 120%; margin-left: -10% !important;';
                    content.style = 'font-size: 200%;';
                    
                    current_guesser_idx = i;
                }

                item.classList.add('list-group-item-warning', 'buzzer_list_item_wait');
            }

            buzz_list.appendChild(item);
        }
        else {
            content.innerText = `${player.name}`;
            item.classList.add('list-group-item-secondary', 'buzzer_list_item_stale', 'noselect');
            non_buzz_list.appendChild(item);
        }

        if (current_guesser_idx !== i) {
            item.classList.add('mx-5');
        }
    }

    // create entire div
    var div = document.createElement('div');
    div.className = 'd-grid col-12 mx-auto gap-5 my-auto';
    div.setAttribute('id', id);

    if (buzz_list.childNodes.length > 0)
        div.appendChild(buzz_list);
    if (non_buzz_list.childNodes.length > 0)
        div.appendChild(non_buzz_list);
    return div;
}