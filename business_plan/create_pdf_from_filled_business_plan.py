import argparse

from markdown import markdown
from weasyprint import HTML


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert a markdown file to PDF using markdown and WeasyPrint."
    )
    parser.add_argument("input_file", help="Path to the input markdown file.")
    parser.add_argument("output_file", help="Path to the output PDF file.")

    args = parser.parse_args()

    with open(args.input_file, "r", encoding="utf-8") as f:
        md_text = f.read()

    html_text = markdown(md_text)
    HTML(string=html_text).write_pdf(args.output_file)

    print(f"PDF created: {args.output_file}")


if __name__ == "__main__":
    main()
