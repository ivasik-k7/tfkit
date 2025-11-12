from pathlib import Path

from tfkit.graph.builder import TerraformGraphBuilder
from tfkit.parser.base import ParsingConfig, TerraformParser
from tfkit.parser.dependency import TerraformDependencyBuilder


def main():
    test_path = Path("./examples/main")

    config = ParsingConfig()
    parser = TerraformParser(config)

    parsed_data = parser.parse_directory(test_path)
    dependency_builder = TerraformDependencyBuilder(parsed_data)
    dependencies = dependency_builder.build_dependencies()
    graph_builder = TerraformGraphBuilder(parsed_data, dependencies)

    graph_data = graph_builder.build_graph()

    print(graph_data)

    # dependencies = TerraformDependencyBuilder(catalog).build_dependencies()
    # print("Hello")


if __name__ == "__main__":
    main()
