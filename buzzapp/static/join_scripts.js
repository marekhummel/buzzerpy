
// GUESSING
function create_guessing_input(cols, id) {
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

        div.appendChild(input);
    }
    return div;
}


