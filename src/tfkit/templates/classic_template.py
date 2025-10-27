# templates/classic_template.py
from .base_template import BaseTemplate


class ClassicTemplate(BaseTemplate):
    """Modern, intuitive classic template with enhanced UI and search functionality."""

    @property
    def template_string(self) -> str:
        return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{ title }}</title>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=Exo+2:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            {% set colors = theme_colors %}
            
            * { margin: 0; padding: 0; box-sizing: border-box; }
            
            body {
                font-family: 'Exo 2', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                background: {{ colors.bg_primary }};
                color: {{ colors.text_primary }};
                line-height: 1.6;
            }
            
            .container {
                max-width: 1600px;
                margin: 0 auto;
                padding: 20px;
            }
            
            /* --- MODERN HEADER --- */
            .header {
                background: linear-gradient(135deg, {{ colors.bg_secondary }} 0%, {{ colors.bg_tertiary }} 100%);
                padding: 28px 32px;
                border-radius: 16px;
                margin-bottom: 24px;
                border: 1px solid {{ colors.border }};
                border-left: 6px solid {{ colors.accent }};
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            }
            
            .header h1 {
                color: {{ colors.accent }};
                font-size: 2em;
                font-weight: 700;
                margin-bottom: 8px;
                display: flex;
                align-items: center;
                gap: 12px;
            }
            
            .header .meta {
                color: {{ colors.text_secondary }};
                font-size: 1em;
                font-weight: 500;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            /* --- MODERN STATS GRID --- */
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 20px;
                margin-bottom: 32px;
            }
            
            .stat-card {
                background: linear-gradient(135deg, {{ colors.bg_secondary }} 0%, {{ colors.bg_tertiary }} 100%);
                padding: 24px;
                border-radius: 12px;
                border: 1px solid {{ colors.border }};
                position: relative;
                overflow: hidden;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(0,0,0,0.08);
            }
            
            .stat-card::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                width: 4px;
                height: 100%;
                background: {{ colors.accent }};
            }
            
            .stat-card:hover {
                transform: translateY(-4px);
                box-shadow: 0 8px 25px rgba(0,0,0,0.15);
                border-color: {{ colors.accent }}40;
            }
            
            .stat-card-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 16px;
            }
            
            .stat-icon {
                width: 48px;
                height: 48px;
                background: {{ colors.accent }}20;
                border-radius: 10px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.4em;
                color: {{ colors.accent }};
            }
            
            .stat-value {
                font-size: 2.5em;
                font-weight: 800;
                color: {{ colors.text_primary }};
                line-height: 1;
                margin-bottom: 8px;
                font-family: 'Exo 2', sans-serif;
            }
            
            .stat-label {
                font-size: 0.9em;
                color: {{ colors.text_secondary }};
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            .stat-trend {
                font-size: 0.8em;
                padding: 4px 8px;
                border-radius: 6px;
                font-weight: 600;
                margin-top: 8px;
                display: inline-block;
            }
            
            .stat-trend.positive {
                background: {{ colors.success }}20;
                color: {{ colors.success }};
            }
            
            .stat-trend.negative {
                background: {{ colors.danger }}20;
                color: {{ colors.danger }};
            }
            
            .state-breakdown {
                margin-top: 16px;
                padding-top: 16px;
                border-top: 1px solid {{ colors.border }}40;
            }
            
            .state-item {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 6px 0;
                font-size: 0.85em;
            }
            
            .state-item:last-child {
                padding-bottom: 0;
            }
            
            .state-name {
                color: {{ colors.text_secondary }};
                font-weight: 500;
            }
            
            .state-count {
                color: {{ colors.text_primary }};
                font-weight: 700;
                background: {{ colors.bg_primary }}30;
                padding: 2px 8px;
                border-radius: 12px;
                min-width: 24px;
                text-align: center;
            }
            
            /* --- ENHANCED SEARCH BAR --- */
            .search-container {
                position: relative;
                margin: 0 20px 20px 20px;
            }
            
            .search-box {
                width: 100%;
                padding: 16px 52px 16px 48px;
                border: 2px solid {{ colors.border }};
                background: {{ colors.bg_primary }};
                color: {{ colors.text_primary }};
                border-radius: 12px;
                font-size: 1em;
                transition: all 0.3s ease;
                font-family: 'Exo 2', sans-serif;
            }
            
            .search-box:focus {
                outline: none;
                border-color: {{ colors.accent }};
                box-shadow: 0 0 0 3px {{ colors.accent }}20;
            }
            
            .search-box::placeholder {
                color: {{ colors.text_secondary }};
            }
            
            .search-icon {
                position: absolute;
                left: 16px;
                top: 50%;
                transform: translateY(-50%);
                color: {{ colors.text_secondary }};
                font-size: 1.1em;
            }
            
            .search-clear {
                position: absolute;
                right: 16px;
                top: 50%;
                transform: translateY(-50%);
                background: none;
                border: none;
                color: {{ colors.text_secondary }};
                cursor: pointer;
                padding: 4px;
                border-radius: 4px;
                transition: all 0.2s ease;
                opacity: 0;
            }
            
            .search-clear:hover {
                color: {{ colors.danger }};
                background: {{ colors.danger }}15;
            }
            
            .search-clear.visible {
                opacity: 1;
            }
            
            .search-hint {
                position: absolute;
                right: 16px;
                top: -24px;
                font-size: 0.75em;
                color: {{ colors.text_secondary }};
                background: {{ colors.bg_secondary }};
                padding: 2px 8px;
                border-radius: 6px;
                border: 1px solid {{ colors.border }};
            }
            
            /* --- REST OF THE STYLES (keeping your existing styles with minor updates) --- */
            .main-panel {
                background: {{ colors.bg_secondary }};
                border: 1px solid {{ colors.border }};
                border-radius: 16px;
                overflow: hidden;
                margin-bottom: 24px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            }
            
            .panel-header {
                padding: 20px 24px;
                border-bottom: 1px solid {{ colors.border }};
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
                gap: 16px;
                background: {{ colors.bg_tertiary }};
            }
            
            .panel-title {
                font-size: 1.25em;
                font-weight: 700;
                color: {{ colors.text_primary }};
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .controls {
                display: flex;
                gap: 8px;
                flex-wrap: wrap;
            }
            
            .btn {
                padding: 10px 16px;
                border: 1px solid {{ colors.border }};
                background: {{ colors.bg_primary }};
                color: {{ colors.text_primary }};
                border-radius: 8px;
                font-size: 0.9em;
                cursor: pointer;
                transition: all 0.2s;
                display: flex;
                align-items: center;
                gap: 6px;
                font-weight: 600;
                font-family: 'Exo 2', sans-serif;
            }
            
            .btn:hover {
                background: {{ colors.accent }};
                border-color: {{ colors.accent }};
                color: {{ colors.bg_primary }};
                transform: translateY(-1px);
            }
            
            .btn.active {
                background: {{ colors.accent }};
                border-color: {{ colors.accent }};
                color: {{ colors.bg_primary }};
            }
            
            .graph-container {
                padding: 20px;
                max-height: 70vh;
                overflow-y: auto;
            }
            
            .graph-container::-webkit-scrollbar {
                width: 8px;
            }
            
            .graph-container::-webkit-scrollbar-track {
                background: {{ colors.bg_primary }};
            }
            
            .graph-container::-webkit-scrollbar-thumb {
                background: {{ colors.border }};
                border-radius: 4px;
            }
            
            .graph-container::-webkit-scrollbar-thumb:hover {
                background: {{ colors.text_secondary }};
            }
            
            .graph-nodes {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
                gap: 20px;
            }
            
            .graph-node {
                background: {{ colors.bg_primary }};
                border: 1px solid {{ colors.border }};
                border-radius: 12px;
                padding: 24px;
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
                box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            }
            
            .graph-node:hover {
                border-color: {{ colors.accent }};
                transform: translateY(-2px);
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            }
            
            .node-unused { border-left: 4px solid {{ colors.danger }}; }
            .node-external { border-left: 4px solid {{ colors.info }}; }
            .node-leaf { border-left: 4px solid {{ colors.success }}; }
            .node-orphan { border-left: 4px solid {{ colors.warning }}; }
            .node-warning { border-left: 4px solid {{ colors.warning }}; }
            .node-healthy { border-left: 4px solid {{ colors.success }}; }
            
            .graph-node-header {
                display: flex;
                align-items: flex-start;
                margin-bottom: 16px;
                gap: 16px;
            }
            
            .graph-node-icon {
                width: 48px;
                height: 48px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 10px;
                background: {{ colors.accent }};
                flex-shrink: 0;
                font-size: 1.3em;
                color: {{ colors.bg_primary }};
            }
            
            .graph-node-title-container {
                flex: 1;
                min-width: 0;
            }
            
            .graph-node-title {
                font-weight: 700;
                font-size: 1.2em;
                margin-bottom: 6px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                color: {{ colors.text_primary }};
            }
            
            .graph-node-type {
                color: {{ colors.text_secondary }};
                font-size: 0.9em;
                font-weight: 500;
                margin-bottom: 8px;
            }
            
            .graph-node-state {
                font-size: 0.8em;
                font-weight: 700;
                padding: 6px 12px;
                border-radius: 6px;
                display: inline-block;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            .graph-node-badges {
                display: flex;
                gap: 6px;
                flex-wrap: wrap;
                margin-top: 12px;
            }
            
            .graph-node-badge {
                background: {{ colors.info }};
                color: white;
                font-size: 0.75em;
                padding: 4px 8px;
                border-radius: 6px;
                font-weight: 600;
            }
            
            .graph-node-badge.warning {
                background: {{ colors.warning }};
                color: {{ colors.bg_primary }};
            }
            
            .graph-node-badge.danger {
                background: {{ colors.danger }};
                color: white;
            }
            
            .graph-node-dependencies {
                display: flex;
                gap: 20px;
                margin-top: 16px;
                padding-top: 16px;
                border-top: 1px solid {{ colors.border }}40;
            }
            
            .graph-node-deps-item {
                display: flex;
                align-items: center;
                gap: 8px;
                font-size: 0.9em;
                color: {{ colors.text_secondary }};
                font-weight: 500;
            }
            
            .graph-node-deps-count {
                background: {{ colors.info }};
                color: white;
                border-radius: 12px;
                min-width: 24px;
                height: 24px;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                font-size: 0.8em;
                font-weight: 700;
            }
            
            .graph-node-deps-count.outgoing {
                background: {{ colors.success }};
            }
            
            .graph-node-deps-count.incoming {
                background: {{ colors.purple }};
            }
            
            .graph-node-reason {
                font-size: 0.85em;
                color: {{ colors.text_secondary }};
                font-style: italic;
                margin-top: 12px;
                line-height: 1.4;
            }
            
            .empty-state {
                padding: 80px 20px;
                text-align: center;
                color: {{ colors.text_secondary }};
            }
            
            .empty-state-icon {
                font-size: 4em;
                margin-bottom: 20px;
                opacity: 0.5;
            }
            
            .empty-state h3 {
                font-size: 1.5em;
                margin-bottom: 12px;
                color: {{ colors.text_primary }};
            }
            
            .footer {
                margin-top: 40px;
                padding: 20px;
                text-align: center;
                border-top: 1px solid {{ colors.border }};
            }

            #watermark {
                font-size: 0.85em;
                color: {{ colors.text_secondary }};
                user-select: none;
                font-family: 'Exo 2', sans-serif;
                font-weight: 500;
                letter-spacing: 0.3px;
            }

            #watermark a {
                color: {{ colors.text_secondary }};
                text-decoration: none;
                font-weight: 600;
                transition: all 0.2s ease;
                padding: 4px 8px;
                border-radius: 6px;
            }

            #watermark a:hover {
                color: {{ colors.accent }};
                background: {{ colors.accent }}15;
            }
            
            .filter-info {
                background: {{ colors.bg_tertiary }};
                border: 1px solid {{ colors.border }};
                border-radius: 10px;
                padding: 16px 20px;
                margin: 0 20px 20px 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
                gap: 16px;
            }
            
            .filter-tags {
                display: flex;
                gap: 8px;
                flex-wrap: wrap;
            }
            
            .filter-tag {
                background: {{ colors.accent }};
                color: white;
                padding: 6px 12px;
                border-radius: 12px;
                font-size: 0.85em;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 6px;
            }
            
            .filter-tag .remove {
                cursor: pointer;
                opacity: 0.8;
                transition: opacity 0.2s;
            }
            
            .filter-tag .remove:hover {
                opacity: 1;
            }
            
            @media (max-width: 768px) {
                .stats-grid {
                    grid-template-columns: 1fr;
                }
                .controls {
                    flex-direction: column;
                    width: 100%;
                }
                .btn {
                    justify-content: center;
                }
                .graph-nodes {
                    grid-template-columns: 1fr;
                }
                .panel-header {
                    flex-direction: column;
                    align-items: stretch;
                }
                .search-hint {
                    display: none;
                }
            }
            
            @media (max-width: 480px) {
                .container {
                    padding: 12px;
                }
                .header {
                    padding: 20px;
                }
                .header h1 {
                    font-size: 1.5em;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <!-- Modern Stats Grid -->
            <div class="stats-grid" id="stats-grid">
                <!-- Stats will be populated by JavaScript -->
            </div>
            
            <!-- Main Content Panel -->
            <div class="main-panel">
                <div class="panel-header">
                    <div class="panel-title">
                        <i class="fas fa-cubes"></i>
                        Infrastructure Components
                    </div>
                    <div class="controls">
                        <button class="btn" onclick="sortNodes('name')" id="sort-name">
                            <i class="fas fa-sort-alpha-down"></i> Name
                        </button>
                        <button class="btn" onclick="sortNodes('type')" id="sort-type">
                            <i class="fas fa-layer-group"></i> Type
                        </button>
                        <button class="btn" onclick="sortNodes('dependencies')" id="sort-deps">
                            <i class="fas fa-project-diagram"></i> Dependencies
                        </button>
                        <button class="btn" onclick="filterByState('unused')" id="filter-unused">
                            <i class="fas fa-eye-slash"></i> Unused
                        </button>
                        <button class="btn" onclick="filterByState('warning')" id="filter-warning">
                            <i class="fas fa-exclamation-triangle"></i> Warnings
                        </button>
                        <button class="btn" onclick="resetFilters()">
                            <i class="fas fa-redo"></i> Reset
                        </button>
                    </div>
                </div>
                
                <!-- Enhanced Search Bar -->
                <div class="search-container">
                    <div class="search-hint">
                        <kbd>/</kbd> to search • <kbd>Esc</kbd> to clear
                    </div>
                    <i class="fas fa-search search-icon"></i>
                    <input type="text" class="search-box" placeholder="Search components by name, type, state, or reason..." 
                           id="search-input" />
                    <button class="search-clear" id="search-clear" onclick="clearSearch()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                
                <!-- Filter Info -->
                <div class="filter-info" id="filter-info" style="display: none;">
                    <div>
                        <strong>Active Filters:</strong>
                        <div class="filter-tags" id="filter-tags"></div>
                    </div>
                    <button class="btn" onclick="resetFilters()">
                        <i class="fas fa-times"></i> Clear All
                    </button>
                </div>
                
                <!-- Graph Content -->
                <div class="graph-container">
                    <div class="graph-nodes" id="graph-nodes-container"></div>
                </div>
            </div>
            
            <!-- Footer -->
            <div class="footer">
                <div id="watermark">
                    tfkit (v{{ tfkit_version | default('0.0.0') }}) | <a href="https://github.com/ivasik-k7/tfkit" target="_blank">tfkit.com</a>
                </div>
            </div>         
        </div>
        
        <script>
            const graphData = {{ graph_data|safe }};
            let currentSort = 'name';
            let currentStateFilter = null;
            let currentSearch = '';
            let filterTimeout = null;

            // Enhanced search functionality
            function initializeSearch() {
                const searchInput = document.getElementById('search-input');
                const searchClear = document.getElementById('search-clear');
                
                searchInput.addEventListener('input', function(e) {
                    const query = e.target.value;
                    updateSearchClear(query);
                    debounceFilter(query);
                });
                
                // Show/hide clear button based on input
                function updateSearchClear(query) {
                    if (query.length > 0) {
                        searchClear.classList.add('visible');
                    } else {
                        searchClear.classList.remove('visible');
                    }
                }
            }
            
            function clearSearch() {
                const searchInput = document.getElementById('search-input');
                searchInput.value = '';
                searchInput.focus();
                updateSearchClear('');
                filterNodes('');
            }
            
            // Performance optimization: Debounce search
            function debounceFilter(query) {
                clearTimeout(filterTimeout);
                filterTimeout = setTimeout(() => {
                    filterNodes(query);
                }, 100); // Reduced from 150ms for better responsiveness
            }

            // Calculate summary statistics
            const summary = {
                total_nodes: graphData.nodes.length,
                total_edges: graphData.edges.length,
                state_counts: {
                    healthy: graphData.nodes.filter(n => n.state === 'healthy').length,
                    unused: graphData.nodes.filter(n => n.state === 'unused').length,
                    external: graphData.nodes.filter(n => n.state === 'external').length,
                    leaf: graphData.nodes.filter(n => n.state === 'leaf').length,
                    orphan: graphData.nodes.filter(n => n.state === 'orphan').length,
                    warning: graphData.nodes.filter(n => n.state === 'warning').length
                }
            };
            
            // Font Awesome icons for different node types
            const nodeIcons = {
                'resource': 'fas fa-cube',
                'module': 'fas fa-cubes',
                'variable': 'fas fa-code',
                'output': 'fas fa-arrow-right',
                'data': 'fas fa-database',
                'provider': 'fas fa-cog',
                'local': 'fas fa-code',
                'terraform': 'fas fa-sitemap'
            };
            
            // State configuration
            const stateConfig = {
                'healthy': { class: 'node-healthy', icon: 'fas fa-check-circle', color: '{{ colors.success }}' },
                'unused': { class: 'node-unused', icon: 'fas fa-ban', color: '{{ colors.danger }}' },
                'external': { class: 'node-external', icon: 'fas fa-external-link-alt', color: '{{ colors.info }}' },
                'leaf': { class: 'node-leaf', icon: 'fas fa-leaf', color: '{{ colors.success }}' },
                'orphan': { class: 'node-orphan', icon: 'fas fa-unlink', color: '{{ colors.warning }}' },
                'warning': { class: 'node-warning', icon: 'fas fa-exclamation-triangle', color: '{{ colors.warning }}' }
            };

            function initializeStats() {
                const statsGrid = document.getElementById('stats-grid');
                
                // Calculate health score
                const totalNodes = summary.total_nodes;
                const healthyNodes = summary.state_counts.healthy;
                const healthScore = totalNodes > 0 ? Math.round((healthyNodes / totalNodes) * 100) : 100;
                
                statsGrid.innerHTML = `
                    <div class="stat-card">
                        <div class="stat-card-header">
                            <div class="stat-icon">
                                <i class="fas fa-cubes"></i>
                            </div>
                        </div>
                        <div class="stat-value">${summary.total_nodes}</div>
                        <div class="stat-label">Total Components</div>
    
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-card-header">
                            <div class="stat-icon">
                                <i class="fas fa-project-diagram"></i>
                            </div>
                        </div>
                        <div class="stat-value">${summary.total_edges}</div>
                        <div class="stat-label">Dependencies</div>
                        <div class="stat-trend positive">
                            <i class="fas fa-chart-line"></i> ${calculateAverageDependencies()} avg per component
                        </div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-card-header">
                            <div class="stat-icon">
                                <i class="fas fa-network-wired"></i>
                            </div>
                        </div>
                        <div class="stat-value">${calculateConnectedComponents()}</div>
                        <div class="stat-label">Connected Groups</div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-card-header">
                            <div class="stat-icon">
                                <i class="fas fa-heart"></i>
                            </div>
                        </div>
                        <div class="stat-value">${healthScore}%</div>
                        <div class="stat-label">Health Score</div>
                        <div class="stat-trend ${healthScore > 80 ? 'positive' : 'negative'}">
                            ${healthScore > 80 ? '<i class="fas fa-arrow-up"></i> Excellent' : '<i class="fas fa-arrow-down"></i> Needs Attention'}
                        </div>
                    </div>
                `;
            }

            function calculateAverageDependencies() {
                if (graphData.nodes.length === 0) return 0;
                const totalDeps = graphData.nodes.reduce((sum, node) => 
                    sum + (node.dependencies_out || 0) + (node.dependencies_in || 0), 0);
                return (totalDeps / graphData.nodes.length).toFixed(1);
            }

            function calculateConnectedComponents() {
                // Simple component counting - optimized for performance
                const visited = new Set();
                let components = 0;

                // Build quick adjacency list
                const adj = new Map();
                graphData.nodes.forEach(node => adj.set(node.id, []));
                graphData.edges.forEach(edge => {
                    const sourceId = typeof edge.source === 'object' ? edge.source.id : edge.source;
                    const targetId = typeof edge.target === 'object' ? edge.target.id : edge.target;
                    if (adj.has(sourceId)) adj.get(sourceId).push(targetId);
                    if (adj.has(targetId)) adj.get(targetId).push(sourceId);
                });

                function dfs(nodeId) {
                    const stack = [nodeId];
                    while (stack.length) {
                        const current = stack.pop();
                        if (!visited.has(current)) {
                            visited.add(current);
                            stack.push(...(adj.get(current) || []));
                        }
                    }
                }

                graphData.nodes.forEach(node => {
                    if (!visited.has(node.id)) {
                        dfs(node.id);
                        components++;
                    }
                });

                return components;
            }
            
            function renderGraphNodes() {
                const container = document.getElementById('graph-nodes-container');
                
                let nodesToShow = graphData.nodes.filter(node => {
                    if (currentStateFilter && node.state !== currentStateFilter) {
                        return false;
                    }
                    
                    if (currentSearch) {
                        const searchTerm = currentSearch.toLowerCase();
                        const searchableText = [
                            node.label,
                            node.type,
                            node.subtype || '',
                            node.state,
                            node.state_reason || '',
                            JSON.stringify(node.details || {})
                        ].join(' ').toLowerCase();
                        
                        return searchableText.includes(searchTerm);
                    }
                    
                    return true;
                });
                
                // Sort nodes
                nodesToShow.sort((a, b) => {
                    switch (currentSort) {
                        case 'name':
                            return a.label.localeCompare(b.label);
                        case 'type':
                            return a.type.localeCompare(b.type) || (a.subtype || '').localeCompare(b.subtype || '');
                        case 'dependencies':
                            const aDeps = (a.dependencies_out || 0) + (a.dependencies_in || 0);
                            const bDeps = (b.dependencies_out || 0) + (b.dependencies_in || 0);
                            return bDeps - aDeps;
                        default:
                            return 0;
                    }
                });
                
                if (nodesToShow.length === 0) {
                    container.innerHTML = `
                        <div class="empty-state">
                            <div class="empty-state-icon"><i class="fas fa-search"></i></div>
                            <h3>No components found</h3>
                            <p>Try adjusting your search or filter criteria</p>
                            <p style="margin-top: 12px; font-size: 0.9em; color: {{ colors.text_secondary }};">
                                Search across: name, type, state, description, and file paths
                            </p>
                        </div>
                    `;
                    return;
                }
                
                // Use document fragment for better performance
                const fragment = document.createDocumentFragment();
                
                nodesToShow.forEach(node => {
                    const nodeElement = createNodeElement(node);
                    fragment.appendChild(nodeElement);
                });
                
                container.innerHTML = '';
                container.appendChild(fragment);
                
                updateFilterInfo();
            }
            
            function createNodeElement(node) {
                const nodeElement = document.createElement('div');
                const state = stateConfig[node.state] || stateConfig.healthy;
                const details = node.details || {};
                
                nodeElement.className = `graph-node ${state.class}`;
                
                // Create badges based on node status
                const badges = [];
                if ((node.dependencies_out || 0) === 0 && (node.dependencies_in || 0) > 0) {
                    badges.push('<span class="graph-node-badge"><i class="fas fa-leaf"></i> LEAF</span>');
                }
                if ((node.dependencies_out || 0) > 5 || (node.dependencies_in || 0) > 5) {
                    badges.push('<span class="graph-node-badge"><i class="fas fa-hubspot"></i> HUB</span>');
                }
                if (details.sensitive) {
                    badges.push('<span class="graph-node-badge warning"><i class="fas fa-lock"></i> SENSITIVE</span>');
                }

                nodeElement.innerHTML = `
                    <div class="graph-node-header">
                        <div class="graph-node-icon">
                            <i class="${nodeIcons[node.type] || 'fas fa-cube'}"></i>
                        </div>
                        <div class="graph-node-title-container">
                            <div class="graph-node-title" title="${node.label}">${node.label}</div>
                            <div class="graph-node-type">${node.type} • ${node.subtype || 'N/A'}</div>
                            <span class="graph-node-state" style="background: ${state.color}15; color: ${state.color}; border: 1px solid ${state.color}30;">
                                <i class="${state.icon}"></i> ${node.state.toUpperCase()}
                            </span>
                            ${badges.length > 0 ? `<div class="graph-node-badges">${badges.join('')}</div>` : ''}
                        </div>
                    </div>
                    <div class="graph-node-dependencies">
                        <div class="graph-node-deps-item">
                            <span><i class="fas fa-arrow-up"></i> Uses:</span>
                            <span class="graph-node-deps-count outgoing">${node.dependencies_out || 0}</span>
                        </div>
                        <div class="graph-node-deps-item">
                            <span><i class="fas fa-arrow-down"></i> Used by:</span>
                            <span class="graph-node-deps-count incoming">${node.dependencies_in || 0}</span>
                        </div>
                    </div>
                    ${node.state_reason ? `<div class="graph-node-reason">${node.state_reason}</div>` : ''}
                    ${details.file_path ? `<div class="graph-node-reason"><i class="fas fa-file"></i> ${details.file_path}${details.line_number ? `:${details.line_number}` : ''}</div>` : ''}
                `;
                
                return nodeElement;
            }
            
            function sortNodes(criteria) {
                currentSort = criteria;
                document.querySelectorAll('.btn').forEach(btn => btn.classList.remove('active'));
                document.getElementById(`sort-${criteria}`).classList.add('active');
                renderGraphNodes();
            }
            
            function filterByState(state) {
                currentStateFilter = currentStateFilter === state ? null : state;
                document.querySelectorAll('.btn').forEach(btn => btn.classList.remove('active'));
                document.getElementById('sort-name').classList.add('active');
                
                if (currentStateFilter) {
                    document.getElementById(`filter-${state}`).classList.add('active');
                }
                
                renderGraphNodes();
            }
            
            function filterNodes(query) {
                currentSearch = query;
                renderGraphNodes();
            }
            
            function resetFilters() {
                currentSearch = '';
                currentStateFilter = null;
                currentSort = 'name';
                
                document.querySelectorAll('.btn').forEach(btn => btn.classList.remove('active'));
                document.getElementById('sort-name').classList.add('active');
                document.getElementById('search-input').value = '';
                document.getElementById('search-clear').classList.remove('visible');
                
                renderGraphNodes();
            }
            
            function updateFilterInfo() {
                const filterInfo = document.getElementById('filter-info');
                const filterTags = document.getElementById('filter-tags');
                
                const activeFilters = [];
                if (currentSearch) activeFilters.push(`Search: "${currentSearch}"`);
                if (currentStateFilter) activeFilters.push(`State: ${currentStateFilter}`);
                if (currentSort !== 'name') activeFilters.push(`Sorted by: ${currentSort}`);
                
                if (activeFilters.length > 0) {
                    filterInfo.style.display = 'flex';
                    filterTags.innerHTML = activeFilters.map(filter => 
                        `<span class="filter-tag">${filter} <span class="remove" onclick="removeFilter('${filter.split(':')[0].trim().toLowerCase()}')"><i class="fas fa-times"></i></span></span>`
                    ).join('');
                } else {
                    filterInfo.style.display = 'none';
                }
            }
            
            function removeFilter(filterType) {
                switch (filterType) {
                    case 'search':
                        clearSearch();
                        break;
                    case 'state':
                        currentStateFilter = null;
                        document.querySelectorAll('.btn').forEach(btn => btn.classList.remove('active'));
                        document.getElementById('sort-name').classList.add('active');
                        break;
                    case 'sorted':
                        currentSort = 'name';
                        document.querySelectorAll('.btn').forEach(btn => btn.classList.remove('active'));
                        document.getElementById('sort-name').classList.add('active');
                        break;
                }
                renderGraphNodes();
            }
            
            // Initialize
            function initialize() {
                initializeStats();
                initializeSearch();
                document.getElementById('sort-name').classList.add('active');
                renderGraphNodes();
            }
            
            // Keyboard shortcuts
            document.addEventListener('keydown', (e) => {
                if (e.key === '/' && !e.ctrlKey && !e.metaKey) {
                    e.preventDefault();
                    document.getElementById('search-input').focus();
                } else if (e.key === 'Escape') {
                    resetFilters();
                }
            });
            
            // Initialize on load
            window.addEventListener('load', initialize);
        </script>
    </body>
    </html>
    """
