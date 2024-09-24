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
    const viewCachedContentBtn = document.getElementById('view-cached-content');
    const modal = document.getElementById('cached-content-modal');
    const closeBtn = modal ? modal.querySelector('.close') : null;
    const cachedContent = document.getElementById('cached-content');
    const proxyIPElement = document.getElementById('proxy-ip');
    const responseIPElement = document.getElementById('response-ip');
    let socket;
    let startTime;
    let processedCount = 0;
    let totalUrls = 0;
    let proxyIP = '';
    let lastResponseIP = '';

    if (numNodesSlider && numNodesValue) {
        numNodesSlider.addEventListener('input', () => {
            numNodesValue.textContent = numNodesSlider.value;
        });
    }

    if (urlForm) {
        urlForm.addEventListener('submit', handleFormSubmit);
    }

    function handleFormSubmit(event) {
        event.preventDefault();
        const urls = urlInput ? urlInput.value.split('\n').filter(url => url.trim() !== "") : [];
        const cacheStrategy = cacheStrategySelect ? cacheStrategySelect.value : 'LRU';
        const numNodes = numNodesSlider ? parseInt(numNodesSlider.value) : 1;
        const loadBalancer = loadBalancerSelect ? loadBalancerSelect.value : 'round_robin';
        const cacheSize = cacheSizeInput ? parseInt(cacheSizeInput.value) : 10;

        resetUI();
        closeExistingSocket();
        initializeWebSocket(urls, cacheStrategy, loadBalancer, numNodes, cacheSize);
    }

    function initializeWebSocket(urls, cacheStrategy, loadBalancer, numNodes, cacheSize) {
        socket = new WebSocket('ws://localhost:6789');
        totalUrls = urls.length;

        socket.onopen = () => handleSocketOpen(urls, cacheStrategy, loadBalancer, numNodes, cacheSize);
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

    function handleSocketMessage(event) {
        let response;
        try {
            response = JSON.parse(event.data);
        } catch (e) {
            console.log("Received non-JSON message:", event.data);
            response = { data: event.data };
        }

        if (response.proxyIP) {
            proxyIP = response.proxyIP;
            updateProxyIP();
        }

        if (response.responseIP) {
            lastResponseIP = response.responseIP;
            updateResponseIP();
        }

        if (response.data) {
            updateLog(response.data, response.url, response.responseIP);
            updateProcessedCount();
        }

        if (response.nodeStatus) {
            updateNodeStatus(response.nodeStatus);
        }

        if (response.cacheStats) {
            updateCacheStats(response.cacheStats);
        }

        updateTimeTaken();

        if (response.final) {
            handleProcessingComplete();
        }
    }

    function updateLog(message, url, responseIP) {
        if (logMessages) {
            const newMessage = document.createElement('p');
            newMessage.textContent = `${message} | Response IP: ${responseIP || 'N/A'}`;
            logMessages.appendChild(newMessage);
            logMessages.scrollTop = logMessages.scrollHeight;
        }
    }


    function handleProcessingComplete() {
        if (logMessages) {
            const completionMessage = document.createElement('p');
            completionMessage.textContent = `Processing complete. ${processedCount - 1} out of ${totalUrls} URLs processed.`;
            completionMessage.style.fontWeight = 'bold';
            logMessages.appendChild(completionMessage);
        }

        if (viewCachedContentBtn) {
            viewCachedContentBtn.style.display = 'block';
        }
    }

    function updateNodeStatus(nodeStatus) {
        if (nodeStatusElement && nodeStatus) {
            nodeStatusElement.value = nodeStatus.join('\n');
        }
    }

    function updateProcessedCount() {
        processedCount += 1;
        console.log(`Message ${processedCount}/${totalUrls} received.`);
    }

    function updateTimeTaken() {
        const currentTime = Date.now();
        const timeTaken = (currentTime - startTime) / 1000;
        if (timeTakenElement) {
            timeTakenElement.textContent = `Time Taken: ${timeTaken.toFixed(2)}s`;
        }
        console.log(`Time taken: ${timeTaken.toFixed(2)}s`);
    }

    function updateCacheStats(cacheStats) {
        if (cacheStats) {
            console.log(`Cache Hits: ${cacheStats.hits}`);
            console.log(`Cache Misses: ${cacheStats.misses}`);
            if (cacheHitsElement) {
                cacheHitsElement.textContent = cacheStats.hits;
            }
            if (cacheMissesElement) {
                cacheMissesElement.textContent = cacheStats.misses;
            }
            if (dashboard) {
                dashboard.style.display = 'block';
            }
        }
    }

    function updateProxyIP() {
        if (proxyIPElement) {
            proxyIPElement.textContent = `Proxy IP: ${proxyIP}`;
            proxyIPElement.style.display = 'block';
        }
    }

    function updateResponseIP() {
        if (responseIPElement) {
            responseIPElement.textContent = `Response IP: ${lastResponseIP}`;
            responseIPElement.style.display = 'block';
        }
    }

    function resetUI() {
        if (logMessages) {
            logMessages.innerHTML = '';
        }
        if (dashboard) {
            dashboard.style.display = 'none';
        }
        if (nodeStatusElement) {
            nodeStatusElement.value = '';
        }
        processedCount = 0;
        startTime = Date.now();
        if (viewCachedContentBtn) {
            viewCachedContentBtn.style.display = 'none';
        }
        if (proxyIPElement) {
            proxyIPElement.textContent = '';
        }
        if (responseIPElement) {
            responseIPElement.textContent = '';
        }
        if (cacheHitsElement) {
            cacheHitsElement.textContent = '0';
        }
        if (cacheMissesElement) {
            cacheMissesElement.textContent = '0';
        }
    }

    function closeExistingSocket() {
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.close();
        }
    }

    function handleSocketError(error) {
        console.error('WebSocket Error:', error);
    }

    function handleSocketClose(event) {
        console.log('WebSocket connection closed:', event);
    }

    if (viewCachedContentBtn) {
        viewCachedContentBtn.addEventListener('click', () => {
            fetchCachedContent();
            if (modal) {
                modal.style.display = 'flex';
            }
        });
    }

    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            if (modal) {
                modal.style.display = 'none';
            }
        });
    }

    window.addEventListener('click', (event) => {
        if (modal && event.target === modal) {
            modal.style.display = 'none';
        }
    });

    function fetchCachedContent() {
        fetch('http://localhost:5001/get_cached_content')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Error: ${response.status} - ${response.statusText}`);
                }
                return response.text();
            })
            .then(data => {
                if (cachedContent) {
                    cachedContent.textContent = data;
                }
            })
            .catch(error => {
                console.error('Error fetching cached content:', error);
                if (cachedContent) {
                    cachedContent.textContent = 'Error fetching cached content. Please try again.';
                }
            });
    }
});