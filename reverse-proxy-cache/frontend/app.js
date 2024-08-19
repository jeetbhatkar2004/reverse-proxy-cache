document.getElementById('url-form').addEventListener('submit', function(event) {
    event.preventDefault();
    const urls = document.getElementById('urls').value.split('\n');
    const cacheStrategy = document.getElementById('cache-strategy').value;

    const socket = new WebSocket('ws://localhost:6789');

    socket.onopen = function() {
        const data = JSON.stringify({ urls, cacheStrategy });
        socket.send(data);
    };

    socket.onmessage = function(event) {
        const log = document.getElementById('log-messages');
        const newMessage = document.createElement('li');
        newMessage.textContent = event.data;
        log.appendChild(newMessage);
    };
});
