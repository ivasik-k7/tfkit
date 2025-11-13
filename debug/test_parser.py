from pathlib import Path

from tfkit.dependency.base import TerraformDependencyBuilder
from tfkit.graph.base import TerraformGraphBuilder
from tfkit.parser.base import ParsingConfig, TerraformParser

# from tfkit.parser.dependency import TerraformDependencyBuilder


def main():
    test_path = Path("./examples/simple")

    config = ParsingConfig()
    parser = TerraformParser(config)

    catalog = parser.parse_directory(test_path)
    dependency_builder = TerraformDependencyBuilder(catalog)
    dependencies = dependency_builder.build_dependencies()

    result = catalog.get_by_address("var.aws_region")

    graph_builder = TerraformGraphBuilder(catalog)
    node_data = graph_builder.build_graph(dependencies)  # noqa

    # analytics comes after TerraformGraphBuilder
    # analytics based on nodes and links and other types of data from tgb

    # graph_data = graph_builder.build_graph()

    print(result)

    # dependencies = TerraformDependencyBuilder(catalog).build_dependencies()
    # print("Hello")


if __name__ == "__main__":
    main()
