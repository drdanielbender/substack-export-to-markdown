# Substack Export to Markdown Converter

A Python script that converts HTML files from a Substack export to clean Markdown format with proper frontmatter.

## Features

- Converts Substack HTML exports to Markdown files
- Preserves post metadata (title, subtitle, date, publication status)
- Cleans up Substack-specific elements (subscription widgets, polls, share buttons)
- Interactive directory selection with last modification dates
- Skips unpublished posts automatically
- Generates clean filenames from post titles

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd substack-archive-to-markdown
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Creating a Substack Export

1. Login to your Substack account
2. Go to Settings → Import / Export → Export your data → New export
3. Wait for the ZIP file to be created (this may take some time)
4. Download the ZIP file from the export page when ready

## Usage

1. Create an `export` folder in the project directory
2. Unzip your Substack export ZIP file as a subfolder into the `export` folder
3. Run the converter:
```bash
python main.py
```

4. Select the export directory from the interactive menu
5. Converted Markdown files will be saved in `markdown_posts` subfolder within your selected export directory

## Export Structure

Your Substack export should have this structure:
```
export/
└── your-export-folder/
    ├── posts/
    │   ├── post1.html
    │   ├── post2.html
    │   └── ...
    └── posts.csv
```

## Output Format

Each converted post includes:
- YAML frontmatter with metadata
- Clean Markdown content
- Preserved images with captions
- Filename format: `{post_id}_{clean_title}.md`

Example output:
```markdown
---
title: "Your Post Title"
subtitle: "Optional subtitle"
date: 2024-01-15
type: newsletter
published: true
substack_id: 123456789
---

Your post content in Markdown format...
```

## Requirements

- Python 3.6+
- beautifulsoup4
- html2text

## License

MIT License - see LICENSE file for details.
