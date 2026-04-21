class SeasonsBite {
    constructor() {
        this.currentSeason = null;
        this.currentPackage = null;
        this.selectedPackageType = 'basic';
        this.init();
    }

    async init() {
        await this.loadSeasonInfo();
        this.bindEvents();
    }

    async loadSeasonInfo() {
        try {
            const response = await fetch('/api/season');
            const data = await response.json();
            this.currentSeason = data.season;
            this.updateSeasonDisplay(data);
        } catch (error) {
            console.error('Failed to load season info:', error);
        }
    }

    updateSeasonDisplay(data) {
        const seasonIconEl = document.getElementById('season-icon');
        const seasonNameEl = document.getElementById('season-name');
        const seasonDescEl = document.getElementById('season-desc');

        const icons = {
            spring: '🌱',
            summer: '☀️',
            autumn: '🍂',
            winter: '❄️'
        };

        seasonIconEl.textContent = icons[data.season] || '🌱';
        seasonNameEl.textContent = data.season_name;
        seasonDescEl.textContent = data.season_desc;
    }

    bindEvents() {
        document.querySelectorAll('.package-option').forEach(option => {
            option.addEventListener('click', (e) => {
                this.selectPackageType(option);
            });
        });

        const drawBtn = document.getElementById('draw-btn');
        if (drawBtn) {
            drawBtn.addEventListener('click', () => this.drawPackage());
        }

        const redrawAllBtn = document.getElementById('redraw-all-btn');
        if (redrawAllBtn) {
            redrawAllBtn.addEventListener('click', () => this.redrawAll());
        }

        const generateTextBtn = document.getElementById('generate-text-btn');
        if (generateTextBtn) {
            generateTextBtn.addEventListener('click', () => this.generateText());
        }

        const generateScreenshotBtn = document.getElementById('generate-screenshot-btn');
        if (generateScreenshotBtn) {
            generateScreenshotBtn.addEventListener('click', () => this.generateScreenshot());
        }

        document.getElementById('close-text-modal')?.addEventListener('click', () => {
            document.getElementById('text-modal').style.display = 'none';
        });

        document.getElementById('close-screenshot-modal')?.addEventListener('click', () => {
            document.getElementById('screenshot-modal').style.display = 'none';
        });

        document.getElementById('copy-text-btn')?.addEventListener('click', () => {
            this.copyToClipboard();
        });

        document.getElementById('download-screenshot-btn')?.addEventListener('click', () => {
            this.downloadScreenshot();
        });

        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.style.display = 'none';
                }
            });
        });
    }

    selectPackageType(option) {
        document.querySelectorAll('.package-option').forEach(opt => {
            opt.classList.remove('active');
            const radio = opt.querySelector('input[type="radio"]');
            if (radio) radio.checked = false;
        });

        option.classList.add('active');
        const radio = option.querySelector('input[type="radio"]');
        if (radio) radio.checked = true;

        this.selectedPackageType = option.dataset.package;
    }

    async drawPackage() {
        const drawBtn = document.getElementById('draw-btn');
        const originalText = drawBtn.innerHTML;
        drawBtn.innerHTML = '<span class="loading"></span> 抽取中...';
        drawBtn.disabled = true;

        try {
            const response = await fetch(
                `/api/draw?package_type=${this.selectedPackageType}`,
                { method: 'POST' }
            );
            const result = await response.json();

            if (result.success) {
                this.currentPackage = result.data;
                this.showResult();
            } else {
                alert('抽取失败，请重试');
            }
        } catch (error) {
            console.error('Draw failed:', error);
            alert('抽取失败，请检查网络连接');
        } finally {
            drawBtn.innerHTML = originalText;
            drawBtn.disabled = false;
        }
    }

    showResult() {
        document.getElementById('draw-section').style.display = 'none';
        document.getElementById('result-section').style.display = 'block';

        const resultSubtitle = document.getElementById('result-season');
        resultSubtitle.textContent = `${this.currentPackage.season_name} · ${this.currentPackage.season_desc}`;

        this.renderCards();
    }

    renderCards() {
        const container = document.getElementById('cards-container');
        container.innerHTML = '';

        const typeIcons = {
            meats: '🥩',
            vegetables: '🥗',
            soups: '🍲',
            staples: '🍚'
        };

        const typeLabels = {
            meats: '荤菜',
            vegetables: '素菜',
            soups: '汤品',
            staples: '主食'
        };

        const allDishes = [];
        
        this.currentPackage.meats.forEach((dish, index) => {
            allDishes.push({ ...dish, type: 'meats', index });
        });
        
        this.currentPackage.vegetables.forEach((dish, index) => {
            allDishes.push({ ...dish, type: 'vegetables', index });
        });
        
        this.currentPackage.soups.forEach((dish, index) => {
            allDishes.push({ ...dish, type: 'soups', index });
        });
        
        if (this.currentPackage.staples && this.currentPackage.staples.length > 0) {
            this.currentPackage.staples.forEach((dish, index) => {
                allDishes.push({ ...dish, type: 'staples', index });
            });
        }

        allDishes.forEach((dish, cardIndex) => {
            const cardHtml = this.createCardHtml(dish, cardIndex);
            container.insertAdjacentHTML('beforeend', cardHtml);
        });

        container.querySelectorAll('.dish-card-wrapper').forEach(wrapper => {
            this.bindCardEvents(wrapper);
        });
    }

    bindCardEvents(wrapper) {
        wrapper.addEventListener('click', (e) => {
            if (e.target.tagName === 'BUTTON' || e.target.closest('button')) {
                return;
            }
            const card = wrapper.querySelector('.dish-card');
            card.classList.toggle('flipped');
        });

        const redrawBtn = wrapper.querySelector('.btn-redraw');
        if (redrawBtn) {
            redrawBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                const dishType = wrapper.dataset.type;
                const dishIndex = parseInt(wrapper.dataset.index);
                this.redrawSingle(dishType, dishIndex, wrapper);
            });
        }

        const lockBtn = wrapper.querySelector('.btn-lock');
        if (lockBtn) {
            lockBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                const dishType = wrapper.dataset.type;
                const dishIndex = parseInt(wrapper.dataset.index);
                this.toggleLock(dishType, dishIndex, lockBtn, wrapper);
            });
        }
    }

    createCardHtml(dish, cardIndex) {
        const typeIcons = {
            meats: '🥩',
            vegetables: '🥗',
            soups: '🍲',
            staples: '🍚'
        };

        const typeLabels = {
            meats: '荤菜',
            vegetables: '素菜',
            soups: '汤品',
            staples: '主食'
        };

        const imageUrl = `https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=${encodeURIComponent(dish.image_hint)}&image_size=square`;

        const lockedClass = dish.is_locked ? 'locked' : '';
        const lockedIndicator = dish.is_locked ? 
            '<div class="locked-indicator"><span>🔒</span> 已锁定</div>' : '';

        return `
            <div class="dish-card-wrapper dish-type-${dish.type}" 
                 data-type="${dish.type}" 
                 data-index="${dish.index}"
                 data-id="${dish.id}">
                <div class="dish-card">
                    <div class="dish-card-face dish-card-front">
                        <div class="card-front-icon">${typeIcons[dish.type]}</div>
                        <div class="card-front-label">${typeLabels[dish.type]}</div>
                        <div class="card-front-hint">点击翻转查看菜品</div>
                    </div>
                    <div class="dish-card-face dish-card-back">
                        ${lockedIndicator}
                        <div class="dish-card-image">
                            <img src="${imageUrl}" alt="${dish.name}" 
                                 onerror="this.style.display='none'; this.parentElement.innerHTML='${typeIcons[dish.type]}';">
                        </div>
                        <div class="dish-card-content">
                            <div class="dish-card-type">${typeLabels[dish.type]}</div>
                            <h4 class="dish-card-name">${dish.name}</h4>
                            <p class="dish-card-desc">${dish.desc}</p>
                            <div class="dish-card-actions">
                                <button class="btn-redraw" ${dish.is_locked ? 'disabled' : ''}>
                                    <span>🎲</span> 换一道
                                </button>
                                <button class="btn-lock ${lockedClass}">
                                    <span>${dish.is_locked ? '🔓' : '🔒'}</span> 
                                    ${dish.is_locked ? '解锁' : '锁定'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    async redrawSingle(dishType, dishIndex, wrapper) {
        const redrawBtn = wrapper.querySelector('.btn-redraw');
        const originalText = redrawBtn.innerHTML;
        redrawBtn.innerHTML = '<span class="loading"></span>';
        redrawBtn.disabled = true;

        const currentIds = this.currentPackage[dishType].map(d => d.id);
        const excludeIds = [wrapper.dataset.id];

        try {
            const response = await fetch(
                `/api/redraw?dish_type=${dishType}&season=${this.currentSeason}&exclude_ids=${excludeIds.join(',')}&current_ids=${currentIds.join(',')}`,
                { method: 'POST' }
            );
            const result = await response.json();

            if (result.success) {
                const newDish = {
                    ...result.data,
                    type: dishType,
                    index: dishIndex
                };
                
                this.currentPackage[dishType][dishIndex] = result.data;
                
                const newCardHtml = this.createCardHtml(newDish, 0);
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = newCardHtml;
                const newWrapper = tempDiv.firstElementChild;
                
                wrapper.parentNode.replaceChild(newWrapper, wrapper);
                
                const newCard = newWrapper.querySelector('.dish-card');
                if (newCard) {
                    newCard.classList.add('flipped');
                }
                
                this.bindCardEvents(newWrapper);
            }
        } catch (error) {
            console.error('Redraw failed:', error);
            alert('重抽失败，请重试');
        } finally {
            const currentWrapper = document.querySelector(`[data-type="${dishType}"][data-index="${dishIndex}"]`);
            if (currentWrapper) {
                const currentBtn = currentWrapper.querySelector('.btn-redraw');
                if (currentBtn) {
                    currentBtn.innerHTML = '<span>🎲</span> 换一道';
                }
            }
        }
    }

    toggleLock(dishType, dishIndex, btn, wrapper) {
        const dish = this.currentPackage[dishType][dishIndex];
        dish.is_locked = !dish.is_locked;

        if (dish.is_locked) {
            btn.classList.add('locked');
            btn.innerHTML = '<span>🔓</span> 解锁';
            wrapper.querySelector('.btn-redraw').disabled = true;
            
            const cardBack = wrapper.querySelector('.dish-card-back');
            if (!cardBack.querySelector('.locked-indicator')) {
                const indicator = document.createElement('div');
                indicator.className = 'locked-indicator';
                indicator.innerHTML = '<span>🔒</span> 已锁定';
                cardBack.insertBefore(indicator, cardBack.firstChild);
            }
        } else {
            btn.classList.remove('locked');
            btn.innerHTML = '<span>🔒</span> 锁定';
            wrapper.querySelector('.btn-redraw').disabled = false;
            
            const indicator = wrapper.querySelector('.locked-indicator');
            if (indicator) indicator.remove();
        }
    }

    redrawAll() {
        document.getElementById('result-section').style.display = 'none';
        document.getElementById('draw-section').style.display = 'block';
    }

    async generateText() {
        try {
            const response = await fetch('/api/generate-text', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    package: this.currentPackage
                })
            });
            const result = await response.json();

            if (result.success) {
                document.getElementById('menu-text').textContent = result.data.text;
                document.getElementById('text-modal').style.display = 'flex';
            }
        } catch (error) {
            console.error('Generate text failed:', error);
            alert('生成文本失败，请重试');
        }
    }

    async copyToClipboard() {
        const text = document.getElementById('menu-text').textContent;
        const copyBtn = document.getElementById('copy-text-btn');
        const originalText = copyBtn.innerHTML;

        try {
            await navigator.clipboard.writeText(text);
            copyBtn.innerHTML = '<span>✅</span> 已复制';
            copyBtn.classList.add('copy-success');
            
            setTimeout(() => {
                copyBtn.innerHTML = originalText;
                copyBtn.classList.remove('copy-success');
            }, 2000);
        } catch (error) {
            console.error('Copy failed:', error);
            alert('复制失败，请手动复制');
        }
    }

    async generateScreenshot() {
        const preview = document.getElementById('screenshot-preview');
        const downloadBtn = document.getElementById('download-screenshot-btn');
        
        preview.innerHTML = '<p>正在生成截图，请稍候...</p>';
        downloadBtn.style.display = 'none';
        
        document.getElementById('screenshot-modal').style.display = 'flex';

        try {
            const canvas = await this.createScreenshotCanvas();
            const dataUrl = canvas.toDataURL('image/png');
            
            this.screenshotDataUrl = dataUrl;
            preview.innerHTML = `<img src="${dataUrl}" alt="菜单截图">`;
            downloadBtn.style.display = 'flex';
        } catch (error) {
            console.error('Generate screenshot failed:', error);
            preview.innerHTML = '<p>生成截图失败，您可以使用系统截图功能保存</p>';
        }
    }

    async createScreenshotCanvas() {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        const padding = 40;
        const cardWidth = 280;
        const cardHeight = 350;
        const cardGap = 20;
        
        const dishes = this.getAllDishes();
        const cardsPerRow = Math.min(dishes.length, 2);
        const rows = Math.ceil(dishes.length / cardsPerRow);
        
        const contentWidth = cardsPerRow * cardWidth + (cardsPerRow - 1) * cardGap;
        const contentHeight = rows * cardHeight + (rows - 1) * cardGap;
        
        canvas.width = contentWidth + padding * 2;
        canvas.height = contentHeight + padding * 2 + 120;
        
        const gradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
        gradient.addColorStop(0, '#ffecd2');
        gradient.addColorStop(1, '#fcb69f');
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        ctx.fillStyle = '#5a3e36';
        ctx.font = 'bold 24px "Noto Serif SC", serif';
        ctx.textAlign = 'center';
        ctx.fillText('时节食匣', canvas.width / 2, padding + 30);
        
        ctx.fillStyle = '#7a5c52';
        ctx.font = '14px "Noto Sans SC", sans-serif';
        ctx.fillText(
            `${this.currentPackage.season_name} · ${this.currentPackage.season_desc}`,
            canvas.width / 2,
            padding + 55
        );

        const typeLabels = {
            meats: '荤菜',
            vegetables: '素菜',
            soups: '汤品',
            staples: '主食'
        };

        for (let i = 0; i < dishes.length; i++) {
            const dish = dishes[i];
            const col = i % cardsPerRow;
            const row = Math.floor(i / cardsPerRow);
            
            const x = padding + col * (cardWidth + cardGap);
            const y = padding + 80 + row * (cardHeight + cardGap);
            
            ctx.fillStyle = 'white';
            this.roundRect(ctx, x, y, cardWidth, cardHeight, 16);
            ctx.fill();
            
            ctx.strokeStyle = 'rgba(232, 168, 124, 0.5)';
            ctx.lineWidth = 2;
            this.roundRect(ctx, x, y, cardWidth, cardHeight, 16);
            ctx.stroke();
            
            ctx.fillStyle = '#f5f7fa';
            this.roundRect(ctx, x + 20, y + 20, cardWidth - 40, 100, 8);
            ctx.fill();
            
            ctx.fillStyle = '#888';
            ctx.font = '36px sans-serif';
            ctx.textAlign = 'center';
            const typeEmojis = { meats: '🥩', vegetables: '🥗', soups: '🍲', staples: '🍚' };
            ctx.fillText(typeEmojis[dish.type] || '🍽️', x + cardWidth / 2, y + 85);
            
            ctx.fillStyle = '#e8a87c';
            ctx.font = 'bold 12px "Noto Sans SC", sans-serif';
            ctx.textAlign = 'left';
            ctx.fillText(typeLabels[dish.type], x + 20, y + 140);
            
            ctx.fillStyle = '#333';
            ctx.font = 'bold 18px "Noto Serif SC", serif';
            ctx.fillText(this.truncateText(dish.name, 10), x + 20, y + 165);
            
            ctx.fillStyle = '#666';
            ctx.font = '13px "Noto Sans SC", sans-serif';
            const descLines = this.wrapText(dish.desc, cardWidth - 40, ctx);
            let descY = y + 190;
            for (let j = 0; j < Math.min(descLines.length, 3); j++) {
                ctx.fillText(descLines[j], x + 20, descY);
                descY += 20;
            }
        }

        ctx.fillStyle = '#7a5c52';
        ctx.font = '12px "Noto Sans SC", sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(
            '用浪漫与仪式感治愈你的吃饭选择困难症',
            canvas.width / 2,
            canvas.height - padding - 10
        );

        return canvas;
    }

    roundRect(ctx, x, y, width, height, radius) {
        ctx.beginPath();
        ctx.moveTo(x + radius, y);
        ctx.lineTo(x + width - radius, y);
        ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
        ctx.lineTo(x + width, y + height - radius);
        ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
        ctx.lineTo(x + radius, y + height);
        ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
        ctx.lineTo(x, y + radius);
        ctx.quadraticCurveTo(x, y, x + radius, y);
        ctx.closePath();
    }

    wrapText(text, maxWidth, ctx) {
        const words = text.split('');
        const lines = [];
        let currentLine = '';

        for (let i = 0; i < words.length; i++) {
            const testLine = currentLine + words[i];
            const metrics = ctx.measureText(testLine);
            
            if (metrics.width > maxWidth && currentLine !== '') {
                lines.push(currentLine);
                currentLine = words[i];
            } else {
                currentLine = testLine;
            }
        }
        
        if (currentLine) {
            lines.push(currentLine);
        }
        
        return lines;
    }

    truncateText(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength - 1) + '…';
    }

    getAllDishes() {
        const dishes = [];
        
        this.currentPackage.meats.forEach((dish, index) => {
            dishes.push({ ...dish, type: 'meats', index });
        });
        
        this.currentPackage.vegetables.forEach((dish, index) => {
            dishes.push({ ...dish, type: 'vegetables', index });
        });
        
        this.currentPackage.soups.forEach((dish, index) => {
            dishes.push({ ...dish, type: 'soups', index });
        });
        
        if (this.currentPackage.staples && this.currentPackage.staples.length > 0) {
            this.currentPackage.staples.forEach((dish, index) => {
                dishes.push({ ...dish, type: 'staples', index });
            });
        }
        
        return dishes;
    }

    downloadScreenshot() {
        if (!this.screenshotDataUrl) return;

        const link = document.createElement('a');
        link.download = `时节食匣_${this.currentPackage.season_name}_${Date.now()}.png`;
        link.href = this.screenshotDataUrl;
        link.click();
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new SeasonsBite();
});
