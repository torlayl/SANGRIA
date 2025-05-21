# Process all markdown files in the current directory
# python Split_Markdown.py .

# Process all markdown files recursively, including subdirectories
# python Split_Markdown.py ./docs --recursive

# Split at level 1 and 2 headings only
# python Split_Markdown.py ./content --max-level 2 --output-dir ./split_content



import os
import re
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional

def read_markdown_file(file_path: str) -> str:
    """Read a markdown file and return its content as a string."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def is_heading(line: str) -> Tuple[bool, int]:
    """
    Check if a line is a markdown heading.
    Returns (is_heading, level) where level is the heading level (1-6).
    """
    heading_pattern = r'^(#{1,6})\s+'
    match = re.match(heading_pattern, line)
    if match:
        return True, len(match.group(1))
    return False, 0

def split_by_headings(content: str, max_heading_level: Optional[int] = None) -> List[Dict]:
    """
    Split markdown content into chunks by headings.
    
    Args:
        content: The markdown content as a string
        max_heading_level: If provided, only split at headings up to this level.
                          For example, if max_heading_level=2, only split at # and ## headings.
    
    Returns:
        A list of dictionaries, each containing:
        - 'heading': The heading text (including the # symbols)
        - 'content': The content under that heading (up to the next heading)
        - 'level': The heading level (1-6)
    """
    lines = content.split('\n')
    chunks = []
    current_chunk = {"heading": "", "content": [], "level": 0}
    
    for line in lines:
        is_head, level = is_heading(line)
        
        # If this is a heading we care about (respecting max_heading_level)
        if is_head and (max_heading_level is None or level <= max_heading_level):
            # If we have a current chunk with content, save it
            if current_chunk["heading"] or current_chunk["content"]:
                current_chunk["content"] = '\n'.join(current_chunk["content"])
                chunks.append(current_chunk)
            
            # Start a new chunk
            current_chunk = {
                "heading": line,
                "content": [],
                "level": level
            }
        else:
            # Add to the current chunk's content
            current_chunk["content"].append(line)
    
    # Don't forget to add the last chunk
    if current_chunk["heading"] or current_chunk["content"]:
        current_chunk["content"] = '\n'.join(current_chunk["content"])
        chunks.append(current_chunk)
    
    return chunks

def save_chunks(chunks: List[Dict], output_dir: str, base_filename: str) -> None:
    """
    Save each chunk as a separate file.
    
    Args:
        chunks: List of chunk dictionaries
        output_dir: Directory to save the files in
        base_filename: Base name for the output files
    """
    os.makedirs(output_dir, exist_ok=True)
    
    for i, chunk in enumerate(chunks):
        # Create a filename based on the heading if possible
        if chunk["heading"]:
            # Extract text from heading and make it filename-friendly
            heading_text = chunk["heading"].lstrip('#').strip()
            filename = re.sub(r'[^\w\s-]', '', heading_text).strip().lower()
            filename = re.sub(r'[-\s]+', '-', filename)
        else:
            filename = "chunk"
        
        # Include source filename and chunk number to ensure uniqueness
        filename = f"{base_filename}_{i:03d}_{filename}"
        
        # Write to file
        output_path = os.path.join(output_dir, f"{filename}.md")
        with open(output_path, 'w', encoding='utf-8') as f:
            # Add source filename as metadata
            f.write(f"Source: {base_filename}\n\n")
            if chunk["heading"]:
                f.write(f"{chunk['heading']}\n\n")
            f.write(chunk["content"])
        
        print(f"Saved chunk to {output_path}")

def process_markdown_file(markdown_file: str, output_dir: str, max_level: Optional[int] = None) -> None:
    """Process a single markdown file, splitting it into chunks."""
    try:
        content = read_markdown_file(markdown_file)
        chunks = split_by_headings(content, max_level)
        
        # Get base filename without creating a subdirectory
        base_filename = Path(markdown_file).stem
        
        # Save all chunks directly to the output directory
        save_chunks(chunks, output_dir, base_filename)
        print(f"Split {markdown_file} into {len(chunks)} chunks in {output_dir}")
    except Exception as e:
        print(f"Error processing {markdown_file}: {e}")

def find_markdown_files(directory: str, recursive: bool = False) -> List[str]:
    """Find all markdown files in a directory."""
    markdown_files = []
    
    if recursive:
        for root, _, files in os.walk(directory):
            for file in files:
                if file.lower().endswith('.md'):
                    markdown_files.append(os.path.join(root, file))
    else:
        for file in os.listdir(directory):
            if file.lower().endswith('.md'):
                markdown_files.append(os.path.join(directory, file))
    
    return markdown_files

def main():
    parser = argparse.ArgumentParser(description="Split markdown files into chunks based on headings")
    parser.add_argument("input_dir", help="Directory containing markdown files to split")
    parser.add_argument("-o", "--output-dir", default="chunks", help="Directory to save the chunks in")
    parser.add_argument("-l", "--max-level", type=int, default=None, 
                        help="Maximum heading level to split at (1-6)")
    parser.add_argument("-r", "--recursive", action="store_true", 
                        help="Search for markdown files recursively in subdirectories")
    
    args = parser.parse_args()
    
    # Check if input directory exists
    if not os.path.isdir(args.input_dir):
        print(f"Error: Input directory '{args.input_dir}' does not exist")
        return 1
    
    # Find all markdown files
    markdown_files = find_markdown_files(args.input_dir, args.recursive)
    
    if not markdown_files:
        print(f"No markdown files found in {args.input_dir}")
        return 0
        
    print(f"Found {len(markdown_files)} markdown files to process")
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Process each markdown file
    for md_file in markdown_files:
        process_markdown_file(md_file, args.output_dir, args.max_level)
    
    print(f"All files processed. Chunks saved in {args.output_dir}")
    return 0

if __name__ == "__main__":
    exit(main())