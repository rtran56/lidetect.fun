var socketio = io();

// const game_over = document.querySelector('#game-over').textContent;
// console.log('Game over?', game_over);
// console.log('Game over?', (game_over === 'False'));

socketio.on("redirect", (dest) => {
    window.location.pathname = dest;
    // if (game_over === 'False') {
    //     console.log('Redirecting!!');
        
    // }
});
