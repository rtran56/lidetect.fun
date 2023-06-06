var socketio = io();

socketio.on("redirect", (dest) => {
    console.log(dest);
    window.location.pathname = dest;
});

