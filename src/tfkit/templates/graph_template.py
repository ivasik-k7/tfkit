# templates/graph_template.py
from .base_template import BaseTemplate


class GraphTemplate(BaseTemplate):
    """Graph-focused template with advanced D3 visualization."""

    @property
    def template_string(self) -> str:
        return """
<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{ title }} - Graph View</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;700;900&family=Exo+2:wght@300;400;500;600&display=swap" rel="stylesheet">
        <style>
            {% set colors = theme_colors %}
            
            * { margin: 0; padding: 0; box-sizing: border-box; }
            
            body { 
                font-family: 'Exo 2', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif; 
                background: {{ colors.bg_primary }}; 
                color: {{ colors.text_primary }}; 
                overflow: hidden; 
            }
            
            #graph-container { 
                width: 100vw; 
                height: 100vh; 
                position: relative; 
                background: {{ colors.bg_primary }};
            }

            /* --- ENHANCED GRID BACKGROUND --- */
            #grid-pattern {
                fill: url(#grid);
            }

            /* --- WATERMARK --- */
            #watermark {
                position: absolute;
                bottom: 10px;
                left: 20px;
                font-size: 0.7em;
                color: {{ colors.text_secondary }}80;
                user-select: none;
                z-index: 1000;
                font-family: 'Exo 2', sans-serif;
            }

            /* --- NEXUS-STYLE HUD PANEL --- */
            .nexus-hud {
                position: absolute; 
                top: 20px; 
                left: 20px; 
                background: linear-gradient(135deg, {{ colors.bg_secondary }}e6 0%, {{ colors.bg_secondary }}cc 100%);
                border: 1px solid {{ colors.accent }}60;
                border-radius: 16px; 
                padding: 24px 20px;
                backdrop-filter: blur(15px) saturate(180%);
                box-shadow: 
                    0 8px 32px rgba(0,0,0,0.4),
                    0 0 0 1px {{ colors.accent }}20,
                    inset 0 1px 0 {{ colors.accent }}20;
                z-index: 1000;
                min-width: 260px;
                max-height: calc(100vh - 40px);
                overflow-y: auto;
                font-family: 'Exo 2', sans-serif;
            }

            .nexus-header {
                display: flex;
                align-items: center;
                gap: 12px;
                margin-bottom: 20px;
                padding-bottom: 16px;
                border-bottom: 1px solid {{ colors.accent }}30;
                position: relative;
            }

            .nexus-header::after {
                content: '';
                position: absolute;
                bottom: -1px;
                left: 0;
                width: 40%;
                height: 2px;
                background: linear-gradient(90deg, {{ colors.accent }}, transparent);
            }

            .nexus-icon {
                width: 40px;
                height: 40px;
                background: linear-gradient(135deg, {{ colors.accent }}, {{ colors.accent_secondary }});
                border-radius: 10px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.2em;
                color: {{ colors.bg_primary }};
                box-shadow: 0 4px 12px {{ colors.accent }}40;
            }

            .nexus-title {
                color: {{ colors.text_primary }}; 
                font-size: 1.3em; 
                font-weight: 700;
                font-family: 'Orbitron', sans-serif;
                letter-spacing: 0.5px;
            }
            
            .nexus-stats {
                display: flex;
                flex-direction: column;
                gap: 12px;
            }
            
            .nexus-stat { 
                display: flex; 
                justify-content: space-between; 
                align-items: center;
                font-size: 0.9em; 
                padding: 8px 12px;
                background: {{ colors.bg_primary }}15;
                border-radius: 8px;
                border: 1px solid {{ colors.border }}30;
                transition: all 0.3s ease;
            }
            
            .nexus-stat:hover {
                background: {{ colors.bg_primary }}25;
                border-color: {{ colors.accent }}40;
                transform: translateX(4px);
            }
            
            .nexus-stat-label { 
                color: {{ colors.text_secondary }}; 
                font-weight: 500;
            }
            
            .nexus-stat-value { 
                color: {{ colors.text_primary }}; 
                font-weight: 700;
                font-size: 1.1em;
                font-family: 'Orbitron', sans-serif;
            }
            
            .nexus-indicators {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 8px;
                margin-top: 20px;
                padding-top: 20px;
                border-top: 1px solid {{ colors.accent }}30;
            }
            
            .nexus-indicator {
                font-size: 0.75em;
                padding: 6px 10px;
                border-radius: 8px;
                font-weight: 600;
                text-align: center;
                cursor: pointer;
                transition: all 0.3s ease;
                border: 1px solid transparent;
                font-family: 'Exo 2', sans-serif;
            }
            
            .nexus-indicator:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            }
            
            /* Enhanced state styles for all states */
            .state-external_data { 
                background: linear-gradient(135deg, #a855f720, #a855f710); 
                color: #a855f7; 
                border-color: #a855f740; 
            }
            .state-integrated { 
                background: linear-gradient(135deg, #84cc1620, #84cc1610); 
                color: #84cc16; 
                border-color: #84cc1640; 
            }
            .state-active { 
                background: linear-gradient(135deg, #22c55e20, #22c55e10); 
                color: #22c55e; 
                border-color: #22c55e40; 
            }
            .state-input { 
                background: linear-gradient(135deg, #3b82f620, #3b82f610); 
                color: #3b82f6; 
                border-color: #3b82f640; 
            }
            .state-orphaned { 
                background: linear-gradient(135deg, #fb923c20, #fb923c10); 
                color: #fb923c; 
                border-color: #fb923c40; 
            }
            .state-configuration { 
                background: linear-gradient(135deg, #8b5cf620, #8b5cf610); 
                color: #8b5cf6; 
                border-color: #8b5cf640; 
            }
            .state-unused { 
                background: linear-gradient(135deg, #f59e0b20, #f59e0b10); 
                color: #f59e0b; 
                border-color: #f59e0b40; 
            }
            .state-incomplete { 
                background: linear-gradient(135deg, #ef444420, #ef444410); 
                color: #ef4444; 
                border-color: #ef444440; 
            }
            
            .controls {
                position: absolute; 
                bottom: 20px; 
                left: 50%; 
                transform: translateX(-50%);
                background: {{ colors.bg_secondary }}d0;
                border: 1px solid {{ colors.border }}; 
                border-radius: 12px;
                padding: 12px 20px; 
                display: flex; 
                gap: 8px; 
                backdrop-filter: blur(10px);
                box-shadow: 0 8px 32px rgba(0,0,0,0.3);
                z-index: 1000;
            }
            
            .control-btn {
                background: {{ colors.bg_primary }}; 
                border: 1px solid {{ colors.border }}; 
                color: {{ colors.text_primary }};
                padding: 8px 16px; 
                border-radius: 8px; 
                cursor: pointer; 
                font-size: 0.85em;
                transition: all 0.2s ease;
                display: flex;
                align-items: center;
                gap: 6px;
                font-weight: 500;
            }
            
            .control-btn:hover { 
                background: {{ colors.accent }}; 
                border-color: {{ colors.accent }}; 
                color: {{ colors.bg_primary }}; 
                transform: translateY(-1px);
            }
            
            .control-btn:active {
                transform: translateY(0);
            }
            
            .scale-controls {
                position: absolute;
                bottom: 20px;
                right: 20px;
                background: {{ colors.bg_secondary }}d0;
                border: 1px solid {{ colors.border }};
                border-radius: 12px;
                padding: 12px;
                display: flex;
                flex-direction: column;
                gap: 8px;
                backdrop-filter: blur(10px);
                box-shadow: 0 8px 32px rgba(0,0,0,0.3);
                z-index: 1000;
            }
            
            .scale-btn {
                background: {{ colors.bg_primary }};
                border: 1px solid {{ colors.border }};
                color: {{ colors.text_primary }};
                width: 36px;
                height: 36px;
                border-radius: 8px;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.1em;
                transition: all 0.2s ease;
            }
            
            .scale-btn:hover {
                background: {{ colors.accent }};
                border-color: {{ colors.accent }};
                color: {{ colors.bg_primary }};
                transform: translateY(-1px);
            }
            
            .scale-btn:active {
                transform: translateY(0);
            }
            
            /* --- ENHANCED LEGEND WITH INTERACTIVE FEATURES --- */
            .legend {
                position: absolute; 
                top: 20px; 
                right: 20px; 
                background: {{ colors.bg_secondary }}d0;
                border: 1px solid {{ colors.border }}; 
                border-radius: 12px; 
                padding: 16px; 
                backdrop-filter: blur(10px);
                box-shadow: 0 8px 32px rgba(0,0,0,0.3);
                z-index: 1000;
                min-width: 200px;
                max-height: calc(100vh - 40px);
                overflow-y: auto;
                transition: all 0.3s ease;
            }
            
            .legend-title { 
                color: {{ colors.text_primary }}; 
                margin-bottom: 12px; 
                font-size: 0.9em; 
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 8px;
                cursor: pointer;
                user-select: none;
            }
            
            .legend-title:hover {
                color: {{ colors.accent }};
            }
            
            .legend-section {
                margin-bottom: 12px;
            }
            
            .legend-section-title {
                font-size: 0.8em;
                color: {{ colors.text_secondary }};
                margin-bottom: 8px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                display: flex;
                align-items: center;
                gap: 6px;
                cursor: pointer;
                user-select: none;
            }
            
            .legend-section-title:hover {
                color: {{ colors.text_primary }};
            }
            
            .legend-section-content {
                display: flex;
                flex-direction: column;
                gap: 6px;
            }
            
            .legend-item { 
                display: flex; 
                align-items: center; 
                gap: 8px; 
                margin: 4px 0; 
                font-size: 0.8em; 
                cursor: pointer;
                padding: 4px 6px;
                border-radius: 6px;
                transition: all 0.2s ease;
            }
            
            .legend-item:hover {
                background: {{ colors.bg_primary }}20;
                transform: translateX(4px);
            }
            
            .legend-dot { 
                width: 10px; 
                height: 10px; 
                border-radius: 50%; 
                flex-shrink: 0;
                transition: all 0.2s ease;
            }
            
            .legend-item:hover .legend-dot {
                transform: scale(1.2);
            }
            
            .legend-count {
                margin-left: auto;
                font-size: 0.75em;
                color: {{ colors.text_secondary }};
                background: {{ colors.bg_primary }}30;
                padding: 2px 6px;
                border-radius: 10px;
                min-width: 20px;
                text-align: center;
            }
            
            .node { 
                cursor: pointer; 
            }
            
            .node circle { 
                stroke-width: 2px; 
                transition: all 0.3s ease;
            }
            
            .node text { 
                font-size: 10px; 
                fill: {{ colors.text_primary }}; 
                text-shadow: 0 1px 3px {{ colors.bg_primary }};
                pointer-events: none; 
                font-weight: 500;
                transition: all 0.3s ease;
            }

            .node-icon {
                font-family: "Font Awesome 6 Free";
                font-weight: 900;
                font-size: 10px;
                fill: {{ colors.bg_primary }};
                pointer-events: none;
                text-anchor: middle;
                dominant-baseline: central;
                text-rendering: optimizeLegibility;
            }
            
            .node text.node-icon {
                font-family: "Font Awesome 6 Free", sans-serif;
                font-weight: 900;
                fill: {{ colors.bg_primary }}; 
            }
            
            .node:hover circle { 
                stroke-width: 3px; 
                filter: drop-shadow(0 0 8px currentColor);
            }
            
            .node:hover text {
                font-weight: 600;
            }
            
            .link { 
                stroke: {{ colors.text_secondary }}; 
                stroke-opacity: 0.3; 
                stroke-width: 1.5; 
                transition: all 0.3s ease;
            }
            
            .link-arrow { 
                fill: {{ colors.text_secondary }}; 
                opacity: 0.5; 
            }
            
            .particle {
                fill: {{ colors.accent }}; 
                opacity: 0.9; 
                transition: opacity 0.1s;
            }
            
            /* --- ENHANCED TOOLTIP - MULTI-THEME SUPPORT --- */
            .node-tooltip {
                position: absolute;
                background: linear-gradient(135deg, {{ colors.bg_secondary }}ee 0%, {{ colors.bg_tertiary }}dd 100%);
                border: 1px solid {{ colors.accent }}60;
                backdrop-filter: blur(12px) saturate(180%);
                box-shadow: 
                    0 0 25px {{ colors.accent }}20,
                    0 8px 40px rgba(0,0,0,0.3),
                    inset 0 1px 0 {{ colors.accent }}15;
                font-family: 'Exo 2', monospace;
                border-radius: 12px;
                padding: 16px;
                font-size: 0.85em;
                pointer-events: none;
                opacity: 0;
                transition: opacity 0.3s ease, transform 0.3s ease;
                z-index: 1001;
                max-width: 320px;
                transform: translateY(10px);
            }

            .node-tooltip.show {
                opacity: 1;
                transform: translateY(0);
            }
            
            .node-info {
                display: flex;
                flex-direction: column;
                gap: 6px;
            }
            
            .node-info-title {
                font-weight: 700;
                color: {{ colors.accent }};
                margin-bottom: 8px;
                font-size: 1.1em;
                border-bottom: 1px solid {{ colors.accent }}30;
                padding-bottom: 6px;
                font-family: 'Orbitron', sans-serif;
                letter-spacing: 0.5px;
            }
                
            .node-info-dep {
                font-size: 0.8em;
                color: {{ colors.text_secondary }};
                display: flex;
                align-items: center;
                gap: 4px;
            }
                
            .node-state {
                font-size: 0.75em;
                padding: 4px 8px;
                border-radius: 6px;
                margin-top: 8px;
                display: inline-block;
                width: fit-content;
                font-weight: 600;
                border: 1px solid;
                background: {{ colors.bg_primary }}20;
            }

            /* Theme-specific state colors in tooltip */
            .node-state.external_data { color: #a855f7; border-color: #a855f740; background: #a855f715; }
            .node-state.integrated { color: #84cc16; border-color: #84cc1640; background: #84cc1615; }
            .node-state.active { color: #22c55e; border-color: #22c55e40; background: #22c55e15; }
            .node-state.input { color: #3b82f6; border-color: #3b82f640; background: #3b82f615; }
            .node-state.orphaned { color: #fb923c; border-color: #fb923c40; background: #fb923c15; }
            .node-state.configuration { color: #8b5cf6; border-color: #8b5cf640; background: #8b5cf615; }
            .node-state.unused { color: #f59e0b; border-color: #f59e0b40; background: #f59e0b15; }
            .node-state.incomplete { color: #ef4444; border-color: #ef444440; background: #ef444415; }
                
            .tooltip-stat {
                display: flex;
                justify-content: space-between;
                gap: 15px;
                margin-top: 8px;
                padding-top: 8px;
                border-top: 1px solid {{ colors.border }}40;
                font-size: 0.9em;
            }
            
            .tooltip-stat span:first-child {
                color: {{ colors.text_secondary }};
                font-weight: 500;
            }
            
            .tooltip-stat span:last-child {
                color: {{ colors.text_primary }};
                font-weight: 600;
            }

            .tooltip-section {
                margin-top: 10px;
                padding-top: 10px;
                border-top: 1px solid {{ colors.border }}30;
            }

            .tooltip-label {
                font-size: 0.75em;
                color: {{ colors.text_secondary }};
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 4px;
            }

            .tooltip-value {
                font-size: 0.85em;
                color: {{ colors.text_primary }};
                font-family: 'Exo 2', monospace;
            }

            /* Performance optimizations */
            .performance-optimized {
                transform: translate3d(0, 0, 0);
                backface-visibility: hidden;
                perspective: 1000px;
            }

            /* Responsive design */
            @media (max-width: 768px) {
                .nexus-hud, .legend {
                    min-width: 200px;
                    padding: 16px;
                }
                
                .controls {
                    flex-wrap: wrap;
                    justify-content: center;
                }
                
                .node-tooltip {
                    max-width: 280px;
                    font-size: 0.8em;
                    padding: 12px;
                }
            }
        </style>
    </head>
    <body>
        <div id="graph-container"></div>
        
        <div id="watermark">
            tfkit (v{{ tfkit_version | default('0.0.0') }}) | <a href="https://github.com/ivasik-k7/tfkit" target="_blank" style="color: {{ colors.text_secondary }};">tfkit.com</a>
        </div>

        <!-- Nexus-style HUD Panel -->
        <div class="nexus-hud">
            <div class="nexus-header">
                <div class="nexus-icon">
                    <i class="fas fa-project-diagram"></i>
                </div>
                <div class="nexus-title">DEPENDENCIES</div>
            </div>
            <div class="nexus-stats">
                <div class="nexus-stat">
                    <span class="nexus-stat-label">NODES</span>
                    <span class="nexus-stat-value" id="node-count">0</span>
                </div>
                <div class="nexus-stat">
                    <span class="nexus-stat-label">DEPENDENCIES</span>
                    <span class="nexus-stat-value" id="edge-count">0</span>
                </div>
                <div class="nexus-stat">
                    <span class="nexus-stat-label">COMPONENTS</span>
                    <span class="nexus-stat-value" id="component-count">0</span>
                </div>
            </div>
            <div class="nexus-indicators" id="state-indicators">
                <!-- State indicators will be populated here -->
            </div>
        </div>
        
        <!-- Enhanced Legend with Interactive Features -->
        <div class="legend">
            <div class="legend-title" onclick="toggleLegendSection('types')">
                <i class="fas fa-layer-group"></i> Resource Types <i class="fas fa-chevron-down" id="types-chevron"></i>
            </div>
            <div class="legend-section" id="types-section">
                <div class="legend-section-content">
                    <div class="legend-item" onclick="filterByType('resource')">
                        <div class="legend-dot" style="background: {{ colors.success }};"></div>
                        <span>Resources</span>
                        <span class="legend-count" id="resource-count">0</span>
                    </div>
                    <div class="legend-item" onclick="filterByType('module')">
                        <div class="legend-dot" style="background: {{ colors.accent_secondary }};"></div>
                        <span>Modules</span>
                        <span class="legend-count" id="module-count">0</span>
                    </div>
                    <div class="legend-item" onclick="filterByType('variable')">
                        <div class="legend-dot" style="background: {{ colors.warning }};"></div>
                        <span>Variables</span>
                        <span class="legend-count" id="variable-count">0</span>
                    </div>
                    <div class="legend-item" onclick="filterByType('output')">
                        <div class="legend-dot" style="background: {{ colors.accent }};"></div>
                        <span>Outputs</span>
                        <span class="legend-count" id="output-count">0</span>
                    </div>
                    <div class="legend-item" onclick="filterByType('data')">
                        <div class="legend-dot" style="background: {{ colors.danger }};"></div>
                        <span>Data Sources</span>
                        <span class="legend-count" id="data-count">0</span>
                    </div>
                    <div class="legend-item" onclick="filterByType('provider')">
                        <div class="legend-dot" style="background: {{ colors.info }};"></div>
                        <span>Providers</span>
                        <span class="legend-count" id="provider-count">0</span>
                    </div>
                    <div class="legend-item" onclick="filterByType('local')">
                        <div class="legend-dot" style="background: {{ colors.info }};"></div>
                        <span>Locals</span>
                        <span class="legend-count" id="local-count">0</span>
                    </div>
                </div>
            </div>
            
            <div class="legend-section">
                <div class="legend-section-title" onclick="toggleLegendSection('states')">
                    <i class="fas fa-tachometer-alt"></i> Node States <i class="fas fa-chevron-down" id="states-chevron"></i>
                </div>
                <div class="legend-section-content" id="states-section">
                    <!-- State legend items will be populated dynamically -->
                </div>
            </div>
        </div>
        
        <div class="controls">
            <button class="control-btn" onclick="resetView()"><i class="fas fa-crosshairs"></i> Reset</button>
            <button class="control-btn" onclick="togglePhysics()" id="physics-btn"><i class="fas fa-bolt"></i> Physics</button>
            <button class="control-btn" onclick="centerGraph()"><i class="fas fa-bullseye"></i> Center</button>
            <button class="control-btn" onclick="toggleAnimations()" id="animations-btn"><i class="fas fa-sparkles"></i> Animations</button>
            <button class="control-btn" onclick="clearFilters()"><i class="fas fa-filter"></i> Clear Filters</button>
        </div>
        
        <div class="scale-controls">
            <button class="scale-btn" onclick="zoomIn()"><i class="fas fa-search-plus"></i></button>
            <button class="scale-btn" onclick="zoomOut()"><i class="fas fa-search-minus"></i></button>
            <button class="scale-btn" onclick="resetZoom()"><i class="fas fa-expand-arrows-alt"></i></button>
        </div>
        
        <div class="node-tooltip" id="node-tooltip"></div>
        
        <script>
            // Process the graph data to match expected format
            const rawGraphData = {{ graph_data|safe }};
            
            // Transform nodes to expected format with enhanced data processing
            const graphData = {
                nodes: rawGraphData.nodes.map(node => ({
                    id: node.id,
                    label: node.label,
                    type: node.type,
                    subtype: node.subtype,
                    state: node.state,
                    state_reason: node.state_reason,
                    dependencies_out: node.dependencies_out,
                    dependencies_in: node.dependencies_in,
                    details: node.details || {}
                })),
                edges: rawGraphData.edges.map(edge => ({
                    source: edge.source,
                    target: edge.target,
                    type: edge.type,
                    strength: edge.strength || 0.5
                }))
            };
            
            let simulation, physicsEnabled = true, animationsEnabled = true;
            let currentTransform = d3.zoomIdentity;
            let hoveredNode = null;
            let highlightedNodes = new Set();
            let highlightedEdges = new Set();
            let animationTimer = null;
            let graphG;
            let currentFilters = {
                types: new Set(),
                states: new Set()
            };

            // Enhanced configuration for states from your data
            const config = {
                zoomSpeed: 0.2,
                physics: {
                    charge: {
                        external_data: -250, integrated: -360, active: -380,
                        input: -200, orphaned: -100, configuration: -180,
                        unused: -150, incomplete: -180
                    },
                    link: {
                        external_data: 140, integrated: 110, active: 115,
                        input: 80, orphaned: 80, configuration: 70,
                        unused: 60, incomplete: 70
                    },
                    collision: {
                        base: 8, module: 12, resource: 10, multiplier: 0.8
                    },
                    force: {
                        center: 0.1, unusedAttraction: 0.05, stateGrouping: 0.02
                    }
                },
                animation: {
                    particleInterval: 50,
                    transitionDuration: 300, 
                    hoverGlow: true
                },
                performance: {
                    debounceDelay: 50,
                    maxParticles: 100,
                    throttleRender: true
                }
            };
            
            // Calculate summary statistics
            const summary = {
                total_nodes: graphData.nodes.length,
                total_edges: graphData.edges.length,
                type_counts: {},
                state_counts: {}
            };
            
            // Count types and states
            graphData.nodes.forEach(node => {
                summary.type_counts[node.type] = (summary.type_counts[node.type] || 0) + 1;
                summary.state_counts[node.state] = (summary.state_counts[node.state] || 0) + 1;
            });
            
            function buildNodeGraph() {
                const nodeMap = new Map();
                const adjacencyList = new Map();
                
                graphData.nodes.forEach(node => {
                    nodeMap.set(node.id, node);
                    adjacencyList.set(node.id, { in: [], out: [] });
                });
                
                graphData.edges.forEach(edge => {
                    const sourceId = typeof edge.source === 'object' ? edge.source.id : edge.source;
                    const targetId = typeof edge.target === 'object' ? edge.target.id : edge.target;
                    
                    if (adjacencyList.has(sourceId)) {
                        adjacencyList.get(sourceId).out.push(targetId);
                    }
                    if (adjacencyList.has(targetId)) {
                        adjacencyList.get(targetId).in.push(sourceId);
                    }
                });
                
                return { nodeMap, adjacencyList };
            }
            
            const { nodeMap, adjacencyList } = buildNodeGraph();
            
            function calculateConnectedComponents() {
                const visited = new Set();
                let components = 0;
                
                function dfs(nodeId) {
                    const stack = [nodeId];
                    while (stack.length) {
                        const current = stack.pop();
                        if (!visited.has(current)) {
                            visited.add(current);
                            const neighbors = [...(adjacencyList.get(current)?.in || []), ...(adjacencyList.get(current)?.out || [])];
                            neighbors.forEach(neighbor => {
                                if (!visited.has(neighbor)) stack.push(neighbor);
                            });
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
            
            summary.connected_components = calculateConnectedComponents();
            
            // Update HUD statistics
            document.getElementById('node-count').textContent = summary.total_nodes.toLocaleString();
            document.getElementById('edge-count').textContent = summary.total_edges.toLocaleString();
            document.getElementById('component-count').textContent = summary.connected_components.toLocaleString();
            
            // Update type counts in legend
            Object.entries(summary.type_counts).forEach(([type, count]) => {
                const element = document.getElementById(`${type}-count`);
                if (element) element.textContent = count.toLocaleString();
            });
            
            // Update state indicators and legend
            const stateIndicators = document.getElementById('state-indicators');
            const statesSection = document.getElementById('states-section');
            
            Object.entries(summary.state_counts).forEach(([state, count]) => {
                if (count > 0) {
                    // Add to HUD indicators
                    const indicator = document.createElement('div');
                    indicator.className = `nexus-indicator state-${state}`;
                    indicator.textContent = `${state}: ${count}`;
                    indicator.title = `${count} ${state} nodes`;
                    indicator.onclick = () => filterByState(state);
                    stateIndicators.appendChild(indicator);
                    
                    // Add to legend
                    const legendItem = document.createElement('div');
                    legendItem.className = 'legend-item';
                    legendItem.onclick = () => filterByState(state);
                    
                    const stateConfig = getStateConfig(state);
                    legendItem.innerHTML = `
                        <div class="legend-dot" style="background: ${stateConfig.stroke};"></div>
                        <span>${state.replace('_', ' ')}</span>
                        <span class="legend-count">${count}</span>
                    `;
                    statesSection.appendChild(legendItem);
                }
            });

            // Enhanced node configuration with theme colors and ICONS
            const nodeConfig = {
                'resource': { color: '{{ colors.success }}', icon: '\\uf1b3' },
                'module': { color: '{{ colors.accent_secondary }}', icon: '\\uf1b3' },
                'variable': { color: '{{ colors.warning }}', icon: '\\uf121' },
                'output': { color: '{{ colors.accent }}', icon: '\\uf061' },
                'data': { color: '{{ colors.danger }}', icon: '\\uf1c0' },
                'provider': { color: '{{ colors.info }}', icon: '\\uf013' },
                'local': { color: '{{ colors.info }}', icon: '\\uf121' },
                'terraform': { color: '{{ colors.accent }}', icon: '\\uf0e8' }
            };
            
            // Enhanced state-based styling
            function getStateConfig(state) {
                const stateConfigs = {
                    'external_data': { stroke: '#a855f7', glow: '#a855f740' },
                    'integrated': { stroke: '#84cc16', glow: '#84cc1640' },
                    'active': { stroke: '#22c55e', glow: '#22c55e40' },
                    'input': { stroke: '#3b82f6', glow: '#3b82f640' },
                    'orphaned': { stroke: '#fb923c', glow: '#fb923c40' },
                    'configuration': { stroke: '#8b5cf6', glow: '#8b5cf640' },
                    'unused': { stroke: '#f59e0b', glow: '#f59e0b40' },
                    'incomplete': { stroke: '#ef4444', glow: '#ef444440' }
                };
                return stateConfigs[state] || { stroke: '#666', glow: '#6666' };
            }

            // Performance-optimized initialization
            let renderThrottled = false;
            
            function init() {
                const container = document.getElementById('graph-container');
                const width = container.clientWidth, height = container.clientHeight;
                
                // Clear previous SVG
                d3.select('#graph-container svg').remove();
                
                const svg = d3.select('#graph-container').append('svg')
                    .attr('width', width)
                    .attr('height', height)
                    .classed('performance-optimized', true);

                const defs = svg.append('defs');

                // Enhanced grid pattern
                const grid_size = 50;
                defs.append('pattern')
                    .attr('id', 'grid')
                    .attr('width', grid_size)
                    .attr('height', grid_size)
                    .attr('patternUnits', 'userSpaceOnUse')
                    .append('path')
                    .attr('d', `M ${grid_size} 0 L 0 0 0 ${grid_size}`)
                    .attr('fill', 'none')
                    .attr('stroke', '{{ colors.text_secondary }}')
                    .attr('stroke-opacity', 0.1)
                    .attr('stroke-width', 1);

                svg.append('rect')
                    .attr('width', '100%')
                    .attr('height', '100%')
                    .attr('fill', 'url(#grid)');

                // Create arrow markers
                Object.keys(nodeConfig).forEach(type => {
                    defs.append('marker')
                        .attr('id', `arrow-${type}`)
                        .attr('viewBox', '0 -5 10 10')
                        .attr('refX', 18)
                        .attr('refY', 0)
                        .attr('markerWidth', 8)
                        .attr('markerHeight', 8)
                        .attr('orient', 'auto')
                        .append('path')
                        .attr('d', 'M0,-5L10,0L0,5')
                        .attr('class', 'link-arrow')
                        .style('fill', nodeConfig[type].color)
                        .style('opacity', '0.7');
                });

                const g = svg.append('g');
                graphG = g.append('g').classed('performance-optimized', true);

                // Enhanced zoom behavior with performance optimizations
                const zoom = d3.zoom()
                    .scaleExtent([0.05, 8])
                    .wheelDelta(function(event) {
                        const delta = -event.deltaY * (event.deltaMode ? 120 : 1) / 500;
                        return delta * config.zoomSpeed;
                    })
                    .on('zoom', (event) => {
                        currentTransform = event.transform;
                        g.attr('transform', event.transform);
                    });
                    
                svg.call(zoom)
                .call(zoom.transform, d3.zoomIdentity);

                // Initialize enhanced force simulation
                simulation = d3.forceSimulation(graphData.nodes)
                    .force('link', d3.forceLink(graphData.edges)
                        .id(d => d.id)
                        .distance(d => {
                            const source = typeof d.source === 'object' ? d.source : nodeMap.get(d.source);
                            const target = typeof d.target === 'object' ? d.target : nodeMap.get(d.target);
                            const sourceState = source?.state || 'active';
                            const targetState = target?.state || 'active';
                            return Math.min(
                                config.physics.link[sourceState] || config.physics.link.active,
                                config.physics.link[targetState] || config.physics.link.active
                            );
                        })
                        .strength(0.2)
                    )
                    .force('charge', d3.forceManyBody()
                        .strength(d => {
                            const stateStrength = config.physics.charge[d.state] || config.physics.charge.active;
                            const dependencyFactor = 1 + ((d.dependencies_out || 0) + (d.dependencies_in || 0)) * 0.1;
                            return stateStrength * dependencyFactor;
                        })
                        .distanceMax(400)
                    )
                    .force('center', d3.forceCenter(width / 2, height / 2).strength(config.physics.force.center))
                    .force('collision', d3.forceCollide()
                        .radius(d => {
                            const baseRadius = d.type === 'module' ? config.physics.collision.module : 
                                                d.type === 'resource' ? config.physics.collision.resource : 
                                                config.physics.collision.base;
                            const dependencyCount = (d.dependencies_out || 0) + (d.dependencies_in || 0);
                            return baseRadius + Math.min(dependencyCount * config.physics.collision.multiplier, 6);
                        })
                        .strength(0.8)
                    )
                    .alphaDecay(0.0228)
                    .velocityDecay(0.4);

                // Create links
                const link = graphG.append('g')
                    .selectAll('line')
                    .data(graphData.edges)
                    .join('line')
                    .attr('class', 'link')
                    .attr('data-source', d => typeof d.source === 'object' ? d.source.id : d.source)
                    .attr('data-target', d => typeof d.target === 'object' ? d.target.id : d.target)
                    .attr('marker-end', d => {
                        const target = typeof d.target === 'object' ? d.target : nodeMap.get(d.target);
                        return target ? `url(#arrow-${target.type})` : '';
                    })
                    .style('stroke-width', 1.5)
                    .style('opacity', 0.4);

                // Create nodes with proper icon handling
                const node = graphG.append('g')
                    .selectAll('g')
                    .data(graphData.nodes)
                    .join('g')
                    .attr('class', d => `node ${d.type} ${d.state}`)
                    .attr('data-id', d => d.id)
                    .call(d3.drag()
                        .on('start', dragstarted)
                        .on('drag', dragged)
                        .on('end', dragended))
                    .on('mouseover', (event, d) => showTooltip(event, d))
                    .on('mouseout', (event, d) => hideTooltip(event, d))
                    .on('click', (event, d) => highlightConnected(event, d));

                // Enhanced node circles
                node.append('circle')
                    .attr('r', d => {
                        const baseRadius = d.type === 'module' ? 14 : d.type === 'resource' ? 11 : 9;
                        const dependencyCount = (d.dependencies_out || 0) + (d.dependencies_in || 0);
                        return baseRadius + Math.min(dependencyCount * 0.6, 6);
                    })
                    .style('fill', d => nodeConfig[d.type]?.color || '#666')
                    .style('stroke', d => getStateConfig(d.state).stroke)
                    .style('stroke-width', 2)
                    .style('cursor', 'pointer')
                    .style('filter', d => `drop-shadow(0 0 8px ${getStateConfig(d.state).glow})`);
                    
                node.append('text')
                    .attr('class', 'node-icon')
                    .attr('text-anchor', 'middle')
                    .attr('dominant-baseline', 'central')
                    .attr('x', 0)
                    .attr('y', 0)
                    .text(d => nodeConfig[d.type]?.icon || '')
                    .style('font-size', d => d.type === 'module' ? '12px' : '10px')
                    .style('fill', '{{ colors.bg_primary }}')
                    .style('pointer-events', 'none');

                // Enhanced labels
                node.append('text')
                    .attr('dx', d => {
                        const radius = d.type === 'module' ? 14 : d.type === 'resource' ? 11 : 9;
                        const dependencyCount = (d.dependencies_out || 0) + (d.dependencies_in || 0);
                        return radius + Math.min(dependencyCount * 0.6, 6) + 4;
                    })
                    .attr('dy', 4)
                    .text(d => {
                        const maxLength = d.type === 'module' ? 25 : 18;
                        return d.label.length > maxLength ? d.label.substring(0, maxLength) + '...' : d.label;
                    })
                    .style('fill', '{{ colors.text_primary }}')
                    .style('font-size', d => d.type === 'module' ? '12px' : '11px')
                    .style('font-weight', '500')
                    .style('pointer-events', 'none')
                    .style('text-shadow', `0 1px 4px {{ colors.bg_primary }}`);

                // Performance-optimized simulation tick
                simulation.on('tick', () => {
                    if (config.performance.throttleRender && renderThrottled) return;
                    renderThrottled = true;
                    
                    requestAnimationFrame(() => {
                        link.attr('x1', d => d.source.x)
                            .attr('y1', d => d.source.y)
                            .attr('x2', d => d.target.x)
                            .attr('y2', d => d.target.y);
                        
                        node.attr('transform', d => `translate(${d.x},${d.y})`);
                        renderThrottled = false;
                    });
                });
                
                // Export for global access
                window.zoom = zoom;
                window.svg = svg;
                window.width = width;
                window.height = height;

                // Apply initial filters
                applyFilters();

                // Start animations if enabled
                if (animationsEnabled) {
                    startLinkAnimation();
                }
            }

            // Enhanced filter system
            function filterByType(type) {
                if (currentFilters.types.has(type)) {
                    currentFilters.types.delete(type);
                } else {
                    currentFilters.types.add(type);
                }
                applyFilters();
            }

            function filterByState(state) {
                if (currentFilters.states.has(state)) {
                    currentFilters.states.delete(state);
                } else {
                    currentFilters.states.add(state);
                }
                applyFilters();
            }

            function applyFilters() {
                const nodes = graphG.selectAll('.node');
                const links = graphG.selectAll('.link');
                
                nodes.style('display', d => {
                    if (currentFilters.types.size > 0 && !currentFilters.types.has(d.type)) return 'none';
                    if (currentFilters.states.size > 0 && !currentFilters.states.has(d.state)) return 'none';
                    return null;
                });
                
                links.style('display', d => {
                    const source = typeof d.source === 'object' ? d.source : nodeMap.get(d.source);
                    const target = typeof d.target === 'object' ? d.target : nodeMap.get(d.target);
                    
                    if (!source || !target) return 'none';
                    if (currentFilters.types.size > 0 && 
                        (!currentFilters.types.has(source.type) || !currentFilters.types.has(target.type))) return 'none';
                    if (currentFilters.states.size > 0 && 
                        (!currentFilters.states.has(source.state) || !currentFilters.states.has(target.state))) return 'none';
                    return null;
                });
            }

            function clearFilters() {
                currentFilters.types.clear();
                currentFilters.states.clear();
                applyFilters();
            }

            // Enhanced legend interactions
            function toggleLegendSection(section) {
                const content = document.getElementById(`${section}-section`);
                const chevron = document.getElementById(`${section}-chevron`);
                
                if (content.style.display === 'none') {
                    content.style.display = 'block';
                    chevron.className = 'fas fa-chevron-down';
                } else {
                    content.style.display = 'none';
                    chevron.className = 'fas fa-chevron-right';
                }
            }

            // Zoom control functions
            function zoomHandler(direction) {
                const zoomAmount = direction === 'in' ? 1.2 : 1 / 1.2;
                window.svg.transition().duration(300).call(window.zoom.scaleBy, zoomAmount);
            }

            function zoomIn() { zoomHandler('in'); }
            function zoomOut() { zoomHandler('out'); }
            function resetZoom() {
                window.svg.transition().duration(500).call(window.zoom.transform, d3.zoomIdentity);
            }
            function centerGraph() {
                const initialScale = 1;
                const x = window.width / 2;
                const y = window.height / 2;

                const transform = d3.zoomIdentity
                    .translate(x, y)
                    .scale(initialScale)
                    .translate(-x, -y);

                window.svg.transition().duration(500).call(window.zoom.transform, transform);
            }
            
            function resetView() {
                resetZoom();
                clearHighlight();
                clearFilters();
                if (!physicsEnabled) togglePhysics();
            }

            function togglePhysics() {
                physicsEnabled = !physicsEnabled;
                const btn = document.getElementById('physics-btn');
                btn.innerHTML = physicsEnabled ? '<i class="fas fa-bolt"></i> Physics' : '<i class="fas fa-bolt-slash"></i> Physics';
                
                if (physicsEnabled) {
                    simulation.alpha(0.3).restart();
                } else {
                    simulation.stop();
                }
            }
            
            function toggleAnimations() {
                animationsEnabled = !animationsEnabled;
                const btn = document.getElementById('animations-btn');
                if (animationsEnabled) {
                    btn.innerHTML = '<i class="fas fa-sparkles"></i> Animations';
                    startLinkAnimation();
                } else {
                    btn.innerHTML = '<i class="fas fa-ban"></i> Animations';
                    stopLinkAnimation();
                }
            }

            // Enhanced animation system with performance optimizations
            function startLinkAnimation() {
                if (animationTimer || !animationsEnabled) return;
                
                const particles = [];
                const particleRadius = 1.5;

                function addParticle(edge) {
                    if (particles.length >= config.performance.maxParticles) return;
                    
                    const particle = {
                        id: Math.random(),
                        x: edge.source.x,
                        y: edge.source.y,
                        edge: edge,
                        t: 0,
                        speed: 0.02 + Math.random() * 0.01
                    };
                    particles.push(particle);
                }

                animationTimer = d3.interval(() => {
                    if (!animationsEnabled) return;

                    // Add particles for highlighted edges
                    const edges = graphData.edges.filter(edge => {
                        const sourceId = typeof edge.source === 'object' ? edge.source.id : edge.source;
                        const targetId = typeof edge.target === 'object' ? edge.target.id : edge.target;
                        return highlightedEdges.has(sourceId + '->' + targetId);
                    });

                    edges.forEach(edge => {
                        if (Math.random() < 0.3) {
                            addParticle(edge);
                        }
                    });

                    // Update and remove particles
                    for (let i = particles.length - 1; i >= 0; i--) {
                        const p = particles[i];
                        p.t += p.speed;

                        if (p.t > 1) {
                            particles.splice(i, 1);
                        } else {
                            p.x = p.edge.source.x * (1 - p.t) + p.edge.target.x * p.t;
                            p.y = p.edge.source.y * (1 - p.t) + p.edge.target.y * p.t;
                        }
                    }

                    // Update particle visualization
                    graphG.selectAll('.particle')
                        .data(particles, d => d.id)
                        .join(
                            enter => enter.append('circle')
                                .attr('class', 'particle')
                                .attr('r', particleRadius)
                                .attr('cx', d => d.x)
                                .attr('cy', d => d.y)
                                .attr('opacity', 0)
                                .transition()
                                .duration(100)
                                .attr('opacity', 0.9),
                            update => update
                                .attr('cx', d => d.x)
                                .attr('cy', d => d.y),
                            exit => exit.transition()
                                .duration(100)
                                .attr('opacity', 0)
                                .remove()
                        );

                }, config.animation.particleInterval);
            }

            function stopLinkAnimation() {
                if (animationTimer) {
                    animationTimer.stop();
                    animationTimer = null;
                }
                graphG.selectAll('.particle').remove();
            }
            
            // Enhanced tooltip functions
            function showTooltip(event, d) {
                if (hoveredNode) hideTooltip(null, hoveredNode);
                hoveredNode = d;

                const tooltip = document.getElementById('node-tooltip');
                let content = `<div class="node-info-title">${d.label}</div>`;
                content += `<div class="node-state state-${d.state}">${d.state.charAt(0).toUpperCase() + d.state.slice(1).replace('_', ' ')}</div>`;
                
                if (d.state_reason) {
                    content += `<div class="tooltip-section">`;
                    content += `<div class="tooltip-label">Status</div>`;
                    content += `<div class="tooltip-value">${d.state_reason}</div>`;
                    content += `</div>`;
                }
                
                // Enhanced tooltip content using details
                const details = d.details || {};
                
                // Resource-specific information
                if (details.resource_type || details.provider) {
                    content += `<div class="tooltip-section">`;
                    content += `<div class="tooltip-label">Resource</div>`;
                    if (details.resource_type) {
                        content += `<div class="tooltip-stat"><span>Type:</span><span>${details.resource_type}</span></div>`;
                    }
                    if (details.provider) {
                        content += `<div class="tooltip-stat"><span>Provider:</span><span>${details.provider}</span></div>`;
                    }
                    content += `</div>`;
                }
                
                // Location information
                if (details.loc) {
                    content += `<div class="tooltip-section">`;
                    content += `<div class="tooltip-label">Location</div>`;
                    content += `<div class="tooltip-value">${details.loc}</div>`;
                    content += `</div>`;
                }
                
                // Dependencies information
                content += `<div class="tooltip-section">`;
                content += `<div class="tooltip-label">Dependencies</div>`;
                content += `<div class="tooltip-stat"><span>Incoming:</span><span>${d.dependencies_in || 0}</span></div>`;
                content += `<div class="tooltip-stat"><span>Outgoing:</span><span>${d.dependencies_out || 0}</span></div>`;
                content += `</div>`;

                // Additional details
                if (details.desc) {
                    content += `<div class="tooltip-section">`;
                    content += `<div class="tooltip-label">Description</div>`;
                    content += `<div class="tooltip-value">${details.desc}</div>`;
                    content += `</div>`;
                }

                tooltip.innerHTML = content;
                tooltip.style.left = (event.pageX + 15) + 'px';
                tooltip.style.top = (event.pageY + 15) + 'px';
                tooltip.classList.add('show');

                // Enhanced hover effect
                d3.select(event.currentTarget).select('circle')
                    .style('filter', `drop-shadow(0 0 15px ${getStateConfig(d.state).glow})`);
            }

            function hideTooltip(event, d) {
                const tooltip = document.getElementById('node-tooltip');
                tooltip.classList.remove('show');
                
                if (d && !highlightedNodes.has(d.id)) {
                    const selector = event ? event.currentTarget : `[data-id="${d.id}"]`;
                    d3.select(selector).select('circle')
                        .style('filter', `drop-shadow(0 0 8px ${getStateConfig(d.state).glow})`);
                }
                hoveredNode = null;
            }

            function dragstarted(event, d) {
                if (!event.active) simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            }

            function dragged(event, d) {
                d.fx = event.x;
                d.fy = event.y;
            }

            function dragended(event, d) {
                if (!event.active) simulation.alphaTarget(0);
            }
            
            // Enhanced highlight system
            function highlightConnected(event, d) {
                event.stopPropagation();
                
                if (highlightedNodes.has(d.id)) {
                    clearHighlight();
                    return;
                }

                clearHighlight();
                highlightedNodes.add(d.id);

                const incoming = adjacencyList.get(d.id)?.in || [];
                const outgoing = adjacencyList.get(d.id)?.out || [];

                incoming.forEach(id => highlightedNodes.add(id));
                outgoing.forEach(id => highlightedNodes.add(id));
                
                // Create edge keys for highlighted edges
                incoming.forEach(id => highlightedEdges.add(id + '->' + d.id));
                outgoing.forEach(id => highlightedEdges.add(d.id + '->' + id));
                
                // Apply highlights
                d3.selectAll('.node').transition().duration(300)
                    .style('opacity', n => highlightedNodes.has(n.id) ? 1 : 0.2);

                d3.selectAll('.link').transition().duration(300)
                    .style('stroke-opacity', edge => {
                        const sourceId = typeof edge.source === 'object' ? edge.source.id : edge.source;
                        const targetId = typeof edge.target === 'object' ? edge.target.id : edge.target;
                        const edgeKey = sourceId + '->' + targetId;
                        return highlightedEdges.has(edgeKey) ? 1 : 0.1;
                    })
                    .style('stroke', edge => {
                        const sourceId = typeof edge.source === 'object' ? edge.source.id : edge.source;
                        const targetId = typeof edge.target === 'object' ? edge.target.id : edge.target;
                        const edgeKey = sourceId + '->' + targetId;
                        const target = nodeMap.get(targetId);
                        return highlightedEdges.has(edgeKey) ? (nodeConfig[target?.type]?.color || '{{ colors.accent }}') : '{{ colors.text_secondary }}';
                    });

                // Restart animations for highlighted edges
                if (animationsEnabled) {
                    stopLinkAnimation();
                    startLinkAnimation();
                }
            }
            
            function clearHighlight() {
                highlightedNodes.clear();
                highlightedEdges.clear();

                d3.selectAll('.node').transition().duration(300)
                    .style('opacity', 1);

                d3.selectAll('.link').transition().duration(300)
                    .style('stroke-opacity', 0.4)
                    .style('stroke', '{{ colors.text_secondary }}');

                if (animationsEnabled) {
                    stopLinkAnimation();
                }
            }

            // Global function exports
            window.filterByType = filterByType;
            window.filterByState = filterByState;
            window.clearFilters = clearFilters;
            window.toggleLegendSection = toggleLegendSection;
            window.resetView = resetView;
            window.zoomIn = zoomIn;
            window.zoomOut = zoomOut;
            window.resetZoom = resetZoom;
            window.centerGraph = centerGraph;
            window.togglePhysics = togglePhysics;
            window.toggleAnimations = toggleAnimations;
            window.clearHighlight = clearHighlight;
            
            // Initialize on load and resize with debouncing
            let resizeTimer;
            window.addEventListener('resize', () => {
                clearTimeout(resizeTimer);
                resizeTimer = setTimeout(init, config.performance.debounceDelay);
            });
            
            // Add click outside to clear highlights
            document.addEventListener('click', (event) => {
                if (!event.target.closest('.node') && !event.target.closest('.nexus-indicator') && !event.target.closest('.legend-item')) {
                    clearHighlight();
                }
            });

            // Initialize the graph
            init();
        </script>
    </body>
    </html>
    """
