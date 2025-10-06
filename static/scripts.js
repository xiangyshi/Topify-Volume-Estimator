// ChatGPT Volume Estimator - JavaScript

// Update parameter values when sliders change
document.getElementById('visWeight').addEventListener('input', function() {
    document.getElementById('visValue').textContent = this.value;
});

document.getElementById('semWeight').addEventListener('input', function() {
    document.getElementById('semValue').textContent = this.value;
});

// Authority and Est. Clicks are disabled - no event listeners needed
document.getElementById('featWeight').addEventListener('input', function() {
    document.getElementById('featValue').textContent = this.value;
});

document.getElementById('alpha').addEventListener('input', function() {
    document.getElementById('alphaValue').textContent = this.value;
});

// Check data availability when inputs change
document.getElementById('keyword').addEventListener('input', checkDataAvailability);
document.getElementById('domain').addEventListener('input', checkDataAvailability);

// View toggle event listeners
document.getElementById('normalView').addEventListener('change', switchView);
document.getElementById('aggregateView').addEventListener('change', switchView);

async function checkDataAvailability() {
    const keyword = document.getElementById('keyword').value.trim();
    const domain = document.getElementById('domain').value.trim();
    
    if (keyword && domain) {
        try {
            const response = await fetch('/api/check-data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ keyword, domain })
            });
            
            const data = await response.json();
            
            if (data.exists) {
                showStatus(data.message, 'status-info');
            } else {
                showStatus(data.message, 'status-info');
            }
        } catch (error) {
            console.error('Error checking data:', error);
        }
    }
}

function showStatus(message, type) {
    const statusDiv = document.getElementById('statusMessage');
    statusDiv.textContent = message;
    statusDiv.className = `status-message ${type}`;
    statusDiv.style.display = 'block';
}

async function analyze() {
    const keyword = document.getElementById('keyword').value.trim();
    const domain = document.getElementById('domain').value.trim();
    const token = document.getElementById('apiToken').value.trim();
    
    if (!keyword || !domain || !token) {
        showStatus('Please enter keyword, domain, and API token', 'status-error');
        return;
    }
    
    // Get parameter values (Authority and Est. Clicks are disabled/fixed)
    const lambdas = [
        parseFloat(document.getElementById('visWeight').value),
        parseFloat(document.getElementById('semWeight').value),
        0.0, // Authority weight - disabled, set to 0
        parseFloat(document.getElementById('featWeight').value),
        0.0  // Est. Clicks weight - disabled, set to 0
    ];
    const alpha = parseFloat(document.getElementById('alpha').value);
    
    // Show loading
    document.getElementById('loading').style.display = 'block';
    document.getElementById('results').style.display = 'none';
    document.getElementById('analyzeBtn').disabled = true;
    
    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                keyword,
                domain,
                token,
                lambdas,
                alpha
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Analysis failed');
        }
        
        const data = await response.json();
        
        if (data.success) {
            displayResults(data);
            showStatus('✅ Analysis completed successfully!', 'status-success');
        } else {
            throw new Error(data.error || 'Analysis failed');
        }
        
    } catch (error) {
        showStatus('❌ Error: ' + error.message, 'status-error');
    } finally {
        document.getElementById('loading').style.display = 'none';
        document.getElementById('analyzeBtn').disabled = false;
    }
}

function displayResults(data) {
    // Store data globally for view switching
    window.currentData = data;
    
    // Update metrics
    document.getElementById('keywordResult').textContent = data.keyword;
    document.getElementById('domainResult').textContent = data.domain;
    document.getElementById('totalVolume').textContent = data.total_volume.toFixed(1);
    document.getElementById('topShare').textContent = data.top_share.toFixed(3);
    document.getElementById('dataFile').textContent = data.data_file;
    
    // Display target domain summary if available
    if (data.target_domain_stats) {
        displayTargetDomainSummary(data.target_domain_stats);
    }
    
    // Show view toggle
    document.getElementById('viewToggle').style.display = 'block';
    
    // Display current view
    switchView();
    
    // Show results
    document.getElementById('results').style.display = 'block';
}

function switchView() {
    if (!window.currentData) return;
    
    const isNormalView = document.getElementById('normalView').checked;
    const data = window.currentData;
    
    // Update title
    document.getElementById('resultsTitle').textContent = isNormalView ? 
        'Top Performing Domains' : 'Top Performing Domains (Aggregated)';
    
    // Update table headers
    const headerRow = document.getElementById('resultsHeader').querySelector('tr');
    if (isNormalView) {
        headerRow.innerHTML = `
            <th>Domain</th>
            <th>Google Search Rank</th>
            <th>Logit Score</th>
            <th>Domain Share</th>
            <th>AI Potential Volume</th>
        `;
    } else {
        headerRow.innerHTML = `
            <th>Domain</th>
            <th>Appearances</th>
            <th>Best Rank</th>
            <th>Worst Rank</th>
            <th>Avg Rank</th>
            <th>Avg Logit</th>
            <th>Total Domain Share</th>
            <th>Total AI Volume</th>
        `;
    }
    
    // Update table content
    const tbody = document.getElementById('resultsBody');
    tbody.innerHTML = '';
    
    const results = isNormalView ? (data.normal_results || []) : (data.results || []);
    
    if (results.length === 0) {
        const tr = document.createElement('tr');
        tr.innerHTML = '<td colspan="5" style="text-align: center; color: #6b7280;">No data available</td>';
        tbody.appendChild(tr);
        return;
    }
    
    results.forEach(row => {
        const tr = document.createElement('tr');
        
        // Check if this row is the target domain
        const isTargetDomain = row.domain === data.domain;
        
        // Add special class for target domain
        if (isTargetDomain) {
            tr.className = 'target-domain-row';
        }
        
        if (isNormalView) {
            tr.innerHTML = `
                <td>${row.domain}${isTargetDomain ? ' 🎯' : ''}</td>
                <td>${row.rank_absolute}</td>
                <td>${row.logit.toFixed(2)}</td>
                <td>${row.domain_share.toFixed(3)}</td>
                <td>${row.ai_potential_volume.toFixed(1)}</td>
            `;
        } else {
            tr.innerHTML = `
                <td>${row.domain}${isTargetDomain ? ' 🎯' : ''}</td>
                <td>${row.appearances}</td>
                <td>${row.best_rank}</td>
                <td>${row.worst_rank}</td>
                <td>${row.avg_rank.toFixed(1)}</td>
                <td>${row.avg_logit.toFixed(2)}</td>
                <td>${row.total_domain_share.toFixed(3)}</td>
                <td>${row.total_ai_volume.toFixed(1)}</td>
            `;
        }
        tbody.appendChild(tr);
    });
}

function displayTargetDomainSummary(stats) {
    const summaryDiv = document.getElementById('targetDomainStats');
    summaryDiv.innerHTML = `
        <div class="stat-item">
            <span class="stat-value">${stats.appearances}</span>
            <span class="stat-label">Appearances</span>
        </div>
        <div class="stat-item">
            <span class="stat-value">${stats.best_rank}</span>
            <span class="stat-label">Best Rank</span>
        </div>
        <div class="stat-item">
            <span class="stat-value">${stats.worst_rank}</span>
            <span class="stat-label">Worst Rank</span>
        </div>
        <div class="stat-item">
            <span class="stat-value">${stats.avg_rank}</span>
            <span class="stat-label">Average Rank</span>
        </div>
        <div class="stat-item">
            <span class="stat-value">${stats.total_domain_share}</span>
            <span class="stat-label">Total Share</span>
        </div>
        <div class="stat-item">
            <span class="stat-value">${stats.total_ai_volume}</span>
            <span class="stat-label">Total AI Volume</span>
        </div>
        <div class="stat-item">
            <span class="stat-value">${stats.avg_logit}</span>
            <span class="stat-label">Avg Logit</span>
        </div>
        <div class="stat-item">
            <span class="stat-value">${stats.max_logit}</span>
            <span class="stat-label">Max Logit</span>
        </div>
    `;
    
    // Show target domain summary
    document.getElementById('targetDomainSummary').style.display = 'block';
}
