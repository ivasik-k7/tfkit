import json
from pathlib import Path

from tfkit.analytics.base import TerraformGraphAnalytics
from tfkit.dependency.base import TerraformDependencyBuilder
from tfkit.graph.base import TerraformGraphBuilder
from tfkit.parser.base import ParsingConfig, TerraformParser
from tfkit.renderer import Browser, TemplateRenderer
from tfkit.templates.theme_manager import ThemeManager


def main():
    test_path = Path("./examples/simple")

    config = ParsingConfig()
    parser = TerraformParser(config)

    catalog = parser.parse_directory(test_path)
    dependency_builder = TerraformDependencyBuilder(catalog)
    dependencies = dependency_builder.build_dependencies()

    graph_builder = TerraformGraphBuilder(catalog)
    graph_data = graph_builder.build_graph(dependencies)

    analytics = TerraformGraphAnalytics(graph_data).analyze()

    try:
        from tfkit import __version__
    except ImportError:
        __version__ = "Unknown"

    theme = "github-dark"
    layout = "graph"

    json_string = json.dumps(graph_data.to_dict())

    output_path = Path("./out/data.json")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(json_string)
        print(f"✅ Successfully saved data to: {output_path.resolve()}")
    except OSError as e:
        print(f"❌ Error writing file to {output_path}: {e}")

    path = TemplateRenderer().render(
        output_path=None,
        layout=layout,
        theme=theme,
        title="Terraform Test Visualization",
        dataset=json.dumps(graph_data.to_dict()),
        config_data=[],
        theme_name=theme,
        theme_colors=ThemeManager.get_theme_colors(theme),
        version=__version__,
    )

    with Browser(path) as b:
        b.open()

    # analytics comes after TerraformGraphBuilder
    # analytics based on nodes and links and other types of data from tgb


if __name__ == "__main__":
    main()
