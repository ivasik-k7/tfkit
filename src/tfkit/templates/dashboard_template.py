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
    <title>{{ title }}</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {
            --bg-primary: {{ theme_colors.bg_primary }};
            --bg-secondary: {{ theme_colors.bg_secondary }};
            --bg-tertiary: {{ theme_colors.bg_tertiary }};
            --text-primary: {{ theme_colors.text_primary }};
            --text-secondary: {{ theme_colors.text_secondary }};
            --border: {{ theme_colors.border }};
            --accent: {{ theme_colors.accent }};
            --accent-secondary: {{ theme_colors.accent_secondary }};
            --success: {{ theme_colors.success }};
            --warning: {{ theme_colors.warning }};
            --danger: {{ theme_colors.danger }};
            --info: {{ theme_colors.info }};
        }
        
        * { 
            margin: 0; 
            padding: 0; 
            box-sizing: border-box; 
        }
        
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif; 
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            min-height: 100vh;
            overflow-x: hidden;
        }
        
        /* Backdrop for modals */
        .backdrop {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            backdrop-filter: blur(4px);
            z-index: 10000;
            opacity: 0;
            visibility: hidden;
            transition: all 0.2s ease;
        }
        
        .backdrop.show {
            opacity: 1;
            visibility: visible;
        }
        
        /* Toast Notifications */
        .toast-container {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10001;
            display: flex;
            flex-direction: column;
            gap: 10px;
            max-width: 400px;
            pointer-events: none;
        }
        
        .toast {
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-left: 4px solid var(--accent);
            padding: 16px;
            border-radius: 8px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
            transform: translateX(400px);
            transition: transform 0.3s ease;
            display: flex;
            align-items: center;
            gap: 12px;
            pointer-events: auto;
        }
        
        .toast.show {
            transform: translateX(0);
        }
        
        .toast.success { border-left-color: var(--success); }
        .toast.error { border-left-color: var(--danger); }
        .toast.warning { border-left-color: var(--warning); }
        .toast.info { border-left-color: var(--info); }
        
        .toast-icon {
            font-size: 1.2em;
            color: var(--accent);
        }
        
        .toast.success .toast-icon { color: var(--success); }
        .toast.error .toast-icon { color: var(--danger); }
        .toast.warning .toast-icon { color: var(--warning); }
        .toast.info .toast-icon { color: var(--info); }
        
        .toast-content {
            flex: 1;
        }
        
        .toast-title {
            font-weight: 600;
            margin-bottom: 4px;
        }
        
        .toast-message {
            font-size: 0.9em;
            color: var(--text-secondary);
        }
        
        .toast-close {
            background: none;
            border: none;
            color: var(--text-secondary);
            cursor: pointer;
            padding: 4px;
            border-radius: 4px;
            transition: all 0.2s ease;
        }
        
        .toast-close:hover {
            background: var(--bg-tertiary);
            color: var(--text-primary);
        }
        
        /* Command Palette */
        .command-palette {
            position: fixed;
            top: 20%;
            left: 50%;
            transform: translateX(-50%) scale(0.9);
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 12px;
            box-shadow: 0 25px 50px rgba(0,0,0,0.25);
            width: 90%;
            max-width: 600px;
            z-index: 10001;
            opacity: 0;
            visibility: hidden;
            transition: all 0.2s ease;
        }
        
        .command-palette.show {
            opacity: 1;
            visibility: visible;
            transform: translateX(-50%) scale(1);
        }
        
        .command-header {
            padding: 20px;
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .command-input {
            background: none;
            border: none;
            color: var(--text-primary);
            font-size: 1.1em;
            flex: 1;
            outline: none;
        }
        
        .command-input::placeholder {
            color: var(--text-secondary);
        }
        
        .command-shortcut {
            background: var(--bg-primary);
            color: var(--text-secondary);
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 0.8em;
            font-family: monospace;
        }
        
        .command-list {
            max-height: 400px;
            overflow-y: auto;
        }
        
        .command-item {
            padding: 16px 20px;
            border-bottom: 1px solid var(--border);
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 12px;
            transition: background 0.2s ease;
        }
        
        .command-item:hover,
        .command-item.selected {
            background: var(--bg-tertiary);
        }
        
        .command-item:last-child {
            border-bottom: none;
        }
        
        .command-icon {
            width: 20px;
            text-align: center;
            color: var(--accent);
        }
        
        .command-content {
            flex: 1;
        }
        
        .command-title {
            font-weight: 600;
            margin-bottom: 4px;
        }
        
        .command-description {
            font-size: 0.85em;
            color: var(--text-secondary);
        }
        
        .command-shortcut-item {
            background: var(--bg-primary);
            color: var(--text-secondary);
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 0.8em;
            font-family: monospace;
        }
        
        /* Quick Actions Bar */
        .quick-actions {
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 50px;
            padding: 12px 20px;
            display: flex;
            gap: 8px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
            z-index: 9999;
            backdrop-filter: blur(10px);
        }
        
        .quick-action {
            background: var(--bg-primary);
            border: 1px solid var(--border);
            color: var(--text-primary);
            padding: 12px 16px;
            border-radius: 25px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.2s ease;
            font-size: 0.9em;
            font-weight: 500;
        }
        
        .quick-action:hover {
            background: var(--accent);
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px var(--accent);
        }
        
        .quick-action:active {
            transform: translateY(0);
        }
        
        /* Touch-friendly enhancements */
        @media (hover: none) and (pointer: coarse) {
            .quick-action {
                padding: 16px 20px;
                min-width: 44px;
                min-height: 44px;
            }
            
            .command-item {
                padding: 20px;
                min-height: 60px;
            }
            
            .resource-card {
                padding: 24px;
            }
            
            .stat-card {
                padding: 28px 24px;
            }
        }
        
        .dashboard { 
            max-width: 1400px; 
            margin: 0 auto;
            padding: 24px;
            padding-bottom: 100px;
        }
        
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 32px;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--border);
        }
        
        .header-content h1 {
            color: var(--text-primary);
            font-size: 2.2em;
            font-weight: 700;
            margin-bottom: 4px;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .header-content p {
            color: var(--text-secondary);
            font-size: 1.1em;
        }
        
        .theme-badge {
            background: var(--accent);
            color: white;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
        }
        
        .main-grid {
            display: grid;
            grid-template-columns: 1fr 400px;
            gap: 24px;
            margin-bottom: 32px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }
        
        .stat-card {
            background: var(--bg-secondary);
            padding: 24px;
            border-radius: 12px;
            border: 1px solid var(--border);
            text-align: center;
            transition: all 0.3s ease;
            cursor: pointer;
            position: relative;
            overflow: hidden;
        }
        
        .stat-card:active {
            transform: scale(0.98);
        }
        
        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, var(--bg-tertiary), transparent);
            transition: left 0.6s ease;
        }
        
        .stat-card:hover::before {
            left: 100%;
        }
        
        .stat-icon {
            font-size: 2em;
            margin-bottom: 12px;
            opacity: 0.9;
        }
        
        .stat-value {
            font-size: 2.5em;
            font-weight: 800;
            color: var(--accent);
            line-height: 1;
            margin-bottom: 8px;
        }
        
        .stat-label {
            color: var(--text-secondary);
            font-size: 0.9em;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 24px;
            margin-bottom: 32px;
        }
        
        .chart-card {
            background: var(--bg-secondary);
            padding: 24px;
            border-radius: 12px;
            border: 1px solid var(--border);
            position: relative;
        }
        
        .chart-card:active {
            transform: scale(0.995);
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
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .chart-actions {
            display: flex;
            gap: 8px;
        }
        
        .chart-action {
            background: var(--bg-primary);
            border: 1px solid var(--border);
            color: var(--text-secondary);
            width: 32px;
            height: 32px;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        .chart-action:hover {
            background: var(--accent);
            color: white;
            border-color: var(--accent);
        }
        
        .chart-container {
            height: 280px;
            position: relative;
            touch-action: manipulation;
        }
        
        .chart-container.hidden {
            display: none;
        }
        
        .sidebar {
            display: flex;
            flex-direction: column;
            gap: 24px;
        }
        
        .health-card, .type-breakdown {
            background: var(--bg-secondary);
            padding: 24px;
            border-radius: 12px;
            border: 1px solid var(--border);
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
            color: var(--text-primary);
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
            padding: 12px 8px;
            border-bottom: 1px solid var(--border);
            cursor: pointer;
            transition: background 0.2s ease;
            border-radius: 6px;
        }
        
        .health-item:active {
            background: var(--bg-tertiary);
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
        
        .health-healthy { color: var(--success); }
        .health-unused { color: var(--danger); }
        .health-external { color: var(--info); }
        .health-warning { color: var(--warning); }
        
        .type-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        
        .type-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 8px;
            border-bottom: 1px solid var(--border);
            cursor: pointer;
            transition: background 0.2s ease;
            border-radius: 6px;
        }
        
        .type-item:active {
            background: var(--bg-tertiary);
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
            color: var(--accent);
        }
        
        .resources-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 16px;
            margin-bottom: 32px;
        }
        
        .resource-card {
            background: var(--bg-secondary);
            padding: 20px;
            border-radius: 12px;
            border: 1px solid var(--border);
            transition: all 0.3s ease;
            cursor: pointer;
            position: relative;
        }
        
        .resource-card:active {
            transform: scale(0.98);
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
            background: var(--bg-tertiary);
            color: var(--accent);
        }
        
        .resource-title {
            font-weight: 600;
            font-size: 1.1em;
        }
        
        .resource-description {
            color: var(--text-secondary);
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
            background: var(--bg-primary);
            border-radius: 8px;
            border: 1px solid var(--border);
        }
        
        .resource-stat-value {
            font-size: 1.3em;
            font-weight: 700;
            color: var(--accent);
        }
        
        .resource-stat-label {
            font-size: 0.8em;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .footer {
            margin-top: 40px;
            padding: 16px;
            text-align: center;
        }

        #watermark {
            font-size: 0.75em;
            color: var(--text-secondary);
            user-select: none;
            z-index: 1000;
            font-family: 'Exo 2', sans-serif;
            font-weight: 500;
            letter-spacing: 0.3px;
        }

        #watermark a {
            color: var(--text-secondary);
            text-decoration: none;
            font-weight: 600;
            transition: all 0.2s ease;
            padding: 2px 6px;
            border-radius: 4px;
        }

        #watermark a:hover {
            color: var(--accent);
            background: var(--bg-tertiary);
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
            
            .quick-actions {
                flex-wrap: wrap;
                justify-content: center;
                border-radius: 20px;
                bottom: 10px;
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
            
            .command-palette {
                width: 95%;
                top: 10%;
            }
        }
        
        /* Selection states for touch */
        .stat-card.selected,
        .resource-card.selected,
        .health-item.selected,
        .type-item.selected {
            background: var(--bg-tertiary);
            border-color: var(--accent);
        }
        
        /* Performance optimizations */
        .chart-container canvas {
            will-change: transform;
        }
        
        .stat-card, .resource-card, .chart-card {
            will-change: transform;
        }
    </style>
</head>
<body>
    <!-- Backdrop -->
    <div class="backdrop" id="backdrop"></div>
    
    <!-- Toast Notifications -->
    <div class="toast-container" id="toastContainer"></div>
    
    <!-- Command Palette -->
    <div class="command-palette" id="commandPalette">
        <div class="command-header">
            <i class="fas fa-search"></i>
            <input type="text" class="command-input" id="commandInput" placeholder="Search commands...">
            <div class="command-shortcut">ESC</div>
        </div>
        <div class="command-list" id="commandList">
            <!-- Commands will be populated dynamically -->
        </div>
    </div>
    
    <!-- Quick Actions Bar -->
    <div class="quick-actions" id="quickActions">
        <div class="quick-action" data-action="command">
            <i class="fas fa-terminal"></i>
            <span>Command</span>
        </div>
        <div class="quick-action" data-action="export">
            <i class="fas fa-download"></i>
            <span>Export</span>
        </div>
        <div class="quick-action" data-action="refresh">
            <i class="fas fa-sync-alt"></i>
            <span>Refresh</span>
        </div>
        <div class="quick-action" data-action="fullscreen">
            <i class="fas fa-expand"></i>
            <span>Fullscreen</span>
        </div>
        <div class="quick-action" data-action="help">
            <i class="fas fa-question-circle"></i>
            <span>Help</span>
        </div>
    </div>

    <div class="dashboard">
        <div class="main-grid">
            <!-- Main Content -->
            <div class="main-content">
                <!-- Resource Overview -->
                <div class="resources-grid">
                    <div class="resource-card" data-type="resources" tabindex="0">
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
                                <div class="resource-stat-value" id="resources-total">0</div>
                                <div class="resource-stat-label">Total</div>
                            </div>
                            <div class="resource-stat">
                                <div class="resource-stat-value" id="resource-unused">0</div>
                                <div class="resource-stat-label">Unused</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="resource-card" data-type="modules" tabindex="0">
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
                                <div class="resource-stat-value" id="modules-total">0</div>
                                <div class="resource-stat-label">Total</div>
                            </div>
                            <div class="resource-stat">
                                <div class="resource-stat-value" id="module-unused">0</div>
                                <div class="resource-stat-label">Unused</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="resource-card" data-type="dependencies" tabindex="0">
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
                    
                    <div class="resource-card" data-type="health" tabindex="0">
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
                
                <!-- Stats Overview -->
                <div class="stats-grid">
                    <div class="stat-card" data-stat="nodes" tabindex="0">
                        <div class="stat-icon">
                            <i class="fas fa-circle-nodes"></i>
                        </div>
                        <div class="stat-value" id="total-nodes">0</div>
                        <div class="stat-label">Total Nodes</div>
                    </div>
                    
                    <div class="stat-card" data-stat="edges" tabindex="0">
                        <div class="stat-icon">
                            <i class="fas fa-link"></i>
                        </div>
                        <div class="stat-value" id="total-edges">0</div>
                        <div class="stat-label">Connections</div>
                    </div>
                    
                    <div class="stat-card" data-stat="health" tabindex="0">
                        <div class="stat-icon">
                            <i class="fas fa-heart-pulse"></i>
                        </div>
                        <div class="stat-value" id="health-score">0%</div>
                        <div class="stat-label">Health Score</div>
                    </div>
                </div>
                
                <!-- Charts -->
                <div class="charts-grid">
                    <div class="chart-card" tabindex="0">
                        <div class="chart-header">
                            <div class="chart-title">
                                <i class="fas fa-chart-pie"></i> Component Distribution
                            </div>
                            <div class="chart-actions">
                                <button class="chart-action" data-action="export-chart" data-chart="overview">
                                    <i class="fas fa-download"></i>
                                </button>
                                <button class="chart-action" data-action="toggle-chart" data-chart="overview">
                                    <i class="fas fa-eye"></i>
                                </button>
                            </div>
                        </div>
                        <div class="chart-container" id="overviewContainer">
                            <canvas id="overviewChart"></canvas>
                        </div>
                    </div>
                    
                    <div class="chart-card" tabindex="0">
                        <div class="chart-header">
                            <div class="chart-title">
                                <i class="fas fa-heartbeat"></i> Health Distribution
                            </div>
                            <div class="chart-actions">
                                <button class="chart-action" data-action="export-chart" data-chart="health">
                                    <i class="fas fa-download"></i>
                                </button>
                                <button class="chart-action" data-action="toggle-chart" data-chart="health">
                                    <i class="fas fa-eye"></i>
                                </button>
                            </div>
                        </div>
                        <div class="chart-container" id="healthContainer">
                            <canvas id="healthChart"></canvas>
                        </div>
                    </div>
                    
                    <div class="chart-card" tabindex="0">
                        <div class="chart-header">
                            <div class="chart-title">
                                <i class="fas fa-project-diagram"></i> Dependency Analysis
                            </div>
                            <div class="chart-actions">
                                <button class="chart-action" data-action="export-chart" data-chart="dependency">
                                    <i class="fas fa-download"></i>
                                </button>
                                <button class="chart-action" data-action="toggle-chart" data-chart="dependency">
                                    <i class="fas fa-eye"></i>
                                </button>
                            </div>
                        </div>
                        <div class="chart-container" id="dependencyContainer">
                            <canvas id="dependencyChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Sidebar -->
            <div class="sidebar">
                <div class="health-card">
                    <div class="health-header">
                        <i class="fas fa-heartbeat" style="color: var(--success);"></i>
                        <div class="health-title">Health Status</div>
                    </div>
                    <div class="health-stats">
                        <div class="health-item" data-health="healthy" tabindex="0">
                            <div class="health-label">
                                <i class="fas fa-check-circle"></i>
                                <span>Healthy</span>
                            </div>
                            <div class="health-value health-healthy" id="healthy-count">0</div>
                        </div>
                        <div class="health-item" data-health="unused" tabindex="0">
                            <div class="health-label">
                                <i class="fas fa-exclamation-triangle"></i>
                                <span>Unused</span>
                            </div>
                            <div class="health-value health-unused" id="unused-count">0</div>
                        </div>
                        <div class="health-item" data-health="external" tabindex="0">
                            <div class="health-label">
                                <i class="fas fa-external-link-alt"></i>
                                <span>External</span>
                            </div>
                            <div class="health-value health-external" id="external-count">0</div>
                        </div>
                        <div class="health-item" data-health="warning" tabindex="0">
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
                        <div class="type-item" data-type="resources" tabindex="0">
                            <div class="type-name">
                                <i class="fas fa-cube" style="color: var(--success);"></i>
                                <span>Resources</span>
                            </div>
                            <div class="type-count" id="type-resources">0</div>
                        </div>
                        <div class="type-item" data-type="modules" tabindex="0">
                            <div class="type-name">
                                <i class="fas fa-cubes" style="color: var(--accent-secondary);"></i>
                                <span>Modules</span>
                            </div>
                            <div class="type-count" id="type-modules">0</div>
                        </div>
                        <div class="type-item" data-type="variables" tabindex="0">
                            <div class="type-name">
                                <i class="fas fa-code" style="color: var(--warning);"></i>
                                <span>Variables</span>
                            </div>
                            <div class="type-count" id="type-variables">0</div>
                        </div>
                        <div class="type-item" data-type="outputs" tabindex="0">
                            <div class="type-name">
                                <i class="fas fa-arrow-right" style="color: var(--info);"></i>
                                <span>Outputs</span>
                            </div>
                            <div class="type-count" id="type-outputs">0</div>
                        </div>
                        <div class="type-item" data-type="data" tabindex="0">
                            <div class="type-name">
                                <i class="fas fa-database" style="color: var(--danger);"></i>
                                <span>Data Sources</span>
                            </div>
                            <div class="type-count" id="type-data">0</div>
                        </div>
                        <div class="type-item" data-type="providers" tabindex="0">
                            <div class="type-name">
                                <i class="fas fa-cog" style="color: var(--accent);"></i>
                                <span>Providers</span>
                            </div>
                            <div class="type-count" id="type-providers">0</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <div id="watermark">
                tfkit (v{{ tfkit_version | default('0.0.0') }}) | <a href="https://github.com/ivasik-k7/tfkit" target="_blank">tfkit.com</a>
            </div>
        </div>   
    </div>
    
    <script>
        // Enhanced Interactive Dashboard with Theme Colors
        class InteractiveDashboard {
            constructor() {
                this.backdrop = document.getElementById('backdrop');
                this.commandPalette = document.getElementById('commandPalette');
                this.commandInput = document.getElementById('commandInput');
                this.commandList = document.getElementById('commandList');
                this.toastContainer = document.getElementById('toastContainer');
                this.quickActions = document.getElementById('quickActions');
                this.selectedCommandIndex = 0;
                this.charts = {};
                this.chartInstances = {};
                this.isFullscreen = false;
                this.graphData = {{ graph_data | safe }};
                
                this.commands = [
                    {
                        id: 'export-data',
                        title: 'Export Data',
                        description: 'Export all dashboard data as JSON',
                        icon: 'fas fa-download',
                        shortcut: 'Ctrl+E',
                        action: () => this.exportData()
                    },
                    {
                        id: 'toggle-fullscreen',
                        title: 'Toggle Fullscreen',
                        description: 'Enter or exit fullscreen mode',
                        icon: 'fas fa-expand',
                        shortcut: 'F11',
                        action: () => this.toggleFullscreen()
                    },
                    {
                        id: 'refresh-data',
                        title: 'Refresh Data',
                        description: 'Reload all dashboard data',
                        icon: 'fas fa-sync-alt',
                        shortcut: 'Ctrl+R',
                        action: () => this.refreshData()
                    },
                    {
                        id: 'show-help',
                        title: 'Show Help',
                        description: 'Display keyboard shortcuts and tips',
                        icon: 'fas fa-question-circle',
                        shortcut: 'F1',
                        action: () => this.showHelp()
                    },
                    {
                        id: 'focus-search',
                        title: 'Focus Search',
                        description: 'Quickly focus on search functionality',
                        icon: 'fas fa-search',
                        shortcut: 'Ctrl+K',
                        action: () => this.showCommandPalette()
                    }
                ];
                
                this.init();
            }
            
            init() {
                this.setupEventListeners();
                this.calculateStatistics();
                this.setupCharts();
                this.setupTouchInteractions();
                this.showToast('Dashboard Ready', 'Interactive dashboard loaded successfully', 'success');
            }
            
            setupEventListeners() {
                // Keyboard shortcuts
                document.addEventListener('keydown', (e) => this.handleKeyboard(e));
                
                // Command palette
                this.commandInput.addEventListener('input', () => this.filterCommands());
                this.commandInput.addEventListener('keydown', (e) => this.handleCommandNavigation(e));
                
                // Quick actions
                this.quickActions.addEventListener('click', (e) => {
                    const action = e.target.closest('.quick-action');
                    if (action) {
                        this.handleQuickAction(action.dataset.action);
                    }
                });
                
                // Backdrop click
                this.backdrop.addEventListener('click', () => {
                    this.hideCommandPalette();
                });
                
                // Touch interactions
                this.setupCardInteractions();
                this.setupChartInteractions();
            }
            
            setupTouchInteractions() {
                const interactiveElements = document.querySelectorAll('.stat-card, .resource-card, .health-item, .type-item, .chart-card');
                
                interactiveElements.forEach(element => {
                    element.addEventListener('touchstart', () => {
                        element.classList.add('selected');
                    }, { passive: true });
                    
                    element.addEventListener('touchend', () => {
                        setTimeout(() => element.classList.remove('selected'), 150);
                    }, { passive: true });
                });
            }
            
            setupCardInteractions() {
                document.querySelectorAll('.stat-card, .resource-card').forEach(card => {
                    card.addEventListener('click', () => {
                        this.handleCardClick(card);
                    });
                });
                
                document.querySelectorAll('.health-item, .type-item').forEach(item => {
                    item.addEventListener('click', () => {
                        this.filterByType(item.dataset.health || item.dataset.type);
                    });
                });
            }
            
            setupChartInteractions() {
                document.querySelectorAll('.chart-action').forEach(button => {
                    button.addEventListener('click', (e) => {
                        e.stopPropagation();
                        const action = button.dataset.action;
                        const chart = button.dataset.chart;
                        this.handleChartAction(action, chart);
                    });
                });
            }
            
            handleKeyboard(event) {
                // Global shortcuts
                if (event.key === 'Escape') {
                    this.hideCommandPalette();
                    return;
                }
                
                if (event.key === 'F1') {
                    event.preventDefault();
                    this.showHelp();
                    return;
                }
                
                if (event.key === 'F11') {
                    event.preventDefault();
                    this.toggleFullscreen();
                    return;
                }
                
                if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
                    event.preventDefault();
                    this.showCommandPalette();
                    return;
                }
                
                if ((event.ctrlKey || event.metaKey) && event.key === 'r') {
                    event.preventDefault();
                    this.refreshData();
                    return;
                }
                
                if ((event.ctrlKey || event.metaKey) && event.key === 'e') {
                    event.preventDefault();
                    this.exportData();
                    return;
                }
            }
            
            handleQuickAction(action) {
                switch (action) {
                    case 'command':
                        this.showCommandPalette();
                        break;
                    case 'export':
                        this.exportData();
                        break;
                    case 'refresh':
                        this.refreshData();
                        break;
                    case 'fullscreen':
                        this.toggleFullscreen();
                        break;
                    case 'help':
                        this.showHelp();
                        break;
                }
            }
            
            handleCardClick(card) {
                const type = card.dataset.type || card.dataset.stat;
                this.showToast('Card Selected', `Viewing details for ${type}`, 'info');
            }
            
            handleChartAction(action, chartId) {
                switch (action) {
                    case 'export-chart':
                        this.exportChart(chartId);
                        break;
                    case 'toggle-chart':
                        this.toggleChart(chartId);
                        break;
                }
            }
            
            showCommandPalette() {
                this.backdrop.classList.add('show');
                this.commandPalette.classList.add('show');
                this.commandInput.focus();
                this.filterCommands();
            }
            
            hideCommandPalette() {
                this.backdrop.classList.remove('show');
                this.commandPalette.classList.remove('show');
                this.commandInput.value = '';
                this.selectedCommandIndex = 0;
            }
            
            filterCommands() {
                const query = this.commandInput.value.toLowerCase();
                const filteredCommands = this.commands.filter(cmd => 
                    cmd.title.toLowerCase().includes(query) || 
                    cmd.description.toLowerCase().includes(query)
                );
                
                this.renderCommands(filteredCommands);
            }
            
            renderCommands(commands) {
                this.commandList.innerHTML = '';
                this.selectedCommandIndex = 0;
                
                commands.forEach((command, index) => {
                    const item = document.createElement('div');
                    item.className = `command-item ${index === 0 ? 'selected' : ''}`;
                    item.innerHTML = `
                        <div class="command-icon">
                            <i class="${command.icon}"></i>
                        </div>
                        <div class="command-content">
                            <div class="command-title">${command.title}</div>
                            <div class="command-description">${command.description}</div>
                        </div>
                        <div class="command-shortcut-item">${command.shortcut}</div>
                    `;
                    
                    item.addEventListener('click', () => this.executeCommand(command));
                    this.commandList.appendChild(item);
                });
            }
            
            handleCommandNavigation(event) {
                const items = this.commandList.querySelectorAll('.command-item');
                
                switch (event.key) {
                    case 'ArrowDown':
                        event.preventDefault();
                        this.selectedCommandIndex = Math.min(this.selectedCommandIndex + 1, items.length - 1);
                        this.updateCommandSelection();
                        break;
                    case 'ArrowUp':
                        event.preventDefault();
                        this.selectedCommandIndex = Math.max(this.selectedCommandIndex - 1, 0);
                        this.updateCommandSelection();
                        break;
                    case 'Enter':
                        event.preventDefault();
                        if (items[this.selectedCommandIndex]) {
                            items[this.selectedCommandIndex].click();
                        }
                        break;
                }
            }
            
            updateCommandSelection() {
                const items = this.commandList.querySelectorAll('.command-item');
                items.forEach((item, index) => {
                    item.classList.toggle('selected', index === this.selectedCommandIndex);
                });
                
                // Scroll selected item into view
                if (items[this.selectedCommandIndex]) {
                    items[this.selectedCommandIndex].scrollIntoView({ block: 'nearest', behavior: 'smooth' });
                }
            }
            
            executeCommand(command) {
                command.action();
                this.hideCommandPalette();
                this.showToast('Command Executed', command.title, 'success');
            }
            
            showToast(title, message, type = 'info') {
                const toast = document.createElement('div');
                toast.className = `toast ${type}`;
                
                const icons = {
                    success: 'fas fa-check-circle',
                    error: 'fas fa-exclamation-circle',
                    warning: 'fas fa-exclamation-triangle',
                    info: 'fas fa-info-circle'
                };
                
                toast.innerHTML = `
                    <div class="toast-icon">
                        <i class="${icons[type] || icons.info}"></i>
                    </div>
                    <div class="toast-content">
                        <div class="toast-title">${title}</div>
                        <div class="toast-message">${message}</div>
                    </div>
                    <button class="toast-close">
                        <i class="fas fa-times"></i>
                    </button>
                `;
                
                this.toastContainer.appendChild(toast);
                
                setTimeout(() => toast.classList.add('show'), 10);
                
                const autoRemove = setTimeout(() => {
                    toast.classList.remove('show');
                    setTimeout(() => toast.remove(), 300);
                }, 5000);
                
                toast.querySelector('.toast-close').addEventListener('click', () => {
                    clearTimeout(autoRemove);
                    toast.classList.remove('show');
                    setTimeout(() => toast.remove(), 300);
                });
            }
            
            calculateStatistics() {
                console.log(this.graphData);
                
                const nodes = this.graphData.nodes;
                const edges = this.graphData.edges;
                
                // Calculate type counts
                const resourceCount = nodes.filter(n => n.type === 'resource').length;
                const moduleCount = nodes.filter(n => n.type === 'module').length;
                const variableCount = nodes.filter(n => n.type === 'variable').length;
                const outputCount = nodes.filter(n => n.type === 'output').length;
                const dataCount = nodes.filter(n => n.type === 'data').length;
                const providerCount = nodes.filter(n => n.type === 'provider').length;
                
                // Calculate health statistics
                const healthyStates = ['active', 'integrated', 'leaf', 'input', 'configuration'];
                const healthyCount = nodes.filter(n => healthyStates.includes(n.state)).length;
                const unusedCount = nodes.filter(n => n.state === 'unused').length;
                const externalCount = nodes.filter(n => n.state === 'external_data').length;
                const warningStates = ['orphaned', 'isolated'];
                const warningCount = nodes.filter(n => warningStates.includes(n.state)).length;
                
                // Update UI
                this.updateStatisticsUI({
                    resources: resourceCount,
                    modules: moduleCount,
                    variables: variableCount,
                    outputs: outputCount,
                    dataSources: dataCount,
                    providers: providerCount,
                    totalNodes: nodes.length,
                    totalEdges: edges.length,
                    healthyCount,
                    unusedCount,
                    externalCount,
                    warningCount
                });
            }
            
            updateStatisticsUI(stats) {
                document.getElementById('resources-total').textContent = stats.resources;
                document.getElementById('modules-total').textContent = stats.modules;
                document.getElementById('total-nodes').textContent = stats.totalNodes;
                document.getElementById('total-edges').textContent = stats.totalEdges;
                
                document.getElementById('type-resources').textContent = stats.resources;
                document.getElementById('type-modules').textContent = stats.modules;
                document.getElementById('type-variables').textContent = stats.variables;
                document.getElementById('type-outputs').textContent = stats.outputs;
                document.getElementById('type-data').textContent = stats.dataSources;
                document.getElementById('type-providers').textContent = stats.providers;
                
                document.getElementById('healthy-count').textContent = stats.healthyCount;
                document.getElementById('unused-count').textContent = stats.unusedCount;
                document.getElementById('external-count').textContent = stats.externalCount;
                document.getElementById('warning-count').textContent = stats.warningCount;
                
                const healthPercentage = Math.round((stats.healthyCount / stats.totalNodes) * 100);
                const coverageScore = Math.round(((stats.totalNodes - stats.unusedCount) / stats.totalNodes) * 100);
                
                document.getElementById('health-score').textContent = healthPercentage + '%';
                document.getElementById('healthy-percentage').textContent = healthPercentage + '%';
                document.getElementById('coverage-score').textContent = coverageScore + '%';
                
                const avgDependencies = stats.totalNodes > 0 ? (stats.totalEdges * 2 / stats.totalNodes).toFixed(1) : '0';
                document.getElementById('total-dependencies').textContent = stats.totalEdges;
                document.getElementById('avg-dependencies').textContent = avgDependencies;
                
                const resourceUnused = this.graphData.nodes.filter(n => n.type === 'resource' && n.state === 'unused').length;
                const moduleUnused = this.graphData.nodes.filter(n => n.type === 'module' && n.state === 'unused').length;
                document.getElementById('resource-unused').textContent = resourceUnused;
                document.getElementById('module-unused').textContent = moduleUnused;
            }
            
            setupCharts() {
                const style = getComputedStyle(document.documentElement);
                const colors = {
                    textPrimary: style.getPropertyValue('--text-primary').trim(),
                    textSecondary: style.getPropertyValue('--text-secondary').trim(),
                    border: style.getPropertyValue('--border').trim(),
                    success: style.getPropertyValue('--success').trim(),
                    warning: style.getPropertyValue('--warning').trim(),
                    danger: style.getPropertyValue('--danger').trim(),
                    info: style.getPropertyValue('--info').trim(),
                    accent: style.getPropertyValue('--accent').trim(),
                    accentSecondary: style.getPropertyValue('--accent-secondary').trim()
                };
                
                Chart.defaults.color = colors.textSecondary;
                Chart.defaults.borderColor = colors.border;
                
                this.initializeDistributionChart(colors);
                this.initializeOverviewChart(colors);
                this.initializeHealthChart(colors);
                this.initializeDependencyChart(colors);
            }
            
            initializeDistributionChart(colors) {
                const ctx = document.getElementById('overviewChart');
                if (!ctx) return;
                
                const nodes = this.graphData.nodes;
                const resourceCount = nodes.filter(n => n.type === 'resource').length;
                const moduleCount = nodes.filter(n => n.type === 'module').length;
                const variableCount = nodes.filter(n => n.type === 'variable').length;
                const outputCount = nodes.filter(n => n.type === 'output').length;
                const dataCount = nodes.filter(n => n.type === 'data').length;
                const providerCount = nodes.filter(n => n.type === 'provider').length;
                
                this.chartInstances.overview = new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        labels: ['Resources', 'Modules', 'Variables', 'Outputs', 'Data Sources', 'Providers'],
                        datasets: [{
                            data: [resourceCount, moduleCount, variableCount, outputCount, dataCount, providerCount],
                            backgroundColor: [colors.success, colors.accentSecondary, colors.warning, colors.info, colors.danger, colors.accent],
                            borderWidth: 0,
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
                                    color: colors.textPrimary,
                                    padding: 20,
                                    font: { size: 11 }
                                }
                            }
                        }
                    }
                });
            }
            
            initializeOverviewChart(colors) {
                const ctx = document.getElementById('distributionChart');
                if (!ctx) return;
                
                const nodes = this.graphData.nodes;
                const resourceCount = nodes.filter(n => n.type === 'resource').length;
                const moduleCount = nodes.filter(n => n.type === 'module').length;
                const variableCount = nodes.filter(n => n.type === 'variable').length;
                const outputCount = nodes.filter(n => n.type === 'output').length;
                const dataCount = nodes.filter(n => n.type === 'data').length;
                const providerCount = nodes.filter(n => n.type === 'provider').length;
                
                this.chartInstances.distribution = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: ['Resources', 'Modules', 'Variables', 'Outputs', 'Data', 'Providers'],
                        datasets: [{
                            data: [resourceCount, moduleCount, variableCount, outputCount, dataCount, providerCount],
                            backgroundColor: [colors.success, colors.accentSecondary, colors.warning, colors.info, colors.danger, colors.accent],
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
                                grid: { color: colors.border },
                                ticks: { color: colors.textSecondary }
                            },
                            x: {
                                grid: { display: false },
                                ticks: { color: colors.textSecondary }
                            }
                        }
                    }
                });
            }
            
            initializeHealthChart(colors) {
                const ctx = document.getElementById('healthChart');
                if (!ctx) return;
                
                const nodes = this.graphData.nodes;
                const healthyStates = ['active', 'integrated', 'leaf', 'input', 'configuration'];
                const healthyCount = nodes.filter(n => healthyStates.includes(n.state)).length;
                const unusedCount = nodes.filter(n => n.state === 'unused').length;
                const externalCount = nodes.filter(n => n.state === 'external_data').length;
                const warningStates = ['orphaned', 'isolated'];
                const warningCount = nodes.filter(n => warningStates.includes(n.state)).length;
                
                this.chartInstances.health = new Chart(ctx, {
                    type: 'pie',
                    data: {
                        labels: ['Healthy', 'Unused', 'External', 'Warnings'],
                        datasets: [{
                            data: [healthyCount, unusedCount, externalCount, warningCount],
                            backgroundColor: [colors.success, colors.danger, colors.info, colors.warning],
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
                                    color: colors.textPrimary,
                                    font: { size: 11 }
                                }
                            }
                        }
                    }
                });
            }
            
            initializeDependencyChart(colors) {
                const ctx = document.getElementById('dependencyChart');
                if (!ctx) return;
                
                const nodes = this.graphData.nodes;
                const getAvgDeps = (type) => {
                    const typeNodes = nodes.filter(n => n.type === type);
                    if (typeNodes.length === 0) return 0;
                    const totalDeps = typeNodes.reduce((sum, n) => sum + (n.dependencies_out || 0), 0);
                    return (totalDeps / typeNodes.length).toFixed(1);
                };
                
                this.chartInstances.dependency = new Chart(ctx, {
                    type: 'radar',
                    data: {
                        labels: ['Resources', 'Modules', 'Variables', 'Outputs', 'Data', 'Providers'],
                        datasets: [{
                            label: 'Avg Dependencies',
                            data: [
                                getAvgDeps('resource'),
                                getAvgDeps('module'),
                                getAvgDeps('variable'),
                                getAvgDeps('output'),
                                getAvgDeps('data'),
                                getAvgDeps('provider')
                            ],
                            backgroundColor: colors.accent + '33',
                            borderColor: colors.accent,
                            pointBackgroundColor: colors.accent,
                            pointBorderColor: '#fff',
                            pointHoverBackgroundColor: '#fff',
                            pointHoverBorderColor: colors.accent
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            r: {
                                beginAtZero: true,
                                grid: { color: colors.border },
                                angleLines: { color: colors.border },
                                pointLabels: { color: colors.textSecondary },
                                ticks: {
                                    color: 'transparent',
                                    backdropColor: 'transparent'
                                }
                            }
                        },
                        plugins: {
                            legend: {
                                labels: { color: colors.textPrimary }
                            }
                        }
                    }
                });
            }
            
            filterByType(type) {
                this.showToast('Filter Applied', `Showing items of type: ${type}`, 'info');
                // Add filtering logic here
            }
            
            exportData() {
                const data = {
                    timestamp: new Date().toISOString(),
                    graphData: this.graphData,
                    statistics: this.calculateExportStatistics()
                };
                
                const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `dashboard-export-${new Date().toISOString().split('T')[0]}.json`;
                a.click();
                URL.revokeObjectURL(url);
                
                this.showToast('Export Complete', 'Dashboard data exported successfully', 'success');
            }
            
            calculateExportStatistics() {
                const nodes = this.graphData.nodes;
                return {
                    totalNodes: nodes.length,
                    totalEdges: this.graphData.edges.length,
                    healthScore: document.getElementById('health-score').textContent,
                    resourceCount: nodes.filter(n => n.type === 'resource').length,
                    moduleCount: nodes.filter(n => n.type === 'module').length,
                    exportTime: new Date().toISOString()
                };
            }
            
            exportChart(chartId) {
                const canvas = document.getElementById(chartId);
                if (!canvas) return;
                
                const url = canvas.toDataURL('image/png');
                const a = document.createElement('a');
                a.href = url;
                a.download = `${chartId}-${new Date().toISOString().split('T')[0]}.png`;
                a.click();
                
                this.showToast('Chart Exported', `${chartId} chart saved as PNG`, 'success');
            }
            
            toggleChart(chartId) {
                const container = document.getElementById(chartId + 'Container');
                if (container) {
                    container.classList.toggle('hidden');
                    const isHidden = container.classList.contains('hidden');
                    this.showToast('Chart Toggled', `${chartId} chart ${isHidden ? 'hidden' : 'shown'}`, 'info');
                }
            }
            
            toggleFullscreen() {
                if (!document.fullscreenElement) {
                    document.documentElement.requestFullscreen().catch(err => {
                        this.showToast('Fullscreen Error', 'Failed to enter fullscreen mode', 'error');
                    });
                    this.isFullscreen = true;
                } else {
                    document.exitFullscreen();
                    this.isFullscreen = false;
                }
            }
            
            refreshData() {
                this.showToast('Refreshing', 'Loading latest data...', 'info');
                // Simulate API call or data refresh
                setTimeout(() => {
                    this.calculateStatistics();
                    this.refreshCharts();
                    this.showToast('Refresh Complete', 'Data updated successfully', 'success');
                }, 1500);
            }
            
            refreshCharts() {
                Object.values(this.chartInstances).forEach(chart => {
                    if (chart) {
                        chart.destroy();
                    }
                });
                this.setupCharts();
            }
            
            showHelp() {
                const helpContent = `
Interactive Dashboard Help

📊 Dashboard Features:
• Real-time statistics and metrics
• Interactive charts with export capabilities
• Health monitoring and analysis
• Resource type breakdown
• Dependency visualization

⌨️ Keyboard Shortcuts:
• Ctrl+K / Cmd+K - Open command palette
• F1 - Show this help dialog
• F11 - Toggle fullscreen mode
• Ctrl+R / Cmd+R - Refresh data
• Ctrl+E / Cmd+E - Export data
• Escape - Close modals/palettes

👆 Touch Interactions:
• Tap cards for details
• Long press for context menus
• Swipe to navigate
• Pinch to zoom charts

🚀 Quick Actions:
• Command Palette - Advanced operations
• Export - Download data and charts
• Refresh - Update all data
• Fullscreen - Maximize view
• Help - This information

For more information, visit the documentation.
                `;
                
                this.showToast('Help & Shortcuts', 'Check the console for detailed help information', 'info');
                console.log(helpContent);
                
                // Show help modal (simplified version)
                const helpModal = document.createElement('div');
                helpModal.style.cssText = `
                    position: fixed;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    background: var(--bg-secondary);
                    border: 1px solid var(--border);
                    border-radius: 12px;
                    padding: 24px;
                    max-width: 500px;
                    max-height: 80vh;
                    overflow-y: auto;
                    z-index: 10002;
                    box-shadow: 0 25px 50px rgba(0,0,0,0.3);
                `;
                
                helpModal.innerHTML = `
                    <div style="display: flex; justify-content: between; align-items: center; margin-bottom: 20px;">
                        <h3 style="color: var(--text-primary); margin: 0;">Help & Shortcuts</h3>
                        <button onclick="this.parentElement.parentElement.remove()" style="background: none; border: none; color: var(--text-secondary); cursor: pointer; font-size: 1.2em;">×</button>
                    </div>
                    <div style="color: var(--text-secondary); line-height: 1.6;">
                        <p><strong>Press F1</strong> to show this help</p>
                        <p><strong>Ctrl+K</strong> to open command palette</p>
                        <p><strong>F11</strong> to toggle fullscreen</p>
                        <p>Check browser console for complete documentation</p>
                    </div>
                `;
                
                document.body.appendChild(helpModal);
                
                // Close on backdrop click
                const backdrop = document.getElementById('backdrop');
                backdrop.classList.add('show');
                backdrop.onclick = () => {
                    helpModal.remove();
                    backdrop.classList.remove('show');
                };
            }
        }
        
        // Initialize dashboard when DOM is fully loaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                new InteractiveDashboard();
            });
        } else {
            new InteractiveDashboard();
        }
    </script>
    </body>
    </html>
    """
