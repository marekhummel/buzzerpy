function create_player_list(array, current_player, id, host) {
    if (array.length == 0) {
        var list = document.createElement('ul');
        list.className = 'list-group mx-auto';
        list.style = 'width: 70%;'

        var item = document.createElement('li');
        item.className = 'list-group-item list-group-item-secondary';

        var p = document.createElement('b');
        p.style = 'font-size: 130%;';
        p.innerText = "No players joined yet";
        item.appendChild(p);

        list.appendChild(item);

        var div = document.createElement('div');
        div.setAttribute("id", id);
        div.appendChild(list);
        return div;
    }


    // Sort by buzzer first, then by time
    // array.sort(function (a, b) { return -(a.has_buzzed - b.has_buzzed) || a.buzz_time - b.buzz_time })

    var buzz_list = document.createElement('ul');
    buzz_list.className = 'list-group mx-auto';
    buzz_list.style = 'width: 70%;'
    var non_buzz_list = document.createElement('ul');
    non_buzz_list.className = 'list-group mx-auto';
    non_buzz_list.style = 'width: 70%;'

    var list = buzz_list;

    for (var i = 0; i < array.length; i++) {
        var item = document.createElement('li');
        item.className = 'list-group-item';

        var p = document.createElement('span');
        p.style = 'font-size: 130%;';


        if (host) {
            var btn = document.createElement('button');
            btn.className = 'btn btn-sm btn-danger ms-4';
            btn.style = 'font-size: 90%; float:right;';
            btn.innerText = 'Kick';
            const kicked_name = array[i].name;
            btn.onclick = function () { socket.emit('host_kick_player', { playername: kicked_name }); };
            item.appendChild(btn);
        }

        if (array[i].has_buzzed) {
            var nr = document.createElement('span');
            nr.innerText = (i + 1) + '.';
            nr.className = 'me-3';
            var name = document.createElement('span');
            name.innerText = array[i].name;
            p.appendChild(nr);
            p.appendChild(name);
            if (i == current_player) {
                item.className += ' list-group-item-success';
                p.className = 'fw-bold';
            } else if (i < current_player) {
                item.className += ' list-group-item-danger';
            } else {
                item.className += ' list-group-item-warning';
            }

            list = buzz_list;

            if (array[i].buzz_time_sw) {
                var sw = document.createElement('span');
                sw.style = 'font-size: 90%; float:right;';
                sw.className = 'badge bg-secondary mt-1';
                sw.innerText = array[i].buzz_time_sw;
                item.appendChild(sw);
            }
        }
        else {
            p.innerText = `${array[i].name}`;
            item.className += ' list-group-item-secondary';
            list = non_buzz_list;
        }

        item.appendChild(p);
        list.appendChild(item);
    }

    var div = document.createElement('div');
    div.className = "d-grid col-12 mx-auto gap-3";
    div.setAttribute("id", id);

    if (buzz_list.childNodes.length > 0)
        div.appendChild(buzz_list);
    if (non_buzz_list.childNodes.length > 0)
        div.appendChild(non_buzz_list);
    return div;
}

function create_scoreboard(players, id) {
    if (players.length == 0) {
        var tbody = document.createElement('tbody');
        tbody.setAttribute("id", id);

        var tr = document.createElement('tr');

        var td = document.createElement('td');
        td.className = 'text-center pt-2 pb-4';
        td.setAttribute('colspan', 6);
        td.innerText = "No players joined yet";

        tr.appendChild(td);
        tbody.appendChild(tr);
        return tbody;
    }

    // Sort by pts, correct, wrong, bonus, name
    var cmp_func = function (a, b) { return -(a.pts - b.pts) || -(a.correct_answers - b.correct_answers) };
    players.sort(cmp_func);

    var tbody = document.createElement('tbody');
    tbody.setAttribute("id", id);
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

        tbody.appendChild(row);
    }

    return tbody;
}

function create_dropdown(players, id) {
    // <select id="player_dropdown" class="form-select form-select-sm" required>
    //     <option value="" disabled selected hidden>Select Player</option>
    // </select>

    players.sort(function (a, b) { return -a.name.localeCompare(b.name); });

    var select = document.createElement('select');
    select.setAttribute('id', id);
    select.className = 'form-select form-select-sm';
    select.required = true;

    var default_opt = document.createElement('option');
    default_opt.value = "";
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