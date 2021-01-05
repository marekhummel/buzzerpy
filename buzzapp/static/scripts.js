function create_player_list(array, id) {
    // Sort by buzzer first, then by time
    array.sort(function (a, b) { return -(a.has_buzzed - b.has_buzzed) || a.buzz_time - b.buzz_time })


    var list = document.createElement('ul');
    list.setAttribute("id", id);

    for (var i = 0; i < array.length; i++) {
        var item = document.createElement('li');
        var str = array[i].name;
        if (array[i].has_buzzed) {
            str += ": BUZZED";
            if (array[i].buzz_time_sw) {
                str += " (sw " + array[i].buzz_time_sw.toString() + ")";
            }
        }
        item.appendChild(document.createTextNode(str));
        list.appendChild(item);
    }

    return list;
}