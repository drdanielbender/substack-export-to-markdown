#!/usr/bin/env python3
"""
Substack Export to Markdown Converter

This script converts HTML files from a Substack export to Markdown format.
It processes the posts directory and converts each article to a clean Markdown file.
"""

import os
import csv
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

try:
    from bs4 import BeautifulSoup
    import html2text
except ImportError:
    print("Required packages not found. Please install:")
    print("pip install beautifulsoup4 html2text")
    exit(1)


class SubstackConverter:
    def __init__(self, export_dir: str, output_dir: str = "markdown_posts"):
        self.export_dir = Path(export_dir)
        self.output_dir = Path(output_dir)
        self.posts_dir = self.export_dir / "posts"
        self.posts_csv = self.export_dir / "posts.csv"
        
        # Create output directory
        self.output_dir.mkdir(exist_ok=True)
        
        # HTML to Markdown converter configuration
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False
        self.h2t.ignore_images = False
        self.h2t.ignore_emphasis = False
        self.h2t.body_width = 0  # No line wrapping
        self.h2t.unicode_snob = True
        self.h2t.skip_internal_links = True
        
        # Load posts metadata
        self.posts_metadata = self._load_posts_metadata()
    
    def _load_posts_metadata(self) -> Dict[str, Dict]:
        """Load posts metadata from posts.csv"""
        metadata = {}
        
        if not self.posts_csv.exists():
            print(f"Warning: {self.posts_csv} not found")
            return metadata
        
        try:
            with open(self.posts_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    post_id = row['post_id'].split('.')[0]  # Extract just the numeric ID
                    metadata[post_id] = {
                        'title': row['title'],
                        'subtitle': row['subtitle'],
                        'date': row['post_date'],
                        'type': row['type'],
                        'published': row['is_published'] == 'true'
                    }
        except Exception as e:
            print(f"Error reading posts.csv: {e}")
        
        return metadata
    
    def _extract_post_id(self, filename: str) -> str:
        """Extract post ID from filename"""
        return filename.split('.')[0]
    
    def _clean_html_content(self, html_content: str) -> str:
        """Clean and prepare HTML content for conversion"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove subscription widgets and other Substack-specific elements
        for elem in soup.find_all(['div'], class_=['subscription-widget', 'subscription-widget-wrap-editor']):
            elem.decompose()
        
        # Remove poll embeds
        for elem in soup.find_all(['div'], class_=['poll-embed']):
            elem.decompose()
        
        # Remove share buttons
        for elem in soup.find_all(['div'], class_=['captioned-button-wrap']):
            elem.decompose()
        
        # Clean up image containers - keep images but simplify structure
        for img_container in soup.find_all(['div'], class_=['captioned-image-container']):
            # Find the actual image
            img = img_container.find('img')
            if img:
                # Get the caption if it exists
                caption = img_container.find('figcaption')
                caption_text = caption.get_text().strip() if caption else ""
                
                # Create a simplified structure
                new_content = f'<img src="{img.get("src", "")}" alt="{img.get("alt", "")}">'
                if caption_text:
                    new_content += f'<br><em>{caption_text}</em>'
                
                img_container.replace_with(BeautifulSoup(new_content, 'html.parser'))
        
        # Remove excessive whitespace and clean up
        cleaned = str(soup)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = re.sub(r'<br\s*/?>\s*<br\s*/?>', '\n\n', cleaned)
        
        return cleaned
    
    def _format_date(self, date_str: str) -> str:
        """Format date string for frontmatter"""
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d')
        except:
            return date_str
    
    def _create_frontmatter(self, post_id: str, metadata: Dict) -> str:
        """Create frontmatter for the markdown file"""
        frontmatter = "---\n"
        frontmatter += f"title: \"{metadata.get('title', 'Untitled')}\"\n"
        
        subtitle = metadata.get('subtitle', '').strip()
        if subtitle:
            frontmatter += f"subtitle: \"{subtitle}\"\n"
        
        frontmatter += f"date: {self._format_date(metadata.get('date', ''))}\n"
        frontmatter += f"type: {metadata.get('type', 'post')}\n"
        frontmatter += f"published: {str(metadata.get('published', False)).lower()}\n"
        frontmatter += f"substack_id: {post_id}\n"
        frontmatter += "---\n\n"
        
        return frontmatter
    
    def convert_file(self, html_file: Path) -> bool:
        """Convert a single HTML file to Markdown"""
        try:
            # Read HTML content
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Extract post ID
            post_id = self._extract_post_id(html_file.name)
            
            # Get metadata
            metadata = self.posts_metadata.get(post_id, {})
            
            # Skip unpublished posts
            if not metadata.get('published', True):
                print(f"Skipping unpublished post: {html_file.name}")
                return False
            
            # Clean HTML content
            cleaned_html = self._clean_html_content(html_content)
            
            # Convert to Markdown
            markdown_content = self.h2t.handle(cleaned_html)
            
            # Clean up markdown
            markdown_content = re.sub(r'\n\s*\n\s*\n', '\n\n', markdown_content)
            markdown_content = markdown_content.strip()
            
            # Create frontmatter
            frontmatter = self._create_frontmatter(post_id, metadata)
            
            # Combine frontmatter and content
            full_content = frontmatter + markdown_content
            
            # Generate output filename
            title = metadata.get('title', html_file.stem)
            # Clean title for filename
            safe_title = re.sub(r'[^\w\s-]', '', title).strip()
            safe_title = re.sub(r'[-\s]+', '-', safe_title)
            
            output_filename = f"{post_id}_{safe_title}.md"
            output_path = self.output_dir / output_filename
            
            # Write Markdown file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(full_content)
            
            print(f"Converted: {html_file.name} -> {output_filename}")
            return True
            
        except Exception as e:
            print(f"Error converting {html_file.name}: {e}")
            return False
    
    def convert_all(self) -> None:
        """Convert all HTML files in the posts directory"""
        if not self.posts_dir.exists():
            print(f"Posts directory not found: {self.posts_dir}")
            return
        
        # Find all HTML files
        html_files = list(self.posts_dir.glob("*.html"))
        
        if not html_files:
            print("No HTML files found in posts directory")
            return
        
        print(f"Found {len(html_files)} HTML files to convert")
        
        # Convert each file
        successful = 0
        for html_file in html_files:
            if self.convert_file(html_file):
                successful += 1
        
        print(f"\nConversion complete: {successful}/{len(html_files)} files converted successfully")
        print(f"Markdown files saved to: {os.path.abspath(self.output_dir)}")


def select_export_directory():
    """Scan export folder and let user select which directory to use"""
    export_base = "export"
    
    # Check if export folder exists
    if not os.path.exists(export_base):
        print(f"Export folder '{export_base}' not found.")
        print("Please create the export folder and unzip your Substack export zip file in it.")
        return None
    
    # Get all directories in export folder with their modification times
    directories = []
    for d in os.listdir(export_base):
        dir_path = os.path.join(export_base, d)
        if os.path.isdir(dir_path):
            mod_time = os.path.getmtime(dir_path)
            directories.append((d, mod_time))
    
    if not directories:
        print("No directories found in the export folder.")
        print("Please unzip your Substack export zip file in the export folder.")
        return None
    
    # Display directories and let user choose
    print("\nAvailable export directories:")
    for i, (directory, mod_time) in enumerate(directories, 1):
        last_modified = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M')
        print(f"{i}. {directory} (last modified: {last_modified})")
    
    while True:
        try:
            choice = input(f"\nEnter a number (1-{len(directories)}) to select a directory, or 'q' to quit: ").strip()
            
            if choice.lower() == 'q':
                return None
            
            if choice.isdigit():
                index = int(choice) - 1
                if 0 <= index < len(directories):
                    selected_dir = os.path.join(export_base, directories[index][0])
                    print(f"Selected: {selected_dir}")
                    return selected_dir
            
            print("Invalid choice. Please try again.")
            
        except (KeyboardInterrupt, EOFError):
            print("\nOperation cancelled.")
            return None


def main():
    """Main function"""
    # Select export directory interactively
    export_dir = select_export_directory()
    
    if not export_dir:
        return
    
    # Create output directory as subfolder of selected export directory
    output_dir = os.path.join(export_dir, "markdown_posts")
    print(f"\nOutput directory: {output_dir}")
    
    # Create converter and run
    converter = SubstackConverter(export_dir, output_dir)
    converter.convert_all()


if __name__ == "__main__":
    main()
