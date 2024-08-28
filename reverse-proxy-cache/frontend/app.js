document.addEventListener('DOMContentLoaded', () => {
    const urlForm = document.getElementById('url-form');
    const urlInput = document.getElementById('urls');
    const cacheStrategySelect = document.getElementById('cache-strategy');
    const numNodesSlider = document.getElementById('num-nodes');
    const numNodesValue = document.getElementById('num-nodes-value');
    const logMessages = document.getElementById('log-messages');
    const dashboard = document.getElementById('dashboard');
    const timeTakenElement = document.getElementById('time-taken');
    const cacheHitsElement = document.getElementById('cache-hits-value');
    const cacheMissesElement = document.getElementById('cache-misses-value');
    const nodeStatusElement = document.getElementById('node-status');
    const cacheSizeInput = document.getElementById('cache-size');
    const loadBalancerSelect = document.getElementById('load-balancer');


    let socket;
    let startTime;
    let processedCount;
    let totalUrls;

    numNodesSlider.addEventListener('input', () => {
        numNodesValue.textContent = numNodesSlider.value;
    });

    urlForm.addEventListener('submit', handleFormSubmit);

    function handleFormSubmit(event) {
        event.preventDefault();
        const urls = urlInput.value.split('\n').filter(url => url.trim() !== "");
        const cacheStrategy = cacheStrategySelect.value;
        const numNodes = parseInt(numNodesSlider.value);
        const loadBalancer = loadBalancerSelect.value;
        const cacheSize = parseInt(cacheSizeInput.value);

        resetUI();
        closeExistingSocket();
        initializeWebSocket(urls, cacheStrategy, loadBalancer, numNodes, cacheSize);
    }

    function initializeWebSocket(urls, cacheStrategy, loadBalancer,numNodes, cacheSize) {
        socket = new WebSocket('ws://localhost:6789');
        totalUrls = urls.length;

        socket.onopen = () => handleSocketOpen(urls, cacheStrategy,loadBalancer, numNodes, cacheSize);
        socket.onmessage = handleSocketMessage;
        socket.onerror = handleSocketError;
        socket.onclose = handleSocketClose;

        console.log('Form submitted. Starting WebSocket connection...');
    }

    function handleSocketOpen(urls, cacheStrategy, loadBalancer, numNodes, cacheSize) {
        const data = JSON.stringify({ urls, cacheStrategy, loadBalancer, numNodes, cacheSize });
        socket.send(data);
        console.log('WebSocket opened. Sent initial data:', data);
    }

    function resetUI() {
        logMessages.innerHTML = '';
        dashboard.style.display = 'none';
        nodeStatusElement.innerHTML = '';
        processedCount = 0;
        startTime = Date.now();
    }

    function closeExistingSocket() {
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.close();
        }
    }

    function initializeWebSocket(urls, cacheStrategy, loadBalancer,numNodes, cacheSize) {
        socket = new WebSocket('ws://localhost:6789');
        totalUrls = urls.length;

        socket.onopen = () => handleSocketOpen(urls, cacheStrategy, loadBalancer, numNodes, cacheSize);
        socket.onmessage = handleSocketMessage;
        socket.onerror = handleSocketError;
        socket.onclose = handleSocketClose;

        console.log('Form submitted. Starting WebSocket connection...');
    }

    function handleSocketOpen(urls, cacheStrategy, loadBalancer,numNodes, cacheSize) {
        const data = JSON.stringify({ urls, cacheStrategy, loadBalancer,numNodes, cacheSize });
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
        updateNodeStatus(response.nodeStatus);
        updateProcessedCount();
        updateTimeTaken();
        updateCacheStats(response.cacheStats);

        if (response.data.includes("Failed to fetch") || processedCount === totalUrls) {
            handleProcessingComplete();
        }
    }

    function updateLog(message) {
        const newMessage = document.createElement('li');
        newMessage.textContent = message;
        logMessages.appendChild(newMessage);

        if (message.includes("All nodes busy")) {
            const busyMessage = document.createElement('li');
            busyMessage.textContent = "Processing stopped: All nodes are busy";
            busyMessage.style.color = 'red';
            logMessages.appendChild(busyMessage);
        }
    }

    function handleProcessingComplete() {
        const completionMessage = document.createElement('li');
        completionMessage.textContent = `Processing complete. ${processedCount} out of ${totalUrls} URLs processed.`;
        completionMessage.style.fontWeight = 'bold';
        logMessages.appendChild(completionMessage);

        console.log(`All URLs processed or stopped due to busy nodes. Final time: ${((Date.now() - startTime) / 1000).toFixed(2)}s`);
    }

    function updateNodeStatus(nodeStatus) {
        if (nodeStatus) {
            nodeStatusElement.innerHTML = nodeStatus.join('<br>');
        }
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

    function updateCacheStats(cacheStats) {
        if (cacheStats) {
            console.log(`Cache Hits: ${cacheStats.hits}`);
            console.log(`Cache Misses: ${cacheStats.misses}`);
            cacheHitsElement.textContent = cacheStats.hits;
            cacheMissesElement.textContent = cacheStats.misses;
            dashboard.style.display = 'block';
        }
    }

    function handleSocketError(error) {
        console.error('WebSocket Error:', error);
    }

    function handleSocketClose(event) {
        console.log('WebSocket connection closed:', event);
    }
});