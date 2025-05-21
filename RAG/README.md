# RAG Data Processing Tools

This repository contains Python tools for crawling websites into markdown files and splitting them into chunks

## Scripts

### 1. URL_Crawler.py

A web crawler that fetches content from websites and converts it to markdown format. It intelligently extracts content while filtering out navigation elements and other customed parts of web pages.

#### Usage

```bash
python URL_Crawler.py [URL] [options]
```

Options:
- `--depth N`: Maximum crawling depth (default: 0 - only crawls the initial page)
- `--output DIR`: Directory to save markdown files (default: "web_content")
- `--allow-external`: Allow following external links (default: off)

### 2. Split_Markdown.py

A utility for splitting markdown files into smaller, semantically meaningful chunks based on headings. 

#### Usage

```bash
python Split_Markdown.py INPUT_DIR [options]
```

Options:
- `-o, --output-dir DIR`: Directory to save the chunks (default: "chunks")
- `-l, --max-level N`: Maximum heading level to split at (1-6)
- `-r, --recursive`: Search for markdown files recursively in subdirectories

## Workflow

A complete workflow using these tools might look like:

1. **Collect data** by crawling websites:
   ```bash
   python URL_Crawler.py https://example.com --depth 1 --output raw_content
   ```

2. **Process and chunk** the collected markdown:
   ```bash
   python Split_Markdown.py raw_content --output-dir chunks --max-level 2
   ```



## Requirements

See the `requirements.txt` file for dependencies. Install them with:

```bash
pip install -r requirements.txt
```

## License

MIT
