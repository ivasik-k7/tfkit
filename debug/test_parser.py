from pathlib import Path

from tfkit.parser.base import ParsingConfig, TerraformParser


def main():
    test_path = Path("./examples/simple")

    config = ParsingConfig()
    parser = TerraformParser(config)

    module = parser.parse_directory(test_path)
    print("Hello")


if __name__ == "__main__":
    main()
