document.getElementById('url-form').addEventListener('submit', function(event) {
    event.preventDefault();

    const urls = document.getElementById('urls').value.split('\n').filter(url => url.trim() !== "");
    const cacheStrategy = document.getElementById('cache-strategy').value;

    // Clear the previous logs
    const log = document.getElementById('log-messages');
    log.innerHTML = '';  // Clear the log messages

    // Hide the dashboard initially
    document.getElementById('dashboard').style.display = 'none';

    // Close the previous WebSocket connection if it exists and is open
    if (window.socket && window.socket.readyState === WebSocket.OPEN) {
        window.socket.close();
    }

    // Create a new WebSocket connection
    window.socket = new WebSocket('ws://localhost:6789');  // Ensure this matches your WebSocket server port

    // Counter to keep track of how many URLs are processed
    let processedCount = 0;

    window.socket.onopen = function() {
        const data = JSON.stringify({ urls, cacheStrategy });
        window.socket.send(data);
    };

    window.socket.onmessage = function(event) {
        let response;
        try {
            // Try to parse the response as JSON
            response = JSON.parse(event.data);
        } catch (e) {
            // If parsing fails, treat the response as plain text
            response = { data: event.data };
        }

        console.log('Received response:', response);  // Log the received response

        // Update the log messages
        const newMessage = document.createElement('li');
        newMessage.textContent = response.data;
        log.appendChild(newMessage);

        // Update the processed count
        processedCount += 1;

        // If cache stats are available, update the dashboard
        if (response.cacheStats) {
            document.getElementById('cache-hits-value').textContent = response.cacheStats.hits;
            document.getElementById('cache-misses-value').textContent = response.cacheStats.misses;
            document.getElementById('dashboard').style.display = 'block';
        }

        // If all URLs are processed, ensure the dashboard is visible
        if (processedCount === urls.length) {
            document.getElementById('dashboard').style.display = 'block';
        }
    };

    window.socket.onerror = function(error) {
        console.error('WebSocket Error:', error);
    };

    window.socket.onclose = function(event) {
        console.log('WebSocket connection closed:', event);
    };
});