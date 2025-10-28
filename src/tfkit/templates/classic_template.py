# templates/classic_template.py
from .base_template import BaseTemplate


class ClassicTemplate(BaseTemplate):
    """Enhanced classic template with modern UI, command palette, and 3D visualization."""

    def _build_stats_grid(self):
        total_resources = len(self.project.resources)
        live_resources = len(
            [r for r in self.project.resources if r.lifecycle == "create"]
        )
        replace_resources = len(
            [r for r in self.project.resources if r.lifecycle == "replace"]
        )
        delete_resources = len(
            [r for r in self.project.resources if r.lifecycle == "delete"]
        )

        # Get provider distribution
        provider_counts = {}
        for resource in self.project.resources:
            provider = resource.type.split("_")[0]
            provider_counts[provider] = provider_counts.get(provider, 0) + 1

        # Sort providers by count
        sorted_providers = sorted(
            provider_counts.items(), key=lambda x: x[1], reverse=True
        )

        # Generate provider list HTML
        provider_list_html = []
        for provider, count in sorted_providers[:3]:  # Show top 3 providers
            provider_list_html.append(f"""
            <div class="provider-item">
                <i class="ph-cube-thin"></i>
                <span>{provider}</span>
                <span class="provider-count">{count}</span>
            </div>""")
        provider_list_html = "".join(provider_list_html)

        total_health_score = 100 - (delete_resources + replace_resources) * 5
        health_class = "warning" if total_health_score < 80 else "positive"

        return f"""
        <div class="stats-grid">
            <div class="stat-card highlight" style="background: linear-gradient(135deg, var(--accent) 0%, var(--accent-secondary) 100%);">
                <div class="stat-header">
                    <i class="ph-cube-thin"></i>
                    <span>Resource Overview</span>
                </div>
                <div class="stat-body">
                    <div class="stat-row major">
                        <div class="stat-title">Total Resources</div>
                        <div class="stat-value">{total_resources}</div>
                    </div>
                    <div class="stat-row">
                        <div class="stat-title">Live Resources</div>
                        <div class="stat-value">{live_resources}</div>
                    </div>
                    <div class="stat-row warning">
                        <div class="stat-title">Resources to Replace</div>
                        <div class="stat-value">{replace_resources}</div>
                    </div>
                    <div class="stat-row danger">
                        <div class="stat-title">Resources to Delete</div>
                        <div class="stat-value">{delete_resources}</div>
                    </div>
                </div>
                <div class="stat-footer clickable">
                    <span>View Resource Details</span>
                    <i class="ph-arrow-right-thin"></i>
                </div>
            </div>

            <div class="stat-card">
                <div class="stat-header">
                    <i class="ph-chart-line-up-thin"></i>
                    <span>Project Health</span>
                </div>
                <div class="stat-body">
                    <div class="stat-row major">
                        <div class="stat-title">Health Score</div>
                        <div class="stat-value with-trend">
                            {total_health_score}%
                            <span class="trend {health_class}">
                                <i class="ph-trend-{"up" if health_class == "positive" else "down"}-thin"></i>
                            </span>
                        </div>
                    </div>
                </div>
                <div class="stat-footer">
                    Based on resource state and changes
                </div>
            </div>

            <div class="stat-card">
                <div class="stat-header">
                    <i class="ph-plug-thin"></i>
                    <span>Provider Distribution</span>
                </div>
                <div class="stat-body">
                    <div class="provider-list">
                        {provider_list_html}
                    </div>
                </div>
                <div class="stat-footer">
                    Showing top 3 providers by usage
                </div>
            </div>
        </div>
        """

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
            column-count: 4;
            column-gap: 24px;
            margin: 24px;
            margin-bottom: 32px;
        }

        @media (max-width: 1600px) { .stats-grid { column-count: 4; } }
        @media (max-width: 1200px) { .stats-grid { column-count: 2; } }
        @media (max-width: 768px) { .stats-grid { column-count: 1; } }

        .stat-card {
            break-inside: avoid;
            margin-bottom: 24px;
            width: 100%;
            background: var(--bg-secondary);
            border-radius: 16px;
            border: 1px solid var(--border);
            position: relative;
            overflow: hidden;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
            cursor: pointer;
        }

        .stat-card.highlight {
            background: linear-gradient(135deg, var(--accent) 0%, var(--accent-secondary) 100%);
            color: white;
            border: none;
        }

        .stat-card {
            padding: 20px;
        }

        .stat-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
            border-color: var(--accent);
        }

        .stat-header {
            display: flex;
            align-items: center;
            gap: 12px;
            color: var(--text-secondary);
            font-size: 0.9em;
            font-weight: 600;
            padding-bottom: 16px;
            border-bottom: 1px solid var(--border);
        }

        .stat-header i {
            font-size: 1.1em;
        }

        .stat-body {
            padding: 16px 0;
        }

        .stat-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
        }

        .stat-row.major {
            padding: 12px 0;
        }

        .stat-row.major .stat-value {
            font-size: 1.8em;
        }

        .stat-row.warning .stat-value {
            color: var(--warning);
        }

        .stat-row.danger .stat-value {
            color: var(--danger);
        }

        .stat-title {
            color: var(--text-secondary);
            font-size: 0.9em;
        }

        .stat-value {
            font-weight: 600;
            font-size: 1.1em;
            font-family: 'Exo 2', sans-serif;
        }

        .stat-value.with-trend {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .trend {
            font-size: 0.7em;
            padding: 4px;
            border-radius: 4px;
        }

        .trend.positive {
            color: var(--success);
        }

        .trend.negative {
            color: var(--danger);
        }

        .trend.warning {
            color: var(--warning);
        }

        .stat-footer {
            padding-top: 16px;
            border-top: 1px solid var(--border);
            color: var(--text-secondary);
            font-size: 0.85em;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .stat-footer.clickable {
            cursor: pointer;
            justify-content: space-between;
            color: var(--accent);
            font-weight: 500;
        }

        .stat-footer.clickable:hover {
            color: var(--accent-secondary);
        }

        /* Provider List Styles */
        .provider-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
            padding: 8px 0;
        }

        .provider-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 8px;
            border-radius: 8px;
            background: var(--bg-primary);
            font-size: 0.9em;
        }

        .provider-item i {
            font-size: 1.2em;
            color: var(--accent);
            width: 20px;
            text-align: center;
        }

        .provider-count {
            margin-left: auto;
            background: var(--bg-tertiary);
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }

        /* Highlight Card Styles */
        .stat-card.highlight .stat-header {
            color: rgba(255, 255, 255, 0.9);
            border-color: rgba(255, 255, 255, 0.2);
        }

        .stat-card.highlight .stat-title {
            color: rgba(255, 255, 255, 0.7);
        }

        .stat-card.highlight .stat-value {
            color: white;
        }

        .stat-card.highlight .stat-footer {
            color: rgba(255, 255, 255, 0.7);
            border-color: rgba(255, 255, 255, 0.2);
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
            column-count: 4;
            column-gap: 20px;
            padding: 20px;
        }

        @media (max-width: 1600px) { .graph-nodes { column-count: 3; } }
        @media (max-width: 1200px) { .graph-nodes { column-count: 2; } }
        @media (max-width: 768px) { .graph-nodes { column-count: 1; } }

        .graph-node {
            break-inside: avoid;
            margin-bottom: 20px;
            display: inline-block;
            width: 100%;
            background: var(--bg-primary);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 20px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1),
                      0 2px 4px -1px rgba(0, 0, 0, 0.06);
            cursor: pointer;
        }

        .graph-node:hover {
            border-color: var(--accent);
            transform: translateY(-2px) scale(1.01);
            box-shadow: 0 8px 15px -3px rgba(0, 0, 0, 0.1),
                      0 4px 6px -2px rgba(0, 0, 0, 0.05);
        }

        .graph-node:hover .graph-node-icon {
            transform: scale(1.05);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }

        .graph-node:active {
            transform: translateY(-1px) scale(1.005);
        }

        .node-unused {
            background: linear-gradient(135deg, var(--danger) 0%, var(--bg-primary) 3%);
            border-color: var(--danger);
        }
        .node-external {
            background: linear-gradient(135deg, var(--info) 0%, var(--bg-primary) 3%);
            border-color: var(--info);
        }
        .node-leaf {
            background: linear-gradient(135deg, var(--success) 0%, var(--bg-primary) 3%);
            border-color: var(--success);
        }
        .node-orphan {
            background: linear-gradient(135deg, var(--warning) 0%, var(--bg-primary) 3%);
            border-color: var(--warning);
        }
        .node-warning {
            background: linear-gradient(135deg, var(--warning) 0%, var(--bg-primary) 3%);
            border-color: var(--warning);
        }
        .node-healthy {
            background: linear-gradient(135deg, var(--success) 0%, var(--bg-primary) 3%);
            border-color: var(--success);
        }

        .graph-node-header {
            display: flex;
            align-items: flex-start;
            margin-bottom: 16px;
            gap: 16px;
            position: relative;
        }

        .graph-node-icon {
            width: 48px;
            height: 48px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 12px;
            background: var(--accent);
            flex-shrink: 0;
            font-size: 1.3em;
            color: var(--bg-primary);
            transition: all 0.2s ease;
            position: relative;
            overflow: hidden;
        }

        .graph-node-icon::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, rgba(255,255,255,0.2) 0%, rgba(255,255,255,0) 60%);
        }

        .graph-node-title-container {
            flex: 1;
            min-width: 0;
        }

        .graph-node-title {
            font-weight: 700;
            font-size: 1.2em;
            margin-bottom: 6px;
            overflow: hidden;
            text-overflow: ellipsis;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            color: var(--text-primary);
            line-height: 1.3;
        }

        .graph-node-type {
            color: var(--text-secondary);
            font-size: 0.9em;
            font-weight: 600;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .graph-node-type i {
            font-size: 1.1em;
            opacity: 0.7;
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
            gap: 8px;
            flex-wrap: wrap;
            margin-top: 12px;
        }

        .graph-node-badge {
            background: var(--bg-tertiary);
            color: var(--text-primary);
            font-size: 0.75em;
            padding: 4px 10px;
            border-radius: 20px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 4px;
            border: 1px solid var(--border);
            transition: all 0.2s ease;
        }

        .graph-node-badge i {
            font-size: 1.1em;
        }

        .graph-node-badge.warning {
            background: var(--warning);
            color: var(--bg-primary);
            border-color: var(--warning);
        }

        .graph-node-badge.danger {
            background: var(--danger);
            color: white;
            border-color: var(--danger);
        }

        .graph-node-badge.success {
            background: var(--success);
            color: white;
            border-color: var(--success);
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
            padding: 12px 18px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            border-top: 1px solid var(--border);
            background: linear-gradient(90deg, rgba(0,0,0,0.02), transparent);
            border-radius: 12px;
        }

        .footer-left {
            display: flex;
            align-items: center;
            gap: 12px;
            color: var(--text-secondary);
            font-size: 0.9em;
        }

        .footer-left .version {
            font-weight: 600;
            color: var(--text-primary);
            font-size: 0.95em;
        }

        .footer-links {
            display: flex;
            gap: 10px;
            align-items: center;
        }

        .footer-links a {
            color: var(--text-secondary);
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 6px 8px;
            border-radius: 8px;
            transition: all 0.15s ease;
            font-weight: 600;
            font-size: 0.9em;
        }

        .footer-links a:hover {
            color: var(--accent);
            background: var(--bg-tertiary);
            transform: translateY(-1px);
        }

        .footer-right {
            display: flex;
            gap: 8px;
            align-items: center;
        }

        .icon-btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            padding: 8px 10px;
            border-radius: 10px;
            background: var(--bg-primary);
            border: 1px solid var(--border);
            color: var(--text-secondary);
            cursor: pointer;
            transition: all 0.12s ease;
            font-weight: 600;
        }

        .icon-btn i { font-size: 1.05em; }

        .icon-btn:hover {
            color: var(--accent);
            border-color: var(--accent);
            transform: translateY(-2px);
            box-shadow: 0 6px 18px rgba(0,0,0,0.06);
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

        /* Modern Search Interface */
        .search-interface {
            padding: 24px;
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border);
        }

        .search-wrapper {
            display: flex;
            gap: 12px;
            max-width: 800px;
            margin: 0 auto;
        }

        .search-field {
            position: relative;
            flex: 1;
        }

        .search-input-wrapper {
            display: flex;
            align-items: center;
            background: var(--bg-primary);
            border: 2px solid var(--border);
            border-radius: 16px;
            padding: 0 8px;
            transition: all 0.2s ease;
        }

        .search-input-wrapper i {
            padding: 12px;
            color: var(--text-secondary);
            font-size: 1.1em;
        }

        .search-input {
            flex: 1;
            border: none;
            background: none;
            padding: 16px 8px;
            font-size: 1em;
            color: var(--text-primary);
            font-family: 'Exo 2', sans-serif;
            min-width: 0;
        }

        .search-input:focus {
            outline: none;
        }

        .search-input::placeholder {
            color: var(--text-secondary);
            opacity: 0.7;
        }

        .search-field:focus-within .search-input-wrapper {
            border-color: var(--accent);
            box-shadow: 0 0 0 3px var(--accent-secondary);
        }

        .search-shortcuts {
            padding: 0 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .search-shortcuts kbd {
            min-width: 20px;
            height: 20px;
            padding: 0 6px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            border-radius: 4px;
            font-family: 'Exo 2', monospace;
            font-size: 0.75em;
            color: var(--text-secondary);
        }

        .search-tools {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .search-tool-btn {
            width: 44px;
            height: 44px;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 2px solid var(--border);
            border-radius: 12px;
            background: var(--bg-primary);
            color: var(--text-secondary);
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .search-tool-btn:hover {
            border-color: var(--accent);
            color: var(--accent);
            background: var(--bg-tertiary);
        }

        .search-divider {
            width: 1px;
            height: 24px;
            background: var(--border);
        }

        .search-suggestions {
            position: absolute;
            top: calc(100% + 12px);
            left: 0;
            right: 0;
            background: var(--bg-primary);
            border: 1px solid var(--border);
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            padding: 12px;
            display: none;
            z-index: 1000;
            animation: suggestionsFade 0.2s ease;
        }

        .search-suggestions.show {
            display: block;
        }

        .suggestion-group {
            padding: 8px 0;
        }

        .suggestion-group:not(:last-child) {
            border-bottom: 1px solid var(--border);
        }

        .suggestion-header {
            padding: 8px 12px;
            color: var(--text-secondary);
            font-size: 0.85em;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .suggestion-item {
            padding: 10px 12px;
            display: flex;
            align-items: center;
            gap: 12px;
            color: var(--text-primary);
            cursor: pointer;
            border-radius: 8px;
            transition: all 0.15s ease;
        }

        .suggestion-item:hover {
            background: var(--bg-tertiary);
            color: var(--accent);
        }

        .suggestion-item i {
            width: 20px;
            text-align: center;
            color: var(--text-secondary);
        }

        .suggestion-item:hover i {
            color: inherit;
        }

        @keyframes suggestionsFade {
            from { opacity: 0; transform: translateY(-8px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Active Filters */
        .active-filters {
            margin-top: 16px;
            display: none;
            justify-content: space-between;
            align-items: center;
            gap: 16px;
        }

        .active-filters.show {
            display: flex;
        }

        .filter-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }

        .filter-tag {
            background: var(--bg-primary);
            border: 1px solid var(--border);
            color: var(--text-primary);
            padding: 6px 10px 6px 12px;
            border-radius: 25px;
            font-size: 0.85em;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.2s ease;
            cursor: default;
        }

        .filter-tag:hover {
            border-color: var(--accent);
            background: var(--bg-tertiary);
        }

        .filter-tag .remove {
            width: 18px;
            height: 18px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            cursor: pointer;
            transition: all 0.15s ease;
            margin: -2px -4px -2px 0;
        }

        .filter-tag .remove:hover {
            background: var(--danger);
            color: white;
        }

        .clear-filters {
            background: none;
            border: none;
            color: var(--text-secondary);
            font-size: 0.85em;
            padding: 8px 12px;
            border-radius: 6px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: all 0.2s ease;
        }

        .clear-filters:hover {
            background: var(--bg-tertiary);
            color: var(--danger);
        }

        /* Filter Info and Tags */
        .filter-info {
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            border-radius: 12px;
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
            margin-top: 8px;
        }

        .filter-tag {
            background: var(--accent);
            color: white;
            padding: 6px 12px 6px 14px;
            border-radius: 25px;
            font-size: 0.85em;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.2s ease;
            user-select: none;
        }

        .filter-tag .remove {
            cursor: pointer;
            opacity: 0.8;
            transition: opacity 0.2s;
            padding: 4px;
            margin: -4px;
            border-radius: 50%;
        }

        .filter-tag .remove:hover {
            opacity: 1;
            background: rgba(0, 0, 0, 0.1);
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
                    <i class="fas fa-cubes"></i> Infrastructure Components
                </div>
            </div>

            <!-- Modern Search Interface -->
            <div class="search-interface">
                <div class="search-wrapper">
                    <div class="search-field">
                        <div class="search-input-wrapper">
                            <i class="fas fa-search"></i>
                            <input type="text"
                                   class="search-input"
                                   id="search-input"
                                   spellcheck="false"
                                   autocomplete="off"
                                   placeholder="Search infrastructure components..." />
                            <div class="search-shortcuts">
                                <kbd>/</kbd>
                            </div>
                        </div>
                        <div class="search-suggestions" id="search-suggestions">
                            <div class="suggestion-group">
                                <div class="suggestion-header">Common Filters</div>
                                <div class="suggestion-item" data-filter="type:resource"><i class="fas fa-cube"></i> Resources</div>
                                <div class="suggestion-item" data-filter="state:unused"><i class="fas fa-ban"></i> Unused Components</div>
                                <div class="suggestion-item" data-filter="has:warning"><i class="fas fa-exclamation-triangle"></i> With Warnings</div>
                            </div>
                            <div class="suggestion-group">
                                <div class="suggestion-header">Providers</div>
                                <div class="suggestion-item" data-filter="provider:aws"><i class="fab fa-aws"></i> AWS Resources</div>
                                <div class="suggestion-item" data-filter="provider:azure"><i class="fab fa-microsoft"></i> Azure Resources</div>
                                <div class="suggestion-item" data-filter="provider:google"><i class="fab fa-google"></i> Google Cloud</div>
                            </div>
                            <div class="suggestion-group">
                                <div class="suggestion-header">Sort Options</div>
                                <div class="suggestion-item" data-filter="sort:name"><i class="fas fa-sort-alpha-down"></i> Sort by Name</div>
                                <div class="suggestion-item" data-filter="sort:deps"><i class="fas fa-project-diagram"></i> By Dependencies</div>
                            </div>
                        </div>
                    </div>
                    <div class="search-tools">
                        <button class="search-tool-btn" id="search-clear" onclick="classicDashboard.clearSearch()">
                            <i class="fas fa-times"></i>
                        </button>
                        <div class="search-divider"></div>
                        <button class="search-tool-btn" onclick="classicDashboard.showCommandPalette()">
                            <i class="fas fa-terminal"></i>
                        </button>
                    </div>
                </div>

                <div class="active-filters" id="filter-info">
                    <div class="filter-tags" id="filter-tags"></div>
                    <button class="clear-filters" onclick="classicDashboard.resetFilters()">
                        <i class="fas fa-times"></i>
                        <span>Clear filters</span>
                    </button>
                </div>
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
            <div class="footer-left">
                <div class="version">tfkit <span style="opacity:0.8; font-weight:500">(v{{ tfkit_version | default('0.0.0') }})</span></div>
                <div class="footer-links">
                    <a href="https://tfkit.netlify.app/" target="_blank" title="Homepage"><i class="fas fa-home"></i> Homepage</a>
                    <a href="https://github.com/ivasik-k7/tfkit" target="_blank" title="GitHub"><i class="fab fa-github"></i> GitHub</a>
                </div>
            </div>
            <div class="footer-right">
                <button class="icon-btn" onclick="classicDashboard.exportData()" title="Export">
                    <i class="fas fa-download"></i>
                </button>
                <button class="icon-btn" onclick="classicDashboard.showHelp()" title="Help">
                    <i class="fas fa-question-circle"></i>
                </button>
                <a class="icon-btn" href="https://github.com/ivasik-k7/tfkit/issues" target="_blank" title="Report Issue">
                    <i class="fas fa-bug"></i>
                </a>
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
                this.enableBacktickKey = true; // allow ` to open command palette
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
                this.currentSort = 'name';
            }

            toggleSortDropdown() {
                const dropdown = document.getElementById('sort-dropdown-content');
                dropdown.classList.toggle('show');
                
                // Close dropdown when clicking outside
                const closeDropdown = (e) => {
                    if (!e.target.closest('#sort-dropdown') && !e.target.closest('#sort-dropdown-content')) {
                        dropdown.classList.remove('show');
                        document.removeEventListener('click', closeDropdown);
                    }
                };
                
                if (dropdown.classList.contains('show')) {
                    setTimeout(() => document.addEventListener('click', closeDropdown), 0);
                }
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

                if (this.enableBacktickKey && event.key === '`' && !event.ctrlKey && !event.metaKey && !event.altKey) {
                    event.preventDefault();
                    this.showCommandPalette();
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
                const searchSuggestions = document.getElementById('search-suggestions');

                // Initialize search state
                this.parsedFilters = null;
                this.searchFocused = false;

                // Handle input changes with debounce
                searchInput.addEventListener('input', (e) => {
                    const query = e.target.value;
                    this.updateSearchClear(query);
                    this.debounceFilter(query);

                    // Show/hide suggestions based on input
                    if (this.searchFocused) {
                        searchSuggestions.classList.add('show');
                    }
                });

                // Show suggestions on focus
                searchInput.addEventListener('focus', () => {
                    this.searchFocused = true;
                    searchSuggestions.classList.add('show');
                });

                // Handle keyboard navigation
                searchInput.addEventListener('keydown', (e) => {
                    if (e.key === 'Escape') {
                        e.preventDefault();
                        if (searchInput.value) {
                            this.clearSearch();
                        } else {
                            searchInput.blur();
                        }
                        return;
                    }

                    if (e.key === 'ArrowDown' && this.searchFocused) {
                        e.preventDefault();
                        const firstSuggestion = searchSuggestions.querySelector('.suggestion-item');
                        if (firstSuggestion) {
                            firstSuggestion.focus();
                        }
                    }
                });

                // Close suggestions when clicking outside
                document.addEventListener('click', (e) => {
                    if (!e.target.closest('.search-field')) {
                        this.searchFocused = false;
                        searchSuggestions.classList.remove('show');
                    }
                });

                // Handle suggestion clicks
                const suggestions = document.querySelectorAll('.suggestion-item');
                suggestions.forEach(suggestion => {
                    suggestion.addEventListener('click', () => {
                        const filter = suggestion.dataset.filter;
                        if (filter) {
                            const currentValue = searchInput.value.trim();
                            const newValue = currentValue ? `${currentValue} ${filter}` : filter;
                            searchInput.value = newValue;
                            searchInput.focus();
                            this.debounceFilter(newValue);
                        }
                    });

                    // Keyboard navigation within suggestions
                    suggestion.addEventListener('keydown', (e) => {
                        if (e.key === 'ArrowDown') {
                            e.preventDefault();
                            const next = suggestion.nextElementSibling;
                            if (next && next.classList.contains('suggestion-item')) {
                                next.focus();
                            }
                        }
                        if (e.key === 'ArrowUp') {
                            e.preventDefault();
                            const prev = suggestion.previousElementSibling;
                            if (prev && prev.classList.contains('suggestion-item')) {
                                prev.focus();
                            } else {
                                searchInput.focus();
                            }
                        }
                        if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            suggestion.click();
                        }
                        if (e.key === 'Escape') {
                            e.preventDefault();
                            searchInput.focus();
                            searchSuggestions.classList.remove('show');
                        }
                    });
                });

                // Global keyboard shortcut to focus search
                document.addEventListener('keydown', (e) => {
                    if (e.key === '/' && !e.ctrlKey && !e.metaKey && !e.altKey) {
                        e.preventDefault();
                        searchInput.focus();
                    }
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
                this.parsedFilters = null;
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
                // parse advanced filters into structured object
                this.parsedFilters = this.parseFilterQuery(query || '');
                this.renderGraphNodes();
            }

            // Parse query into structured filters and free-text terms
            parseFilterQuery(query) {
                const result = { filters: {}, terms: [] };
                if (!query || typeof query !== 'string') return result;

                // split by spaces but allow quoted phrases
                const tokens = query.match(/(?:"([^\"]+)")|(?:'([^']+)')|([^\\s]+)/g) || [];
                tokens.forEach(raw => {
                    const token = raw.replace(/^"|"$|^'|'$/g, '').trim();
                    const parts = token.split(/:(.+)/); // split on first ':'
                    if (parts.length === 3) {
                        const key = parts[0].toLowerCase();
                        const value = parts[1].toLowerCase();
                        switch (key) {
                            case 'type':
                            case 'state':
                            case 'provider':
                            case 'subtype':
                                result.filters[key] = value;
                                break;
                            case 'mindeps':
                            case 'min_deps':
                            case 'mindependencies':
                                result.filters.minDeps = parseInt(value, 10) || 0;
                                break;
                            case 'maxdeps':
                            case 'max_deps':
                            case 'maxdependencies':
                                result.filters.maxDeps = parseInt(value, 10) || 0;
                                break;
                            case 'badge':
                            case 'tag':
                                result.filters.badge = value;
                                break;
                            case 'sort':
                                switch (value) {
                                    case 'name':
                                    case 'alpha':
                                        this.currentSort = 'name';
                                        break;
                                    case 'type':
                                        this.currentSort = 'type';
                                        break;
                                    case 'deps':
                                    case 'dependencies':
                                        this.currentSort = 'dependencies';
                                        break;
                                }
                                break;
                            case 'has':
                                if (['warning', 'error', 'deps', 'dependencies', 'badge', 'tag'].includes(value)) {
                                    result.filters[`has_${value}`] = true;
                                }
                                break;
                            default:
                                // unknown key -> treat as term
                                result.terms.push(token);
                                break;
                        }
                    } else {
                        // plain term
                        if (token.length) result.terms.push(token);
                    }
                });

                return result;
            }

            // Return true if node matches parsedFilters
            matchNodeWithFilters(node, parsed) {
                if (!parsed) return true;
                const f = parsed.filters || {};
                const terms = parsed.terms || [];

                // Type/state/provider/subtype checks
                if (f.type && String(node.type).toLowerCase() !== String(f.type).toLowerCase()) return false;
                if (f.state && String(node.state).toLowerCase() !== String(f.state).toLowerCase()) return false;
                if (f.provider) {
                    // match provider in node.provider or details.provider
                    const provider = (node.provider || (node.details && node.details.provider) || '').toString().toLowerCase();
                    if (!provider.includes(f.provider.toLowerCase())) return false;
                }
                if (f.subtype && String(node.subtype || '').toLowerCase() !== String(f.subtype).toLowerCase()) return false;

                // min/max deps
                const deps = (node.dependencies_out || 0) + (node.dependencies_in || 0);
                if (typeof f.minDeps === 'number' && deps < f.minDeps) return false;
                if (typeof f.maxDeps === 'number' && deps > f.maxDeps) return false;

                // badge/tag (simple substring search in badges / details)
                if (f.badge) {
                    const badgesText = ((node.badges || []).join(' ') || '') + ' ' + (node.details && JSON.stringify(node.details) || '');
                    if (!badgesText.toLowerCase().includes(String(f.badge).toLowerCase())) return false;
                }

                // "has:" filters
                if (f.has_warning && node.state !== 'warning') return false;
                if (f.has_error && !['error', 'critical'].includes(node.state)) return false;
                if (f.has_deps && deps === 0) return false;
                if (f.has_badge && (!node.badges || node.badges.length === 0)) return false;

                // free-text terms: all must be present
                if (terms.length > 0) {
                    const searchableText = [
                        node.label,
                        node.type,
                        node.subtype || '',
                        node.state,
                        node.state_reason || '',
                        node.details && JSON.stringify(node.details) || ''
                    ].join(' ').toLowerCase();

                    for (const t of terms) {
                        if (!searchableText.includes(t.toLowerCase())) return false;
                    }
                }

                return true;
            }

            // Stats Methods
            initializeStats() {
                const statsGrid = document.getElementById('stats-grid');
                const nodes = this.graphData.nodes || [];
                const edges = this.graphData.edges || [];

                // Calculate statistics
                const stats = {
                    totalNodes: nodes.length,
                    totalEdges: edges.length,
                    resources: nodes.filter(n => n.type === 'resource'),
                    modules: nodes.filter(n => n.type === 'module'),
                    variables: nodes.filter(n => n.type === 'variable'),
                    providers: nodes.filter(n => n.type === 'provider'),
                    data: nodes.filter(n => n.type === 'data'),
                    outputs: nodes.filter(n => n.type === 'output'),
                    healthyNodes: nodes.filter(n => ['active', 'integrated', 'leaf', 'input', 'configuration', 'healthy'].includes(n.state)),
                    warnings: nodes.filter(n => n.state === 'warning'),
                    unused: nodes.filter(n => n.state === 'unused'),
                    external: nodes.filter(n => n.state === 'external')
                };

                const healthScore = stats.totalNodes > 0 ? Math.round((stats.healthyNodes.length / stats.totalNodes) * 100) : 100;
                
                // Calculate provider distribution
                const providerStats = nodes.reduce((acc, node) => {
                    const provider = (node.provider || (node.details && node.details.provider) || '').toString().toLowerCase();
                    if (provider) {
                        acc[provider] = (acc[provider] || 0) + 1;
                    }
                    return acc;
                }, {});

                // Calculate dependency metrics
                const dependencyStats = {
                    avgDeps: this.calculateAverageDependencies(),
                    maxDeps: Math.max(...nodes.map(n => (n.dependencies_out || 0) + (n.dependencies_in || 0))),
                    connectedGroups: this.calculateConnectedComponents(),
                    isolatedNodes: nodes.filter(n => !n.dependencies_out && !n.dependencies_in).length
                };

                // Build provider insights card
                const providerCards = Object.entries(providerStats)
                    .sort(([,a], [,b]) => b - a)
                    .slice(0, 3)
                    .map(([provider, count]) => `
                        <div class="provider-item">
                            <i class="fab fa-${provider.includes('aws') ? 'aws' : 
                                         provider.includes('azure') ? 'microsoft' :
                                         provider.includes('google') ? 'google' : 'cloud'}"></i>
                            <span>${provider.toUpperCase()}</span>
                            <span class="provider-count">${count}</span>
                        </div>
                    `).join('');

                statsGrid.innerHTML = `
                    <div class="stat-card">
                        <div class="stat-header">
                            <i class="fas fa-cloud"></i>
                            <span>Cloud Providers</span>
                        </div>
                        <div class="stat-body">
                            <div class="provider-list">
                                ${providerCards}
                            </div>
                        </div>
                        <div class="stat-footer clickable" onclick="classicDashboard.showVisualization()">
                            View distribution
                            <i class="fas fa-arrow-right"></i>
                        </div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-header">
                            <i class="fas fa-heart-pulse"></i>
                            <span>Health Overview</span>
                        </div>
                        <div class="stat-body">
                            <div class="stat-row major">
                                <span class="stat-title">Health Score</span>
                                <div class="stat-value with-trend">
                                    ${healthScore}%
                                    <span class="trend ${healthScore > 80 ? 'positive' : 'negative'}">
                                        <i class="fas fa-${healthScore > 80 ? 'arrow-up' : 'arrow-down'}"></i>
                                    </span>
                                </div>
                            </div>
                            <div class="stat-row warning">
                                <span class="stat-title">Warnings</span>
                                <span class="stat-value">${stats.warnings.length}</span>
                            </div>
                            <div class="stat-row danger">
                                <span class="stat-title">Unused</span>
                                <span class="stat-value">${stats.unused.length}</span>
                            </div>
                        </div>
                        <div class="stat-footer clickable" onclick="classicDashboard.showToast('Healthy Components', '${stats.healthyNodes.length} components are in optimal state', 'success')">
                            View health details
                            <i class="fas fa-arrow-right"></i>
                        </div>
                    </div>

                    <div class="stat-card">
                        <div class="stat-header">
                            <i class="fas fa-diagram-project"></i>
                            <span>Dependencies</span>
                        </div>
                        <div class="stat-body">
                            <div class="stat-row major">
                                <span class="stat-title">Total Relations</span>
                                <span class="stat-value">${stats.totalEdges}</span>
                            </div>
                            <div class="stat-row">
                                <span class="stat-title">Avg Dependencies</span>
                                <div class="stat-value with-trend">
                                    ${dependencyStats.avgDeps}
                                    <span class="trend ${dependencyStats.avgDeps < 4 ? 'positive' : 'warning'}">
                                        <i class="fas fa-chart-line"></i>
                                    </span>
                                </div>
                            </div>
                            <div class="stat-row">
                                <span class="stat-title">Isolated Components</span>
                                <span class="stat-value">${dependencyStats.isolatedNodes}</span>
                            </div>
                        </div>
                        <div class="stat-footer">
                            ${dependencyStats.connectedGroups} connected groups
                        </div>
                    </div>

                    <div class="stat-card">
                        <div class="stat-header">
                            <i class="fas fa-code-branch"></i>
                            <span>Configuration</span>
                        </div>
                        <div class="stat-body">
                            <div class="stat-row">
                                <span class="stat-title">Variables</span>
                                <span class="stat-value">${stats.variables.length}</span>
                            </div>
                            <div class="stat-row">
                                <span class="stat-title">Outputs</span>
                                <span class="stat-value">${stats.outputs.length}</span>
                            </div>
                            <div class="stat-row">
                                <span class="stat-title">External Data</span>
                                <span class="stat-value">${stats.external.length}</span>
                            </div>
                        </div>
                        <div class="stat-footer">
                            ${(stats.variables.length + stats.outputs.length)} total endpoints
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
                    // If advanced parsed filters present, use them (overrides simple state/search)
                    if (this.parsedFilters && ((this.parsedFilters.filters && Object.keys(this.parsedFilters.filters).length > 0) || (this.parsedFilters.terms && this.parsedFilters.terms.length > 0))) {
                        return this.matchNodeWithFilters(node, this.parsedFilters);
                    }

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

            resetFilters() {
                this.currentSearch = '';
                this.currentSort = 'name';
                this.parsedFilters = null;

                const searchInput = document.getElementById('search-input');
                searchInput.value = '';
                searchInput.focus();
                
                document.getElementById('search-clear').classList.remove('visible');
                document.getElementById('filter-info').style.display = 'none';

                this.renderGraphNodes();
                this.showToast('Filters Reset', 'All filters and searches cleared', 'info');
            }

            updateFilterInfo() {
                const filterInfo = document.getElementById('filter-info');
                const filterTags = document.getElementById('filter-tags');

                const tags = [];

                // Structured parsed filters take precedence
                if (this.parsedFilters && this.parsedFilters.filters) {
                    Object.keys(this.parsedFilters.filters).forEach(key => {
                        const val = this.parsedFilters.filters[key];
                        if (val !== undefined && val !== null && String(val).length > 0) {
                            tags.push({ label: `${key}: ${val}`, token: `${key}|${String(val).replace(/'/g, "\\'")}` });
                        }
                    });
                }

                // Free-text search terms
                if (this.parsedFilters && Array.isArray(this.parsedFilters.terms) && this.parsedFilters.terms.length > 0) {
                    this.parsedFilters.terms.forEach(t => tags.push({ label: `Search: "${t}"`, token: `term|${String(t).replace(/'/g, "\\'")}` }));
                }

                // Backwards compatible single search/state/sort
                if ((!this.parsedFilters || (Object.keys(this.parsedFilters.filters || {}).length === 0 && (!this.parsedFilters.terms || this.parsedFilters.terms.length === 0))) ) {
                    if (this.currentSearch) tags.push({ label: `Search: "${this.currentSearch}"`, token: `search|${String(this.currentSearch).replace(/'/g, "\\'")}` });
                    if (this.currentStateFilter) tags.push({ label: `State: ${this.currentStateFilter}`, token: `state|${String(this.currentStateFilter).replace(/'/g, "\\'")}` });
                    if (this.currentSort && this.currentSort !== 'name') tags.push({ label: `Sorted by: ${this.currentSort}`, token: `sorted|${String(this.currentSort).replace(/'/g, "\\'")}` });
                }

                if (tags.length > 0) {
                    filterInfo.style.display = 'flex';
                    filterTags.innerHTML = tags.map(t =>
                        `<span class="filter-tag">${t.label} <span class="remove" onclick="classicDashboard.removeFilter('${t.token}')"><i class="fas fa-times"></i></span></span>`
                    ).join('');
                } else {
                    filterInfo.style.display = 'none';
                    filterTags.innerHTML = '';
                }
            }

            removeFilter(spec) {
                // spec format: "key|value" where key can be type,state,provider,term,search,sorted
                if (!spec) return;
                const parts = String(spec).split('|');
                const key = parts[0];
                const value = parts.slice(1).join('|');

                switch (key) {
                    case 'type':
                    case 'state':
                    case 'provider':
                    case 'subtype':
                    case 'badge':
                        if (this.parsedFilters && this.parsedFilters.filters) {
                            delete this.parsedFilters.filters[key];
                        }
                        break;
                    case 'term':
                        if (this.parsedFilters && Array.isArray(this.parsedFilters.terms)) {
                            this.parsedFilters.terms = this.parsedFilters.terms.filter(t => t !== value);
                        }
                        break;
                    case 'search':
                        this.clearSearch();
                        break;
                    case 'state':
                        this.currentStateFilter = null;
                        break;
                    case 'sorted':
                        this.currentSort = 'name';
                        break;
                    case 'provider':
                        if (this.parsedFilters && this.parsedFilters.filters) delete this.parsedFilters.filters.provider;
                        break;
                    default:
                        // fallback: if parsedFilters had the key, delete it
                        if (this.parsedFilters && this.parsedFilters.filters && this.parsedFilters.filters[key]) {
                            delete this.parsedFilters.filters[key];
                        }
                        break;
                }

                // Rebuild the search input to reflect remaining filters when applicable
                try {
                    const input = document.getElementById('search-input');
                    if (this.parsedFilters) {
                        const parts = [];
                        if (this.parsedFilters.filters) {
                            Object.keys(this.parsedFilters.filters).forEach(k => {
                                const v = this.parsedFilters.filters[k];
                                if (v !== undefined && v !== null && String(v).length > 0) parts.push(`${k}:${v}`);
                            });
                        }
                        if (this.parsedFilters.terms && this.parsedFilters.terms.length) {
                            this.parsedFilters.terms.forEach(t => parts.push(t));
                        }
                        input.value = parts.join(' ');
                        this.updateSearchClear(input.value);
                    } else {
                        input.value = '';
                        this.updateSearchClear('');
                    }
                } catch (err) {
                    // ignore
                }

                this.renderGraphNodes();
                this.updateFilterInfo();
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
