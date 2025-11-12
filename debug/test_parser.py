from pathlib import Path

from tfkit.parser.base import ParsingConfig, TerraformParser
from tfkit.parser.dependency import TerraformDependencyBuilder


def main():
    test_path = Path("./examples/simple")

    config = ParsingConfig()
    parser = TerraformParser(config)

    catalog = parser.parse_directory(test_path)
    catalog.to_yaml(Path("out/catalog.yaml"))
    catalog.to_json(Path("out/catalog.json"))
    dependencies = TerraformDependencyBuilder(catalog).build_dependencies()
    print("Hello")


if __name__ == "__main__":
    main()
