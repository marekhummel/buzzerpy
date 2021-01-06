function create_player_list(array, id, host) {
    if (array.length == 0) {
        var list = document.createElement('ul');
        list.className = 'list-group';

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
    array.sort(function (a, b) { return -(a.has_buzzed - b.has_buzzed) || a.buzz_time - b.buzz_time })


    var buzz_list = document.createElement('ul');
    buzz_list.className = 'list-group';
    var non_buzz_list = document.createElement('ul');
    non_buzz_list.className = 'list-group';

    var list = buzz_list;

    for (var i = 0; i < array.length; i++) {
        var item = document.createElement('li');
        item.className = 'list-group-item';
        // if (i == 0) item.className += ' list-group-item-success';

        var p = document.createElement('b');
        p.style = 'font-size: 130%;';
        p.innerText = array[i].name;
        item.appendChild(p);

        if (array[i].has_buzzed) {
            item.className += ' list-group-item-success';
            list = buzz_list;

            if (array[i].buzz_time_sw) {
                var sw = document.createElement('span');
                sw.style = 'font-size: 100%; vertical-align: middle;';
                sw.className = 'badge badge-secondary float-right';
                sw.innerText = array[i].buzz_time_sw;
                item.appendChild(sw);
            }
        }
        else {
            item.className += ' list-group-item-danger';
            list = non_buzz_list;
        }


        if (host) {
            var btn = document.createElement('button');
            btn.className = 'btn btn-danger ml-2';
            btn.innerText = 'Kick';
            const kicked_name = array[i].name;
            btn.onclick = function () { socket.emit('host_kick_player', { playername: kicked_name }); };
            item.appendChild(btn);
        }

        list.appendChild(item);
    }

    var div = document.createElement('div');
    div.setAttribute("id", id);
    if (buzz_list.childNodes.length > 0 && non_buzz_list.childNodes.length > 0)
        buzz_list.className += ' mb-4';
    if (buzz_list.childNodes.length > 0) 
        div.appendChild(buzz_list);
    if (non_buzz_list.childNodes.length > 0) 
        div.appendChild(non_buzz_list);
    return div;
}
