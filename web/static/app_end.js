var socketio = io();

socketio.on("redirect", (dest) => {
    window.location.pathname = dest;
});
