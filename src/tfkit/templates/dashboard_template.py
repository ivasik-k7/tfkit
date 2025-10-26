# templates/dashboard_template.py
from .base_template import BaseTemplate


class DashboardTemplate(BaseTemplate):
    """Modern dashboard-style template with metrics and charts."""

    @property
    def template_string(self) -> str:
        return """
<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{ title }} - Dashboard</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <style>
            * { 
                margin: 0; 
                padding: 0; 
                box-sizing: border-box; 
            }
            
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif; 
                background: {{ theme_colors.bg_primary }}; 
                color: {{ theme_colors.text_primary }}; 
                line-height: 1.6;
                min-height: 100vh;
            }
            
            .dashboard { 
                max-width: 1400px; 
                margin: 0 auto;
                padding: 24px;
            }
            
            /* Header */
            .header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 32px;
                padding-bottom: 20px;
                border-bottom: 1px solid {{ theme_colors.border }};
            }
            
            .header-content h1 {
                color: {{ theme_colors.text_primary }};
                font-size: 2.2em;
                font-weight: 700;
                margin-bottom: 4px;
                display: flex;
                align-items: center;
                gap: 12px;
            }
            
            .header-content p {
                color: {{ theme_colors.text_secondary }};
                font-size: 1.1em;
            }
            
            .theme-badge {
                background: {{ theme_colors.accent }};
                color: white;
                padding: 6px 12px;
                border-radius: 20px;
                font-size: 0.85em;
                font-weight: 600;
            }
            
            /* Main Grid */
            .main-grid {
                display: grid;
                grid-template-columns: 1fr 400px;
                gap: 24px;
                margin-bottom: 32px;
            }
            
            /* Stats Grid */
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 16px;
                margin-bottom: 24px;
            }
            
            .stat-card {
                background: {{ theme_colors.bg_secondary }};
                padding: 24px;
                border-radius: 12px;
                border: 1px solid {{ theme_colors.border }};
                text-align: center;
                transition: all 0.3s ease;
            }
            
            .stat-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            }
            
            .stat-icon {
                font-size: 2em;
                margin-bottom: 12px;
                opacity: 0.9;
            }
            
            .stat-value {
                font-size: 2.5em;
                font-weight: 800;
                color: {{ theme_colors.accent }};
                line-height: 1;
                margin-bottom: 8px;
            }
            
            .stat-label {
                color: {{ theme_colors.text_secondary }};
                font-size: 0.9em;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            /* Charts */
            .charts-grid {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 24px;
                margin-bottom: 32px;
            }
            
            .chart-card {
                background: {{ theme_colors.bg_secondary }};
                padding: 24px;
                border-radius: 12px;
                border: 1px solid {{ theme_colors.border }};
            }
            
            .chart-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
            }
            
            .chart-title {
                font-size: 1.2em;
                font-weight: 600;
                color: {{ theme_colors.text_primary }};
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .chart-container {
                height: 280px;
                position: relative;
            }
            
            /* Sidebar */
            .sidebar {
                display: flex;
                flex-direction: column;
                gap: 24px;
            }
            
            .health-card {
                background: {{ theme_colors.bg_secondary }};
                padding: 24px;
                border-radius: 12px;
                border: 1px solid {{ theme_colors.border }};
            }
            
            .health-header {
                display: flex;
                align-items: center;
                gap: 10px;
                margin-bottom: 20px;
            }
            
            .health-title {
                font-size: 1.2em;
                font-weight: 600;
                color: {{ theme_colors.text_primary }};
            }
            
            .health-stats {
                display: flex;
                flex-direction: column;
                gap: 12px;
            }
            
            .health-item {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 12px 0;
                border-bottom: 1px solid {{ theme_colors.border }}20;
            }
            
            .health-item:last-child {
                border-bottom: none;
            }
            
            .health-label {
                display: flex;
                align-items: center;
                gap: 8px;
                font-weight: 500;
            }
            
            .health-value {
                font-weight: 700;
                font-size: 1.1em;
            }
            
            .health-healthy { color: {{ theme_colors.success }}; }
            .health-unused { color: {{ theme_colors.danger }}; }
            .health-external { color: {{ theme_colors.info }}; }
            .health-warning { color: {{ theme_colors.warning }}; }
            
            .type-breakdown {
                background: {{ theme_colors.bg_secondary }};
                padding: 24px;
                border-radius: 12px;
                border: 1px solid {{ theme_colors.border }};
            }
            
            .type-list {
                display: flex;
                flex-direction: column;
                gap: 12px;
            }
            
            .type-item {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 10px 0;
                border-bottom: 1px solid {{ theme_colors.border }}20;
            }
            
            .type-item:last-child {
                border-bottom: none;
            }
            
            .type-name {
                display: flex;
                align-items: center;
                gap: 8px;
                font-weight: 500;
            }
            
            .type-count {
                font-weight: 600;
                color: {{ theme_colors.accent }};
            }
            
            /* Resource Grid */
            .resources-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 16px;
                margin-bottom: 32px;
            }
            
            .resource-card {
                background: {{ theme_colors.bg_secondary }};
                padding: 20px;
                border-radius: 12px;
                border: 1px solid {{ theme_colors.border }};
                transition: all 0.3s ease;
            }
            
            .resource-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            }
            
            .resource-header {
                display: flex;
                align-items: center;
                gap: 12px;
                margin-bottom: 12px;
            }
            
            .resource-icon {
                font-size: 1.5em;
                width: 40px;
                height: 40px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 8px;
                background: {{ theme_colors.accent }}20;
                color: {{ theme_colors.accent }};
            }
            
            .resource-title {
                font-weight: 600;
                font-size: 1.1em;
            }
            
            .resource-description {
                color: {{ theme_colors.text_secondary }};
                font-size: 0.9em;
                margin-bottom: 12px;
                line-height: 1.4;
            }
            
            .resource-stats {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 12px;
                margin-top: 12px;
            }
            
            .resource-stat {
                text-align: center;
                padding: 8px;
                background: {{ theme_colors.bg_primary }};
                border-radius: 8px;
                border: 1px solid {{ theme_colors.border }};
            }
            
            .resource-stat-value {
                font-size: 1.3em;
                font-weight: 700;
                color: {{ theme_colors.accent }};
            }
            
            .resource-stat-label {
                font-size: 0.8em;
                color: {{ theme_colors.text_secondary }};
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            .link.highlighted {
                stroke: {{ colors.accent }}; 
                stroke-opacity: 1.0 !important; 
                stroke-width: 2.5 !important;
                filter: drop-shadow(0 0 4px {{ colors.accent }}80);
                /* **Animation Fix:** Ensure highlighted links have a smooth transition */
                transition: stroke 0.3s, stroke-opacity 0.3s, stroke-width 0.3s;
            }
            
            .node.highlighted circle { 
                stroke-width: 4px !important; 
                stroke: {{ colors.accent }} !important;
                filter: drop-shadow(0 0 10px {{ colors.accent }}80); /* Neon effect on active node */
            }

            .link.highlighted[marker-end^="url(#arrow-"] {
                /* This is tricky in pure CSS. D3 will handle updating the marker properties, 
                but we need a CSS hook for the link line itself. */
            }
            
            /* Footer */
            .footer {
                text-align: center;
                color: {{ theme_colors.text_secondary }};
                font-size: 0.9em;
                padding: 24px;
                border-top: 1px solid {{ theme_colors.border }};
                margin-top: 32px;
            }
            
            /* Responsive */
            @media (max-width: 1200px) {
                .main-grid {
                    grid-template-columns: 1fr;
                }
                
                .stats-grid {
                    grid-template-columns: repeat(2, 1fr);
                }
                
                .charts-grid {
                    grid-template-columns: 1fr;
                }
            }
            
            @media (max-width: 768px) {
                .dashboard {
                    padding: 16px;
                }
                
                .stats-grid {
                    grid-template-columns: 1fr;
                }
                
                .header {
                    flex-direction: column;
                    gap: 16px;
                    text-align: center;
                }
                
                .resources-grid {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <div class="dashboard">
            <!-- Header -->
            <div class="header">
                <div class="header-content">
                    <h1><i class="fas fa-chart-network"></i> Infrastructure Dashboard</h1>
                    <p>{{ timestamp }} • {{ title }}</p>
                </div>
            </div>
            
            <div class="main-grid">
                <!-- Main Content -->
                <div class="main-content">
                    <!-- Resource Overview -->
                    <div class="resources-grid">
                        <div class="resource-card">
                            <div class="resource-header">
                                <div class="resource-icon">
                                    <i class="fas fa-cube"></i>
                                </div>
                                <div class="resource-title">Resources</div>
                            </div>
                            <div class="resource-description">
                                Core infrastructure components and services
                            </div>
                            <div class="resource-stats">
                                <div class="resource-stat">
                                    <div class="resource-stat-value">{{ stats.resources }}</div>
                                    <div class="resource-stat-label">Total</div>
                                </div>
                                <div class="resource-stat">
                                    <div class="resource-stat-value" id="resource-unused">0</div>
                                    <div class="resource-stat-label">Unused</div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="resource-card">
                            <div class="resource-header">
                                <div class="resource-icon">
                                    <i class="fas fa-cubes"></i>
                                </div>
                                <div class="resource-title">Modules</div>
                            </div>
                            <div class="resource-description">
                                Reusable infrastructure modules and components
                            </div>
                            <div class="resource-stats">
                                <div class="resource-stat">
                                    <div class="resource-stat-value">{{ stats.modules }}</div>
                                    <div class="resource-stat-label">Total</div>
                                </div>
                                <div class="resource-stat">
                                    <div class="resource-stat-value" id="module-unused">0</div>
                                    <div class="resource-stat-label">Unused</div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="resource-card">
                            <div class="resource-header">
                                <div class="resource-icon">
                                    <i class="fas fa-project-diagram"></i>
                                </div>
                                <div class="resource-title">Dependencies</div>
                            </div>
                            <div class="resource-description">
                                Component relationships and connections
                            </div>
                            <div class="resource-stats">
                                <div class="resource-stat">
                                    <div class="resource-stat-value" id="total-dependencies">0</div>
                                    <div class="resource-stat-label">Links</div>
                                </div>
                                <div class="resource-stat">
                                    <div class="resource-stat-value" id="avg-dependencies">0</div>
                                    <div class="resource-stat-label">Avg/Node</div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="resource-card">
                            <div class="resource-header">
                                <div class="resource-icon">
                                    <i class="fas fa-shield-alt"></i>
                                </div>
                                <div class="resource-title">Health Status</div>
                            </div>
                            <div class="resource-description">
                                Infrastructure health and usage analysis
                            </div>
                            <div class="resource-stats">
                                <div class="resource-stat">
                                    <div class="resource-stat-value" id="healthy-percentage">0%</div>
                                    <div class="resource-stat-label">Healthy</div>
                                </div>
                                <div class="resource-stat">
                                    <div class="resource-stat-value" id="coverage-score">0%</div>
                                    <div class="resource-stat-label">Coverage</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Charts -->
                    <div class="charts-grid">
                        <div class="chart-card">
                            <div class="chart-header">
                                <div class="chart-title">
                                    <i class="fas fa-chart-pie"></i> Component Distribution
                                </div>
                            </div>
                            <div class="chart-container">
                                <canvas id="distributionChart"></canvas>
                            </div>
                        </div>
                        
                        <div class="chart-card">
                            <div class="chart-header">
                                <div class="chart-title">
                                    <i class="fas fa-chart-bar"></i> Infrastructure Overview
                                </div>
                            </div>
                            <div class="chart-container">
                                <canvas id="overviewChart"></canvas>
                            </div>
                        </div>
                        
                        <div class="chart-card">
                            <div class="chart-header">
                                <div class="chart-title">
                                    <i class="fas fa-heartbeat"></i> Health Distribution
                                </div>
                            </div>
                            <div class="chart-container">
                                <canvas id="healthChart"></canvas>
                            </div>
                        </div>
                        
                        <div class="chart-card">
                            <div class="chart-header">
                                <div class="chart-title">
                                    <i class="fas fa-project-diagram"></i> Dependency Analysis
                                </div>
                            </div>
                            <div class="chart-container">
                                <canvas id="dependencyChart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Sidebar -->
                <div class="sidebar">
                    <div class="health-card">
                        <div class="health-header">
                            <i class="fas fa-heartbeat" style="color: {{ theme_colors.success }};"></i>
                            <div class="health-title">Health Status</div>
                        </div>
                        <div class="health-stats">
                            <div class="health-item">
                                <div class="health-label">
                                    <i class="fas fa-check-circle"></i>
                                    <span>Healthy</span>
                                </div>
                                <div class="health-value health-healthy" id="healthy-count">0</div>
                            </div>
                            <div class="health-item">
                                <div class="health-label">
                                    <i class="fas fa-exclamation-triangle"></i>
                                    <span>Unused</span>
                                </div>
                                <div class="health-value health-unused" id="unused-count">0</div>
                            </div>
                            <div class="health-item">
                                <div class="health-label">
                                    <i class="fas fa-external-link-alt"></i>
                                    <span>External</span>
                                </div>
                                <div class="health-value health-external" id="external-count">0</div>
                            </div>
                            <div class="health-item">
                                <div class="health-label">
                                    <i class="fas fa-bell"></i>
                                    <span>Warnings</span>
                                </div>
                                <div class="health-value health-warning" id="warning-count">0</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="type-breakdown">
                        <div class="chart-header">
                            <div class="chart-title">
                                <i class="fas fa-layer-group"></i> Type Breakdown
                            </div>
                        </div>
                        <div class="type-list">
                            <div class="type-item">
                                <div class="type-name">
                                    <i class="fas fa-cube" style="color: {{ theme_colors.success }};"></i>
                                    <span>Resources</span>
                                </div>
                                <div class="type-count">{{ stats.resources }}</div>
                            </div>
                            <div class="type-item">
                                <div class="type-name">
                                    <i class="fas fa-cubes" style="color: {{ theme_colors.accent_secondary }};"></i>
                                    <span>Modules</span>
                                </div>
                                <div class="type-count">{{ stats.modules }}</div>
                            </div>
                            <div class="type-item">
                                <div class="type-name">
                                    <i class="fas fa-code" style="color: {{ theme_colors.warning }};"></i>
                                    <span>Variables</span>
                                </div>
                                <div class="type-count">{{ stats.variables }}</div>
                            </div>
                            <div class="type-item">
                                <div class="type-name">
                                    <i class="fas fa-arrow-right" style="color: {{ theme_colors.info }};"></i>
                                    <span>Outputs</span>
                                </div>
                                <div class="type-count">{{ stats.outputs }}</div>
                            </div>
                            <div class="type-item">
                                <div class="type-name">
                                    <i class="fas fa-database" style="color: {{ theme_colors.danger }};"></i>
                                    <span>Data Sources</span>
                                </div>
                                <div class="type-count">{{ stats.data_sources }}</div>
                            </div>
                            <div class="type-item">
                                <div class="type-name">
                                    <i class="fas fa-cog" style="color: {{ theme_colors.accent }};"></i>
                                    <span>Providers</span>
                                </div>
                                <div class="type-count">{{ stats.providers }}</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="footer">
                TFKIT • Terraform Intelligence & Analysis Suite • Generated on {{ timestamp }}
            </div>
        </div>
        
        <script>
            // Component Distribution Chart
            new Chart(document.getElementById('distributionChart'), {
                type: 'doughnut',
                data: {
                    labels: ['Resources', 'Modules', 'Variables', 'Outputs', 'Data Sources', 'Providers'],
                    datasets: [{
                        data: [
                            {{ stats.resources }},
                            {{ stats.modules }}, 
                            {{ stats.variables }},
                            {{ stats.outputs }},
                            {{ stats.data_sources }},
                            {{ stats.providers }}
                        ],
                        backgroundColor: [
                            '{{ theme_colors.success }}',
                            '{{ theme_colors.accent_secondary }}',
                            '{{ theme_colors.warning }}',
                            '{{ theme_colors.info }}',
                            '{{ theme_colors.danger }}',
                            '{{ theme_colors.accent }}'
                        ],
                        borderWidth: 0,
                        borderColor: '{{ theme_colors.bg_primary }}',
                        hoverOffset: 8
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '65%',
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                color: '{{ theme_colors.text_primary }}',
                                padding: 20,
                                font: { size: 11 }
                            }
                        }
                    }
                }
            });
            
            // Overview Bar Chart
            new Chart(document.getElementById('overviewChart'), {
                type: 'bar',
                data: {
                    labels: ['Resources', 'Modules', 'Variables', 'Outputs', 'Data Sources', 'Providers'],
                    datasets: [{
                        data: [
                            {{ stats.resources }},
                            {{ stats.modules }},
                            {{ stats.variables }},
                            {{ stats.outputs }},
                            {{ stats.data_sources }},
                            {{ stats.providers }}
                        ],
                        backgroundColor: [
                            '{{ theme_colors.success }}',
                            '{{ theme_colors.accent_secondary }}',
                            '{{ theme_colors.warning }}',
                            '{{ theme_colors.info }}',
                            '{{ theme_colors.danger }}',
                            '{{ theme_colors.accent }}'
                        ],
                        borderWidth: 0,
                        borderRadius: 6,
                        borderSkipped: false,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: { color: '{{ theme_colors.border }}20' },
                            ticks: { color: '{{ theme_colors.text_secondary }}' }
                        },
                        x: {
                            grid: { display: false },
                            ticks: { color: '{{ theme_colors.text_secondary }}' }
                        }
                    }
                }
            });
            
            // Calculate health statistics from graph data
            {% if graph_data %}
            const graphData = {{ graph_data|safe }};
            
            // Calculate state counts
            const stateCounts = {
                healthy: 0,
                unused: 0,
                external: 0,
                leaf: 0,
                orphan: 0,
                warning: 0
            };
            
            graphData.nodes.forEach(node => {
                if (stateCounts.hasOwnProperty(node.state)) {
                    stateCounts[node.state]++;
                }
            });
            
            // Calculate type-specific unused counts
            let resourceUnused = 0;
            let moduleUnused = 0;
            
            graphData.nodes.forEach(node => {
                if (node.state === 'unused') {
                    if (node.type === 'resource') resourceUnused++;
                    if (node.type === 'module') moduleUnused++;
                }
            });
            
            // Calculate dependency statistics
            const totalDependencies = graphData.edges.length;
            const avgDependencies = graphData.nodes.length > 0 
                ? (totalDependencies * 2 / graphData.nodes.length).toFixed(1) 
                : '0';
            
            // Calculate health percentages
            const totalNodes = graphData.nodes.length;
            const healthyPercentage = totalNodes > 0 
                ? Math.round((stateCounts.healthy / totalNodes) * 100) 
                : 0;
            
            const coverageScore = totalNodes > 0 
                ? Math.round(((totalNodes - stateCounts.unused) / totalNodes) * 100)
                : 0;
            
            // Update UI with calculated values
            document.getElementById('healthy-count').textContent = stateCounts.healthy;
            document.getElementById('unused-count').textContent = stateCounts.unused ;
            document.getElementById('external-count').textContent = stateCounts.external;
            document.getElementById('warning-count').textContent = stateCounts.warning;
            
            document.getElementById('resource-unused').textContent = resourceUnused;
            document.getElementById('module-unused').textContent = moduleUnused;
            document.getElementById('total-dependencies').textContent = totalDependencies;
            document.getElementById('avg-dependencies').textContent = avgDependencies;
            document.getElementById('healthy-percentage').textContent = healthyPercentage + '%';
            document.getElementById('coverage-score').textContent = coverageScore + '%';
            
            // Health Distribution Chart
            new Chart(document.getElementById('healthChart'), {
                type: 'pie',
                data: {
                    labels: ['Healthy', 'Unused', 'External', 'Leaf', 'Orphan', 'Warning'],
                    datasets: [{
                        data: [
                            stateCounts.healthy,
                            stateCounts.unused,
                            stateCounts.external,
                            stateCounts.leaf,
                            stateCounts.orphan,
                            stateCounts.warning
                        ],
                        backgroundColor: [
                            '{{ theme_colors.success }}',
                            '{{ theme_colors.danger }}',
                            '{{ theme_colors.info }}',
                            '{{ theme_colors.success }}',
                            '{{ theme_colors.warning }}',
                            '{{ theme_colors.warning }}'
                        ],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                color: '{{ theme_colors.text_primary }}',
                                font: { size: 11 }
                            }
                        }
                    }
                }
            });
            
            // Dependency Analysis Chart
            const nodeTypes = ['resource', 'module', 'variable', 'output', 'data', 'provider'];
            const avgDependenciesByType = nodeTypes.map(type => {
                const nodesOfType = graphData.nodes.filter(n => n.type === type);
                if (nodesOfType.length === 0) return 0;
                const totalDeps = nodesOfType.reduce((sum, node) => 
                    sum + (node.dependencies_out || 0) + (node.dependencies_in || 0), 0);
                return (totalDeps / nodesOfType.length).toFixed(1);
            });
            
            new Chart(document.getElementById('dependencyChart'), {
                type: 'radar',
                data: {
                    labels: ['Resources', 'Modules', 'Variables', 'Outputs', 'Data Sources', 'Providers'],
                    datasets: [{
                        label: 'Avg Dependencies per Node',
                        data: avgDependenciesByType,
                        backgroundColor: '{{ theme_colors.accent }}20',
                        borderColor: '{{ theme_colors.accent }}',
                        pointBackgroundColor: '{{ theme_colors.accent }}',
                        pointBorderColor: '#fff',
                        pointHoverBackgroundColor: '#fff',
                        pointHoverBorderColor: '{{ theme_colors.accent }}'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        r: {
                            beginAtZero: true,
                            grid: { color: '{{ theme_colors.border }}20' },
                            angleLines: { color: '{{ theme_colors.border }}20' },
                            pointLabels: { color: '{{ theme_colors.text_secondary }}' },
                            ticks: { color: 'transparent', backdropColor: 'transparent' }
                        }
                    },
                    plugins: {
                        legend: {
                            labels: { color: '{{ theme_colors.text_primary }}' }
                        }
                    }
                }
            });
            {% endif %}
            
            // Set chart defaults
            Chart.defaults.color = '{{ theme_colors.text_secondary }}';
            Chart.defaults.borderColor = '{{ theme_colors.border }}20';
        </script>
    </body>
    </html>
    """
