document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const urlForm = document.getElementById('url-form');
    const urlInput = document.getElementById('urls');
    const cacheStrategySelect = document.getElementById('cache-strategy');
    const numNodesSlider = document.getElementById('num-nodes');
    const numNodesValue = document.getElementById('num-nodes-value');
    const logMessages = document.getElementById('log-messages');
    const timeTakenElement = document.getElementById('time-taken');
    const cacheHitsElement = document.getElementById('cache-hits-value');
    const cacheMissesElement = document.getElementById('cache-misses-value');
    const cacheSizeInput = document.getElementById('cache-size');
    const loadBalancerSelect = document.getElementById('load-balancer');
    const viewCachedContentBtn = document.getElementById('view-cached-content');
    const modal = document.getElementById('cached-content-modal');
    const closeBtn = modal.querySelector('.close');
    const cachedContent = document.getElementById('cached-content');
    const proxyIPElement = document.getElementById('proxy-ip');
    const packetsSentElement = document.getElementById('packets-sent');
    const packetsReceivedElement = document.getElementById('packets-received');
    const networkReportBody = document.getElementById('network-report-body');

    // State variables
    let socket;
    let startTime;
    let processedCount = 0;
    let totalUrls = 0;

    // Event Listeners
    urlForm.addEventListener('submit', handleFormSubmit);
    numNodesSlider.addEventListener('input', updateNumNodesValue);
    viewCachedContentBtn.addEventListener('click', showCachedContentModal);
    closeBtn.addEventListener('click', hideCachedContentModal);
    window.addEventListener('click', handleModalOutsideClick);

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

    function initializeWebSocket(urls, cacheStrategy, loadBalancer, numNodes, cacheSize) {
        socket = new WebSocket('ws://localhost:6789');
        totalUrls = urls.length;

        socket.onopen = () => {
            const data = JSON.stringify({ urls, cacheStrategy, loadBalancer, numNodes, cacheSize });
            socket.send(data);
            console.log('WebSocket opened. Sent initial data:', data);
        };
        socket.onmessage = handleSocketMessage;
        socket.onerror = error => console.error('WebSocket Error:', error);
        socket.onclose = event => console.log('WebSocket connection closed:', event);

        startTime = Date.now();
    }

    function handleSocketMessage(event) {
        let response;
        try {
            response = JSON.parse(event.data);
        } catch (e) {
            console.log("Received non-JSON message:", event.data);
            response = { data: event.data };
        }

        if (response.data) {
            updateLog(response.data);
            updateNetworkReport(response.url, response.responseIP, response.data);
            updateProcessedCount();
        }

        if (response.cacheStats) {
            updateCacheStats(response.cacheStats);
        }

        if (response.traceReport) {
            updateTraceReport(response.traceReport);
        }

        updateTimeTaken();

        if (response.final) {
            handleProcessingComplete();
        }
    }

    function updateLog(message) {
        const newMessage = document.createElement('p');
        newMessage.textContent = message;
        logMessages.appendChild(newMessage);
        logMessages.scrollTop = logMessages.scrollHeight;
    }

    function updateNetworkReport(url, responseIP, status) {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${url}</td>
            <td>${responseIP}</td>
            <td>${status}</td>
            <td>${new Date().toLocaleTimeString()}</td>
        `;
        networkReportBody.appendChild(row);
    }

    function updateProcessedCount() {
        processedCount += 1;
        console.log(`Message ${processedCount}/${totalUrls} received.`);
    }

    function updateTimeTaken() {
        const currentTime = Date.now();
        const timeTaken = (currentTime - startTime) / 1000;
        timeTakenElement.textContent = `Time Taken: ${timeTaken.toFixed(2)}s`;
    }

    function updateCacheStats(cacheStats) {
        cacheHitsElement.textContent = cacheStats.hits;
        cacheMissesElement.textContent = cacheStats.misses;
    }

    function updateTraceReport(traceReport) {
        packetsSentElement.textContent = traceReport.packetsSent;
        packetsReceivedElement.textContent = traceReport.packetsReceived;
        proxyIPElement.textContent = traceReport.proxyIP;
    }

    function handleProcessingComplete() {
        updateLog(`Processing complete. ${processedCount} out of ${totalUrls} URLs processed.`);
        viewCachedContentBtn.style.display = 'block';
    }

    function updateNumNodesValue() {
        numNodesValue.textContent = numNodesSlider.value;
    }

    function resetUI() {
        logMessages.innerHTML = '';
        networkReportBody.innerHTML = '';
        processedCount = 0;
        startTime = Date.now();
        timeTakenElement.textContent = 'Time Taken: 0s';
        cacheHitsElement.textContent = '0';
        cacheMissesElement.textContent = '0';
        packetsSentElement.textContent = '0';
        packetsReceivedElement.textContent = '0';
        proxyIPElement.textContent = '';
        viewCachedContentBtn.style.display = 'none';
    }

    function closeExistingSocket() {
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.close();
        }
    }


    function showCachedContentModal() {
        fetchCachedContent();
        modal.style.display = 'block';
    }

    function hideCachedContentModal() {
        modal.style.display = 'none';
    }

    function handleModalOutsideClick(event) {
        if (event.target === modal) {
            hideCachedContentModal();
        }
    }

    function fetchCachedContent() {
        fetch('http://localhost:5001/get_cached_content')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.text();
            })
            .then(data => {
                cachedContent.textContent = data;
            })
            .catch(error => {
                console.error('Error fetching cached content:', error);
                cachedContent.textContent = 'Error fetching cached content. Please try again.';
            });
    }
});