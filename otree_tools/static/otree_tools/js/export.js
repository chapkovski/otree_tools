function makeid(length) {
    var text = "";
    var possible = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";

    for (var i = 0; i < length; i++)
        text += possible.charAt(Math.floor(Math.random() * possible.length));

    return text;
}

var ws_scheme = window.location.protocol == "https:" ? "wss" : "ws";
var ws_path = ws_scheme + '://' + window.location.host + "/exporttracker/" + makeid(10);
var socket = new WebSocket(ws_path);

function sendingEvent() {
    var msg = JSON.stringify({
        'request': 'export',
        'tracker_type': tracker_type,
    });
    if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify(msg));
    }
    ;
}

$(function () {
        var $button_container = $('#export_data');
        $button_container.click(function () {
            sendingEvent();

        });
        socket.onmessage = function (event) {
            var obj = jQuery.parseJSON(event.data);
            $button_container.html(obj.button);
            var has_url = obj.hasOwnProperty('url');
            if (has_url) {
                window.open(obj.url, '_blank');
            }
            ;
        };
    }
)