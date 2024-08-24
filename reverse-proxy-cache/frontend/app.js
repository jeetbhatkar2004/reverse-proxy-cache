document.addEventListener('DOMContentLoaded', () => {
    const urlForm = document.getElementById('url-form');
    const urlInput = document.getElementById('urls');
    const cacheStrategySelect = document.getElementById('cache-strategy');
    const logMessages = document.getElementById('log-messages');
    const dashboard = document.getElementById('dashboard');
    const timeTakenElement = document.getElementById('time-taken');
    const cacheHitsElement = document.getElementById('cache-hits-value');
    const cacheMissesElement = document.getElementById('cache-misses-value');

    let socket;
    let startTime;
    let processedCount;
    let totalUrls;

    urlForm.addEventListener('submit', handleFormSubmit);

    function handleFormSubmit(event) {
        event.preventDefault();
        const urls = urlInput.value.split('\n').filter(url => url.trim() !== "");
        const cacheStrategy = cacheStrategySelect.value;

        resetUI();
        closeExistingSocket();
        initializeWebSocket(urls, cacheStrategy);
    }

    function resetUI() {
        logMessages.innerHTML = '';
        dashboard.style.display = 'none';
        processedCount = 0;
        startTime = Date.now();
    }

    function closeExistingSocket() {
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.close();
        }
    }

    function initializeWebSocket(urls, cacheStrategy) {
        socket = new WebSocket('ws://localhost:6789');
        totalUrls = urls.length;

        socket.onopen = () => handleSocketOpen(urls, cacheStrategy);
        socket.onmessage = handleSocketMessage;
        socket.onerror = handleSocketError;
        socket.onclose = handleSocketClose;

        console.log('Form submitted. Starting WebSocket connection...');
    }

    function handleSocketOpen(urls, cacheStrategy) {
        const data = JSON.stringify({ urls, cacheStrategy });
        socket.send(data);
        console.log('WebSocket opened. Sent initial data.');
    }

    function handleSocketMessage(event) {
        let response;
        try {
            response = JSON.parse(event.data);
        } catch (e) {
            console.log("Received non-JSON message:", event.data);
            response = { data: event.data };
        }

        updateLog(response.data);
        updateProcessedCount();
        updateTimeTaken();

        if (processedCount === totalUrls) {
            handleAllUrlsProcessed(response.cacheStats);
        }
    }

    function updateLog(message) {
        const newMessage = document.createElement('li');
        newMessage.textContent = message;
        logMessages.appendChild(newMessage);
    }

    function updateProcessedCount() {
        processedCount += 1;
        console.log(`Message ${processedCount}/${totalUrls} received.`);
    }

    function updateTimeTaken() {
        const currentTime = Date.now();
        const timeTaken = (currentTime - startTime) / 1000;
        timeTakenElement.textContent = `Time Taken: ${timeTaken.toFixed(2)}s`;
        console.log(`Time taken: ${timeTaken.toFixed(2)}s`);
    }

    function handleAllUrlsProcessed(cacheStats) {
        if (cacheStats) {
            console.log(`Cache Hits: ${cacheStats.hits}`);
            console.log(`Cache Misses: ${cacheStats.misses}`);
            cacheHitsElement.textContent = cacheStats.hits;
            cacheMissesElement.textContent = cacheStats.misses;
            dashboard.style.display = 'block';
        }
        console.log(`All URLs processed. Final time: ${((Date.now() - startTime) / 1000).toFixed(2)}s`);
    }

    function handleSocketError(error) {
        console.error('WebSocket Error:', error);
    }

    function handleSocketClose(event) {
        console.log('WebSocket connection closed:', event);
    }
});