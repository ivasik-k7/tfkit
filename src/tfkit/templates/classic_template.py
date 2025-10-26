# templates/classic_template.py
from .base_template import BaseTemplate


class ClassicTemplate(BaseTemplate):
    """Clean, intuitive classic template with graph nodes and enhanced visualization."""

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
        <style>
            {% set colors = {
                'light': {
                    'bg': '#ffffff', 'bg_alt': '#f8f9fa', 'text': '#212529', 'text_muted': '#6c757d',
                    'border': '#dee2e6', 'accent': '#0d6efd', 'success': '#198754', 'warning': '#ffc107',
                    'danger': '#dc3545', 'info': '#0dcaf0', 'purple': '#6610f2'
                },
                'dark': {
                    'bg': '#1a1d29', 'bg_alt': '#252837', 'text': '#e4e6eb', 'text_muted': '#9ca3af',
                    'border': '#3a3f52', 'accent': '#3b82f6', 'success': '#10b981', 'warning': '#f59e0b',
                    'danger': '#ef4444', 'info': '#06b6d4', 'purple': '#8b5cf6'
                },
                'cyber': {
                    'bg': '#000000', 'bg_alt': '#0a0a0a', 'text': '#00ffff', 'text_muted': '#00cccc',
                    'border': '#00ffff', 'accent': '#ff00ff', 'success': '#00ff00', 'warning': '#ffff00',
                    'danger': '#ff0000', 'info': '#00ffff', 'purple': '#ff00ff'
                },
                'nord': {
                    'bg': '#2e3440', 'bg_alt': '#3b4252', 'text': '#eceff4', 'text_muted': '#d8dee9',
                    'border': '#4c566a', 'accent': '#88c0d0', 'success': '#a3be8c', 'warning': '#ebcb8b',
                    'danger': '#bf616a', 'info': '#5e81ac', 'purple': '#b48ead'
                }
            }[theme] %}
            
            * { margin: 0; padding: 0; box-sizing: border-box; }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                background: {{ colors.bg }};
                color: {{ colors.text }};
                line-height: 1.6;
            }
            
            .container {
                max-width: 1600px;
                margin: 0 auto;
                padding: 20px;
            }
            
            .header {
                background: {{ colors.bg_alt }};
                padding: 24px 28px;
                border-radius: 8px;
                margin-bottom: 24px;
                border: 1px solid {{ colors.border }};
            }
            
            .header h1 {
                color: {{ colors.accent }};
                font-size: 1.75em;
                font-weight: 600;
                margin-bottom: 6px;
            }
            
            .header .meta {
                color: {{ colors.text_muted }};
                font-size: 0.875em;
            }
            
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 16px;
                margin-bottom: 24px;
            }
            
            .stat-card {
                background: {{ colors.bg_alt }};
                padding: 20px;
                border-radius: 8px;
                border: 1px solid {{ colors.border }};
                text-align: center;
            }
            
            .stat-value {
                font-size: 2em;
                font-weight: 700;
                color: {{ colors.accent }};
                line-height: 1;
                margin-bottom: 8px;
            }
            
            .stat-label {
                font-size: 0.85em;
                color: {{ colors.text_muted }};
                text-transform: uppercase;
                letter-spacing: 0.5px;
                font-weight: 500;
            }
            
            .state-indicators {
                display: flex;
                gap: 8px;
                margin-top: 8px;
                flex-wrap: wrap;
                justify-content: center;
            }
            
            .state-indicator {
                font-size: 0.7em;
                padding: 2px 6px;
                border-radius: 4px;
                font-weight: 600;
            }
            
            .state-healthy { background: {{ colors.success }}; color: white; }
            .state-unused { background: {{ colors.danger }}; color: white; }
            .state-external { background: {{ colors.info }}; color: white; }
            .state-leaf { background: {{ colors.success }}20; color: {{ colors.success }}; border: 1px solid {{ colors.success }}; }
            .state-orphan { background: {{ colors.warning }}20; color: {{ colors.warning }}; border: 1px solid {{ colors.warning }}; }
            .state-warning { background: {{ colors.warning }}; color: {{ colors.bg }}; }
            
            .main-panel {
                background: {{ colors.bg_alt }};
                border: 1px solid {{ colors.border }};
                border-radius: 8px;
                overflow: hidden;
                margin-bottom: 24px;
            }
            
            .panel-header {
                padding: 16px 20px;
                border-bottom: 1px solid {{ colors.border }};
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
                gap: 12px;
            }
            
            .panel-title {
                font-size: 1.125em;
                font-weight: 600;
                color: {{ colors.text }};
            }
            
            .controls {
                display: flex;
                gap: 8px;
                flex-wrap: wrap;
            }
            
            .btn {
                padding: 8px 16px;
                border: 1px solid {{ colors.border }};
                background: {{ colors.bg }};
                color: {{ colors.text }};
                border-radius: 6px;
                font-size: 0.875em;
                cursor: pointer;
                transition: all 0.2s;
                display: flex;
                align-items: center;
                gap: 6px;
                font-weight: 500;
            }
            
            .btn:hover {
                background: {{ colors.accent }};
                border-color: {{ colors.accent }};
                color: {{ colors.bg }};
            }
            
            .btn.active {
                background: {{ colors.accent }};
                border-color: {{ colors.accent }};
                color: {{ colors.bg }};
            }
            
            .btn-warning {
                background: {{ colors.warning }};
                border-color: {{ colors.warning }};
                color: {{ colors.bg }};
            }
            
            .btn-warning:hover {
                background: {{ colors.danger }};
                border-color: {{ colors.danger }};
            }
            
            .search-box {
                width: 100%;
                padding: 12px 16px;
                border: 1px solid {{ colors.border }};
                background: {{ colors.bg }};
                color: {{ colors.text }};
                border-radius: 8px;
                font-size: 0.9em;
                margin: 16px 20px;
                max-width: calc(100% - 40px);
            }
            
            .search-box:focus {
                outline: none;
                border-color: {{ colors.accent }};
                box-shadow: 0 0 0 2px {{ colors.accent }}20;
            }
            
            .search-box::placeholder {
                color: {{ colors.text_muted }};
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
                background: {{ colors.bg }};
            }
            
            .graph-container::-webkit-scrollbar-thumb {
                background: {{ colors.border }};
                border-radius: 4px;
            }
            
            .graph-container::-webkit-scrollbar-thumb:hover {
                background: {{ colors.text_muted }};
            }
            
            /* Graph Nodes Styles */
            .graph-nodes {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
                gap: 16px;
            }
            
            .graph-node {
                background: {{ colors.bg }};
                border: 1px solid {{ colors.border }};
                border-radius: 12px;
                padding: 20px;
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
            }
            
            .graph-node:hover {
                border-color: {{ colors.accent }};
                transform: translateY(-4px);
                box-shadow: 0 8px 25px rgba(0,0,0,0.15);
            }
            
            /* Node states */
            .node-unused { 
                border-left: 6px solid {{ colors.danger }};
                background: linear-gradient(135deg, {{ colors.bg }} 0%, {{ colors.danger }}08 100%);
            }
            
            .node-external { 
                border-left: 6px solid {{ colors.info }};
                background: linear-gradient(135deg, {{ colors.bg }} 0%, {{ colors.info }}08 100%);
            }
            
            .node-leaf { 
                border-left: 6px solid {{ colors.success }};
                background: linear-gradient(135deg, {{ colors.bg }} 0%, {{ colors.success }}08 100%);
            }
            
            .node-orphan { 
                border-left: 6px solid {{ colors.warning }};
                background: linear-gradient(135deg, {{ colors.bg }} 0%, {{ colors.warning }}08 100%);
            }
            
            .node-warning { 
                border-left: 6px solid {{ colors.warning }};
                background: linear-gradient(135deg, {{ colors.bg }} 0%, {{ colors.warning }}08 100%);
            }
            
            .node-healthy { 
                border-left: 6px solid {{ colors.success }};
            }
            
            .graph-node-header {
                display: flex;
                align-items: flex-start;
                margin-bottom: 12px;
                gap: 12px;
            }
            
            .graph-node-icon {
                width: 40px;
                height: 40px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 8px;
                background: {{ colors.bg_alt }};
                flex-shrink: 0;
                font-size: 1.2em;
                color: {{ colors.accent }};
            }
            
            .graph-node-title-container {
                flex: 1;
                min-width: 0;
            }
            
            .graph-node-title {
                font-weight: 600;
                font-size: 1.1em;
                margin-bottom: 4px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            
            .graph-node-type {
                color: {{ colors.text_muted }};
                font-size: 0.85em;
                font-weight: 500;
                margin-bottom: 4px;
            }
            
            .graph-node-state {
                font-size: 0.8em;
                font-weight: 600;
                padding: 2px 8px;
                border-radius: 4px;
                display: inline-block;
            }
            
            .graph-node-badges {
                display: flex;
                gap: 6px;
                flex-wrap: wrap;
                margin-top: 8px;
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
                color: {{ colors.bg }};
            }
            
            .graph-node-badge.danger {
                background: {{ colors.danger }};
                color: white;
            }
            
            .graph-node-dependencies {
                display: flex;
                gap: 16px;
                margin-top: 12px;
                padding-top: 12px;
                border-top: 1px solid {{ colors.border }};
            }
            
            .graph-node-deps-item {
                display: flex;
                align-items: center;
                gap: 6px;
                font-size: 0.85em;
                color: {{ colors.text_muted }};
            }
            
            .graph-node-deps-count {
                background: {{ colors.info }};
                color: white;
                border-radius: 12px;
                min-width: 20px;
                height: 20px;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                font-size: 0.75em;
                font-weight: 600;
            }
            
            .graph-node-deps-count.outgoing {
                background: {{ colors.success }};
            }
            
            .graph-node-deps-count.incoming {
                background: {{ colors.purple }};
            }
            
            .graph-node-reason {
                font-size: 0.8em;
                color: {{ colors.text_muted }};
                font-style: italic;
                margin-top: 8px;
            }
            
            .empty-state {
                padding: 60px 20px;
                text-align: center;
                color: {{ colors.text_muted }};
            }
            
            .empty-state-icon {
                font-size: 3em;
                margin-bottom: 16px;
                opacity: 0.5;
            }
            
            .footer {
                margin-top: 24px;
                padding: 16px;
                text-align: center;
                color: {{ colors.text_muted }};
                font-size: 0.875em;
            }
            
            .filter-info {
                background: {{ colors.bg_alt }};
                border: 1px solid {{ colors.border }};
                border-radius: 8px;
                padding: 12px 16px;
                margin-bottom: 16px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
                gap: 12px;
            }
            
            .filter-tags {
                display: flex;
                gap: 8px;
                flex-wrap: wrap;
            }
            
            .filter-tag {
                background: {{ colors.accent }};
                color: white;
                padding: 4px 8px;
                border-radius: 12px;
                font-size: 0.8em;
                font-weight: 500;
            }
            
            .legend {
                display: flex;
                gap: 16px;
                flex-wrap: wrap;
                margin-bottom: 16px;
                padding: 12px 16px;
                background: {{ colors.bg_alt }};
                border-radius: 8px;
                border: 1px solid {{ colors.border }};
            }
            
            .legend-item {
                display: flex;
                align-items: center;
                gap: 6px;
                font-size: 0.8em;
                color: {{ colors.text_muted }};
            }
            
            .legend-color {
                width: 12px;
                height: 12px;
                border-radius: 2px;
            }
            
            @media (max-width: 768px) {
                .stats-grid {
                    grid-template-columns: repeat(2, 1fr);
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
                .legend {
                    flex-direction: column;
                    gap: 8px;
                }
            }
            
            @media (max-width: 480px) {
                .stats-grid {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="main-panel">
                <div class="panel-header">
                    <div class="panel-title">Infrastructure Components</div>
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
                
                <div class="filter-info" id="filter-info" style="display: none;">
                    <div>
                        <strong>Active Filters:</strong>
                        <div class="filter-tags" id="filter-tags"></div>
                    </div>
                    <button class="btn" onclick="resetFilters()">
                        <i class="fas fa-times"></i> Clear All
                    </button>
                </div>
                
                <input type="text" class="search-box" placeholder="Search components by name, type, or state..." onkeyup="filterNodes(this.value)" />
                
                <div class="graph-container">
                    <div class="graph-nodes" id="graph-nodes-container"></div>
                </div>
            </div>
            
            <div class="footer">
                TFKIT • Terraform Intelligence & Analysis Suite • Theme: {{ theme }}
            </div>
        </div>
        
        <script>
            const graphData = {{ graph_data|safe }};
            let currentSort = 'name';
            let currentStateFilter = null;
            let currentSearch = '';
            
            // Font Awesome icons for different node types
            const nodeIcons = {
                'resource': 'fas fa-cube',
                'module': 'fas fa-cubes',
                'variable': 'fas fa-code',
                'output': 'fas fa-arrow-right',
                'data': 'fas fa-database',
                'provider': 'fas fa-cog'
            };
            
            // State colors and icons
            const stateConfig = {
                'healthy': { class: 'node-healthy', icon: 'fas fa-check-circle', color: '{{ colors.success }}' },
                'unused': { class: 'node-unused', icon: 'fas fa-ban', color: '{{ colors.danger }}' },
                'external': { class: 'node-external', icon: 'fas fa-external-link-alt', color: '{{ colors.info }}' },
                'leaf': { class: 'node-leaf', icon: 'fas fa-leaf', color: '{{ colors.success }}' },
                'orphan': { class: 'node-orphan', icon: 'fas fa-unlink', color: '{{ colors.warning }}' },
                'warning': { class: 'node-warning', icon: 'fas fa-exclamation-triangle', color: '{{ colors.warning }}' }
            };

            function renderGraphNodes() {
                const container = document.getElementById('graph-nodes-container');
                container.innerHTML = '';
                
                let nodesToShow = graphData.nodes.filter(node => {
                    // Filter by state if enabled
                    if (currentStateFilter && node.state !== currentStateFilter) {
                        return false;
                    }
                    
                    // Filter by search term
                    if (currentSearch) {
                        const searchTerm = currentSearch.toLowerCase();
                        const matchesName = node.label.toLowerCase().includes(searchTerm);
                        const matchesType = node.type.toLowerCase().includes(searchTerm) || 
                                        node.subtype.toLowerCase().includes(searchTerm);
                        const matchesState = node.state.toLowerCase().includes(searchTerm) ||
                                        node.state_reason.toLowerCase().includes(searchTerm);
                        return matchesName || matchesType || matchesState;
                    }
                    
                    return true;
                });
                
                // Sort nodes
                nodesToShow.sort((a, b) => {
                    switch (currentSort) {
                        case 'name':
                            return a.label.localeCompare(b.label);
                        case 'type':
                            return a.type.localeCompare(b.type) || a.subtype.localeCompare(b.subtype);
                        case 'dependencies':
                            const aDeps = a.dependencies_out + a.dependencies_in;
                            const bDeps = b.dependencies_out + b.dependencies_in;
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
                        </div>
                    `;
                    return;
                }
                
                nodesToShow.forEach(node => {
                    const nodeElement = createNodeElement(node);
                    container.appendChild(nodeElement);
                });
                
                updateFilterInfo();
            }
            
            function createNodeElement(node) {
                const nodeElement = document.createElement('div');
                const state = stateConfig[node.state] || stateConfig.healthy;
                
                nodeElement.className = `graph-node ${state.class}`;
                
                // Create badges based on node status
                const badges = [];
                if (node.dependencies_out === 0 && node.dependencies_in > 0) {
                    badges.push('<span class="graph-node-badge"><i class="fas fa-leaf"></i> LEAF</span>');
                }
                if (node.dependencies_out > 5 || node.dependencies_in > 5) {
                    badges.push('<span class="graph-node-badge"><i class="fas fa-hubspot"></i> HUB</span>');
                }
                
                nodeElement.innerHTML = `
                    <div class="graph-node-header">
                        <div class="graph-node-icon">
                            <i class="${nodeIcons[node.type] || 'fas fa-cube'}"></i>
                        </div>
                        <div class="graph-node-title-container">
                            <div class="graph-node-title" title="${node.label}">${node.label}</div>
                            <div class="graph-node-type">${node.type} • ${node.subtype}</div>
                            <span class="graph-node-state" style="background: ${state.color}; color: white;">
                                <i class="${state.icon}"></i> ${node.state.toUpperCase()}
                            </span>
                            ${badges.length > 0 ? `<div class="graph-node-badges">${badges.join('')}</div>` : ''}
                        </div>
                    </div>
                    <div class="graph-node-dependencies">
                        <div class="graph-node-deps-item">
                            <span><i class="fas fa-arrow-up"></i> Uses:</span>
                            <span class="graph-node-deps-count outgoing">${node.dependencies_out}</span>
                        </div>
                        <div class="graph-node-deps-item">
                            <span><i class="fas fa-arrow-down"></i> Used by:</span>
                            <span class="graph-node-deps-count incoming">${node.dependencies_in}</span>
                        </div>
                    </div>
                    <div class="graph-node-reason">${node.state_reason}</div>
                `;
                
                return nodeElement;
            }
            
            function sortNodes(criteria) {
                currentSort = criteria;
                
                // Update active button states
                document.querySelectorAll('.btn').forEach(btn => btn.classList.remove('active'));
                document.getElementById(`sort-${criteria}`).classList.add('active');
                
                renderGraphNodes();
            }
            
            function filterByState(state) {
                currentStateFilter = currentStateFilter === state ? null : state;
                
                // Update UI
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
                
                // Reset UI states
                document.querySelectorAll('.btn').forEach(btn => btn.classList.remove('active'));
                document.getElementById('sort-name').classList.add('active');
                document.querySelector('.search-box').value = '';
                
                renderGraphNodes();
            }
            
            function updateFilterInfo() {
                const filterInfo = document.getElementById('filter-info');
                const filterTags = document.getElementById('filter-tags');
                
                const activeFilters = [];
                
                if (currentSearch) {
                    activeFilters.push(`Search: "${currentSearch}"`);
                }
                
                if (currentStateFilter) {
                    activeFilters.push(`State: ${currentStateFilter}`);
                }
                
                if (currentSort !== 'name') {
                    activeFilters.push(`Sorted by: ${currentSort}`);
                }
                
                if (activeFilters.length > 0) {
                    filterInfo.style.display = 'flex';
                    filterTags.innerHTML = activeFilters.map(filter => 
                        `<span class="filter-tag">${filter}</span>`
                    ).join('');
                } else {
                    filterInfo.style.display = 'none';
                }
            }
            
            // Initialize
            document.getElementById('sort-name').classList.add('active');
            renderGraphNodes();
            
            // Keyboard shortcuts
            document.addEventListener('keydown', (e) => {
                if (e.key === '/' && !e.ctrlKey && !e.metaKey) {
                    e.preventDefault();
                    document.querySelector('.search-box').focus();
                } else if (e.key === 'Escape') {
                    resetFilters();
                } else if (e.key === '1' && (e.ctrlKey || e.metaKey)) {
                    e.preventDefault();
                    filterByState('unused');
                } else if (e.key === '2' && (e.ctrlKey || e.metaKey)) {
                    e.preventDefault();
                    filterByState('warning');
                }
            });
        </script>
    </body>
    </html>
    """
