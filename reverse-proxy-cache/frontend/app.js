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
    // Start the timer
    const startTime = Date.now();
    // Counter to keep track of how many URLs are processed
    let processedCount = 0;
    
    console.log('Form submitted. Starting WebSocket connection...');

    window.socket.onopen = function() {
        const data = JSON.stringify({ urls, cacheStrategy });
        window.socket.send(data);
        console.log('WebSocket opened. Sent initial data.');
    };
    
    window.socket.onmessage = function(event) {
        let response;
        try {
            // Attempt to parse as JSON
            response = JSON.parse(event.data);
        } catch (e) {
            // If parsing fails, treat it as plain text
            console.log("Received non-JSON message:", event.data);
            response = { data: event.data };
        }
        // Update the log messages
        const newMessage = document.createElement('li');
        newMessage.textContent = response.data;
        log.appendChild(newMessage);
        // Update the processed count
        processedCount += 1;
        
        // Update the time taken for each message
        const currentTime = Date.now();
        const timeTaken = (currentTime - startTime) / 1000;  // Time in seconds
        document.getElementById('time-taken').textContent = `Time Taken: ${timeTaken.toFixed(2)}s`;
        
        // Debugging: Print time to console
        console.log(`Message ${processedCount}/${urls.length} received. Time taken: ${timeTaken.toFixed(2)}s`);
        
        // If all URLs are processed, update the dashboard
        if (processedCount === urls.length) {
            const cacheStats = response.cacheStats;
            if (cacheStats) {
                // Print cache hits and misses to the console for debugging
                console.log(`Cache Hits: ${cacheStats.hits}`);
                console.log(`Cache Misses: ${cacheStats.misses}`);
                // Update the dashboard with cache stats
                document.getElementById('cache-hits-value').textContent = cacheStats.hits;
                document.getElementById('cache-misses-value').textContent = cacheStats.misses;
                // Display the dashboard
                document.getElementById('dashboard').style.display = 'block';
            }
            console.log('All URLs processed. Final time:', timeTaken.toFixed(2), 's');
        }
    };
    window.socket.onerror = function(error) {
        console.error('WebSocket Error:', error);
    };
    window.socket.onclose = function(event) {
        console.log('WebSocket connection closed:', event);
    };
});