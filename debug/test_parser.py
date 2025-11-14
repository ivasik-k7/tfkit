import json
from datetime import datetime
from pathlib import Path

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
    graph_data = graph_builder.build_graph(dependencies)  # noqa

    try:
        from tfkit import __version__
    except ImportError:
        __version__ = "Unknown"

    theme = "solarized-light"
    layout = "graph"

    json_string = json.dumps(graph_data.to_dict())

    # 2. Define the output path
    output_path = Path("./out/data.json")

    # 3. Ensure the parent directory exists
    # 'parents=True' creates any necessary parent directories (like 'out/').
    # 'exist_ok=True' prevents an error if the directory already exists.
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 4. Write the JSON string to the file
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
