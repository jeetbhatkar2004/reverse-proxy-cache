let socket;
document.getElementById('url-form').addEventListener('submit', function(event) {
    event.preventDefault();

    // Get the log element
    const log = document.getElementById('log-messages');

    // Debug: Print the current innerHTML before clearing
    console.log("Before clearing, log-messages innerHTML:");
    console.log(log.innerHTML);

    // Clear the previous logs
    log.innerHTML = '';  // This clears the log-messages container

    // Debug: Print the innerHTML after clearing to ensure it is empty
    console.log("After clearing, log-messages innerHTML:");
    console.log(log.innerHTML);

    const urls = document.getElementById('urls').value.split('\n').filter(url => url.trim() !== "");
    const cacheStrategy = document.getElementById('cache-strategy').value;

    // Close the previous WebSocket connection if it exists and is open
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.close();
    }

    // Create a new WebSocket connection
    socket = new WebSocket('ws://localhost:6789');  // Ensure this matches your WebSocket server port

    socket.onopen = function() {
        const data = JSON.stringify({ urls, cacheStrategy });
        socket.send(data);
    };

    socket.onmessage = function(event) {
        const newMessage = document.createElement('li');
        newMessage.textContent = event.data;
        log.appendChild(newMessage);
    };

    socket.onerror = function(error) {
        console.error('WebSocket Error:', error);
    };

    socket.onclose = function(event) {
        console.log('WebSocket connection closed:', event);
    };
});
