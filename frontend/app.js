class SignalBotApp {
    constructor() {
        this.backendUrl = 'https://your-render-app.onrender.com'; // Замінити на вашу URL
        this.wsUrl = this.backendUrl.replace('https', 'wss') + '/ws';
        this.socket = null;
        this.updateInterval = null;
        this.lastUpdate = null;
        
        this.initializeElements();
        this.setupEventListeners();
        this.connectWebSocket();
        this.startAutoUpdate();
    }
    
    initializeElements() {
        this.elements = {
            signalsList: document.getElementById('signals-list'),
            connectionStatus: document.getElementById('connection-status'),
            lastUpdate: document.getElementById('last-update'),
            totalSignals: document.getElementById('total-signals'),
            confidenceFilter: document.getElementById('confidence-filter'),
            confidenceValue: document.getElementById('confidence-value'),
            timeframeFilter: document.getElementById('timeframe-filter'),
            directionFilter: document.getElementById('direction-filter'),
            successRate: document.getElementById('success-rate'),
            totalGenerated: document.getElementById('total-generated'),
            nextUpdate: document.getElementById('next-update')
        };
    }
    
    setupEventListeners() {
        // Фільтр впевненості
        this.elements.confidenceFilter.addEventListener('input', (e) => {
            const value = e.target.value;
            this.elements.confidenceValue.textContent = `${value}%`;
            this.filterSignals();
        });
        
        // Фільтр таймфрейму
        this.elements.timeframeFilter.addEventListener('change', () => {
            this.filterSignals();
        });
        
        // Фільтр напрямку
        this.elements.directionFilter.addEventListener('change', () => {
            this.filterSignals();
        });
    }
    
    connectWebSocket() {
        try {
            this.socket = new WebSocket(this.wsUrl);
            
            this.socket.onopen = () => {
                console.log('WebSocket connected');
                this.updateConnectionStatus(true);
                this.socket.send('get_signals');
            };
            
            this.socket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                
                if (data.type === 'new_signal') {
                    this.addSignal(data.data);
                    this.playNotificationSound();
                } else if (data.type === 'signals') {
                    this.displaySignals(data.data);
                }
                
                this.updateLastUpdateTime();
            };
            
            this.socket.onclose = () => {
                console.log('WebSocket disconnected');
                this.updateConnectionStatus(false);
                // Спробувати перепідключитися через 5 секунд
                setTimeout(() => this.connectWebSocket(), 5000);
            };
            
            this.socket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateConnectionStatus(false);
            };
            
        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
            this.updateConnectionStatus(false);
        }
    }
    
    async fetchSignals() {
        try {
            const response = await fetch(`${this.backendUrl}/signals`);
            if (!response.ok) throw new Error('Network response was not ok');
            
            const data = await response.json();
            this.displaySignals(data.signals || []);
            this.updateLastUpdateTime();
            
        } catch (error) {
            console.error('Error fetching signals:', error);
            this.showError('Не вдалося завантажити сигнали');
        }
    }
    
    async fetchStatus() {
        try {
            const response = await fetch(`${this.backendUrl}/status`);
            if (!response.ok) throw new Error('Network response was not ok');
            
            const data = await response.json();
            this.updateStats(data);
            
        } catch (error) {
            console.error('Error fetching status:', error);
        }
    }
    
    displaySignals(signals) {
        if (!signals || signals.length === 0) {
            this.elements.signalsList.innerHTML = `
                <div class="no-signals">
                    <i class="fas fa-search"></i>
                    <p>Наразі сигналів немає. Очікуйте наступного оновлення.</p>
                </div>
            `;
            return;
        }
        
        this.elements.signalsList.innerHTML = '';
        
        // Спочатку відфільтруємо сигнали
        const filteredSignals = this.filterSignalList(signals);
        
        filteredSignals.forEach(signal => {
            const signalElement = this.createSignalElement(signal);
            this.elements.signalsList.appendChild(signalElement);
        });
        
        this.elements.totalSignals.querySelector('span').textContent = 
            `Сигналів сьогодні: ${filteredSignals.length}`;
    }
    
    filterSignalList(signals) {
        const minConfidence = parseInt(this.elements.confidenceFilter.value);
        const timeframeFilter = this.elements.timeframeFilter.value;
        const directionFilter = this.elements.directionFilter.value;
        
        return signals.filter(signal => {
            // Фільтр впевненості
            if (signal.confidence < minConfidence) return false;
            
            // Фільтр таймфрейму
            if (timeframeFilter !== 'all' && signal.timeframe !== parseInt(timeframeFilter)) {
                return false;
            }
            
            // Фільтр напрямку
            if (directionFilter !== 'all' && signal.direction !== directionFilter) {
                return false;
            }
            
            return true;
        });
    }
    
    filterSignals() {
        // Отримуємо всі сигнали і фільтруємо їх
        const signalElements = this.elements.signalsList.querySelectorAll('.signal-card');
        
        signalElements.forEach(element => {
            const confidence = parseInt(element.dataset.confidence);
            const timeframe = element.dataset.timeframe;
            const direction = element.dataset.direction;
            
            const minConfidence = parseInt(this.elements.confidenceFilter.value);
            const timeframeFilter = this.elements.timeframeFilter.value;
            const directionFilter = this.elements.directionFilter.value;
            
            let shouldShow = true;
            
            if (confidence < minConfidence) shouldShow = false;
            if (timeframeFilter !== 'all' && timeframe !== timeframeFilter) shouldShow = false;
            if (directionFilter !== 'all' && direction !== directionFilter) shouldShow = false;
            
            element.style.display = shouldShow ? 'block' : 'none';
        });
    }
    
    createSignalElement(signal) {
        const element = document.createElement('div');
        element.className = `signal-card ${signal.direction}`;
        element.dataset.confidence = signal.confidence;
        element.dataset.timeframe = signal.timeframe;
        element.dataset.direction = signal.direction;
        
        const confidencePercent = Math.round(signal.confidence);
        const confidenceColor = confidencePercent >= 85 ? '#2ed573' : 
                              confidencePercent >= 75 ? '#ffa502' : '#ff4757';
        
        const directionIcon = signal.direction === 'up' ? 
            '<i class="fas fa-arrow-up"></i>' : 
            '<i class="fas fa-arrow-down"></i>';
        
        const directionText = signal.direction === 'up' ? 'CALL (ВВЕРХ)' : 'PUT (ВНИЗ)';
        
        element.innerHTML = `
            <div class="signal-header">
                <div class="asset-name">${signal.asset_name || signal.asset}</div>
                <div class="timeframe">${signal.timeframe_text}</div>
            </div>
            
            <div class="direction ${signal.direction}">
                ${directionIcon} ${directionText}
            </div>
            
            <div class="confidence">
                <div class="confidence-text">
                    <span>Впевненість:</span>
                    <span style="color: ${confidenceColor}">${signal.confidence}%</span>
                </div>
                <div class="confidence-bar">
                    <div class="confidence-fill" style="width: ${confidencePercent}%"></div>
                </div>
            </div>
            
            <div class="signal-info">
                ${signal.reason ? `<div class="info-item">
                    <span><i class="fas fa-comment"></i> Причина:</span>
                    <span>${signal.reason}</span>
                </div>` : ''}
                
                ${signal.entry_price ? `<div class="info-item">
                    <span><i class="fas fa-dollar-sign"></i> Ціна входу:</span>
                    <span>${signal.entry_price}</span>
                </div>` : ''}
                
                ${signal.take_profit ? `<div class="info-item">
                    <span><i class="fas fa-trophy"></i> Тейк1-профіт:</span>
                    <span>${signal.take_profit}</span>
                </div>` : ''}
                
                ${signal.stop_loss ? `<div class="info-item">
                    <span><i class="fas fa-shield-alt"></i> Стоп-лосс:</span>
                    <span>${signal.stop_loss}</span>
                </div>` : ''}
            </div>
            
            <div class="signal-time">
                <i class="far fa-clock"></i> ${signal.human_time}
            </div>
        `;
        
        return element;
    }
    
    addSignal(signal) {
        const element = this.createSignalElement(signal);
        
        // Додати на початок списку
        if (this.elements.signalsList.firstChild) {
            this.elements.signalsList.insertBefore(element, this.elements.signalsList.firstChild);
        } else {
            this.elements.signalsList.appendChild(element);
        }
        
        // Обмежити кількість відображуваних сигналів
        const maxSignals = 20;
        const signalCards = this.elements.signalsList.querySelectorAll('.signal-card');
        if (signalCards.length > maxSignals) {
            signalCards[signalCards.length - 1].remove();
        }
        
        // Оновити статистику
        this.updateStats({ total_signals_generated: signalCards.length });
    }
    
    updateConnectionStatus(connected) {
        const statusDot = this.elements.connectionStatus.querySelector('.status-dot');
        const statusText = this.elements.connectionStatus.querySelector('span:last-child');
        
        if (connected) {
            statusDot.className = 'status-dot connected';
            statusText.textContent = 'Підключено';
        } else {
            statusDot.className = 'status-dot';
            statusText.textContent = 'Відключено';
        }
    }
    
    updateLastUpdateTime() {
        const now = new Date();
        const timeString = now.toLocaleTimeString('uk-UA', { 
            hour: '2-digit', 
            minute: '2-digit',
            second: '2-digit'
        });
        
        this.elements.lastUpdate.querySelector('span:last-child').textContent = 
            `Оновлення: ${timeString}`;
        
        this.lastUpdate = now;
    }
    
    updateStats(data) {
        if (data.total_signals_generated) {
            this.elements.totalGenerated.textContent = data.total_signals_generated;
        }
        
        if (data.success_rate) {
            this.elements.successRate.textContent = `${data.success_rate}%`;
        }
    }
    
    startAutoUpdate() {
        // Оновлювати статус кожні 30 секунд
        setInterval(() => this.fetchStatus(), 30000);
        
        // Оновлювати очікуваний час
        this.updateNextUpdateTime();
        setInterval(() => this.updateNextUpdateTime(), 1000);
    }
    
    updateNextUpdateTime() {
        if (!this.lastUpdate) return;
        
        const now = new Date();
        const nextUpdate = new Date(this.lastUpdate.getTime() + 300000); // +5 хвилин
        const diffMs = nextUpdate - now;
        
        if (diffMs > 0) {
            const minutes = Math.floor(diffMs / 60000);
            const seconds = Math.floor((diffMs % 60000) / 1000);
            this.elements.nextUpdate.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        } else {
            this.elements.nextUpdate.textContent = '0:00';
        }
    }
    
    playNotificationSound() {
        // Створити простий звук сповіщення
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.value = 800;
            oscillator.type = 'sine';
            
            gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.5);
        } catch (error) {
            console.log('Audio not supported');
        }
    }
    
    showError(message) {
        // Створити сповіщення про помилку
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.innerHTML = `
            <i class="fas fa-exclamation-triangle"></i>
            <span>${message}</span>
        `;
        
        errorDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #ff4757;
            color: white;
            padding: 15px 25px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
            z-index: 1000;
            animation: slideIn 0.3s ease-out;
        `;
        
        document.body.appendChild(errorDiv);
        
        // Видалити через 5 секунд
        setTimeout(() => {
            errorDiv.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => errorDiv.remove(), 300);
        }, 5000);
    }
}

// Запуск додатку при завантаженні сторінки
document.addEventListener('DOMContentLoaded', () => {
    window.signalBot = new SignalBotApp();
});
