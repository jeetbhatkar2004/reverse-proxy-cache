document.getElementById('url-form').addEventListener('submit', function(event) {
    event.preventDefault();

    const urls = document.getElementById('urls').value.split('\n').filter(url => url.trim() !== "");
    const cacheStrategy = document.getElementById('cache-strategy').value;

    // Clear the previous logs
    const log = document.getElementById('log-messages');
    log.innerHTML = '';  // Clear the log messages

    // Hide the dashboard initially
    document.getElementById('dashboard').style.display = 'none';

    // Reset cache stats
    let totalHits = 0;
    let totalMisses = 0;

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
        console.log('Raw response:', event.data);  // Log the raw response

        let response;
        try {
            // Try to parse the response as JSON
            response = JSON.parse(event.data);
        } catch (e) {
            // If parsing fails, treat the response as plain text
            response = { data: event.data };
        }

        console.log('Processed response:', response);  // Log the processed response

        // Update the log messages
        const newMessage = document.createElement('li');
        newMessage.textContent = response.data;
        log.appendChild(newMessage);

        // Update cache stats based on the response
        if (response.data.includes("Cache hit")) {
            totalHits++;
        } else if (response.data.includes("Cache miss")) {
            totalMisses++;
        }

        // Update the dashboard
        document.getElementById('cache-hits-value').textContent = totalHits;
        document.getElementById('cache-misses-value').textContent = totalMisses;
        document.getElementById('dashboard').style.display = 'block';

        // Update the processed count
        processedCount++;

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