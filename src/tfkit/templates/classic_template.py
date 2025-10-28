# templates/classic_template.py
from .base_template import BaseTemplate


class ClassicTemplate(BaseTemplate):
    """Enhanced classic template with modern UI, command palette, and 3D visualization."""

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
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
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
            font-family: 'Exo 2', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
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
        
        /* 3D Visualization Modal */
        .visualization-modal {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%) scale(0.9);
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 16px;
            box-shadow: 0 25px 50px rgba(0,0,0,0.3);
            width: 90%;
            height: 80%;
            max-width: 1200px;
            z-index: 10002;
            opacity: 0;
            visibility: hidden;
            transition: all 0.3s ease;
            display: flex;
            flex-direction: column;
        }
        
        .visualization-modal.show {
            opacity: 1;
            visibility: visible;
            transform: translate(-50%, -50%) scale(1);
        }
        
        .visualization-header {
            padding: 20px 24px;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .visualization-title {
            font-size: 1.3em;
            font-weight: 700;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .visualization-close {
            background: none;
            border: none;
            color: var(--text-secondary);
            cursor: pointer;
            padding: 8px;
            border-radius: 6px;
            transition: all 0.2s ease;
        }
        
        .visualization-close:hover {
            background: var(--bg-tertiary);
            color: var(--text-primary);
        }
        
        .visualization-content {
            flex: 1;
            display: flex;
            position: relative;
        }
        
        .visualization-canvas {
            width: 100%;
            height: 100%;
            border-radius: 0 0 16px 16px;
            display: block; /* Important: ensure canvas is block element */
        }

        .visualization-content {
            flex: 1;
            display: flex;
            position: relative;
            min-height: 400px; /* Ensure minimum height */
        }
                
        .visualization-controls {
            position: absolute;
            top: 20px;
            right: 20px;
            display: flex;
            flex-direction: column;
            gap: 8px;
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 12px;
        }
        
        .visualization-control {
            background: var(--bg-primary);
            border: 1px solid var(--border);
            color: var(--text-primary);
            padding: 8px 12px;
            border-radius: 6px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 0.85em;
            transition: all 0.2s ease;
        }
        
        .visualization-control:hover {
            background: var(--accent);
            color: white;
            border-color: var(--accent);
        }
        
        .container {
            max-width: 1600px;
            margin: 0 auto;
            padding: 20px;
            padding-bottom: 100px;
        }
        
        /* Modern Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 32px;
        }
        
        .stat-card {
            background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-tertiary) 100%);
            padding: 24px;
            border-radius: 12px;
            border: 1px solid var(--border);
            position: relative;
            overflow: hidden;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
            cursor: pointer;
        }
        
        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background: var(--accent);
        }
        
        .stat-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
            border-color: var(--accent);
        }
        
        .stat-card:active {
            transform: translateY(-2px);
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
            background: var(--accent);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.4em;
            color: var(--bg-primary);
        }
        
        .stat-value {
            font-size: 2.5em;
            font-weight: 800;
            color: var(--text-primary);
            line-height: 1;
            margin-bottom: 8px;
            font-family: 'Exo 2', sans-serif;
        }
        
        .stat-label {
            font-size: 0.9em;
            color: var(--text-secondary);
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
            background: var(--success);
            color: white;
        }
        
        .stat-trend.negative {
            background: var(--danger);
            color: white;
        }
        
        .state-breakdown {
            margin-top: 16px;
            padding-top: 16px;
            border-top: 1px solid var(--border);
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
            color: var(--text-secondary);
            font-weight: 500;
        }
        
        .state-count {
            color: var(--text-primary);
            font-weight: 700;
            background: var(--bg-primary);
            padding: 2px 8px;
            border-radius: 12px;
            min-width: 24px;
            text-align: center;
        }
        
        /* Enhanced Search Bar */
        .search-container {
            position: relative;
            margin: 30px 20px 20px 20px;
        }
        
        .search-box {
            width: 100%;
            padding: 16px 52px 16px 48px;
            border: 2px solid var(--border);
            background: var(--bg-primary);
            color: var(--text-primary);
            border-radius: 12px;
            font-size: 1em;
            transition: all 0.3s ease;
            font-family: 'Exo 2', sans-serif;
        }
        
        .search-box:focus {
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 0 3px var(--accent);
        }
        
        .search-box::placeholder {
            color: var(--text-secondary);
        }
        
        .search-icon {
            position: absolute;
            left: 16px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-secondary);
            font-size: 1.1em;
        }
        
        .search-clear {
            position: absolute;
            right: 16px;
            top: 50%;
            transform: translateY(-50%);
            background: none;
            border: none;
            color: var(--text-secondary);
            cursor: pointer;
            padding: 4px;
            border-radius: 4px;
            transition: all 0.2s ease;
            opacity: 0;
        }
        
        .search-clear:hover {
            color: var(--danger);
            background: var(--danger);
        }
        
        .search-clear.visible {
            opacity: 1;
        }
        
        .search-hint {
            position: absolute;
            right: 16px;
            top: -24px;
            font-size: 0.75em;
            color: var(--text-secondary);
            background: var(--bg-secondary);
            padding: 2px 8px;
            border-radius: 6px;
            border: 1px solid var(--border);
        }
        
        /* Main Panel */
        .main-panel {
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 16px;
            overflow: hidden;
            margin-bottom: 24px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        }
        
        .panel-header {
            padding: 20px 24px;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
            background: var(--bg-tertiary);
        }
        
        .panel-title {
            font-size: 1.25em;
            font-weight: 700;
            color: var(--text-primary);
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
            border: 1px solid var(--border);
            background: var(--bg-primary);
            color: var(--text-primary);
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
            background: var(--accent);
            border-color: var(--accent);
            color: var(--bg-primary);
            transform: translateY(-1px);
        }
        
        .btn.active {
            background: var(--accent);
            border-color: var(--accent);
            color: var(--bg-primary);
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
            background: var(--bg-primary);
        }
        
        .graph-container::-webkit-scrollbar-thumb {
            background: var(--border);
            border-radius: 4px;
        }
        
        .graph-container::-webkit-scrollbar-thumb:hover {
            background: var(--text-secondary);
        }
        
        .graph-nodes {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
            gap: 20px;
        }
        
        .graph-node {
            background: var(--bg-primary);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 24px;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            cursor: pointer;
        }
        
        .graph-node:hover {
            border-color: var(--accent);
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        
        .graph-node:active {
            transform: translateY(0);
        }
        
        .node-unused { border-left: 4px solid var(--danger); }
        .node-external { border-left: 4px solid var(--info); }
        .node-leaf { border-left: 4px solid var(--success); }
        .node-orphan { border-left: 4px solid var(--warning); }
        .node-warning { border-left: 4px solid var(--warning); }
        .node-healthy { border-left: 4px solid var(--success); }
        
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
            background: var(--accent);
            flex-shrink: 0;
            font-size: 1.3em;
            color: var(--bg-primary);
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
            color: var(--text-primary);
        }
        
        .graph-node-type {
            color: var(--text-secondary);
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
        
        .graph-node-actions {
            position: absolute;
            top: 16px;
            right: 16px;
            display: flex;
            gap: 4px;
            opacity: 0;
            transition: opacity 0.2s ease;
        }
        
        .graph-node:hover .graph-node-actions {
            opacity: 1;
        }
        
        .node-action {
            background: var(--bg-secondary);
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
        
        .node-action:hover {
            background: var(--accent);
            color: white;
            border-color: var(--accent);
        }
        
        .graph-node-badges {
            display: flex;
            gap: 6px;
            flex-wrap: wrap;
            margin-top: 12px;
        }
        
        .graph-node-badge {
            background: var(--info);
            color: white;
            font-size: 0.75em;
            padding: 4px 8px;
            border-radius: 6px;
            font-weight: 600;
        }
        
        .graph-node-badge.warning {
            background: var(--warning);
            color: var(--bg-primary);
        }
        
        .graph-node-badge.danger {
            background: var(--danger);
            color: white;
        }
        
        .graph-node-dependencies {
            display: flex;
            gap: 20px;
            margin-top: 16px;
            padding-top: 16px;
            border-top: 1px solid var(--border);
        }
        
        .graph-node-deps-item {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.9em;
            color: var(--text-secondary);
            font-weight: 500;
        }
        
        .graph-node-deps-count {
            background: var(--info);
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
            background: var(--success);
        }
        
        .graph-node-deps-count.incoming {
            background: var(--accent-secondary);
        }
        
        .graph-node-reason {
            font-size: 0.85em;
            color: var(--text-secondary);
            font-style: italic;
            margin-top: 12px;
            line-height: 1.4;
        }
        
        .empty-state {
            padding: 80px 20px;
            text-align: center;
            color: var(--text-secondary);
        }
        
        .empty-state-icon {
            font-size: 4em;
            margin-bottom: 20px;
            opacity: 0.5;
        }
        
        .empty-state h3 {
            font-size: 1.5em;
            margin-bottom: 12px;
            color: var(--text-primary);
        }
        
        .footer {
            margin-top: 40px;
            padding: 20px;
            text-align: center;
            border-top: 1px solid var(--border);
        }

        #watermark {
            font-size: 0.85em;
            color: var(--text-secondary);
            user-select: none;
            font-family: 'Exo 2', sans-serif;
            font-weight: 500;
            letter-spacing: 0.3px;
        }

        #watermark a {
            color: var(--text-secondary);
            text-decoration: none;
            font-weight: 600;
            transition: all 0.2s ease;
            padding: 4px 8px;
            border-radius: 6px;
        }

        #watermark a:hover {
            color: var(--accent);
            background: var(--accent);
        }
        
        .filter-info {
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
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
            background: var(--accent);
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
            
            .graph-node-actions {
                opacity: 1;
            }
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
            .visualization-modal {
                width: 95%;
                height: 70%;
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
    
    <!-- 3D Visualization Modal -->
    <div class="visualization-modal" id="visualizationModal">
        <div class="visualization-header">
            <div class="visualization-title">
                <i class="fas fa-cube"></i>
                <span id="visualizationTitle">3D Dependency Visualization</span>
            </div>
            <button class="visualization-close" id="visualizationClose">
                <i class="fas fa-times"></i>
            </button>
        </div>
        <div class="visualization-content">
            <canvas class="visualization-canvas" id="visualizationCanvas"></canvas>
            <div class="visualization-controls">
                <button class="visualization-control" id="resetView">
                    <i class="fas fa-sync-alt"></i> Reset View
                </button>
                <button class="visualization-control" id="toggleLabels">
                    <i class="fas fa-tag"></i> Toggle Labels
                </button>
                <button class="visualization-control" id="toggleOrbits">
                    <i class="fas fa-orbit"></i> Toggle Orbits
                </button>
            </div>
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
                </div>
                <div class="controls">
                    <button class="btn" onclick="classicDashboard.sortNodes('name')" id="sort-name">
                        <i class="fas fa-sort-alpha-down"></i> Name
                    </button>
                    <button class="btn" onclick="classicDashboard.sortNodes('type')" id="sort-type">
                        <i class="fas fa-layer-group"></i> Type
                    </button>
                    <button class="btn" onclick="classicDashboard.sortNodes('dependencies')" id="sort-deps">
                        <i class="fas fa-project-diagram"></i> Dependencies
                    </button>
                    <button class="btn" onclick="classicDashboard.filterByState('unused')" id="filter-unused">
                        <i class="fas fa-eye-slash"></i> Unused
                    </button>
                    <button class="btn" onclick="classicDashboard.filterByState('warning')" id="filter-warning">
                        <i class="fas fa-exclamation-triangle"></i> Warnings
                    </button>
                    <button class="btn" onclick="classicDashboard.resetFilters()">
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
                <button class="search-clear" id="search-clear" onclick="classicDashboard.clearSearch()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            
            <!-- Filter Info -->
            <div class="filter-info" id="filter-info" style="display: none;">
                <div>
                    <strong>Active Filters:</strong>
                    <div class="filter-tags" id="filter-tags"></div>
                </div>
                <button class="btn" onclick="classicDashboard.resetFilters()">
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
        // Enhanced Classic Dashboard with Modern Features
        class ClassicDashboard {
            constructor() {
                this.backdrop = document.getElementById('backdrop');
                this.commandPalette = document.getElementById('commandPalette');
                this.commandInput = document.getElementById('commandInput');
                this.commandList = document.getElementById('commandList');
                this.toastContainer = document.getElementById('toastContainer');
                this.quickActions = document.getElementById('quickActions');
                this.visualizationModal = document.getElementById('visualizationModal');
                this.visualizationCanvas = document.getElementById('visualizationCanvas');
                this.selectedCommandIndex = 0;
                this.isFullscreen = false;
                this.threeScene = null;
                
                // Get graph data with safe fallback
                try {
                    this.graphData = {{ graph_data | safe }} || this.getDefaultGraphData();
                } catch (error) {
                    console.warn('Failed to parse graph data, using default:', error);
                    this.graphData = this.getDefaultGraphData();
                }
                
                this.currentSort = 'name';
                this.currentStateFilter = null;
                this.currentSearch = '';
                this.filterTimeout = null;
                
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
                    },
                    {
                        id: 'reset-filters',
                        title: 'Reset Filters',
                        description: 'Clear all active filters and searches',
                        icon: 'fas fa-filter',
                        shortcut: 'Alt+R',
                        action: () => this.resetFilters()
                    }
                ];
                
                this.nodeIcons = {
                    'resource': 'fas fa-cube',
                    'module': 'fas fa-cubes',
                    'variable': 'fas fa-code',
                    'output': 'fas fa-arrow-right',
                    'data': 'fas fa-database',
                    'provider': 'fas fa-cog',
                    'local': 'fas fa-code',
                    'terraform': 'fas fa-sitemap'
                };
                
                this.stateConfig = {
                    'healthy': { class: 'node-healthy', icon: 'fas fa-check-circle', color: 'var(--success)' },
                    'unused': { class: 'node-unused', icon: 'fas fa-ban', color: 'var(--danger)' },
                    'external': { class: 'node-external', icon: 'fas fa-external-link-alt', color: 'var(--info)' },
                    'leaf': { class: 'node-leaf', icon: 'fas fa-leaf', color: 'var(--success)' },
                    'orphan': { class: 'node-orphan', icon: 'fas fa-unlink', color: 'var(--warning)' },
                    'warning': { class: 'node-warning', icon: 'fas fa-exclamation-triangle', color: 'var(--warning)' },
                    'active': { class: 'node-healthy', icon: 'fas fa-bolt', color: 'var(--success)' },
                    'integrated': { class: 'node-healthy', icon: 'fas fa-link', color: 'var(--success)' },
                    'isolated': { class: 'node-orphan', icon: 'fas fa-unlink', color: 'var(--warning)' },
                    'input': { class: 'node-healthy', icon: 'fas fa-sign-in-alt', color: 'var(--info)' },
                    'configuration': { class: 'node-healthy', icon: 'fas fa-cog', color: 'var(--info)' },
                    'external_data': { class: 'node-external', icon: 'fas fa-database', color: 'var(--info)' }
                };
                
                this.init();
            }
            
            getDefaultGraphData() {
                return {
                    nodes: [],
                    edges: [],
                    statistics: {
                        graph: {
                            node_count: 0,
                            edge_count: 0,
                            node_states: {},
                            edge_types: {},
                            graph_health_score: 0,
                            severity_counts: {
                                healthy: 0,
                                neutral: 0,
                                warning: 0,
                                error: 0
                            }
                        },
                        project: {
                            counts: {
                                resources: 0,
                                data_sources: 0,
                                modules: 0,
                                variables: 0,
                                outputs: 0,
                                providers: 0,
                                locals: 0,
                                total: 0
                            }
                        }
                    }
                };
            }
            
            init() {
                this.setupEventListeners();
                this.initializeStats();
                this.initializeSearch();
                this.renderGraphNodes();
                this.setupVisualization();
                this.showToast('Classic Dashboard Ready', 'Enhanced interface loaded successfully', 'success');
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
                    this.hideVisualization();
                });
                
                // Visualization close
                document.getElementById('visualizationClose').addEventListener('click', () => {
                    this.hideVisualization();
                });
                
                // Visualization controls
                document.getElementById('resetView').addEventListener('click', () => {
                    if (this.threeScene) this.threeScene.resetView();
                });
                
                document.getElementById('toggleLabels').addEventListener('click', () => {
                    if (this.threeScene) this.threeScene.toggleLabels();
                });
                
                document.getElementById('toggleOrbits').addEventListener('click', () => {
                    if (this.threeScene) this.threeScene.toggleOrbits();
                });
            }
            
            handleKeyboard(event) {
                // Global shortcuts
                if (event.key === 'Escape') {
                    this.hideCommandPalette();
                    this.hideVisualization();
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
                
                if (event.key === '/' && !event.ctrlKey && !event.metaKey) {
                    event.preventDefault();
                    document.getElementById('search-input').focus();
                }
                
                if (event.altKey && event.key === 'r') {
                    event.preventDefault();
                    this.resetFilters();
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
            
            // Command Palette Methods (same as dashboard)
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
            }
            
            executeCommand(command) {
                command.action();
                this.hideCommandPalette();
                this.showToast('Command Executed', command.title, 'success');
            }
            
            // Toast Methods
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
            
            // Search and Filter Methods
            initializeSearch() {
                const searchInput = document.getElementById('search-input');
                const searchClear = document.getElementById('search-clear');
                
                searchInput.addEventListener('input', (e) => {
                    const query = e.target.value;
                    this.updateSearchClear(query);
                    this.debounceFilter(query);
                });
            }
            
            updateSearchClear(query) {
                const searchClear = document.getElementById('search-clear');
                if (query.length > 0) {
                    searchClear.classList.add('visible');
                } else {
                    searchClear.classList.remove('visible');
                }
            }
            
            clearSearch() {
                const searchInput = document.getElementById('search-input');
                searchInput.value = '';
                this.updateSearchClear('');
                this.filterNodes('');
            }
            
            debounceFilter(query) {
                clearTimeout(this.filterTimeout);
                this.filterTimeout = setTimeout(() => {
                    this.filterNodes(query);
                }, 100);
            }
            
            filterNodes(query) {
                this.currentSearch = query;
                this.renderGraphNodes();
            }
            
            // Stats Methods
            initializeStats() {
                const statsGrid = document.getElementById('stats-grid');
                const nodes = this.graphData.nodes || [];
                const edges = this.graphData.edges || [];
                
                // Calculate statistics
                const totalNodes = nodes.length;
                const totalEdges = edges.length;
                const resourceCount = nodes.filter(n => n.type === 'resource').length;
                const moduleCount = nodes.filter(n => n.type === 'module').length;
                const variableCount = nodes.filter(n => n.type === 'variable').length;
                const healthyCount = nodes.filter(n => 
                    ['active', 'integrated', 'leaf', 'input', 'configuration', 'healthy'].includes(n.state)
                ).length;
                const healthScore = totalNodes > 0 ? Math.round((healthyCount / totalNodes) * 100) : 100;
                
                statsGrid.innerHTML = `
                    <div class="stat-card" onclick="classicDashboard.showToast('Total Components', '${totalNodes} infrastructure components loaded', 'info')">
                        <div class="stat-card-header">
                            <div class="stat-icon">
                                <i class="fas fa-cubes"></i>
                            </div>
                        </div>
                        <div class="stat-value">${totalNodes}</div>
                        <div class="stat-label">Total Components</div>
                        <div class="state-breakdown">
                            <div class="state-item">
                                <span class="state-name">Resources</span>
                                <span class="state-count">${resourceCount}</span>
                            </div>
                            <div class="state-item">
                                <span class="state-name">Modules</span>
                                <span class="state-count">${moduleCount}</span>
                            </div>
                            <div class="state-item">
                                <span class="state-name">Variables</span>
                                <span class="state-count">${variableCount}</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="stat-card" onclick="classicDashboard.showToast('Dependencies', '${totalEdges} dependency relationships', 'info')">
                        <div class="stat-card-header">
                            <div class="stat-icon">
                                <i class="fas fa-project-diagram"></i>
                            </div>
                        </div>
                        <div class="stat-value">${totalEdges}</div>
                        <div class="stat-label">Dependencies</div>
                        <div class="stat-trend ${this.calculateAverageDependencies() > 2 ? 'positive' : 'negative'}">
                            <i class="fas fa-chart-line"></i> ${this.calculateAverageDependencies()} avg per component
                        </div>
                    </div>
                    
                    <div class="stat-card" onclick="classicDashboard.showToast('Connected Groups', '${this.calculateConnectedComponents()} connected component groups', 'info')">
                        <div class="stat-card-header">
                            <div class="stat-icon">
                                <i class="fas fa-network-wired"></i>
                            </div>
                        </div>
                        <div class="stat-value">${this.calculateConnectedComponents()}</div>
                        <div class="stat-label">Connected Groups</div>
                    </div>
                    
                    <div class="stat-card" onclick="classicDashboard.showToast('Health Score', '${healthScore}% of components are healthy', '${healthScore > 80 ? 'success' : 'warning'}')">
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
            
            calculateAverageDependencies() {
                const nodes = this.graphData.nodes || [];
                if (nodes.length === 0) return 0;
                const totalDeps = nodes.reduce((sum, node) => 
                    sum + (node.dependencies_out || 0) + (node.dependencies_in || 0), 0);
                return (totalDeps / nodes.length).toFixed(1);
            }
            
            calculateConnectedComponents() {
                const nodes = this.graphData.nodes || [];
                const edges = this.graphData.edges || [];
                if (nodes.length === 0) return 0;
                
                const visited = new Set();
                let components = 0;
                const adj = new Map();
                
                nodes.forEach(node => adj.set(node.id, []));
                edges.forEach(edge => {
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
                
                nodes.forEach(node => {
                    if (!visited.has(node.id)) {
                        dfs(node.id);
                        components++;
                    }
                });
                
                return components;
            }
            
            // Node Rendering Methods
            renderGraphNodes() {
                const container = document.getElementById('graph-nodes-container');
                const nodes = this.graphData.nodes || [];
                
                let nodesToShow = nodes.filter(node => {
                    if (this.currentStateFilter && node.state !== this.currentStateFilter) {
                        return false;
                    }
                    
                    if (this.currentSearch) {
                        const searchTerm = this.currentSearch.toLowerCase();
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
                    switch (this.currentSort) {
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
                            <p style="margin-top: 12px; font-size: 0.9em; color: var(--text-secondary);">
                                Search across: name, type, state, description, and file paths
                            </p>
                        </div>
                    `;
                    return;
                }
                
                const fragment = document.createDocumentFragment();
                
                nodesToShow.forEach(node => {
                    const nodeElement = this.createNodeElement(node);
                    fragment.appendChild(nodeElement);
                });
                
                container.innerHTML = '';
                container.appendChild(fragment);
                
                this.updateFilterInfo();
            }
            
            createNodeElement(node) {
                const nodeElement = document.createElement('div');
                const state = this.stateConfig[node.state] || this.stateConfig.healthy;
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
                            <i class="${this.nodeIcons[node.type] || 'fas fa-cube'}"></i>
                        </div>
                        <div class="graph-node-title-container">
                            <div class="graph-node-title" title="${node.label}">${node.label}</div>
                            <div class="graph-node-type">${node.type} • ${node.subtype || 'N/A'}</div>
                            <span class="graph-node-state" style="background: ${state.color}15; color: ${state.color}; border: 1px solid ${state.color}30;">
                                <i class="${state.icon}"></i> ${node.state.toUpperCase()}
                            </span>
                            ${badges.length > 0 ? `<div class="graph-node-badges">${badges.join('')}</div>` : ''}
                        </div>
                        <div class="graph-node-actions">
                            <button class="node-action" onclick="classicDashboard.showVisualization(${node.id})" title="3D Visualization">
                                <i class="fas fa-cube"></i>
                            </button>
                            <button class="node-action" onclick="classicDashboard.showNodeDetails(${node.id})" title="View Details">
                                <i class="fas fa-info-circle"></i>
                            </button>
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
                    ${details.loc ? `<div class="graph-node-reason"><i class="fas fa-file"></i> ${details.loc}</div>` : ''}
                `;
                
                return nodeElement;
            }
            
            sortNodes(criteria) {
                this.currentSort = criteria;
                document.querySelectorAll('.btn').forEach(btn => btn.classList.remove('active'));
                document.getElementById(`sort-${criteria}`).classList.add('active');
                this.renderGraphNodes();
            }
            
            filterByState(state) {
                this.currentStateFilter = this.currentStateFilter === state ? null : state;
                document.querySelectorAll('.btn').forEach(btn => btn.classList.remove('active'));
                document.getElementById('sort-name').classList.add('active');
                
                if (this.currentStateFilter) {
                    document.getElementById(`filter-${state}`).classList.add('active');
                }
                
                this.renderGraphNodes();
            }
            
            resetFilters() {
                this.currentSearch = '';
                this.currentStateFilter = null;
                this.currentSort = 'name';
                
                document.querySelectorAll('.btn').forEach(btn => btn.classList.remove('active'));
                document.getElementById('sort-name').classList.add('active');
                document.getElementById('search-input').value = '';
                document.getElementById('search-clear').classList.remove('visible');
                
                this.renderGraphNodes();
                this.showToast('Filters Reset', 'All filters and searches cleared', 'info');
            }
            
            updateFilterInfo() {
                const filterInfo = document.getElementById('filter-info');
                const filterTags = document.getElementById('filter-tags');
                
                const activeFilters = [];
                if (this.currentSearch) activeFilters.push(`Search: "${this.currentSearch}"`);
                if (this.currentStateFilter) activeFilters.push(`State: ${this.currentStateFilter}`);
                if (this.currentSort !== 'name') activeFilters.push(`Sorted by: ${this.currentSort}`);
                
                if (activeFilters.length > 0) {
                    filterInfo.style.display = 'flex';
                    filterTags.innerHTML = activeFilters.map(filter => 
                        `<span class="filter-tag">${filter} <span class="remove" onclick="classicDashboard.removeFilter('${filter.split(':')[0].trim().toLowerCase()}')"><i class="fas fa-times"></i></span></span>`
                    ).join('');
                } else {
                    filterInfo.style.display = 'none';
                }
            }
            
            removeFilter(filterType) {
                switch (filterType) {
                    case 'search':
                        this.clearSearch();
                        break;
                    case 'state':
                        this.currentStateFilter = null;
                        document.querySelectorAll('.btn').forEach(btn => btn.classList.remove('active'));
                        document.getElementById('sort-name').classList.add('active');
                        break;
                    case 'sorted':
                        this.currentSort = 'name';
                        document.querySelectorAll('.btn').forEach(btn => btn.classList.remove('active'));
                        document.getElementById('sort-name').classList.add('active');
                        break;
                }
                this.renderGraphNodes();
            }
            
            setupVisualization() {
                this.threeScene = {
                    scene: null,
                    camera: null,
                    renderer: null,
                    objects: [],
                    animationId: null,
                    webGLAvailable: false,
                    
                    checkWebGLAvailability: () => {
                        try {
                            const canvas = document.createElement('canvas');
                            const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                            return !!(gl && gl instanceof WebGLRenderingContext);
                        } catch (e) {
                            return false;
                        }
                    },
                    
                    init: (canvas) => {
                        this.threeScene.webGLAvailable = this.threeScene.checkWebGLAvailability();
                        
                        if (!this.threeScene.webGLAvailable) {
                            this.threeScene.showFallbackVisualization(canvas);
                            return;
                        }
                        
                        try {
                            // Scene setup
                            this.threeScene.scene = new THREE.Scene();
                            this.threeScene.scene.background = new THREE.Color(0x0f172a);
                            
                            // Camera
                            const aspect = canvas.clientWidth / canvas.clientHeight;
                            this.threeScene.camera = new THREE.PerspectiveCamera(75, aspect, 0.1, 1000);
                            this.threeScene.camera.position.set(0, 0, 50);
                            
                            // Renderer with error handling
                            const contextAttributes = {
                                antialias: true,
                                alpha: true,
                                preserveDrawingBuffer: false
                            };
                            
                            this.threeScene.renderer = new THREE.WebGLRenderer({ 
                                canvas: canvas, 
                                ...contextAttributes
                            });
                            
                            if (!this.threeScene.renderer) {
                                throw new Error('WebGLRenderer creation failed');
                            }
                            
                            this.threeScene.renderer.setSize(canvas.clientWidth, canvas.clientHeight);
                            this.threeScene.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
                            
                            // Lighting
                            const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
                            this.threeScene.scene.add(ambientLight);
                            
                            const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
                            directionalLight.position.set(50, 50, 50);
                            this.threeScene.scene.add(directionalLight);
                            
                            // Create demo scene
                            this.threeScene.createDemoScene();
                            
                            // Handle window resize
                            const resizeObserver = new ResizeObserver(() => {
                                const width = canvas.clientWidth;
                                const height = canvas.clientHeight;
                                this.threeScene.camera.aspect = width / height;
                                this.threeScene.camera.updateProjectionMatrix();
                                this.threeScene.renderer.setSize(width, height);
                            });
                            
                            resizeObserver.observe(canvas);
                            
                            // Start animation
                            this.threeScene.animate();
                            
                        } catch (error) {
                            console.error('Three.js initialization failed:', error);
                            this.threeScene.showFallbackVisualization(canvas);
                        }
                    },
                    
                    showFallbackVisualization: (canvas) => {
                        console.log('Using fallback 2D visualization');
                        const ctx = canvas.getContext('2d');
                        if (!ctx) return;
                        
                        // Clear canvas
                        ctx.fillStyle = '#0f172a';
                        ctx.fillRect(0, 0, canvas.width, canvas.height);
                        
                        // Draw fallback message
                        ctx.fillStyle = '#e2e8f0';
                        ctx.font = '16px Arial';
                        ctx.textAlign = 'center';
                        ctx.fillText('3D Visualization Not Available', canvas.width / 2, canvas.height / 2 - 20);
                        ctx.font = '14px Arial';
                        ctx.fillText('WebGL is required for 3D graphics', canvas.width / 2, canvas.height / 2 + 10);
                        ctx.fillText('Try using a different browser or enable WebGL', canvas.width / 2, canvas.height / 2 + 30);
                        
                        // Draw simple 2D graph
                        this.threeScene.create2DFallbackGraph(ctx, canvas);
                    },
                    
                    create2DFallbackGraph: (ctx, canvas) => {
                        // Draw a simple 2D node graph
                        const centerX = canvas.width / 2;
                        const centerY = canvas.height / 2;
                        const radius = 80;
                        
                        // Draw central node
                        ctx.fillStyle = '#3b82f6';
                        ctx.beginPath();
                        ctx.arc(centerX, centerY, 15, 0, Math.PI * 2);
                        ctx.fill();
                        
                        // Draw orbiting nodes
                        const nodeCount = 6;
                        const colors = ['#10b981', '#8b5cf6', '#f59e0b', '#ef4444', '#06b6d4', '#84cc16'];
                        
                        for (let i = 0; i < nodeCount; i++) {
                            const angle = (i / nodeCount) * Math.PI * 2;
                            const x = centerX + Math.cos(angle) * radius;
                            const y = centerY + Math.sin(angle) * radius;
                            
                            // Draw connection line
                            ctx.strokeStyle = '#475569';
                            ctx.setLineDash([5, 5]);
                            ctx.beginPath();
                            ctx.moveTo(centerX, centerY);
                            ctx.lineTo(x, y);
                            ctx.stroke();
                            ctx.setLineDash([]);
                            
                            // Draw node
                            ctx.fillStyle = colors[i];
                            ctx.beginPath();
                            ctx.arc(x, y, 8, 0, Math.PI * 2);
                            ctx.fill();
                            
                            // Add subtle animation with requestAnimationFrame
                            if (this.threeScene.animationId) {
                                cancelAnimationFrame(this.threeScene.animationId);
                            }
                            
                            this.threeScene.animate2DGraph(ctx, canvas, centerX, centerY, radius, nodeCount, colors);
                        }
                    },
                    
                    animate2DGraph: (ctx, canvas, centerX, centerY, radius, nodeCount, colors) => {
                        const animate = () => {
                            // Clear canvas
                            ctx.fillStyle = '#0f172a';
                            ctx.fillRect(0, 0, canvas.width, canvas.height);
                            
                            // Draw central node
                            ctx.fillStyle = '#3b82f6';
                            ctx.beginPath();
                            ctx.arc(centerX, centerY, 15, 0, Math.PI * 2);
                            ctx.fill();
                            
                            // Draw orbiting nodes with animation
                            const time = Date.now() * 0.001;
                            
                            for (let i = 0; i < nodeCount; i++) {
                                const angle = (i / nodeCount) * Math.PI * 2 + time * 0.5;
                                const x = centerX + Math.cos(angle) * radius;
                                const y = centerY + Math.sin(angle) * radius;
                                
                                // Draw connection line
                                ctx.strokeStyle = '#475569';
                                ctx.setLineDash([5, 5]);
                                ctx.beginPath();
                                ctx.moveTo(centerX, centerY);
                                ctx.lineTo(x, y);
                                ctx.stroke();
                                ctx.setLineDash([]);
                                
                                // Draw animated node
                                ctx.fillStyle = colors[i];
                                ctx.beginPath();
                                ctx.arc(x, y, 8, 0, Math.PI * 2);
                                ctx.fill();
                            }
                            
                            // Draw info text
                            ctx.fillStyle = '#e2e8f0';
                            ctx.font = '16px Arial';
                            ctx.textAlign = 'center';
                            ctx.fillText('2D Fallback Visualization', canvas.width / 2, 30);
                            ctx.font = '12px Arial';
                            ctx.fillText('WebGL is not available in your environment', canvas.width / 2, canvas.height - 20);
                            
                            this.threeScene.animationId = requestAnimationFrame(animate);
                        };
                        
                        animate();
                    },
                    
                    createDemoScene: () => {
                        // Clear existing objects
                        this.threeScene.objects.forEach(obj => {
                            this.threeScene.scene.remove(obj);
                        });
                        this.threeScene.objects = [];
                        
                        // Create central node
                        const centralGeometry = new THREE.SphereGeometry(3, 16, 16);
                        const centralMaterial = new THREE.MeshPhongMaterial({ 
                            color: 0x3b82f6,
                            shininess: 100 
                        });
                        const centralNode = new THREE.Mesh(centralGeometry, centralMaterial);
                        this.threeScene.scene.add(centralNode);
                        this.threeScene.objects.push(centralNode);
                        
                        // Create orbiting nodes
                        const orbitCount = 6;
                        for (let i = 0; i < orbitCount; i++) {
                            const cubeGeometry = new THREE.BoxGeometry(2, 2, 2);
                            const cubeMaterial = new THREE.MeshPhongMaterial({ 
                                color: this.threeScene.getColorForIndex(i),
                                shininess: 80
                            });
                            const cube = new THREE.Mesh(cubeGeometry, cubeMaterial);
                            
                            // Position in orbit
                            const angle = (i / orbitCount) * Math.PI * 2;
                            const radius = 15;
                            cube.position.x = Math.cos(angle) * radius;
                            cube.position.y = Math.sin(angle) * radius;
                            cube.position.z = (Math.random() - 0.5) * 10;
                            
                            // Store orbit properties
                            cube.userData = {
                                angle: angle,
                                radius: radius,
                                speed: 0.5 + Math.random() * 0.5,
                                orbitOffset: Math.random() * Math.PI * 2
                            };
                            
                            this.threeScene.scene.add(cube);
                            this.threeScene.objects.push(cube);
                            
                            // Create connection lines
                            const lineGeometry = new THREE.BufferGeometry().setFromPoints([
                                new THREE.Vector3(0, 0, 0),
                                new THREE.Vector3(cube.position.x, cube.position.y, cube.position.z)
                            ]);
                            const lineMaterial = new THREE.LineBasicMaterial({ 
                                color: 0x64748b,
                                transparent: true,
                                opacity: 0.6
                            });
                            const line = new THREE.Line(lineGeometry, lineMaterial);
                            this.threeScene.scene.add(line);
                            this.threeScene.objects.push(line);
                        }
                    },
                    
                    getColorForIndex: (index) => {
                        const colors = [
                            0x10b981, 0x8b5cf6, 0xf59e0b, 
                            0xef4444, 0x06b6d4, 0x84cc16
                        ];
                        return colors[index % colors.length];
                    },
                    
                    animate: () => {
                        if (!this.threeScene.webGLAvailable) return;
                        
                        this.threeScene.animationId = requestAnimationFrame(() => this.threeScene.animate());
                        
                        // Animate orbiting nodes
                        this.threeScene.objects.forEach((obj, index) => {
                            if (index > 0 && obj.userData) {
                                const time = Date.now() * 0.001;
                                obj.userData.angle += obj.userData.speed * 0.01;
                                
                                obj.position.x = Math.cos(obj.userData.angle + obj.userData.orbitOffset) * obj.userData.radius;
                                obj.position.y = Math.sin(obj.userData.angle + obj.userData.orbitOffset) * obj.userData.radius;
                                
                                obj.rotation.x += 0.01;
                                obj.rotation.y += 0.01;
                                
                                // Update connection lines
                                if (this.threeScene.objects[index + 5]) {
                                    const line = this.threeScene.objects[index + 5];
                                    if (line.isLine) {
                                        line.geometry.attributes.position.array[3] = obj.position.x;
                                        line.geometry.attributes.position.array[4] = obj.position.y;
                                        line.geometry.attributes.position.array[5] = obj.position.z;
                                        line.geometry.attributes.position.needsUpdate = true;
                                    }
                                }
                            }
                        });
                        
                        // Camera movement
                        const time = Date.now() * 0.001;
                        this.threeScene.camera.position.x = Math.sin(time * 0.2) * 5;
                        this.threeScene.camera.position.y = Math.cos(time * 0.2) * 5;
                        this.threeScene.camera.lookAt(0, 0, 0);
                        
                        this.threeScene.renderer.render(this.threeScene.scene, this.threeScene.camera);
                    },
                    
                    resetView: () => {
                        if (this.threeScene.webGLAvailable && this.threeScene.camera) {
                            this.threeScene.camera.position.set(0, 0, 50);
                            this.threeScene.camera.lookAt(0, 0, 0);
                            classicDashboard.showToast('View Reset', 'Camera position reset', 'info');
                        }
                    },
                    
                    toggleLabels: () => {
                        const action = this.threeScene.webGLAvailable ? '3D Labels' : '2D Labels';
                        classicDashboard.showToast(`${action} Toggled`, 'Label visibility changed', 'info');
                    },
                    
                    toggleOrbits: () => {
                        if (this.threeScene.webGLAvailable) {
                            if (this.threeScene.animationId) {
                                cancelAnimationFrame(this.threeScene.animationId);
                                this.threeScene.animationId = null;
                                classicDashboard.showToast('Animation Paused', '3D animation paused', 'warning');
                            } else {
                                this.threeScene.animate();
                                classicDashboard.showToast('Animation Resumed', '3D animation resumed', 'success');
                            }
                        } else {
                            classicDashboard.showToast('2D Mode', 'Animation controls in 2D mode', 'info');
                        }
                    },
                    
                    cleanup: () => {
                        if (this.threeScene.animationId) {
                            cancelAnimationFrame(this.threeScene.animationId);
                            this.threeScene.animationId = null;
                        }
                        if (this.threeScene.renderer) {
                            this.threeScene.renderer.dispose();
                        }
                    }
                };
            }
            
            showVisualization(nodeId) {
                const node = this.graphData.nodes.find(n => n.id === nodeId);
                if (!node) return;
                
                document.getElementById('visualizationTitle').textContent = `Dependency Visualization: ${node.label}`;
                this.backdrop.classList.add('show');
                this.visualizationModal.classList.add('show');
                
                // Initialize visualization on first open
                if (!this.threeScene.webGLAvailable && !this.threeScene.scene) {
                    setTimeout(() => {
                        try {
                            this.threeScene.init(this.visualizationCanvas);
                            const mode = this.threeScene.webGLAvailable ? '3D' : '2D';
                            this.showToast('Visualization Ready', `${mode} dependency visualization loaded`, 'success');
                        } catch (error) {
                            console.error('Visualization initialization failed:', error);
                            this.showToast('Visualization Error', 'Failed to load visualization', 'error');
                        }
                    }, 100);
                } else {
                    const mode = this.threeScene.webGLAvailable ? '3D' : '2D';
                    this.showToast('Visualization', `${mode} view for ${node.label}`, 'info');
                }
                
                // Ensure proper canvas sizing
                setTimeout(() => {
                    const canvas = this.visualizationCanvas;
                    if (this.threeScene.renderer && canvas) {
                        const width = canvas.clientWidth;
                        const height = canvas.clientHeight;
                        this.threeScene.renderer.setSize(width, height, false);
                    }
                }, 50);
            }
            
            showVisualization(nodeId) {
                const node = this.graphData.nodes.find(n => n.id === nodeId);
                if (!node) return;
                
                document.getElementById('visualizationTitle').textContent = `Dependencies: ${node.label}`;
                this.backdrop.classList.add('show');
                this.visualizationModal.classList.add('show');
                
                // Initialize visualization
                setTimeout(() => {
                    try {
                        const canvas = this.visualizationCanvas;
                        // Ensure canvas is proper size
                        canvas.width = canvas.clientWidth;
                        canvas.height = canvas.clientHeight;
                        
                        this.threeScene.init(canvas, nodeId);
                        this.showToast('Dependency View', `Showing dependencies for ${node.label}`, 'success');
                    } catch (error) {
                        console.error('Visualization failed:', error);
                        this.showToast('Error', 'Could not load dependency view', 'error');
                    }
                }, 100);
            }

            hideVisualization() {
                this.backdrop.classList.remove('show');
                this.visualizationModal.classList.remove('show');
                
                // Clean up
                if (this.threeScene && this.threeScene.cleanup) {
                    this.threeScene.cleanup();
                }
            }
            
            showNodeDetails(nodeId) {
                const node = this.graphData.nodes.find(n => n.id === nodeId);
                if (!node) return;
                
                const details = node.details || {};
                const message = `
                    <strong>${node.label}</strong><br>
                    Type: ${node.type}${node.subtype ? ` (${node.subtype})` : ''}<br>
                    State: ${node.state}<br>
                    ${node.state_reason ? `Reason: ${node.state_reason}<br>` : ''}
                    ${details.loc ? `Location: ${details.loc}<br>` : ''}
                    Dependencies: ${node.dependencies_out || 0} outgoing, ${node.dependencies_in || 0} incoming
                `;
                
                this.showToast('Node Details', message, 'info');
            }
            
            // Utility Methods
            exportData() {
                const data = {
                    timestamp: new Date().toISOString(),
                    graphData: this.graphData,
                    exportType: 'classic_dashboard'
                };
                
                const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `classic-dashboard-export-${new Date().toISOString().split('T')[0]}.json`;
                a.click();
                URL.revokeObjectURL(url);
                
                this.showToast('Export Complete', 'Dashboard data exported successfully', 'success');
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
                this.showToast('Refreshing', 'Reloading dashboard data...', 'info');
                setTimeout(() => {
                    this.initializeStats();
                    this.renderGraphNodes();
                    this.showToast('Refresh Complete', 'Data updated successfully', 'success');
                }, 1000);
            }
            
            showHelp() {
                const helpContent = `
Classic Dashboard Help

📊 Enhanced Features:
• Modern command palette with shortcuts
• Advanced search and filtering
• 3D dependency visualization
• Interactive statistics cards
• Touch-friendly interface

⌨️ Keyboard Shortcuts:
• / - Focus search
• Ctrl+K / Cmd+K - Command palette
• F1 - Show this help
• F11 - Toggle fullscreen
• Ctrl+R / Cmd+R - Refresh data
• Ctrl+E / Cmd+E - Export data
• Alt+R - Reset filters
• Escape - Close modals

👆 Node Actions:
• Click node for details
• 3D cube icon for visualization
• Info icon for quick details
• Hover for action buttons

🔍 Search Tips:
• Search by name, type, state
• Filter by unused/warning states
• Sort by dependencies, name, type
• Use clear buttons to reset

For more information, visit the documentation.
                `;
                
                this.showToast('Help & Shortcuts', 'Check the console for detailed help', 'info');
                console.log(helpContent);
            }
        }
        
        // Initialize the dashboard
        let classicDashboard;
        
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                classicDashboard = new ClassicDashboard();
            });
        } else {
            classicDashboard = new ClassicDashboard();
        }
    </script>
</body>
</html>
"""
