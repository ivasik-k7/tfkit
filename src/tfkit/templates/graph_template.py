# templates/graph_template.py
from .base_template import BaseTemplate


class GraphTemplate(BaseTemplate):
    """Graph-focused template with advanced D3 visualization and modern command palette."""

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
            
            /* Command Palette Styles */
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
            
            .command-palette {
                position: fixed;
                top: 20%;
                left: 50%;
                transform: translateX(-50%) scale(0.9);
                background: {{ colors.bg_secondary }};
                border: 1px solid {{ colors.border }};
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
                border-bottom: 1px solid {{ colors.border }};
                display: flex;
                align-items: center;
                gap: 12px;
            }
            
            .command-input {
                background: none;
                border: none;
                color: {{ colors.text_primary }};
                font-size: 1.1em;
                flex: 1;
                outline: none;
                font-family: 'Exo 2', sans-serif;
            }
            
            .command-input::placeholder {
                color: {{ colors.text_secondary }};
            }
            
            .command-shortcut {
                background: {{ colors.bg_primary }};
                color: {{ colors.text_secondary }};
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
                border-bottom: 1px solid {{ colors.border }};
                cursor: pointer;
                display: flex;
                align-items: center;
                gap: 12px;
                transition: background 0.2s ease;
            }
            
            .command-item:hover,
            .command-item.selected {
                background: {{ colors.bg_tertiary }};
            }
            
            .command-item:last-child {
                border-bottom: none;
            }
            
            .command-icon {
                width: 20px;
                text-align: center;
                color: {{ colors.accent }};
            }
            
            .command-content {
                flex: 1;
            }
            
            .command-title {
                font-weight: 600;
                margin-bottom: 4px;
                color: {{ colors.text_primary }};
            }
            
            .command-description {
                font-size: 0.85em;
                color: {{ colors.text_secondary }};
            }
            
            .command-shortcut-item {
                background: {{ colors.bg_primary }};
                color: {{ colors.text_secondary }};
                padding: 4px 8px;
                border-radius: 6px;
                font-size: 0.8em;
                font-family: monospace;
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
                background: {{ colors.bg_secondary }};
                border: 1px solid {{ colors.border }};
                border-left: 4px solid {{ colors.accent }};
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
            
            .toast.success { border-left-color: {{ colors.success }}; }
            .toast.error { border-left-color: {{ colors.danger }}; }
            .toast.warning { border-left-color: {{ colors.warning }}; }
            .toast.info { border-left-color: {{ colors.info }}; }
            
            .toast-icon {
                font-size: 1.2em;
                color: {{ colors.accent }};
            }
            
            .toast.success .toast-icon { color: {{ colors.success }}; }
            .toast.error .toast-icon { color: {{ colors.danger }}; }
            .toast.warning .toast-icon { color: {{ colors.warning }}; }
            .toast.info .toast-icon { color: {{ colors.info }}; }
            
            .toast-content {
                flex: 1;
            }
            
            .toast-title {
                font-weight: 600;
                margin-bottom: 4px;
                color: {{ colors.text_primary }};
            }
            
            .toast-message {
                font-size: 0.9em;
                color: {{ colors.text_secondary }};
            }
            
            .toast-close {
                background: none;
                border: none;
                color: {{ colors.text_secondary }};
                cursor: pointer;
                padding: 4px;
                border-radius: 4px;
                transition: all 0.2s ease;
            }
            
            .toast-close:hover {
                background: {{ colors.bg_tertiary }};
                color: {{ colors.text_primary }};
            }
            
            /* Quick Action Bar */
            .quick-actions {
                position: fixed;
                bottom: 20px;
                left: 50%;
                transform: translateX(-50%);
                background: {{ colors.bg_secondary }}d0;
                border: 1px solid {{ colors.border }};
                border-radius: 50px;
                padding: 12px 20px;
                display: flex;
                gap: 8px;
                box-shadow: 0 8px 25px rgba(0,0,0,0.15);
                z-index: 9999;
                backdrop-filter: blur(10px);
            }
            
            .quick-action {
                background: {{ colors.bg_primary }};
                border: 1px solid {{ colors.border }};
                color: {{ colors.text_primary }};
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
                background: {{ colors.accent }};
                color: white;
                transform: translateY(-2px);
                box-shadow: 0 4px 12px {{ colors.accent }};
            }
            
            .quick-action:active {
                transform: translateY(0);
            }
            
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
                position: fixed; 
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: {{ colors.bg_primary }};
                overflow: hidden;
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

            /* --- MODERN DASHBOARD HUD --- */
            .dashboard-hud {
                position: absolute;
                top: 20px;
                left: 20px;
                z-index: 1000;
                font-family: 'Exo 2', sans-serif;
                width: 320px;
                opacity: 0.95;
                transition: opacity 0.3s ease;
            }

            .dashboard-hud:hover {
                opacity: 1;
            }

            .info-grid {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 12px;
                margin-bottom: 16px;
            }

            .info-card {
                background: {{ colors.bg_secondary }}90;
                backdrop-filter: blur(8px);
                border: 1px solid {{ colors.border }}20;
                padding: 16px;
                border-radius: 8px;
                transition: all 0.2s ease;
                text-align: center;
            }

            .info-card:hover {
                background: {{ colors.bg_secondary }};
                border-color: {{ colors.accent }}30;
                transform: translateY(-2px);
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            }

            .info-value {
                font-size: 1.8em;
                font-weight: 600;
                color: {{ colors.text_primary }};
                font-family: 'Orbitron', sans-serif;
                line-height: 1;
                margin-bottom: 6px;
            }

            .info-label {
                font-size: 0.75em;
                color: {{ colors.text_secondary }};
                letter-spacing: 0.5px;
                text-transform: uppercase;
            }

            .state-section {
                background: {{ colors.bg_secondary }}80;
                backdrop-filter: blur(8px);
                border: 1px solid {{ colors.border }}20;
                border-radius: 12px;
                padding: 20px;
                margin-top: 12px;
            }

            .state-title {
                font-size: 0.75em;
                color: {{ colors.text_secondary }};
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 16px;
                display: flex;
                align-items: center;
                gap: 8px;
                font-weight: 600;
            }

            .state-flow {
                display: flex;
                flex-direction: column;
                gap: 12px;
            }

            .state-item {
                background: {{ colors.bg_primary }}08;
                border-radius: 10px;
                padding: 12px;
                cursor: pointer;
                transition: all 0.2s ease;
                position: relative;
                overflow: hidden;
            }

            .state-item::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                width: 4px;
                height: 100%;
                transition: all 0.2s ease;
            }

            .state-item:hover {
                transform: translateX(4px);
                background: {{ colors.bg_primary }}12;
            }

            .state-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 6px;
            }

            .state-name {
                display: flex;
                align-items: center;
                gap: 8px;
                font-weight: 600;
                font-size: 0.85em;
                color: {{ colors.text_primary }};
            }

            .state-icon {
                width: 24px;
                height: 24px;
                border-radius: 6px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 0.9em;
            }

            .state-count {
                font-family: 'Orbitron', sans-serif;
                font-weight: 600;
                padding: 3px 8px;
                border-radius: 12px;
                font-size: 0.8em;
                background: {{ colors.bg_primary }}15;
                color: {{ colors.text_primary }};
            }

            .state-info {
                display: flex;
                align-items: center;
                gap: 12px;
                padding-left: 32px;
            }

            .state-metric {
                display: flex;
                align-items: center;
                gap: 4px;
                font-size: 0.75em;
                color: {{ colors.text_secondary }};
            }

            .state-metric i {
                font-size: 0.9em;
                opacity: 0.7;
            }

            /* State-specific styles */
            /* State indicator hover effects */
            .state-item {
                transition: all 0.2s ease;
                position: relative;
                overflow: hidden;
            }

            .state-item::before {
                content: '';
                position: absolute;
                left: 0;
                top: 0;
                height: 100%;
                width: 4px;
                opacity: 0;
                transition: opacity 0.2s ease;
            }

            .state-item:hover {
                transform: translateX(4px);
                background: {{ colors.bg_primary }}12;
            }

            .state-item:hover::before {
                opacity: 1;
            }

            .state-icon {
                width: 32px;
                height: 32px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 8px;
                font-size: 1em;
                transition: all 0.2s ease;
            }

            .state-count {
                padding: 4px 12px;
                border-radius: 12px;
                font-family: 'Orbitron', sans-serif;
                font-weight: 600;
                transition: all 0.2s ease;
            }

            .state-item:hover .state-icon {
                transform: scale(1.1);
            }

            .state-item:hover .state-count {
                transform: scale(1.05);
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
            
            /* --- ENHANCED ANALYTICAL LEGEND --- */
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
                width: 320px;
                max-height: calc(100vh - 40px);
                overflow-y: auto;
                transition: all 0.3s ease;
                font-family: 'Exo 2', sans-serif;
            }

            .legend-header {
                display: flex;
                align-items: center;
                gap: 10px;
                color: {{ colors.text_primary }};
                font-size: 1.1em;
                font-weight: 600;
                margin-bottom: 16px;
                font-family: 'Orbitron', sans-serif;
                letter-spacing: 0.5px;
            }

            .legend-header i {
                color: {{ colors.accent }};
                font-size: 1.2em;
            }
            
            .legend-section {
                background: {{ colors.bg_primary }}08;
                border-radius: 8px;
                padding: 12px;
                margin-bottom: 16px;
            }
            
            .legend-section-title {
                font-size: 0.85em;
                color: {{ colors.text_secondary }};
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                display: flex;
                align-items: center;
                gap: 8px;
                cursor: pointer;
                user-select: none;
                margin-bottom: 12px;
            }

            .legend-section-title i {
                color: {{ colors.accent }};
            }
            
            .legend-section-title:hover {
                color: {{ colors.text_primary }};
            }

            /* Metric Cards */
            .metric-card {
                background: {{ colors.bg_primary }}10;
                border-radius: 8px;
                padding: 12px;
                text-align: center;
                transition: all 0.2s ease;
            }

            .metric-card:hover {
                background: {{ colors.bg_primary }}15;
                transform: translateY(-2px);
            }

            .metric-value {
                font-size: 1.8em;
                font-weight: 700;
                color: {{ colors.text_primary }};
                font-family: 'Orbitron', sans-serif;
                line-height: 1;
                margin-bottom: 4px;
            }

            .metric-label {
                font-size: 0.7em;
                color: {{ colors.text_secondary }};
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }

            #metrics-section {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 8px;
            }

            /* Analysis Rows */
            .analysis-row {
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 10px;
                border-radius: 8px;
                cursor: pointer;
                transition: all 0.2s ease;
                background: {{ colors.bg_primary }}08;
                margin-bottom: 8px;
            }

            .analysis-row:hover {
                background: {{ colors.bg_primary }}15;
                transform: translateX(4px);
            }

            .analysis-icon {
                width: 32px;
                height: 32px;
                border-radius: 8px;
                background: {{ colors.accent }}15;
                color: {{ colors.accent }};
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1em;
            }

            .analysis-content {
                flex: 1;
            }

            .analysis-title {
                font-weight: 600;
                color: {{ colors.text_primary }};
                font-size: 0.9em;
                margin-bottom: 2px;
            }

            .analysis-desc {
                font-size: 0.75em;
                color: {{ colors.text_secondary }};
            }

            .analysis-action {
                color: {{ colors.text_secondary }};
                width: 24px;
                height: 24px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 6px;
                transition: all 0.2s ease;
            }

            .analysis-row:hover .analysis-action {
                color: {{ colors.accent }};
                background: {{ colors.accent }}15;
            }

            /* Filter Chips */
            .filter-chips {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
            }

            .filter-chip {
                background: {{ colors.bg_primary }}10;
                border: 1px solid {{ colors.border }}40;
                color: {{ colors.text_secondary }};
                padding: 6px 12px;
                border-radius: 16px;
                font-size: 0.8em;
                cursor: pointer;
                transition: all 0.2s ease;
                display: flex;
                align-items: center;
                gap: 6px;
            }

            .filter-chip:hover {
                background: {{ colors.accent }}15;
                border-color: {{ colors.accent }}40;
                color: {{ colors.accent }};
                transform: translateY(-1px);
            }

            .filter-chip i {
                font-size: 0.9em;
            }
            
            .node { 
                cursor: pointer; 
            }
            
            .node-shape { 
                transition: all 0.3s ease;
                stroke-width: 2px;
                stroke-dasharray: none;
                fill-opacity: 0.9;
            }
            
            .node-shape.module {
                stroke-dasharray: 3,2;
            }
            
            .node-shape.resource {
                filter: url(#resource-glow);
            }
            
            .node text { 
                font-size: 10px; 
                fill: {{ colors.text_primary }}; 
                text-shadow: 0 1px 3px {{ colors.bg_primary }},
                             0 2px 6px rgba(0,0,0,0.3);
                pointer-events: none; 
                font-weight: 500;
                transition: all 0.3s ease;
                letter-spacing: 0.02em;
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
            
            @keyframes flowAnimation {
                to {
                    stroke-dashoffset: -20;
                }
            }
            
            .link { 
                stroke: {{ colors.text_secondary }}40; 
                stroke-opacity: 0.4; 
                stroke-width: 1.5; 
                transition: all 0.3s ease;
                stroke-linecap: round;
            }
            
            .link.highlight {
                stroke: {{ colors.accent }};
                stroke-opacity: 0.8;
                stroke-width: 2;
                stroke-dasharray: 5, 8;
                animation: flowAnimation 1.5s linear infinite;
            }
            
            .link-arrow { 
                fill: none;
                stroke: {{ colors.text_secondary }};
                stroke-width: 1.5;
                stroke-linecap: round;
                stroke-linejoin: round;
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

            .badge-incoming, .badge-outgoing, .badge-references {
                font-size: 0.85em;
                padding: 2px 8px;
                border-radius: 12px;
                font-weight: 600;
                font-family: 'Exo 2', sans-serif;
            }

            .badge-incoming {
                background: {{ colors.success }}20;
                color: {{ colors.success }};
            }

            .badge-outgoing {
                background: {{ colors.warning }}20;
                color: {{ colors.warning }};
            }

            .badge-references {
                background: {{ colors.info }}20;
                color: {{ colors.info }};
            }

            .source-file {
                font-family: 'Exo 2', monospace;
                font-size: 0.85em;
                color: {{ colors.accent }};
            }

            .source-line {
                font-family: monospace;
                background: {{ colors.bg_primary }}40;
                padding: 1px 4px;
                border-radius: 4px;
                color: {{ colors.text_primary }};
            }

            .tags-container {
                display: flex;
                flex-wrap: wrap;
                gap: 4px;
                margin-top: 4px;
            }

            .node-tag {
                font-size: 0.75em;
                padding: 2px 8px;
                border-radius: 12px;
                background: {{ colors.bg_primary }}30;
                color: {{ colors.text_secondary }};
                border: 1px solid {{ colors.border }}40;
            }

            .tooltip-icon {
                margin-right: 4px;
                color: {{ colors.accent }};
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
        
        <div id="graph-container"></div>
        
        <!-- Quick Actions Bar -->
        <div class="quick-actions" id="quickActions">
            <div class="quick-action" data-action="command">
                <i class="fas fa-terminal"></i>
                <span>Command</span>
            </div>
            <div class="quick-action" data-action="center">
                <i class="fas fa-bullseye"></i>
                <span>Center</span>
            </div>
            <div class="quick-action" data-action="physics">
                <i class="fas fa-bolt"></i>
                <span>Physics</span>
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
        
        <div id="watermark">
            tfkit (v{{ tfkit_version | default('0.0.0') }}) | <a href="https://github.com/ivasik-k7/tfkit" target="_blank" style="color: {{ colors.text_secondary }};">tfkit.com</a>
        </div>

        <!-- Modern Dashboard HUD -->
        <div class="dashboard-hud">
            <div class="info-grid">
                <div class="info-card">
                    <div class="info-value" id="node-count">0</div>
                    <div class="info-label">Nodes</div>
                </div>
                <div class="info-card">
                    <div class="info-value" id="edge-count">0</div>
                    <div class="info-label">Links</div>
                </div>
                <div class="info-card">
                    <div class="info-value" id="component-count">0</div>
                    <div class="info-label">Groups</div>
                </div>
            </div>
            <div class="state-section">
                <div class="state-title">
                    <i class="fas fa-diagram-project"></i>
                    Infrastructure States
                </div>
                <div class="state-flow" id="state-indicators">
                    <!-- State indicators will be populated dynamically -->
                </div>
            </div>
        </div>
        
        <!-- Enhanced Legend with Analytical Insights -->
        <div class="legend">
            <!-- Dependency Metrics -->
            <div class="legend-section">
                <div class="legend-section-title" onclick="toggleLegendSection('metrics')">
                    <i class="fas fa-chart-line"></i> Dependency Metrics
                    <i class="fas fa-chevron-down" id="metrics-chevron"></i>
                </div>
                <div class="legend-section-content" id="metrics-section">
                    <div class="metric-card">
                        <div class="metric-value" id="avg-dependencies">0</div>
                        <div class="metric-label">Avg. Dependencies</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" id="max-depth">0</div>
                        <div class="metric-label">Max Depth</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" id="complexity-score">0</div>
                        <div class="metric-label">Complexity Score</div>
                    </div>
                </div>
            </div>

            <!-- Resource Analysis -->
            <div class="legend-section">
                <div class="legend-section-title" onclick="toggleLegendSection('analysis')">
                    <i class="fas fa-microscope"></i> Resource Analysis
                    <i class="fas fa-chevron-down" id="analysis-chevron"></i>
                </div>
                <div class="legend-section-content" id="analysis-section">
                    <div class="analysis-row" onclick="highlightCriticalPath()">
                        <div class="analysis-icon">
                            <i class="fas fa-route"></i>
                        </div>
                        <div class="analysis-content">
                            <div class="analysis-title">Critical Path</div>
                            <div class="analysis-desc">Longest dependency chain</div>
                        </div>
                        <div class="analysis-action">
                            <i class="fas fa-eye"></i>
                        </div>
                    </div>
                    <div class="analysis-row" onclick="highlightCentralNodes()">
                        <div class="analysis-icon">
                            <i class="fas fa-star"></i>
                        </div>
                        <div class="analysis-content">
                            <div class="analysis-title">Central Nodes</div>
                            <div class="analysis-desc">Most connected resources</div>
                        </div>
                        <div class="analysis-action">
                            <i class="fas fa-eye"></i>
                        </div>
                    </div>
                    <div class="analysis-row" onclick="highlightIsolatedNodes()">
                        <div class="analysis-icon">
                            <i class="fas fa-unlink"></i>
                        </div>
                        <div class="analysis-content">
                            <div class="analysis-title">Isolated Nodes</div>
                            <div class="analysis-desc">Resources without dependencies</div>
                        </div>
                        <div class="analysis-action">
                            <i class="fas fa-eye"></i>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Quick Filters -->
            <div class="legend-section">
                <div class="legend-section-title">
                    <i class="fas fa-filter"></i> Quick Filters
                </div>
                <div class="filter-chips">
                    <div class="filter-chip" onclick="filterByComplexity('high')">
                        <i class="fas fa-exclamation-triangle"></i> High Complexity
                    </div>
                    <div class="filter-chip" onclick="filterByDependencies('many')">
                        <i class="fas fa-project-diagram"></i> Many Dependencies
                    </div>
                    <div class="filter-chip" onclick="filterByState('critical')">
                        <i class="fas fa-exclamation-circle"></i> Critical States
                    </div>
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
            
            // Initialize global state
            let simulation, graphG, animationTimer;
            let physicsEnabled = true;
            let animationsEnabled = true;
            let currentTransform = d3.zoomIdentity;
            let hoveredNode = null;
            let highlightedNodes = new Set();
            let highlightedEdges = new Set();
            let currentFilters = {
                types: new Set(),
                states: new Set()
            };

            // Build node graph first so it's available globally
            const { nodeMap, adjacencyList } = (function buildNodeGraph() {
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
                        adjacencyList.get(targetId).in.push(targetId);
                    }
                });
                
                return { nodeMap, adjacencyList };
            })();

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
            
            // Calculate advanced graph metrics and summary statistics
            const summary = {
                total_nodes: graphData.nodes.length,
                total_edges: graphData.edges.length,
                type_counts: {},
                state_counts: {},
                metrics: {
                    avgDependencies: 0,
                    maxDepth: 0,
                    complexityScore: 0
                }
            };
            
            // Count types and states
            graphData.nodes.forEach(node => {
                summary.type_counts[node.type] = (summary.type_counts[node.type] || 0) + 1;
                summary.state_counts[node.state] = (summary.state_counts[node.state] || 0) + 1;
            });

            // Calculate average dependencies
            const totalDependencies = graphData.nodes.reduce((sum, node) => 
                sum + (node.dependencies_in || 0) + (node.dependencies_out || 0), 0);
            summary.metrics.avgDependencies = (totalDependencies / (graphData.nodes.length * 2)).toFixed(1);

            // Calculate max dependency depth (longest path)
            function calculateMaxDepth() {
                const visited = new Set();
                let maxDepth = 0;

                function dfs(nodeId, depth = 0) {
                    if (visited.has(nodeId)) return depth;
                    visited.add(nodeId);
                    maxDepth = Math.max(maxDepth, depth);

                    const outgoing = adjacencyList.get(nodeId)?.out || [];
                    outgoing.forEach(targetId => {
                        dfs(targetId, depth + 1);
                    });
                    return depth;
                }

                graphData.nodes.forEach(node => {
                    if (!visited.has(node.id)) {
                        dfs(node.id);
                    }
                });

                return maxDepth;
            }
            summary.metrics.maxDepth = calculateMaxDepth();

            // Calculate complexity score based on dependencies and depth
            summary.metrics.complexityScore = Math.min(
                Math.round((summary.metrics.avgDependencies * summary.metrics.maxDepth) / 2),
                10
            );

            // Find central (most connected) nodes
            function findCentralNodes(limit = 5) {
                return graphData.nodes
                    .map(node => ({
                        id: node.id,
                        connections: (node.dependencies_in || 0) + (node.dependencies_out || 0)
                    }))
                    .sort((a, b) => b.connections - a.connections)
                    .slice(0, limit)
                    .map(n => n.id);
            }

            // Find isolated nodes (no dependencies)
            function findIsolatedNodes() {
                return graphData.nodes
                    .filter(node => 
                        (node.dependencies_in || 0) === 0 && 
                        (node.dependencies_out || 0) === 0
                    )
                    .map(n => n.id);
            }

            // Find critical path (longest dependency chain)
            function findCriticalPath() {
                const visited = new Set();
                let criticalPath = [];
                let maxLength = 0;

                function dfs(nodeId, path = []) {
                    if (visited.has(nodeId)) return;
                    visited.add(nodeId);
                    path.push(nodeId);

                    if (path.length > maxLength) {
                        maxLength = path.length;
                        criticalPath = [...path];
                    }

                    const outgoing = adjacencyList.get(nodeId)?.out || [];
                    outgoing.forEach(targetId => {
                        dfs(targetId, [...path]);
                    });
                }

                graphData.nodes.forEach(node => {
                    if (!visited.has(node.id)) {
                        dfs(node.id);
                    }
                });

                return criticalPath;
            }

            // Highlight functions for analytical features
            function highlightCriticalPath() {
                if (!graphG || !adjacencyList) {
                    commandPalette.showToast('Error', 'Graph not yet initialized', 'error');
                    return;
                }
                const path = findCriticalPath();
                clearHighlight();
                
                path.forEach(nodeId => {
                    highlightedNodes.add(nodeId);
                    const idx = path.indexOf(nodeId);
                    if (idx < path.length - 1) {
                        highlightedEdges.add(`${nodeId}->${path[idx + 1]}`);
                    }
                });

                applyHighlight();
                commandPalette.showToast('Critical Path', `Showing longest dependency chain (${path.length} nodes)`, 'info');
            }

            function highlightCentralNodes() {
                if (!graphG || !adjacencyList) {
                    commandPalette.showToast('Error', 'Graph not yet initialized', 'error');
                    return;
                }
                const centralNodes = findCentralNodes();
                clearHighlight();
                
                centralNodes.forEach(nodeId => {
                    highlightedNodes.add(nodeId);
                    const node = nodeMap.get(nodeId);
                    if (node) {
                        (adjacencyList.get(nodeId)?.in || []).forEach(sourceId => {
                            highlightedNodes.add(sourceId);
                            highlightedEdges.add(`${sourceId}->${nodeId}`);
                        });
                        (adjacencyList.get(nodeId)?.out || []).forEach(targetId => {
                            highlightedNodes.add(targetId);
                            highlightedEdges.add(`${nodeId}->${targetId}`);
                        });
                    }
                });

                applyHighlight();
                commandPalette.showToast('Central Nodes', `Showing ${centralNodes.length} most connected nodes`, 'info');
            }

            function highlightIsolatedNodes() {
                if (!graphG || !adjacencyList) {
                    commandPalette.showToast('Error', 'Graph not yet initialized', 'error');
                    return;
                }
                const isolatedNodes = findIsolatedNodes();
                clearHighlight();
                
                isolatedNodes.forEach(nodeId => {
                    highlightedNodes.add(nodeId);
                });

                applyHighlight();
                commandPalette.showToast('Isolated Nodes', `Showing ${isolatedNodes.length} nodes without dependencies`, 'warning');
            }

            // Enhanced filtering system
            function filterByComplexity(level) {
                if (!graphG) {
                    commandPalette.showToast('Error', 'Graph not yet initialized', 'error');
                    return;
                }
                clearFilters();
                const threshold = level === 'high' ? 3 : 1;
                
                graphData.nodes.forEach(node => {
                    const complexity = ((node.dependencies_in || 0) + (node.dependencies_out || 0)) / 2;
                    if (complexity >= threshold) {
                        highlightedNodes.add(node.id);
                    }
                });

                applyHighlight();
                commandPalette.showToast('Complexity Filter', `Showing nodes with ${level} complexity`, 'info');
            }

            function filterByDependencies(amount) {
                clearFilters();
                const threshold = amount === 'many' ? 4 : 2;
                
                graphData.nodes.forEach(node => {
                    if ((node.dependencies_in || 0) + (node.dependencies_out || 0) >= threshold) {
                        highlightedNodes.add(node.id);
                    }
                });

                applyHighlight();
                commandPalette.showToast('Dependency Filter', `Showing nodes with ${amount} dependencies`, 'info');
            }

            function filterByState(importance) {
                clearFilters();
                const criticalStates = ['external_data', 'orphaned', 'incomplete'];
                
                graphData.nodes.forEach(node => {
                    if (criticalStates.includes(node.state)) {
                        highlightedNodes.add(node.id);
                    }
                });

                applyHighlight();
                commandPalette.showToast('State Filter', 'Showing nodes in critical states', 'warning');
            }

            function applyHighlight() {
                if (!graphG) return; // Wait for graph to be initialized
                
                graphG.selectAll('.node').transition().duration(300)
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

                if (animationsEnabled && highlightedEdges.size > 0) {
                    stopLinkAnimation();
                    startLinkAnimation();
                }
            }
            
            // Node graph already built at initialization
            
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
            
            // Function to safely update DOM elements
            function updateDOMElements() {
                // Update HUD statistics if elements exist
                const nodeCount = document.getElementById('node-count');
                const edgeCount = document.getElementById('edge-count');
                const componentCount = document.getElementById('component-count');
                const avgDeps = document.getElementById('avg-dependencies');
                const maxDepth = document.getElementById('max-depth');
                const complexityScore = document.getElementById('complexity-score');

                if (nodeCount) nodeCount.textContent = summary.total_nodes.toLocaleString();
                if (edgeCount) edgeCount.textContent = summary.total_edges.toLocaleString();
                if (componentCount) componentCount.textContent = summary.connected_components.toLocaleString();
                if (avgDeps) avgDeps.textContent = summary.metrics.avgDependencies;
                if (maxDepth) maxDepth.textContent = summary.metrics.maxDepth;
                if (complexityScore) complexityScore.textContent = summary.metrics.complexityScore;
            }

            // Call update function when DOM is ready
            document.addEventListener('DOMContentLoaded', updateDOMElements);
            // Also call it now in case DOM is already loaded
            if (document.readyState === 'complete') {
                updateDOMElements();
            }
            
            // Function to safely update state indicators
            function updateStateIndicators() {
                const stateIndicators = document.getElementById('state-indicators');
                
                if (!stateIndicators) {
                    console.warn('State indicator elements not found, deferring update');
                    return;
                }

                stateIndicators.innerHTML = '';
                
                Object.entries(summary.state_counts).forEach(([state, count]) => {
                    if (count > 0) {
                    const stateInfo = {
                        active: { icon: 'fa-check-circle', desc: 'Active and properly configured resources', color: '#22c55e' },
                        integrated: { icon: 'fa-link', desc: 'Resources integrated with other components', color: '#84cc16' },
                        external_data: { icon: 'fa-database', desc: 'Resources using external data sources', color: '#a855f7' },
                        configuration: { icon: 'fa-cog', desc: 'Resources pending configuration', color: '#8b5cf6' },
                        orphaned: { icon: 'fa-unlink', desc: 'Isolated resources without connections', color: '#fb923c' },
                        unused: { icon: 'fa-ban', desc: 'Unused or deprecated resources', color: '#f59e0b' },
                        leaf: { icon: 'fa-leaf', desc: 'End nodes without outgoing connections', color: '#10b981' },
                        isolated: { icon: 'fa-circle-dot', desc: 'Completely isolated nodes', color: '#ef4444' },
                        root: { icon: 'fa-diagram-project', desc: 'Root nodes without incoming connections', color: '#3b82f6' }
                    }[state] || { icon: 'fa-circle', desc: 'Other resource state', color: '#666666' };

                    const indicator = document.createElement('div');
                    indicator.className = `state-item state-${state}`;
                    
                    const totalNodes = summary.total_nodes;
                    const percentage = ((count / totalNodes) * 100).toFixed(1);
                    
                    indicator.innerHTML = `
                        <div class="state-header">
                            <div class="state-name">
                                <div class="state-icon" style="background: ${stateInfo.color}20; color: ${stateInfo.color}">
                                    <i class="fas ${stateInfo.icon}"></i>
                                </div>
                                ${state.replace('_', ' ').replace(/(^\\w{1})|(\\.\\s+\\w{1})/g, letter => letter.toUpperCase())}
                            </div>
                            <div class="state-count" style="background: ${stateInfo.color}15; color: ${stateInfo.color}">${count}</div>
                        </div>
                        <div class="state-info">
                            <div class="state-metric">
                                <i class="fas fa-chart-pie"></i>
                                ${percentage}%
                            </div>
                            <div class="state-metric">
                                <i class="fas fa-info-circle"></i>
                                ${stateInfo.desc}
                            </div>
                        </div>
                    `;

                    let highlightTimeout;
                    indicator.addEventListener('mouseenter', () => {
                        highlightTimeout = setTimeout(() => {
                            const nodes = graphG.selectAll('.node').filter(d => d.state === state);
                            nodes.each(d => {
                                highlightedNodes.add(d.id);
                                // Add connected edges
                                graphData.edges.forEach(edge => {
                                    const sourceId = typeof edge.source === 'object' ? edge.source.id : edge.source;
                                    const targetId = typeof edge.target === 'object' ? edge.target.id : edge.target;
                                    if (sourceId === d.id || targetId === d.id) {
                                        highlightedEdges.add(`${sourceId}->${targetId}`);
                                    }
                                });
                            });
                            applyHighlight();
                        }, 200); // Small delay to prevent flickering
                    });

                    indicator.addEventListener('mouseleave', () => {
                        clearTimeout(highlightTimeout);
                        clearHighlight();
                    });

                    indicator.addEventListener('click', () => {
                        clearHighlight();
                        filterByState(state);
                        // Show toast with filter info
                        commandPalette.showToast(
                            'Filter Applied', 
                            `Showing ${state.replace('_', ' ')} resources`, 
                            'info'
                        );
                    });
                    stateIndicators.appendChild(indicator);
                    }
                });
            }

            // Call update function when DOM is ready
            document.addEventListener('DOMContentLoaded', updateStateIndicators);
            // Also call it now in case DOM is already loaded
            if (document.readyState === 'complete') {
                updateStateIndicators();
            }

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

                // Add SVG filters and gradients
                const filters = defs.append('g').attr('class', 'filters');

                // Glow filter for resources
                const resourceGlow = filters.append('filter')
                    .attr('id', 'resource-glow')
                    .attr('height', '300%')
                    .attr('width', '300%')
                    .attr('x', '-100%')
                    .attr('y', '-100%');
                
                resourceGlow.append('feGaussianBlur')
                    .attr('stdDeviation', '2')
                    .attr('result', 'coloredBlur');
                
                const resourceGlowMerge = resourceGlow.append('feMerge');
                resourceGlowMerge.append('feMergeNode')
                    .attr('in', 'coloredBlur');
                resourceGlowMerge.append('feMergeNode')
                    .attr('in', 'SourceGraphic');

                // Glow filter for links
                const linkGlow = filters.append('filter')
                    .attr('id', 'link-glow')
                    .attr('height', '300%')
                    .attr('width', '300%')
                    .attr('x', '-100%')
                    .attr('y', '-100%');
                
                linkGlow.append('feGaussianBlur')
                    .attr('stdDeviation', '1')
                    .attr('result', 'coloredBlur');
                
                const linkGlowMerge = linkGlow.append('feMerge');
                linkGlowMerge.append('feMergeNode')
                    .attr('in', 'coloredBlur');
                linkGlowMerge.append('feMergeNode')
                    .attr('in', 'SourceGraphic');

                // Glow filter for particles
                const particleGlow = filters.append('filter')
                    .attr('id', 'particle-glow')
                    .attr('height', '300%')
                    .attr('width', '300%')
                    .attr('x', '-100%')
                    .attr('y', '-100%');
                
                particleGlow.append('feGaussianBlur')
                    .attr('stdDeviation', '1')
                    .attr('result', 'coloredBlur');
                
                const particleGlowMerge = particleGlow.append('feMerge');
                particleGlowMerge.append('feMergeNode')
                    .attr('in', 'coloredBlur');
                particleGlowMerge.append('feMergeNode')
                    .attr('in', 'SourceGraphic');

                // Enhanced gradient for links with multiple color stops
                const linkGradient = defs.append('linearGradient')
                    .attr('id', 'link-gradient')
                    .attr('gradientUnits', 'userSpaceOnUse');
                
                linkGradient.append('stop')
                    .attr('offset', '0%')
                    .attr('stop-color', '{{ colors.accent }}')
                    .attr('stop-opacity', '1');
                
                linkGradient.append('stop')
                    .attr('offset', '50%')
                    .attr('stop-color', '{{ colors.info }}')
                    .attr('stop-opacity', '0.8');
                
                linkGradient.append('stop')
                    .attr('offset', '100%')
                    .attr('stop-color', '{{ colors.success }}')
                    .attr('stop-opacity', '1');
                    
                // Pulse animation for particles
                const pulseAnimation = defs.append('radialGradient')
                    .attr('id', 'particle-pulse')
                    .attr('gradientUnits', 'objectBoundingBox')
                    .attr('cx', '50%')
                    .attr('cy', '50%')
                    .attr('r', '50%');
                    
                pulseAnimation.append('stop')
                    .attr('offset', '0%')
                    .attr('stop-color', '{{ colors.accent }}')
                    .attr('stop-opacity', '1');
                    
                pulseAnimation.append('stop')
                    .attr('offset', '100%')
                    .attr('stop-color', '{{ colors.accent }}')
                    .attr('stop-opacity', '0');

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

                // Create nodes with hexagonal shapes
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

                // Function to create hexagon path
                function hexagonPath(size) {
                    const points = [];
                    for (let i = 0; i < 6; i++) {
                        const angle = (i * Math.PI) / 3;
                        points.push([size * Math.sin(angle), size * Math.cos(angle)]);
                    }
                    return `M${points.map(p => p.join(',')).join('L')}Z`;
                }

                // Enhanced node shapes
                node.append('path')
                    .attr('class', d => `node-shape ${d.type}`)
                    .attr('d', d => {
                        const baseSize = d.type === 'module' ? 16 : d.type === 'resource' ? 13 : 11;
                        const dependencyCount = (d.dependencies_out || 0) + (d.dependencies_in || 0);
                        const size = baseSize + Math.min(dependencyCount * 0.6, 6);
                        return hexagonPath(size);
                    })
                    .style('fill', d => nodeConfig[d.type]?.color || '#666')
                    .style('stroke', d => getStateConfig(d.state).stroke)
                    .style('cursor', 'pointer');
                    
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
                if (!graphG) return; // Wait for graph to be initialized
                
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
                // No need for timer or particles, using CSS animation
                d3.selectAll('.link').classed('highlight', function(d) {
                    const sourceId = typeof d.source === 'object' ? d.source.id : d.source;
                    const targetId = typeof d.target === 'object' ? d.target.id : d.target;
                    return highlightedEdges.has(sourceId + '->' + targetId);
                });
            }

            function stopLinkAnimation() {
                d3.selectAll('.link').classed('highlight', false);
            }
            
            // Enhanced tooltip functions
            function showTooltip(event, d) {
                if (hoveredNode) hideTooltip(null, hoveredNode);
                hoveredNode = d;

                const tooltip = document.getElementById('node-tooltip');
                let content = `<div class="node-info-title">${d.label}</div>`;
                content += `<div class="node-state state-${d.state}">${d.state.charAt(0).toUpperCase() + d.state.slice(1).replace('_', ' ')}</div>`;
                
                const details = d.details || {};
                
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
                
                if (details.loc) {
                    content += `<div class="tooltip-section">`;
                    content += `<div class="tooltip-label">Location</div>`;
                    content += `<div class="tooltip-value">${details.loc}</div>`;
                    content += `</div>`;
                }
                
                // Dependencies information
                content += `<div class="tooltip-section">`;
                content += `<div class="tooltip-label">Dependencies</div>`;
                content += `<div class="tooltip-stat">
                    <span><i class="fas fa-arrow-down"></i> Incoming:</span>
                    <span class="badge-incoming">${d.dependencies_in || 0}</span>
                </div>`;
                content += `<div class="tooltip-stat">
                    <span><i class="fas fa-arrow-up"></i> Outgoing:</span>
                    <span class="badge-outgoing">${d.dependencies_out || 0}</span>
                </div>`;
                content += `</div>`;

                // Reference Count
                if (d.references_count !== undefined) {
                    content += `<div class="tooltip-section">`;
                    content += `<div class="tooltip-label">References</div>`;
                    content += `<div class="tooltip-stat">
                        <span><i class="fas fa-code"></i> Count:</span>
                        <span class="badge-references">${d.references_count}</span>
                    </div>`;
                    content += `</div>`;
                }

                // Additional details with icons
                if (details.desc) {
                    content += `<div class="tooltip-section">`;
                    content += `<div class="tooltip-label">
                        <i class="fas fa-info-circle"></i> Description
                    </div>`;
                    content += `<div class="tooltip-value">${details.desc}</div>`;
                    content += `</div>`;
                }

                // Source file details
                if (details.file || details.line) {
                    content += `<div class="tooltip-section">`;
                    content += `<div class="tooltip-label">
                        <i class="fas fa-file-code"></i> Source
                    </div>`;
                    if (details.file) {
                        content += `<div class="tooltip-stat">
                            <span>File:</span>
                            <span class="source-file">${details.file}</span>
                        </div>`;
                    }
                    if (details.line) {
                        content += `<div class="tooltip-stat">
                            <span>Line:</span>
                            <span class="source-line">${details.line}</span>
                        </div>`;
                    }
                    content += `</div>`;
                }

                // Tags or metadata
                if (details.tags && details.tags.length > 0) {
                    content += `<div class="tooltip-section">`;
                    content += `<div class="tooltip-label">
                        <i class="fas fa-tags"></i> Tags
                    </div>`;
                    content += `<div class="tags-container">`;
                    details.tags.forEach(tag => {
                        content += `<span class="node-tag">${tag}</span>`;
                    });
                    content += `</div>`;
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

                // Get connected nodes from the edge data
                const edges = graphData.edges.filter(edge => {
                    const sourceId = typeof edge.source === 'object' ? edge.source.id : edge.source;
                    const targetId = typeof edge.target === 'object' ? edge.target.id : edge.target;
                    return sourceId === d.id || targetId === d.id;
                });

                // Add connected nodes and edges to highlight sets
                edges.forEach(edge => {
                    const sourceId = typeof edge.source === 'object' ? edge.source.id : edge.source;
                    const targetId = typeof edge.target === 'object' ? edge.target.id : edge.target;
                    highlightedNodes.add(sourceId);
                    highlightedNodes.add(targetId);
                    highlightedEdges.add(`${sourceId}->${targetId}`);
                });
                
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

            // Command Palette and Quick Actions
            class CommandPalette {
                constructor() {
                    this.backdrop = document.getElementById('backdrop');
                    this.commandPalette = document.getElementById('commandPalette');
                    this.commandInput = document.getElementById('commandInput');
                    this.commandList = document.getElementById('commandList');
                    this.toastContainer = document.getElementById('toastContainer');
                    this.quickActions = document.getElementById('quickActions');
                    this.selectedCommandIndex = 0;
                    this.isFullscreen = false;
                    
                    this.commands = [
                        {
                            id: 'toggle-fullscreen',
                            title: 'Toggle Fullscreen',
                            description: 'Enter or exit fullscreen mode',
                            icon: 'fas fa-expand',
                            shortcut: 'F11',
                            action: () => this.toggleFullscreen()
                        },
                        {
                            id: 'reset-view',
                            title: 'Reset View',
                            description: 'Reset zoom, position and filters',
                            icon: 'fas fa-sync-alt',
                            shortcut: 'R',
                            action: () => resetView()
                        },
                        {
                            id: 'toggle-physics',
                            title: 'Toggle Physics',
                            description: 'Enable/disable graph physics',
                            icon: 'fas fa-bolt',
                            shortcut: 'P',
                            action: () => togglePhysics()
                        },
                        {
                            id: 'center-graph',
                            title: 'Center Graph',
                            description: 'Center the graph in view',
                            icon: 'fas fa-bullseye',
                            shortcut: 'C',
                            action: () => centerGraph()
                        },
                        {
                            id: 'toggle-animations',
                            title: 'Toggle Animations',
                            description: 'Enable/disable graph animations',
                            icon: 'fas fa-sparkles',
                            shortcut: 'A',
                            action: () => toggleAnimations()
                        },
                        {
                            id: 'clear-filters',
                            title: 'Clear Filters',
                            description: 'Remove all active filters',
                            icon: 'fas fa-filter',
                            shortcut: 'F',
                            action: () => clearFilters()
                        },
                        {
                            id: 'show-help',
                            title: 'Show Help',
                            description: 'Display keyboard shortcuts and tips',
                            icon: 'fas fa-question-circle',
                            shortcut: 'H',
                            action: () => this.showHelp()
                        }
                    ];
                    
                        // Flags used to pause/resume heavy background work while palette is open
                        this._hadPhysics = false;
                        this._hadAnimations = false;
                        // Allow enabling/disabling backtick key to open palette (can be exposed later)
                        this.enableBacktickKey = true;

                        this.setupEventListeners();
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
                }
                
                handleKeyboard(event) {
                    if (event.target.tagName === 'INPUT') return;
                    
                    // Global shortcuts
                    switch (event.key) {
                        case 'Escape':
                            this.hideCommandPalette();
                            break;
                        case 'F11':
                            event.preventDefault();
                            this.toggleFullscreen();
                            break;
                        case 'k':
                            if (event.ctrlKey || event.metaKey) {
                                event.preventDefault();
                                this.showCommandPalette();
                            }
                            break;
                        case '/':
                            if (!event.ctrlKey && !event.metaKey) {
                                event.preventDefault();
                                this.showCommandPalette();
                            }
                            break;
                        case '`':
                            if (this.enableBacktickKey && !event.ctrlKey && !event.metaKey && !event.altKey) {
                                event.preventDefault();
                                this.showCommandPalette();
                            }
                            break;
                        case 'r':
                        case 'R':
                            if (!event.ctrlKey && !event.metaKey) {
                                event.preventDefault();
                                resetView();
                            }
                            break;
                        case 'p':
                        case 'P':
                            if (!event.ctrlKey && !event.metaKey) {
                                event.preventDefault();
                                togglePhysics();
                            }
                            break;
                        case 'c':
                        case 'C':
                            if (!event.ctrlKey && !event.metaKey) {
                                event.preventDefault();
                                centerGraph();
                            }
                            break;
                        case 'f':
                        case 'F':
                            if (!event.ctrlKey && !event.metaKey) {
                                event.preventDefault();
                                clearFilters();
                            }
                            break;
                        case 'a':
                        case 'A':
                            if (!event.ctrlKey && !event.metaKey) {
                                event.preventDefault();
                                toggleAnimations();
                            }
                            break;
                        case 'h':
                        case 'H':
                            if (!event.ctrlKey && !event.metaKey) {
                                event.preventDefault();
                                this.showHelp();
                            }
                            break;
                    }
                }
                
                showCommandPalette() {
                    // Pause heavy background work (physics simulation & animations) to keep UI responsive
                    try {
                        this._hadPhysics = (typeof physicsEnabled !== 'undefined' && physicsEnabled === true);
                        if (this._hadPhysics && typeof simulation !== 'undefined' && simulation) {
                            simulation.stop();
                        }
                    } catch (err) {
                        // ignore if simulation not available yet
                    }

                    try {
                        this._hadAnimations = (typeof animationTimer !== 'undefined' && animationTimer !== null);
                        if (this._hadAnimations) {
                            stopLinkAnimation();
                        }
                    } catch (err) {
                        // ignore if animation system not available
                    }

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
                    // Resume paused background work if it was running before
                    try {
                        if (this._hadPhysics && typeof simulation !== 'undefined' && simulation) {
                            // restart simulation with a small alpha to smooth back in
                            simulation.alpha(0.3).restart();
                        }
                    } catch (err) {
                        // ignore
                    }

                    try {
                        if (this._hadAnimations && typeof animationsEnabled !== 'undefined' && animationsEnabled) {
                            startLinkAnimation();
                        }
                    } catch (err) {
                        // ignore
                    }
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
                }
                
                executeCommand(command) {
                    command.action();
                    this.hideCommandPalette();
                    this.showToast('Command Executed', command.title, 'success');
                }
                
                handleQuickAction(action) {
                    switch (action) {
                        case 'command':
                            this.showCommandPalette();
                            break;
                        case 'center':
                            centerGraph();
                            break;
                        case 'physics':
                            togglePhysics();
                            break;
                        case 'fullscreen':
                            this.toggleFullscreen();
                            break;
                        case 'help':
                            this.showHelp();
                            break;
                    }
                }
                
                toggleFullscreen() {
                    const updateGraph = () => {
                        const container = document.getElementById('graph-container');
                        
                        // Force graph update
                        simulation.alpha(0.3).restart();
                        
                        // Update SVG dimensions
                        const width = container.clientWidth;
                        const height = container.clientHeight;
                        
                        window.svg
                            .attr('width', width)
                            .attr('height', height)
                            .attr('viewBox', [0, 0, width, height]);
                        
                        // Update viewport
                        window.zoom.extent([[0, 0], [width, height]]);
                        window.svg.call(window.zoom.transform, d3.zoomIdentity);
                        
                        // Force relayout
                        simulation.force('center', d3.forceCenter(width / 2, height / 2));
                        simulation.alpha(0.3).restart();
                    };

                    if (!document.fullscreenElement) {
                        document.documentElement.requestFullscreen().then(() => {
                            this.isFullscreen = true;
                            // Wait for the fullscreen transition to complete
                            setTimeout(updateGraph, 200);
                        }).catch(err => {
                            this.showToast('Fullscreen Error', 'Failed to enter fullscreen mode', 'error');
                        });
                    } else {
                        document.exitFullscreen().then(() => {
                            this.isFullscreen = false;
                            // Wait for the fullscreen exit transition to complete
                            setTimeout(updateGraph, 200);
                        });
                    }
                }
                
                showHelp() {
                    const helpContent = `Graph View Help & Shortcuts

⌨️  Keyboard Shortcuts:
• Ctrl+K / ⌘+K - Command palette
• / - Command palette (alternative)
• F11 - Toggle fullscreen
• R - Reset view
• P - Toggle physics
• C - Center graph
• A - Toggle animations
• F - Clear filters
• H - Show this help
• Escape - Close dialogs

🔍 Navigation:
• Click and drag nodes
• Mouse wheel to zoom
• Click node to highlight connections
• Hover node for details
• Click outside to clear highlight

🎯 Quick Actions:
• Command - Open command palette
• Center - Center the graph
• Physics - Toggle graph physics
• Fullscreen - Toggle fullscreen
• Help - Show this guide`;
                    
                    console.log(helpContent);
                    this.showToast('Help & Shortcuts', 'Check the console for detailed help', 'info');
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
            }
            
            // Initialize components when DOM is ready
            function initializeComponents() {
                // Initialize Command Palette
                const commandPalette = new CommandPalette();
                window.commandPalette = commandPalette;
                
                // Initialize the graph
                init();
                
                // Initialize state indicators
                updateStateIndicators();
                // Update state indicators when window is resized
                window.addEventListener('resize', () => {
                    clearTimeout(resizeTimer);
                    resizeTimer = setTimeout(() => {
                        updateStateIndicators();
                    }, config.performance.debounceDelay);
                });
            }

            // Ensure initialization happens after DOM is ready
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', initializeComponents);
            } else {
                initializeComponents();
            }
        </script>
    </body>
    </html>
    """
