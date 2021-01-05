
let startTime;
let elapsedTime = 0;
let timerInterval;
let is_running = false;


function timeToString(time) {
    let diffInHrs = time / 3600000;
    let hh = Math.floor(diffInHrs);

    let diffInMin = (diffInHrs - hh) * 60;
    let mm = Math.floor(diffInMin);

    let diffInSec = (diffInMin - mm) * 60;
    let ss = Math.floor(diffInSec);

    let diffInMs = (diffInSec - ss) * 100;
    let ms = Math.floor(diffInMs);

    let formattedMM = mm.toString().padStart(2, "0");
    let formattedSS = ss.toString().padStart(2, "0");
    let formattedMS = ms.toString().padStart(2, "0");

    return `${formattedMM}:${formattedSS}:${formattedMS}`;
}


function print(txt) {
    document.getElementById("stopwatch").innerHTML = txt;
}

function stopwatch_start() {
    if (!is_running) {
        startTime = Date.now() - elapsedTime;
        timerInterval = setInterval(function printTime() {
            elapsedTime = Date.now() - startTime;
            print(timeToString(elapsedTime));
        }, 10);
        is_running = true;
    }
}

function stopwatch_stop() {
    if (is_running) {
        clearInterval(timerInterval);
        is_running = false;
    }
}

function stopwatch_reset() {
    if (!is_running) {
        clearInterval(timerInterval);
        print("00:00:00");
        elapsedTime = 0;
    }
}


function get_stopwatch_value() {
    return timeToString(elapsedTime);
}