class SeasonsBite {
    constructor() {
        this.currentSeason = null;
        this.currentPackage = null;
        this.selectedPackageType = 'basic';
        this.currentTab = 'draw';
        this.currentLocation = null;
        this.currentSolarTerm = null;
        this.dietaryRecords = [];
        this.currentRecordItems = [];
        this.healthScore = null;
        this.solarTermsData = null;
        this.selectedShareTheme = 'default';
        this.shareCardDataUrl = null;
        this.init();
    }

    async init() {
        await this.loadSeasonInfo();
        await this.loadSolarTermsData();
        this.setDefaultDate();
        this.bindEvents();
        this.initCurrentTermDisplay();
    }

    async loadSolarTermsData() {
        try {
            const response = await fetch('/api/solar-terms');
            const result = await response.json();
            if (result.success && result.data) {
                const data = result.data;
                this.solarTermsData = {
                    solar_terms: {},
                    seasonal_guidelines: data.seasonal_guidelines || {},
                    regional_adjustment: data.location_adjustment || {}
                };
                if (data.all_terms) {
                    data.all_terms.forEach(term => {
                        this.solarTermsData.solar_terms[term.key] = term;
                    });
                }
            }
        } catch (error) {
            console.error('Failed to load solar terms data:', error);
        }
    }

    setDefaultDate() {
        const today = new Date().toISOString().split('T')[0];
        const dateInputs = document.querySelectorAll('input[type="date"]');
        dateInputs.forEach(input => {
            if (!input.value) {
                input.value = today;
            }
        });
    }

    parseChineseDate(dateStr) {
        if (!dateStr) return { month: 0, day: 0 };
        const match = dateStr.match(/(\d+)月(\d+)日/);
        if (match) {
            return { month: parseInt(match[1]), day: parseInt(match[2]) };
        }
        return { month: 0, day: 0 };
    }

    initCurrentTermDisplay() {
        const now = new Date();
        const month = now.getMonth() + 1;
        const day = now.getDate();
        
        let termKey = null;
        if (this.solarTermsData && this.solarTermsData.solar_terms) {
            for (const [key, term] of Object.entries(this.solarTermsData.solar_terms)) {
                let startMonth, startDay, endMonth, endDay;
                
                if (Array.isArray(term.date_range) && term.date_range.length >= 2) {
                    const startDate = this.parseChineseDate(term.date_range[0]);
                    const endDate = this.parseChineseDate(term.date_range[1]);
                    startMonth = startDate.month;
                    startDay = startDate.day;
                    endMonth = endDate.month;
                    endDay = endDate.day;
                } else if (term.date_range && term.date_range.start) {
                    const [sm, sd] = term.date_range.start.split('-').map(Number);
                    const [em, ed] = term.date_range.end.split('-').map(Number);
                    startMonth = sm;
                    startDay = sd;
                    endMonth = em;
                    endDay = ed;
                } else {
                    continue;
                }
                
                if (startMonth > 0 && endMonth > 0) {
                    if ((month > startMonth || (month === startMonth && day >= startDay)) &&
                        (month < endMonth || (month === endMonth && day <= endDay))) {
                        termKey = key;
                        break;
                    }
                }
            }
        }

        if (termKey && this.solarTermsData && this.solarTermsData.solar_terms[termKey]) {
            const term = this.solarTermsData.solar_terms[termKey];
            const currentTermName = document.getElementById('current-term-name');
            const currentTermIcon = document.getElementById('current-term-icon');
            const currentTermDate = document.getElementById('current-term-date');
            const currentTermDesc = document.getElementById('current-term-desc');

            if (currentTermName) currentTermName.textContent = term.name;
            if (currentTermIcon) currentTermIcon.textContent = term.icon;
            
            let dateDisplay = '';
            if (Array.isArray(term.date_range) && term.date_range.length >= 2) {
                dateDisplay = `${term.date_range[0]} ~ ${term.date_range[1]}`;
            } else if (term.date_range && term.date_range.start) {
                dateDisplay = `${term.date_range.start} ~ ${term.date_range.end}`;
            }
            if (currentTermDate) currentTermDate.textContent = dateDisplay;
            
            if (currentTermDesc) currentTermDesc.textContent = term.description;
        }
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

        this.bindNavigationEvents();
        this.bindLocationEvents();
        this.bindRecordsEvents();
        this.bindHealthEvents();
        this.bindCultureEvents();
        this.bindShareCardEvents();
        this.bindDrawModeEvents();
        this.bindGamesEvents();
        this.bindSettingsEvents();

        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.style.display = 'none';
                }
            });
        });
    }

    bindNavigationEvents() {
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                this.switchTab(tab.dataset.tab);
            });
        });
    }

    bindDrawModeEvents() {
        document.querySelectorAll('.mode-option').forEach(option => {
            option.addEventListener('click', () => {
                document.querySelectorAll('.mode-option').forEach(o => o.classList.remove('selected'));
                option.classList.add('selected');
            });
        });
    }

    bindGamesEvents() {
        document.querySelectorAll('.play-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const gameType = btn.dataset.game;
                if (gameType === 'chef') {
                    this.startChefChallenge();
                } else if (gameType === 'match') {
                    this.startMatchGame();
                } else if (gameType === 'badges') {
                    this.showBadgesCollection();
                }
            });
        });

        const backToGameMenuBtn = document.getElementById('back-to-game-menu-btn');
        if (backToGameMenuBtn) {
            backToGameMenuBtn.addEventListener('click', () => this.showGameMenu());
        }

        const submitChefChallengeBtn = document.getElementById('submit-chef-challenge-btn');
        if (submitChefChallengeBtn) {
            submitChefChallengeBtn.addEventListener('click', () => this.submitChefChallenge());
        }

        const matchGameBackBtn = document.getElementById('match-game-back-btn');
        if (matchGameBackBtn) {
            matchGameBackBtn.addEventListener('click', () => this.showGameMenu());
        }

        const badgesBackBtn = document.getElementById('badges-back-btn');
        if (badgesBackBtn) {
            badgesBackBtn.addEventListener('click', () => this.showGameMenu());
        }
    }

    bindSettingsEvents() {
        const saveSettingsBtn = document.getElementById('save-settings-btn');
        if (saveSettingsBtn) {
            saveSettingsBtn.addEventListener('click', () => this.savePreferences());
        }

        const resetSettingsBtn = document.getElementById('reset-settings-btn');
        if (resetSettingsBtn) {
            resetSettingsBtn.addEventListener('click', () => this.resetPreferences());
        }

        document.querySelectorAll('.taste-option').forEach(option => {
            option.addEventListener('click', () => {
                document.querySelectorAll('.taste-option').forEach(o => o.classList.remove('selected'));
                option.classList.add('selected');
            });
        });

        document.querySelectorAll('.constitution-option').forEach(option => {
            option.addEventListener('click', () => {
                document.querySelectorAll('.constitution-option').forEach(o => o.classList.remove('selected'));
                option.classList.add('selected');
            });
        });
    }

    switchTab(tabName) {
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.tab === tabName);
        });

        const tabContents = {
            'draw': 'draw-section-tab',
            'location': 'location-section',
            'records': 'records-section',
            'health': 'health-section',
            'culture': 'culture-section',
            'games': 'games-section',
            'settings': 'settings-section'
        };

        Object.entries(tabContents).forEach(([tab, sectionId]) => {
            const section = document.getElementById(sectionId);
            if (section) {
                section.style.display = tab === tabName ? 'block' : 'none';
            }
        });

        this.currentTab = tabName;

        if (tabName === 'health') {
            this.loadHealthScore();
        } else if (tabName === 'culture') {
            this.renderSolarTermsTimeline();
        } else if (tabName === 'records') {
            this.loadRecords();
        } else if (tabName === 'games') {
            this.loadBadges();
        } else if (tabName === 'settings') {
            this.loadPreferences();
        }
    }

    bindLocationEvents() {
        const getLocationBtn = document.getElementById('get-location-btn');
        if (getLocationBtn) {
            getLocationBtn.addEventListener('click', () => this.getCurrentLocation());
        }

        const manualLocationBtn = document.getElementById('manual-location-btn');
        if (manualLocationBtn) {
            manualLocationBtn.addEventListener('click', () => {
                document.getElementById('manual-location-modal').style.display = 'flex';
            });
        }

        const closeManualModal = document.getElementById('close-manual-modal');
        if (closeManualModal) {
            closeManualModal.addEventListener('click', () => {
                document.getElementById('manual-location-modal').style.display = 'none';
            });
        }

        document.querySelectorAll('.region-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.selectRegion(btn.dataset.region);
                document.getElementById('manual-location-modal').style.display = 'none';
            });
        });
    }

    async getCurrentLocation() {
        const statusIcon = document.querySelector('#location-status .status-icon');
        const statusText = document.querySelector('#location-status .status-text h3');
        const statusDesc = document.querySelector('#location-status .status-text p');

        statusIcon.textContent = '⏳';
        statusText.textContent = '正在获取位置...';
        statusDesc.textContent = '请等待浏览器获取您的位置信息';

        if ('geolocation' in navigator) {
            navigator.geolocation.getCurrentPosition(
                async (position) => {
                    const latitude = position.coords.latitude;
                    const longitude = position.coords.longitude;
                    await this.submitLocation(latitude, longitude);
                },
                (error) => {
                    statusIcon.textContent = '❌';
                    statusText.textContent = '获取位置失败';
                    statusDesc.textContent = error.message || '无法获取位置信息，请尝试手动选择地区';
                },
                { enableHighAccuracy: true, timeout: 10000 }
            );
        } else {
            statusIcon.textContent = '❌';
            statusText.textContent = '浏览器不支持定位';
            statusDesc.textContent = '请使用手动选择地区功能';
        }
    }

    async submitLocation(latitude, longitude) {
        try {
            const response = await fetch('/api/location', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    latitude: latitude,
                    longitude: longitude
                })
            });

            const result = await response.json();

            if (result.success) {
                this.currentLocation = result.data;
                this.displayLocationResult(result.data);
            } else {
                this.showLocationError(result.message || '位置处理失败');
            }
        } catch (error) {
            console.error('Location submission failed:', error);
            this.showLocationError('网络错误，请重试');
        }
    }

    async selectRegion(region) {
        const regionCoords = {
            north: { lat: 39.9042, lng: 116.4074 },
            south: { lat: 23.1291, lng: 113.2644 },
            east: { lat: 31.2304, lng: 121.4737 },
            west: { lat: 30.5728, lng: 104.0668 }
        };

        const coords = regionCoords[region];
        if (coords) {
            await this.submitLocation(coords.lat, coords.lng);
        }
    }

    displayLocationResult(data) {
        const statusIcon = document.querySelector('#location-status .status-icon');
        const statusText = document.querySelector('#location-status .status-text h3');
        const statusDesc = document.querySelector('#location-status .status-text p');

        statusIcon.textContent = '✅';
        statusText.textContent = '位置获取成功';
        statusDesc.textContent = '已根据您的位置匹配当地节气';

        document.getElementById('location-result').style.display = 'block';
        document.getElementById('location-region').textContent = data.region_name || '未知地区';
        document.getElementById('location-term').textContent = data.solar_term || '未知节气';
        document.getElementById('location-season').textContent = data.season_name || '未知季节';
        document.getElementById('location-coords').textContent = `${data.latitude?.toFixed(4) || '-'}, ${data.longitude?.toFixed(4) || '-'}`;

        if (data.solar_term_key) {
            this.loadSolarTermDetail(data.solar_term_key);
        }
    }

    showLocationError(message) {
        const statusIcon = document.querySelector('#location-status .status-icon');
        const statusText = document.querySelector('#location-status .status-text h3');
        const statusDesc = document.querySelector('#location-status .status-text p');

        statusIcon.textContent = '❌';
        statusText.textContent = '处理失败';
        statusDesc.textContent = message;
    }

    async loadSolarTermDetail(termKey) {
        try {
            const response = await fetch(`/api/solar-term/${termKey}`);
            const result = await response.json();

            if (result.success) {
                this.displaySolarTermDetail(result.data);
            }
        } catch (error) {
            console.error('Failed to load solar term detail:', error);
        }
    }

    displaySolarTermDetail(term) {
        const termDetail = document.getElementById('term-detail');
        termDetail.style.display = 'block';

        document.getElementById('term-icon').textContent = term.icon || '🌱';
        document.getElementById('term-name').textContent = term.name || '节气';
        document.getElementById('term-description').textContent = term.description || '';

        const customsList = document.getElementById('term-customs');
        customsList.innerHTML = '';
        if (term.customs && term.customs.length > 0) {
            term.customs.forEach(custom => {
                const li = document.createElement('li');
                li.textContent = custom;
                customsList.appendChild(li);
            });
        }

        const recommendedList = document.getElementById('term-recommended');
        recommendedList.innerHTML = '';
        if (term.dietary_advice && term.dietary_advice.recommended) {
            term.dietary_advice.recommended.forEach(food => {
                const li = document.createElement('li');
                li.textContent = food;
                recommendedList.appendChild(li);
            });
        }

        const avoidList = document.getElementById('term-avoid');
        avoidList.innerHTML = '';
        if (term.dietary_advice && term.dietary_advice.avoid) {
            term.dietary_advice.avoid.forEach(food => {
                const li = document.createElement('li');
                li.textContent = food;
                avoidList.appendChild(li);
            });
        }

        const healthTipsList = document.getElementById('term-health-tips');
        healthTipsList.innerHTML = '';
        if (term.health_tips && term.health_tips.length > 0) {
            term.health_tips.forEach(tip => {
                const li = document.createElement('li');
                li.textContent = tip;
                healthTipsList.appendChild(li);
            });
        }

        const culturalStory = document.getElementById('term-cultural-story');
        if (culturalStory) {
            culturalStory.textContent = term.cultural_story || '';
        }
    }

    bindRecordsEvents() {
        const addFoodBtn = document.getElementById('add-food-btn');
        if (addFoodBtn) {
            addFoodBtn.addEventListener('click', () => this.addFoodItem());
        }

        const recordForm = document.getElementById('dietary-record-form');
        if (recordForm) {
            recordForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveDietaryRecord();
            });
        }

        const applyFilterBtn = document.getElementById('apply-filter-btn');
        if (applyFilterBtn) {
            applyFilterBtn.addEventListener('click', () => this.filterRecords());
        }
    }

    addFoodItem() {
        const foodName = document.getElementById('record-food-name').value.trim();
        const foodCategory = document.getElementById('record-food-category').value;
        const quantity = parseFloat(document.getElementById('record-quantity').value) || 1;
        const unit = document.getElementById('record-unit').value;
        const mealType = document.getElementById('record-meal-type').value;
        const notes = document.getElementById('record-notes').value.trim();

        if (!foodName) {
            alert('请输入食物名称');
            return;
        }

        const item = {
            id: Date.now(),
            food_name: foodName,
            food_category: foodCategory,
            quantity: quantity,
            unit: unit,
            meal_type: mealType,
            notes: notes
        };

        this.currentRecordItems.push(item);
        this.renderCurrentItems();

        document.getElementById('record-food-name').value = '';
        document.getElementById('record-quantity').value = '';
        document.getElementById('record-notes').value = '';
    }

    renderCurrentItems() {
        const section = document.getElementById('current-items-section');
        const list = document.getElementById('current-items-list');

        if (this.currentRecordItems.length === 0) {
            section.style.display = 'none';
            return;
        }

        section.style.display = 'block';
        list.innerHTML = '';

        const categoryIcons = {
            meat: '🥩',
            vegetable: '🥗',
            soup: '🍲',
            staple: '🍚',
            fruit: '🍎',
            other: '🍽️'
        };

        const mealTypeLabels = {
            breakfast: '早餐',
            lunch: '午餐',
            dinner: '晚餐',
            snack: '加餐'
        };

        this.currentRecordItems.forEach(item => {
            const div = document.createElement('div');
            div.className = 'food-item';
            div.innerHTML = `
                <div class="food-item-icon">${categoryIcons[item.food_category] || '🍽️'}</div>
                <div class="food-item-info">
                    <div class="food-item-name">${item.food_name}</div>
                    <div class="food-item-detail">${mealTypeLabels[item.meal_type]} · ${item.quantity}${item.unit}</div>
                    ${item.notes ? `<div class="food-item-notes">${item.notes}</div>` : ''}
                </div>
                <button class="food-item-remove" data-id="${item.id}">✕</button>
            `;

            const removeBtn = div.querySelector('.food-item-remove');
            removeBtn.addEventListener('click', () => {
                this.currentRecordItems = this.currentRecordItems.filter(i => i.id !== item.id);
                this.renderCurrentItems();
            });

            list.appendChild(div);
        });
    }

    async saveDietaryRecord() {
        if (this.currentRecordItems.length === 0) {
            alert('请至少添加一项食物');
            return;
        }

        const recordDate = document.getElementById('record-date').value;

        try {
            const response = await fetch('/api/records', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    date: recordDate,
                    items: this.currentRecordItems
                })
            });

            const result = await response.json();

            if (result.success) {
                alert('记录保存成功！');
                this.currentRecordItems = [];
                this.renderCurrentItems();
                this.loadRecords();
            } else {
                alert('保存失败：' + (result.message || '未知错误'));
            }
        } catch (error) {
            console.error('Save record failed:', error);
            alert('网络错误，请重试');
        }
    }

    async loadRecords() {
        try {
            const response = await fetch('/api/records');
            const result = await response.json();

            if (result.success && result.data) {
                this.dietaryRecords = result.data.records || [];
                this.renderRecordsList();
            }
        } catch (error) {
            console.error('Load records failed:', error);
        }
    }

    renderRecordsList() {
        const list = document.getElementById('records-list');

        if (this.dietaryRecords.length === 0) {
            list.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">📝</div>
                    <p>还没有饮食记录</p>
                    <p class="empty-hint">添加您的第一条饮食记录吧！</p>
                </div>
            `;
            return;
        }

        list.innerHTML = '';

        const categoryIcons = {
            meat: '🥩',
            vegetable: '🥗',
            soup: '🍲',
            staple: '🍚',
            fruit: '🍎',
            other: '🍽️'
        };

        const mealTypeLabels = {
            breakfast: '早餐',
            lunch: '午餐',
            dinner: '晚餐',
            snack: '加餐'
        };

        this.dietaryRecords.forEach(record => {
            const recordDiv = document.createElement('div');
            recordDiv.className = 'record-item';

            const dateObj = new Date(record.date);
            const dateStr = `${dateObj.getFullYear()}-${(dateObj.getMonth() + 1).toString().padStart(2, '0')}-${dateObj.getDate().toString().padStart(2, '0')}`;

            let itemsHtml = '';
            record.items.forEach(item => {
                itemsHtml += `
                    <div class="record-food-item">
                        <span class="record-food-icon">${categoryIcons[item.food_category] || '🍽️'}</span>
                        <span class="record-food-name">${item.food_name}</span>
                        <span class="record-food-detail">${mealTypeLabels[item.meal_type]} · ${item.quantity}${item.unit}</span>
                    </div>
                `;
            });

            recordDiv.innerHTML = `
                <div class="record-header">
                    <span class="record-date">📅 ${dateStr}</span>
                    <span class="record-count">${record.items.length} 项食物</span>
                </div>
                <div class="record-items">
                    ${itemsHtml}
                </div>
            `;

            list.appendChild(recordDiv);
        });
    }

    filterRecords() {
        const startDate = document.getElementById('filter-start-date').value;
        const endDate = document.getElementById('filter-end-date').value;
        this.renderRecordsList();
    }

    bindHealthEvents() {
        const refreshScoreBtn = document.getElementById('refresh-score-btn');
        if (refreshScoreBtn) {
            refreshScoreBtn.addEventListener('click', () => this.loadHealthScore());
        }

        const generateScoreCardBtn = document.getElementById('generate-score-card-btn');
        if (generateScoreCardBtn) {
            generateScoreCardBtn.addEventListener('click', () => this.generateScoreCard());
        }
    }

    async loadHealthScore() {
        try {
            const response = await fetch('/api/health-score');
            const result = await response.json();

            if (result.success && result.data) {
                const data = result.data;
                const seasonNames = {
                    spring: '春季',
                    summer: '夏季',
                    autumn: '秋季',
                    winter: '冬季'
                };
                
                this.healthScore = {
                    total_score: data.overall_score || 0,
                    level: data.score_level_name || '未知',
                    grade: data.score_level || 'fair',
                    season_name: seasonNames[data.current_season] || '-',
                    dimensions: {},
                    strengths: data.strengths || [],
                    improvements: data.improvements || [],
                    advice: data.advice || []
                };

                if (data.dimensions) {
                    const dimMap = {
                        seasonal_health: 'seasonal',
                        nutritional_balance: 'nutrition',
                        tcm_harmony: 'tcm',
                        dietary_diversity: 'diversity'
                    };
                    Object.entries(data.dimensions).forEach(([key, dim]) => {
                        const newKey = dimMap[key] || key;
                        this.healthScore.dimensions[newKey] = {
                            score: dim.score || 0
                        };
                    });
                }

                this.displayHealthScore();
            }
        } catch (error) {
            console.error('Load health score failed:', error);
        }
    }

    displayHealthScore() {
        if (!this.healthScore) return;

        const scoreValue = document.getElementById('score-value');
        const scoreLevel = document.getElementById('score-level');
        const scoreGrade = document.getElementById('score-grade');
        const scoreSeason = document.getElementById('score-season');

        scoreValue.textContent = this.healthScore.total_score;
        scoreLevel.textContent = this.healthScore.level;
        scoreGrade.textContent = this.healthScore.grade;
        scoreSeason.textContent = this.healthScore.season_name || '-';

        const scoreCircle = document.getElementById('score-circle');
        const score = this.healthScore.total_score;
        let color;
        if (score >= 80) {
            color = '#4caf50';
        } else if (score >= 60) {
            color = '#ff9800';
        } else {
            color = '#f44336';
        }
        scoreCircle.style.borderColor = color;

        const dimensionsList = document.getElementById('score-dimensions-list');
        dimensionsList.innerHTML = '';

        if (this.healthScore.dimensions) {
            Object.entries(this.healthScore.dimensions).forEach(([key, dim]) => {
                const item = document.createElement('div');
                item.className = 'dimension-item';
                
                const icons = {
                    seasonal: '🌱',
                    nutrition: '🥗',
                    tcm: '🧘',
                    diversity: '🌈'
                };

                const labels = {
                    seasonal: '时令健康度',
                    nutrition: '营养均衡度',
                    tcm: '中医调和度',
                    diversity: '饮食多样性'
                };

                item.innerHTML = `
                    <div class="dimension-header">
                        <span class="dimension-icon">${icons[key] || '📊'}</span>
                        <span class="dimension-name">${labels[key] || key}</span>
                        <span class="dimension-score">${dim.score}分</span>
                    </div>
                    <div class="dimension-bar">
                        <div class="dimension-bar-fill" style="width: ${dim.score}%;"></div>
                    </div>
                `;
                dimensionsList.appendChild(item);
            });
        }

        const strengthsList = document.getElementById('score-strengths');
        strengthsList.innerHTML = '';
        if (this.healthScore.strengths && this.healthScore.strengths.length > 0) {
            this.healthScore.strengths.forEach(s => {
                const li = document.createElement('li');
                li.className = 'advice-item';
                li.textContent = s;
                strengthsList.appendChild(li);
            });
        } else {
            strengthsList.innerHTML = '<li class="advice-item">暂无数据</li>';
        }

        const improvementsList = document.getElementById('score-improvements');
        improvementsList.innerHTML = '';
        if (this.healthScore.improvements && this.healthScore.improvements.length > 0) {
            this.healthScore.improvements.forEach(i => {
                const li = document.createElement('li');
                li.className = 'advice-item';
                li.textContent = i;
                improvementsList.appendChild(li);
            });
        } else {
            improvementsList.innerHTML = '<li class="advice-item">暂无数据</li>';
        }

        const adviceList = document.getElementById('score-advice');
        adviceList.innerHTML = '';
        if (this.healthScore.advice && this.healthScore.advice.length > 0) {
            this.healthScore.advice.forEach(a => {
                const li = document.createElement('li');
                li.className = 'recommendation-item';
                li.textContent = a;
                adviceList.appendChild(li);
            });
        }
    }

    generateScoreCard() {
        alert('评分卡片生成功能开发中...');
    }

    bindCultureEvents() {
        document.querySelectorAll('.season-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.filterSolarTermsBySeason(btn.dataset.season);
            });
        });

        document.querySelectorAll('.guideline-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                this.switchGuidelineTab(tab.dataset.season);
            });
        });

        document.querySelectorAll('.regional-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                this.switchRegionalTab(tab.dataset.region);
            });
        });

        const closeTermModal = document.getElementById('close-term-modal');
        if (closeTermModal) {
            closeTermModal.addEventListener('click', () => {
                document.getElementById('term-detail-modal').style.display = 'none';
            });
        }

        const generateTermCardBtn = document.getElementById('generate-term-card-btn');
        if (generateTermCardBtn) {
            generateTermCardBtn.addEventListener('click', () => {
                this.generateTermShareCard();
            });
        }
    }

    renderSolarTermsTimeline(filterSeason = 'all') {
        const timeline = document.getElementById('terms-timeline');
        if (!timeline || !this.solarTermsData || !this.solarTermsData.solar_terms) return;

        timeline.innerHTML = '';

        const seasonIcons = {
            spring: '🌱',
            summer: '☀️',
            autumn: '🍂',
            winter: '❄️'
        };

        const seasonNames = {
            spring: '春季',
            summer: '夏季',
            autumn: '秋季',
            winter: '冬季'
        };

        const seasonOrder = ['spring', 'summer', 'autumn', 'winter'];
        const seasonsToShow = filterSeason === 'all' ? seasonOrder : [filterSeason];

        seasonsToShow.forEach(season => {
            const seasonTerms = Object.entries(this.solarTermsData.solar_terms)
                .filter(([key, term]) => term.season === season);

            if (seasonTerms.length === 0) return;

            const seasonDiv = document.createElement('div');
            seasonDiv.className = 'timeline-season';
            seasonDiv.innerHTML = `
                <div class="timeline-season-header">
                    <span class="timeline-season-icon">${seasonIcons[season]}</span>
                    <span class="timeline-season-name">${seasonNames[season]}</span>
                </div>
            `;

            const termsContainer = document.createElement('div');
            termsContainer.className = 'timeline-terms';

            seasonTerms.forEach(([key, term]) => {
                const termDiv = document.createElement('div');
                termDiv.className = 'timeline-term';
                termDiv.innerHTML = `
                    <div class="timeline-term-icon">${term.icon}</div>
                    <div class="timeline-term-info">
                        <div class="timeline-term-name">${term.name}</div>
                        <div class="timeline-term-date">${term.date_range.start} ~ ${term.date_range.end}</div>
                    </div>
                `;

                termDiv.addEventListener('click', () => {
                    this.showTermDetailModal(key);
                });

                termsContainer.appendChild(termDiv);
            });

            seasonDiv.appendChild(termsContainer);
            timeline.appendChild(seasonDiv);
        });
    }

    filterSolarTermsBySeason(season) {
        document.querySelectorAll('.season-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.season === season);
        });
        this.renderSolarTermsTimeline(season);
    }

    switchGuidelineTab(season) {
        document.querySelectorAll('.guideline-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.season === season);
        });

        if (this.solarTermsData && this.solarTermsData.seasonal_guidelines) {
            const guideline = this.solarTermsData.seasonal_guidelines[season];
            if (guideline) {
                const content = document.getElementById('guidelines-content');
                const seasonNames = {
                    spring: '春季',
                    summer: '夏季',
                    autumn: '秋季',
                    winter: '冬季'
                };

                content.innerHTML = `
                    <div class="guideline-panel active">
                        <h4>${seasonNames[season]}养生</h4>
                        <p class="guideline-desc">${guideline.principle || ''}</p>
                        <div class="guideline-details">
                            <div class="guideline-item">
                                <h5>饮食原则</h5>
                                <p>${guideline.dietary_principle || ''}</p>
                            </div>
                            <div class="guideline-item">
                                <h5>推荐食物</h5>
                                <p>${(guideline.recommended || []).join('、')}</p>
                            </div>
                            <div class="guideline-item">
                                <h5>避免食物</h5>
                                <p>${(guideline.avoid || []).join('、')}</p>
                            </div>
                        </div>
                    </div>
                `;
            }
        }
    }

    switchRegionalTab(region) {
        document.querySelectorAll('.regional-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.region === region);
        });

        if (this.solarTermsData && this.solarTermsData.regional_adjustment) {
            const adjustment = this.solarTermsData.regional_adjustment[region];
            if (adjustment) {
                const content = document.getElementById('regional-content');
                const regionNames = {
                    north: '北方地区',
                    south: '南方地区',
                    east: '华东地区',
                    west: '西南地区'
                };

                let adjustmentsHtml = '';
                if (adjustment.adjustments) {
                    Object.entries(adjustment.adjustments).forEach(([season, desc]) => {
                        const seasonNames = {
                            spring: '春季',
                            summer: '夏季',
                            autumn: '秋季',
                            winter: '冬季'
                        };
                        adjustmentsHtml += `
                            <div class="adjustment-item">
                                <h5>${seasonNames[season] || season}</h5>
                                <p>${desc}</p>
                            </div>
                        `;
                    });
                }

                content.innerHTML = `
                    <div class="regional-panel active">
                        <p class="regional-desc">${adjustment.description || ''}</p>
                        <div class="regional-adjustments">
                            ${adjustmentsHtml}
                        </div>
                    </div>
                `;
            }
        }
    }

    async showTermDetailModal(termKey) {
        try {
            const response = await fetch(`/api/solar-term/${termKey}`);
            const result = await response.json();

            if (result.success) {
                this.displayTermDetailModal(result.data);
            }
        } catch (error) {
            console.error('Failed to load term detail:', error);
        }
    }

    displayTermDetailModal(term) {
        const modal = document.getElementById('term-detail-modal');
        modal.style.display = 'flex';

        document.getElementById('modal-term-name').textContent = term.name || '节气详情';
        document.getElementById('modal-term-icon').textContent = term.icon || '🌱';
        document.getElementById('modal-term-english').textContent = term.english_name || '';
        
        const seasonNames = {
            spring: '春季',
            summer: '夏季',
            autumn: '秋季',
            winter: '冬季'
        };
        document.getElementById('modal-term-season').textContent = seasonNames[term.season] || '';
        document.getElementById('modal-term-date-range').textContent = 
            `${term.date_range?.start || '-'} ~ ${term.date_range?.end || '-'}`;
        document.getElementById('modal-term-description').textContent = term.description || '';

        const customsList = document.getElementById('modal-term-customs');
        customsList.innerHTML = '';
        if (term.customs && term.customs.length > 0) {
            term.customs.forEach(custom => {
                const li = document.createElement('li');
                li.className = 'custom-item';
                li.innerHTML = `
                    <span class="custom-icon">🎊</span>
                    <span class="custom-text">${custom}</span>
                `;
                customsList.appendChild(li);
            });
        }

        const recommendedList = document.getElementById('modal-term-recommended');
        recommendedList.innerHTML = '';
        if (term.dietary_advice && term.dietary_advice.recommended) {
            term.dietary_advice.recommended.forEach(food => {
                const li = document.createElement('li');
                li.className = 'food-item';
                li.innerHTML = `<span>✅</span> ${food}`;
                recommendedList.appendChild(li);
            });
        }

        const avoidList = document.getElementById('modal-term-avoid');
        avoidList.innerHTML = '';
        if (term.dietary_advice && term.dietary_advice.avoid) {
            term.dietary_advice.avoid.forEach(food => {
                const li = document.createElement('li');
                li.className = 'food-item';
                li.innerHTML = `<span>⚠️</span> ${food}`;
                avoidList.appendChild(li);
            });
        }

        const healthTipsList = document.getElementById('modal-term-health-tips');
        healthTipsList.innerHTML = '';
        if (term.health_tips && term.health_tips.length > 0) {
            term.health_tips.forEach(tip => {
                const li = document.createElement('li');
                li.className = 'tip-item';
                li.innerHTML = `<span>💡</span> ${tip}`;
                healthTipsList.appendChild(li);
            });
        }

        const culturalStory = document.getElementById('modal-term-cultural-story');
        if (culturalStory) {
            culturalStory.textContent = term.cultural_story || '';
        }
    }

    generateTermShareCard() {
        alert('节气卡片生成功能开发中...');
    }

    bindShareCardEvents() {
        const generateShareCardBtn = document.getElementById('generate-share-card-btn');
        if (generateShareCardBtn) {
            generateShareCardBtn.addEventListener('click', () => {
                this.openShareCardModal();
            });
        }

        const closeShareCardModal = document.getElementById('close-share-card-modal');
        if (closeShareCardModal) {
            closeShareCardModal.addEventListener('click', () => {
                document.getElementById('share-card-modal').style.display = 'none';
            });
        }

        document.querySelectorAll('.theme-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.selectShareTheme(btn.dataset.theme);
            });
        });

        const generateFinalBtn = document.getElementById('generate-share-card-final-btn');
        if (generateFinalBtn) {
            generateFinalBtn.addEventListener('click', () => {
                this.generateShareCard();
            });
        }

        const downloadShareCardBtn = document.getElementById('download-share-card-btn');
        if (downloadShareCardBtn) {
            downloadShareCardBtn.addEventListener('click', () => {
                this.downloadShareCard();
            });
        }
    }

    openShareCardModal() {
        if (!this.currentPackage) {
            alert('请先抽取食匣再生成分享卡片');
            return;
        }
        document.getElementById('share-card-modal').style.display = 'flex';
    }

    selectShareTheme(theme) {
        document.querySelectorAll('.theme-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.theme === theme);
        });
        this.selectedShareTheme = theme;
    }

    async generateShareCard() {
        if (!this.currentPackage) return;

        const generateBtn = document.getElementById('generate-share-card-final-btn');
        const originalText = generateBtn.innerHTML;
        generateBtn.innerHTML = '<span class="loading"></span> 生成中...';
        generateBtn.disabled = true;

        try {
            this.shareCardDataUrl = await this.createShareCardWithCanvas();
            this.renderShareCardPreview();
            document.getElementById('download-share-card-btn').style.display = 'flex';
        } catch (error) {
            console.error('Generate share card failed:', error);
            alert('生成失败：' + error.message);
        } finally {
            generateBtn.innerHTML = originalText;
            generateBtn.disabled = false;
        }
    }

    createShareCardWithCanvas() {
        return new Promise((resolve, reject) => {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            
            canvas.width = 800;
            canvas.height = 1200;

            const themes = {
                default: {
                    bgGradient: ['#fdfbfb', '#f5f0e8'],
                    primaryColor: '#e8a87c',
                    secondaryColor: '#c38d9e',
                    textColor: '#333333',
                    accentText: '#e8a87c'
                },
                spring: {
                    bgGradient: ['#f1f8e9', '#e8f5e9'],
                    primaryColor: '#81c784',
                    secondaryColor: '#a5d6a7',
                    textColor: '#1b5e20',
                    accentText: '#4caf50'
                },
                summer: {
                    bgGradient: ['#fff3e0', '#ffecb3'],
                    primaryColor: '#ffb74d',
                    secondaryColor: '#ffcc80',
                    textColor: '#e65100',
                    accentText: '#ff9800'
                },
                autumn: {
                    bgGradient: ['#fff3e0', '#fbe9e7'],
                    primaryColor: '#ffab91',
                    secondaryColor: '#ffccbc',
                    textColor: '#bf360c',
                    accentText: '#ff5722'
                },
                winter: {
                    bgGradient: ['#e3f2fd', '#e1f5fe'],
                    primaryColor: '#64b5f6',
                    secondaryColor: '#90caf9',
                    textColor: '#0d47a1',
                    accentText: '#2196f3'
                }
            };

            const theme = themes[this.selectedShareTheme] || themes.default;

            const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
            gradient.addColorStop(0, theme.bgGradient[0]);
            gradient.addColorStop(1, theme.bgGradient[1]);
            ctx.fillStyle = gradient;
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            ctx.fillStyle = theme.primaryColor;
            ctx.globalAlpha = 0.1;
            this.drawDecorativeCircles(ctx, canvas.width, canvas.height);
            ctx.globalAlpha = 1;

            ctx.fillStyle = theme.primaryColor;
            ctx.fillRect(0, 0, canvas.width, 150);

            ctx.fillStyle = '#ffffff';
            ctx.font = 'bold 48px "Noto Serif SC", serif';
            ctx.textAlign = 'center';
            ctx.fillText('时节食匣', canvas.width / 2, 95);

            ctx.font = '28px "Noto Serif SC", serif';
            ctx.globalAlpha = 0.9;
            ctx.fillText('发现时令美食的美好', canvas.width / 2, 135);
            ctx.globalAlpha = 1;

            const pkg = this.currentPackage || {};
            let yOffset = 180;

            ctx.fillStyle = '#ffffff';
            this.drawRoundedRect(ctx, 40, yOffset, canvas.width - 80, 100, 20, true, false);
            yOffset += 25;

            const seasonIcons = { spring: '🌸', summer: '☀️', autumn: '🍂', winter: '❄️' };
            const seasonNames = { spring: '春季', summer: '夏季', autumn: '秋季', winter: '冬季' };
            
            const pkgSeason = pkg.season || 'spring';
            
            ctx.font = '32px sans-serif';
            ctx.fillStyle = theme.accentText;
            ctx.textAlign = 'center';
            ctx.fillText(seasonIcons[pkgSeason] || '🍽️', canvas.width / 2, yOffset + 35);

            ctx.font = 'bold 26px "Noto Serif SC", serif';
            ctx.fillStyle = theme.textColor;
            ctx.fillText(`${seasonNames[pkgSeason] || pkgSeason}限定`, canvas.width / 2, yOffset + 70);

            yOffset += 130;

            ctx.fillStyle = '#ffffff';
            this.drawRoundedRect(ctx, 40, yOffset, canvas.width - 80, 700, 20, true, false);

            yOffset += 40;

            ctx.font = 'bold 32px "Noto Serif SC", serif';
            ctx.fillStyle = theme.accentText;
            ctx.textAlign = 'center';
            const dishName = typeof pkg.dish_name === 'string' ? pkg.dish_name : '时令美食';
            ctx.fillText(`「${dishName}」`, canvas.width / 2, yOffset);

            yOffset += 50;

            ctx.font = '24px sans-serif';
            ctx.fillStyle = theme.textColor;
            ctx.textAlign = 'left';
            const description = typeof pkg.description === 'string' ? pkg.description : '时令美味';
            this.wrapText(ctx, description, 60, yOffset, canvas.width - 120, 35);

            yOffset += 100;

            ctx.font = 'bold 22px "Noto Serif SC", serif';
            ctx.fillStyle = theme.accentText;
            ctx.fillText('🥬 主要食材', 60, yOffset);

            yOffset += 40;
            const ingredients = Array.isArray(pkg.ingredients) ? pkg.ingredients : [];
            if (ingredients.length > 0) {
                ctx.font = '20px sans-serif';
                ctx.fillStyle = '#555555';
                this.wrapText(ctx, ingredients.join('、'), 60, yOffset, canvas.width - 120, 30);
            }

            yOffset += 80;

            ctx.font = 'bold 22px "Noto Serif SC", serif';
            ctx.fillStyle = theme.accentText;
            ctx.fillText('📖 烹饪步骤', 60, yOffset);

            yOffset += 40;
            const steps = Array.isArray(pkg.steps) ? pkg.steps : [];
            if (steps.length > 0) {
                ctx.font = '18px sans-serif';
                ctx.fillStyle = '#555555';
                steps.slice(0, 3).forEach((step, index) => {
                    const stepText = `${index + 1}. ${String(step || '')}`;
                    this.wrapText(ctx, stepText, 60, yOffset, canvas.width - 120, 28);
                    yOffset += 60;
                });
                if (steps.length > 3) {
                    ctx.fillStyle = '#999999';
                    ctx.fillText(`... 还有 ${steps.length - 3} 步`, 60, yOffset);
                }
            }

            yOffset = canvas.height - 120;

            ctx.fillStyle = theme.primaryColor;
            ctx.fillRect(0, yOffset, canvas.width, 120);

            ctx.fillStyle = '#ffffff';
            ctx.font = '24px "Noto Serif SC", serif';
            ctx.textAlign = 'center';
            ctx.fillText('扫码开启舌尖上的时令之旅', canvas.width / 2, yOffset + 50);

            ctx.font = '18px sans-serif';
            ctx.globalAlpha = 0.8;
            ctx.fillText('SeasonsBite · 发现四季美食', canvas.width / 2, yOffset + 85);
            ctx.globalAlpha = 1;

            this.drawQRCodePlaceholder(ctx, canvas.width - 150, yOffset + 15, 90);

            const dataUrl = canvas.toDataURL('image/png');
            resolve(dataUrl);
        });
    }

    drawDecorativeCircles(ctx, width, height) {
        const circles = [
            { x: width - 100, y: 200, r: 80 },
            { x: 100, y: height - 200, r: 120 },
            { x: width - 150, y: height / 2, r: 60 },
            { x: 50, y: 400, r: 40 }
        ];

        circles.forEach(circle => {
            ctx.beginPath();
            ctx.arc(circle.x, circle.y, circle.r, 0, Math.PI * 2);
            ctx.fill();
        });
    }

    drawRoundedRect(ctx, x, y, width, height, radius, fill, stroke) {
        ctx.beginPath();
        ctx.moveTo(x + radius, y);
        ctx.lineTo(x + width - radius, y);
        ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
        ctx.lineTo(x + width, y + height - radius);
        ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
        ctx.lineTo(x + radius, y + height);
        ctx.quadraticCurveTo(x, y + height, x, y + radius);
        ctx.lineTo(x, y + radius);
        ctx.quadraticCurveTo(x, y, x + radius, y);
        ctx.closePath();
        if (fill) ctx.fill();
        if (stroke) ctx.stroke();
    }

    wrapText(ctx, text, x, y, maxWidth, lineHeight, maxLines) {
        let safeText = '';
        if (typeof text === 'string') {
            safeText = text;
        } else if (text !== null && text !== undefined) {
            try {
                safeText = String(text);
            } catch (e) {
                safeText = '';
            }
        }
        
        if (!safeText || typeof safeText !== 'string') return;
        if (typeof safeText.split !== 'function') return;

        const words = safeText.split('');
        let line = '';
        let currentY = y;
        let lineCount = 1;

        for (let n = 0; n < words.length; n++) {
            const testLine = line + words[n];
            const metrics = ctx.measureText(testLine);
            const testWidth = metrics.width;

            if (testWidth > maxWidth && n > 0) {
                if (maxLines && lineCount >= maxLines) {
                    line = line.trimEnd() + '…';
                    break;
                }
                ctx.fillText(line, x, currentY);
                line = words[n];
                currentY += lineHeight;
                lineCount++;
            } else {
                line = testLine;
            }
        }
        ctx.fillText(line, x, currentY);
    }

    drawQRCodePlaceholder(ctx, x, y, size) {
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 2;
        this.drawRoundedRect(ctx, x, y, size, size, 8, false, true);

        ctx.fillStyle = '#ffffff';
        ctx.globalAlpha = 0.6;
        
        const patterns = [
            [0, 0], [0, 1], [1, 0], [1, 1],
            [size - 20, 0], [size - 10, 0], [size - 20, 10], [size - 10, 10],
            [0, size - 20], [0, size - 10], [10, size - 20], [10, size - 10]
        ];

        patterns.forEach(p => {
            ctx.fillRect(x + p[0], y + p[1], 10, 10);
        });

        ctx.globalAlpha = 1;
    }

    renderShareCardPreview() {
        const preview = document.getElementById('share-card-preview');
        if (preview && this.shareCardDataUrl) {
            preview.innerHTML = `<img src="${this.shareCardDataUrl}" alt="分享卡片">`;
        }
    }

    downloadShareCard() {
        if (!this.shareCardDataUrl) return;

        const link = document.createElement('a');
        link.download = `时节食匣分享卡_${Date.now()}.png`;
        link.href = this.shareCardDataUrl;
        link.click();
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

        const selectedMode = document.querySelector('.mode-option.selected');
        const drawMode = selectedMode ? selectedMode.dataset.mode : 'personalized';

        try {
            const response = await fetch(
                `/api/draw?package_type=${this.selectedPackageType}&draw_mode=${drawMode}`,
                { method: 'POST' }
            );
            const result = await response.json();

            if (result.success) {
                this.currentPackage = result.data;
                this.currentDrawReason = result.reason;
                this.currentDrawMode = drawMode;
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

        const reasonCard = document.getElementById('reason-card');
        if (this.currentDrawReason && reasonCard) {
            reasonCard.style.display = 'block';
            document.getElementById('reason-text').textContent = this.currentDrawReason.text;
            document.getElementById('reason-description').textContent = this.currentDrawReason.description || '';
            const modeIndicator = document.getElementById('mode-indicator');
            if (modeIndicator) {
                modeIndicator.textContent = this.currentDrawMode === 'personalized' ? 'AI智能推荐' : '纯随机';
            }
        } else if (reasonCard) {
            reasonCard.style.display = 'none';
        }

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

        const selectedMode = document.querySelector('.mode-option.selected');
        const drawMode = selectedMode ? selectedMode.dataset.mode : (this.currentDrawMode || 'personalized');

        try {
            const response = await fetch(
                `/api/redraw?dish_type=${dishType}&season=${this.currentSeason}&exclude_ids=${excludeIds.join(',')}&current_ids=${currentIds.join(',')}&draw_mode=${drawMode}`,
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
            this.wrapText(ctx, dish.desc, x + 20, y + 190, cardWidth - 40, 20, 3);
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

    truncateText(text, maxLength) {
        if (typeof text !== 'string') {
            if (text !== null && text !== undefined) {
                try {
                    text = String(text);
                } catch (e) {
                    return '';
                }
            } else {
                return '';
            }
        }
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

    async loadPreferences() {
        try {
            const [categoriesResponse, preferencesResponse] = await Promise.all([
                fetch('/api/excluded-categories'),
                fetch('/api/preferences')
            ]);

            const categoriesResult = await categoriesResponse.json();
            const preferencesResult = await preferencesResponse.json();

            if (categoriesResult.success) {
                this.renderExcludedCategories(categoriesResult.data);
            }

            if (preferencesResult.success) {
                this.renderPreferences(preferencesResult.data);
            }
        } catch (error) {
            console.error('Load preferences failed:', error);
        }
    }

    renderExcludedCategories(categories) {
        const container = document.getElementById('excluded-categories-list');
        if (!container) return;

        container.innerHTML = '';

        const categoryIcons = {
            'cilantro': '🌿',
            'offal': '🫀',
            'spicy': '🌶️',
            'seafood': '🦐',
            'mushroom': '🍄',
            'egg': '🥚',
            'milk': '🥛',
            'nuts': '🥜'
        };

        categories.forEach(category => {
            const icon = categoryIcons[category.key] || '🍽️';
            const categoryHtml = `
                <label class="excluded-category">
                    <input type="checkbox" class="category-checkbox" data-category="${category.key}">
                    <span class="category-icon">${icon}</span>
                    <span class="category-name">${category.name}</span>
                </label>
            `;
            container.insertAdjacentHTML('beforeend', categoryHtml);
        });

        container.querySelectorAll('.excluded-category').forEach(label => {
            const checkbox = label.querySelector('input[type="checkbox"]');
            label.addEventListener('click', (e) => {
                if (e.target.tagName !== 'INPUT') {
                    e.preventDefault();
                    checkbox.checked = !checkbox.checked;
                    label.classList.toggle('selected', checkbox.checked);
                } else {
                    label.classList.toggle('selected', checkbox.checked);
                }
            });
        });
    }

    renderPreferences(preferences) {
        if (preferences.excluded_ingredients) {
            preferences.excluded_ingredients.forEach(category => {
                const checkbox = document.querySelector(`input[data-category="${category}"]`);
                if (checkbox) {
                    checkbox.checked = true;
                    checkbox.closest('.excluded-category')?.classList.add('selected');
                }
            });
        }

        if (preferences.taste_preference) {
            document.querySelectorAll('.taste-option').forEach(option => {
                if (option.dataset.taste === preferences.taste_preference) {
                    option.classList.add('selected');
                    const radio = option.querySelector('input[type="radio"]');
                    if (radio) radio.checked = true;
                } else {
                    option.classList.remove('selected');
                }
            });
        }

        if (preferences.constitution_type) {
            document.querySelectorAll('.constitution-option').forEach(option => {
                if (option.dataset.constitution === preferences.constitution_type) {
                    option.classList.add('selected');
                    const radio = option.querySelector('input[type="radio"]');
                    if (radio) radio.checked = true;
                } else {
                    option.classList.remove('selected');
                }
            });
        }
    }

    async savePreferences() {
        const excludedIngredients = [];
        document.querySelectorAll('input[data-category]:checked').forEach(input => {
            excludedIngredients.push(input.dataset.category);
        });

        const selectedTaste = document.querySelector('.taste-option.selected');
        const tastePreference = selectedTaste ? selectedTaste.dataset.taste : 'balanced';

        const selectedConstitution = document.querySelector('.constitution-option.selected');
        const constitutionType = selectedConstitution ? selectedConstitution.dataset.constitution : 'balanced';

        try {
            const response = await fetch('/api/preferences', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    excluded_ingredients: excludedIngredients,
                    taste_preference: tastePreference,
                    constitution_type: constitutionType
                })
            });

            const result = await response.json();

            if (result.success) {
                this.showToast('设置已保存！');
            } else {
                alert('保存失败，请重试');
            }
        } catch (error) {
            console.error('Save preferences failed:', error);
            alert('保存失败，请检查网络连接');
        }
    }

    resetPreferences() {
        document.querySelectorAll('input[data-category]').forEach(input => {
            input.checked = false;
            input.closest('.excluded-category')?.classList.remove('selected');
        });

        document.querySelectorAll('.taste-option').forEach((option, index) => {
            option.classList.toggle('selected', index === 1);
            const radio = option.querySelector('input[type="radio"]');
            if (radio) radio.checked = index === 1;
        });

        document.querySelectorAll('.constitution-option').forEach((option, index) => {
            option.classList.toggle('selected', index === 0);
            const radio = option.querySelector('input[type="radio"]');
            if (radio) radio.checked = index === 0;
        });

        this.showToast('已恢复默认设置');
    }

    showToast(message) {
        const toast = document.getElementById('toast');
        if (toast) {
            toast.querySelector('.toast-message').textContent = message;
            toast.classList.add('show');

            setTimeout(() => {
                toast.classList.remove('show');
            }, 2000);
        }
    }

    showGameMenu() {
        document.getElementById('game-menu').style.display = 'block';
        document.getElementById('chef-challenge-game').style.display = 'none';
        document.getElementById('match-game').style.display = 'none';
        document.getElementById('badges-collection').style.display = 'none';
    }

    async loadBadges() {
        try {
            const response = await fetch('/api/games/badges');
            const result = await response.json();

            if (result.success) {
                this.renderBadgesSummary(result.data);
            }
        } catch (error) {
            console.error('Load badges failed:', error);
        }
    }

    renderBadgesSummary(data) {
        const total = data.total_count || (data.badges ? data.badges.length : 0);
        const unlocked = data.unlocked_count || (data.badges ? data.badges.filter(b => b.unlocked).length : 0);

        const statsElement = document.querySelector('.badges-stats');
        if (statsElement) {
            statsElement.innerHTML = `
                <span class="stat-item">
                    <span class="stat-value">${unlocked}</span>
                    <span class="stat-label">已解锁</span>
                </span>
                <span class="stat-item">
                    <span class="stat-value">${total}</span>
                    <span class="stat-label">总徽章</span>
                </span>
            `;
        }
    }

    async startChefChallenge() {
        const gamesMenu = document.querySelector('.games-menu');
        if (gamesMenu) {
            gamesMenu.style.display = 'none';
        }
        document.getElementById('chef-challenge-game').style.display = 'block';
        document.getElementById('chef-loading').style.display = 'block';
        document.getElementById('chef-game-content').style.display = 'none';

        try {
            const response = await fetch('/api/games/chef-challenge', { method: 'GET' });
            const result = await response.json();

            if (result.success) {
                this.currentChefChallenge = result.data;
                this.renderChefChallenge(result.data);
            }
        } catch (error) {
            console.error('Start chef challenge failed:', error);
            alert('加载失败，请重试');
            this.showGameMenu();
        }
    }

    renderChefChallenge(challenge) {
        document.getElementById('chef-loading').style.display = 'none';
        document.getElementById('chef-game-content').style.display = 'block';
        document.getElementById('chef-result').style.display = 'none';

        document.getElementById('chef-term-name').textContent = challenge.term_name || '未知节气';
        document.getElementById('chef-term-icon').textContent = challenge.term_icon || '🌱';

        const ingredientsContainer = document.getElementById('ingredients-grid');
        if (ingredientsContainer && challenge.available_ingredients) {
            ingredientsContainer.innerHTML = '';
            challenge.available_ingredients.forEach((ingredient, index) => {
                const ingredientHtml = `
                    <div class="ingredient-item" data-ingredient="${ingredient}" data-index="${index}">
                        <div class="ingredient-icon">🍽️</div>
                        <div class="ingredient-name">${ingredient}</div>
                    </div>
                `;
                ingredientsContainer.insertAdjacentHTML('beforeend', ingredientHtml);
            });

            ingredientsContainer.querySelectorAll('.ingredient-item').forEach(item => {
                item.addEventListener('click', () => {
                    item.classList.toggle('selected');
                    this.updateSelectedIngredients();
                });
            });
        }

        this.selectedIngredients = [];
    }

    updateSelectedIngredients() {
        this.selectedIngredients = [];
        document.querySelectorAll('.ingredient-item.selected').forEach(item => {
            this.selectedIngredients.push(item.dataset.ingredient);
        });

        const submitBtn = document.getElementById('chef-submit-btn');
        if (submitBtn) {
            submitBtn.disabled = this.selectedIngredients.length === 0;
        }

        const selectedPreview = document.getElementById('selected-preview');
        const selectedList = document.getElementById('selected-list');
        if (selectedPreview && selectedList) {
            if (this.selectedIngredients.length > 0) {
                selectedPreview.style.display = 'block';
                selectedList.innerHTML = this.selectedIngredients.map(i => `<span class="selected-tag">${i}</span>`).join('');
            } else {
                selectedPreview.style.display = 'none';
            }
        }
    }

    async submitChefChallenge() {
        if (this.selectedIngredients.length === 0) {
            alert('请至少选择一种食材');
            return;
        }

        try {
            const response = await fetch('/api/games/chef-challenge', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    challenge_id: this.currentChefChallenge.challenge_id,
                    selected_ingredients: this.selectedIngredients,
                    time_used: 60
                })
            });

            const result = await response.json();

            if (result.success) {
                this.renderChefChallengeResult(result.data);
            }
        } catch (error) {
            console.error('Submit chef challenge failed:', error);
            alert('提交失败，请重试');
        }
    }

    renderChefChallengeResult(result) {
        document.getElementById('chef-game-content').style.display = 'none';
        document.getElementById('chef-result').style.display = 'block';

        document.getElementById('chef-score').textContent = result.score || 0;

        if (result.correct_list) {
            const correctList = document.getElementById('chef-correct-list');
            if (correctList) {
                correctList.innerHTML = result.correct_list.map(i => `<span class="correct-tag">${i}</span>`).join('');
            }
        }
    }

    showGameMenu() {
        const gamesMenu = document.querySelector('.games-menu');
        if (gamesMenu) {
            gamesMenu.style.display = 'grid';
        }
        document.getElementById('chef-challenge-game').style.display = 'none';
        document.getElementById('match-game').style.display = 'none';

        const badgesCollection = document.getElementById('badges-collection');
        if (badgesCollection) {
            badgesCollection.style.display = 'none';
        }
    }

    async startMatchGame() {
        const gamesMenu = document.querySelector('.games-menu');
        if (gamesMenu) {
            gamesMenu.style.display = 'none';
        }
        document.getElementById('match-game').style.display = 'block';
        document.getElementById('match-loading').style.display = 'block';
        document.getElementById('match-game-content').style.display = 'none';

        try {
            const response = await fetch('/api/games/match-game', { method: 'GET' });
            const result = await response.json();

            if (result.success) {
                this.currentMatchGame = result.data;
                this.renderMatchGame(result.data);
            }
        } catch (error) {
            console.error('Start match game failed:', error);
            alert('加载失败，请重试');
            this.showGameMenu();
        }
    }

    renderMatchGame(game) {
        document.getElementById('match-loading').style.display = 'none';
        document.getElementById('match-game-content').style.display = 'block';
        document.getElementById('match-result').style.display = 'none';

        this.matchGameTimer = game.time_limit || 120;
        this.matchGamePairs = game.pairs || [];
        this.matchGameSelectedCards = [];
        this.matchGameMatchedCount = 0;
        this.matchGameStartTime = Date.now();

        this.updateMatchGameTimer();
        this.matchGameTimerInterval = setInterval(() => {
            this.matchGameTimer--;
            this.updateMatchGameTimer();
            if (this.matchGameTimer <= 0) {
                this.endMatchGame();
            }
        }, 1000);

        this.renderMatchGameCards(game.terms, game.ingredients);
    }

    renderMatchGameCards(terms, ingredients) {
        const gameBoard = document.getElementById('match-grid');
        if (!gameBoard) return;

        gameBoard.innerHTML = '';

        const allCards = [];
        terms.forEach(term => {
            allCards.push({
                type: 'term',
                id: `term_${term.key}`,
                term: term,
                displayText: term.name,
                icon: term.icon || '🌱'
            });
        });

        ingredients.forEach(ingredient => {
            allCards.push({
                type: 'ingredient',
                id: `ingredient_${ingredient.name}`,
                ingredient: ingredient,
                displayText: ingredient.name,
                icon: '🍽️'
            });
        });

        this.shuffleArray(allCards);

        this.matchGameAllCards = allCards;

        allCards.forEach(card => {
            const cardHtml = `
                <div class="match-card" data-card-id="${card.id}" data-type="${card.type}" data-matched="false">
                    <div class="match-card-face match-card-front">
                        <span class="card-front-icon">${card.icon}</span>
                        <span class="card-front-text">${card.displayText}</span>
                    </div>
                </div>
            `;
            gameBoard.insertAdjacentHTML('beforeend', cardHtml);
        });

        gameBoard.querySelectorAll('.match-card').forEach(card => {
            card.addEventListener('click', () => this.handleMatchCardClick(card));
        });
    }

    shuffleArray(array) {
        for (let i = array.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [array[i], array[j]] = [array[j], array[i]];
        }
    }

    handleMatchCardClick(cardElement) {
        const cardId = cardElement.dataset.cardId;
        const isMatched = cardElement.dataset.matched === 'true';
        const isSelected = cardElement.classList.contains('selected');

        if (isMatched || isSelected) return;

        if (this.matchGameSelectedCards.length >= 2) return;

        cardElement.classList.add('selected');
        this.matchGameSelectedCards.push(cardId);

        if (this.matchGameSelectedCards.length === 2) {
            setTimeout(() => this.checkMatch(), 500);
        }
    }

    checkMatch() {
        const [card1Id, card2Id] = this.matchGameSelectedCards;
        const card1 = this.matchGameAllCards.find(c => c.id === card1Id);
        const card2 = this.matchGameAllCards.find(c => c.id === card2Id);

        let isMatch = false;

        if (card1.type === 'term' && card2.type === 'ingredient') {
            isMatch = this.checkTermIngredientMatch(card1.term, card2.ingredient);
        } else if (card1.type === 'ingredient' && card2.type === 'term') {
            isMatch = this.checkTermIngredientMatch(card2.term, card1.ingredient);
        }

        const card1Element = document.querySelector(`[data-card-id="${card1Id}"]`);
        const card2Element = document.querySelector(`[data-card-id="${card2Id}"]`);

        if (isMatch) {
            card1Element.classList.add('matched');
            card2Element.classList.add('matched');
            card1Element.dataset.matched = 'true';
            card2Element.dataset.matched = 'true';
            this.matchGameMatchedCount++;

            const totalPairs = this.matchGamePairs.length;
            document.getElementById('match-pairs').textContent = this.matchGameMatchedCount;
            document.getElementById('match-total').textContent = totalPairs;

            if (this.matchGameMatchedCount >= totalPairs) {
                this.endMatchGame();
            }
        } else {
            card1Element.classList.remove('selected');
            card2Element.classList.remove('selected');
        }

        this.matchGameSelectedCards = [];
    }

    checkTermIngredientMatch(term, ingredient) {
        const matchedPair = this.matchGamePairs.find(pair => 
            pair.term_key === term.key && pair.ingredients.includes(ingredient.name)
        );
        return !!matchedPair;
    }

    updateMatchGameTimer() {
        const minutes = Math.floor(this.matchGameTimer / 60);
        const seconds = this.matchGameTimer % 60;
        document.getElementById('match-timer').textContent = 
            `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }

    async endMatchGame() {
        if (this.matchGameTimerInterval) {
            clearInterval(this.matchGameTimerInterval);
        }

        const timeUsed = Math.floor((Date.now() - this.matchGameStartTime) / 1000);
        const accuracy = this.matchGamePairs.length > 0 ? 
            Math.round((this.matchGameMatchedCount / this.matchGamePairs.length) * 100) : 0;

        try {
            const response = await fetch('/api/games/match-game', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    game_id: this.currentMatchGame.game_id,
                    matched_pairs: this.matchGameMatchedCount,
                    time_used: timeUsed,
                    accuracy: accuracy
                })
            });

            const result = await response.json();

            if (result.success) {
                this.renderMatchGameResult(result.data);
            }
        } catch (error) {
            console.error('End match game failed:', error);
        }
    }

    renderMatchGameResult(result) {
        document.getElementById('match-game-content').style.display = 'none';
        document.getElementById('match-result').style.display = 'block';

        document.getElementById('match-score').textContent = result.score || 0;
    }

    async showBadgesCollection() {
        const gamesMenu = document.querySelector('.games-menu');
        if (gamesMenu) {
            gamesMenu.style.display = 'none';
        }
        document.getElementById('badges-collection').style.display = 'block';

        try {
            const response = await fetch('/api/games/badges');
            const result = await response.json();

            if (result.success) {
                this.renderBadgesCollection(result.data);
            }
        } catch (error) {
            console.error('Load badges failed:', error);
        }
    }

    renderBadgesCollection(data) {
        const grid = document.querySelector('.badges-grid');
        if (!grid) return;

        grid.innerHTML = '';

        const badges = data.badges || data;
        badges.forEach(badge => {
            const lockedClass = badge.unlocked ? '' : 'locked';
            const badgeHtml = `
                <div class="badge-item ${lockedClass}">
                    <div class="badge-icon">${badge.icon || '🏅'}</div>
                    <div class="badge-name">${badge.name}</div>
                    <div class="badge-desc">${badge.description || ''}</div>
                </div>
            `;
            grid.insertAdjacentHTML('beforeend', badgeHtml);
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new SeasonsBite();
});
