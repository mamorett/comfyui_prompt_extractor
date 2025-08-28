import json
import sys
import os
import glob
from PIL import Image
from typing import Dict, Any, List, Optional

def extract_positive_prompts_only(file_path: str) -> Dict[str, Any]:
    """
    Extract only positive prompts from ComfyUI PNG metadata
    
    Args:
        file_path: Path to the PNG file
        
    Returns:
        Dictionary containing extracted positive prompts only
    """
    try:
        with Image.open(file_path) as img:
            if img.format != 'PNG':
                raise ValueError(f"File is not a PNG: {img.format}")
            
            metadata = img.info
            result = {
                'file_info': {
                    'filename': os.path.basename(file_path),
                    'size': img.size,
                    'mode': img.mode
                },
                'positive_prompts': []
            }
            
            # Track processed node IDs to avoid duplicates
            processed_nodes = set()
            
            # Try workflow first (usually more detailed)
            if 'workflow' in metadata:
                try:
                    workflow_data = json.loads(metadata['workflow'])
                    prompts = extract_positive_from_workflow(workflow_data, processed_nodes)
                    result['positive_prompts'].extend(prompts)
                except json.JSONDecodeError as e:
                    print(f"Warning: Could not parse workflow JSON: {e}")
            
            # Only check prompt data if we didn't find anything in workflow
            if not result['positive_prompts'] and 'prompt' in metadata:
                try:
                    prompt_data = json.loads(metadata['prompt'])
                    prompts = extract_positive_from_prompt_data(prompt_data, processed_nodes)
                    result['positive_prompts'].extend(prompts)
                except json.JSONDecodeError as e:
                    print(f"Warning: Could not parse prompt JSON: {e}")
            
            return result
            
    except Exception as e:
        raise Exception(f"Error reading PNG file: {e}")

def extract_positive_from_workflow(workflow_data: Dict, processed_nodes: set) -> List[Dict]:
    """Extract positive prompts from workflow nodes"""
    positive_prompts = []
    
    nodes = workflow_data.get('nodes', [])
    
    for node in nodes:
        node_id = node.get('id')
        node_type = node.get('type', '')
        title = node.get('title', '').lower()
        
        # Skip if already processed
        if node_id in processed_nodes:
            continue
        
        # Look for CLIPTextEncode nodes
        if (node_type == 'CLIPTextEncode' or 
            'cliptext' in node_type.lower() or 
            node.get('properties', {}).get('Node name for S&R') == 'CLIPTextEncode'):
            
            widgets_values = node.get('widgets_values', [])
            
            if widgets_values and len(widgets_values) > 0:
                prompt_text = widgets_values[0]
                
                # Only include if it's likely a positive prompt
                is_positive = (
                    'positive' in title or 
                    'pos' in title or
                    (title == '' and prompt_text.strip() != '' and 'negative' not in prompt_text.lower()[:50]) or
                    (title == 'untitled' and prompt_text.strip() != '' and 'negative' not in prompt_text.lower()[:50])
                )
                
                # Exclude obvious negative prompts
                is_negative = (
                    'negative' in title or 
                    'neg' in title or
                    prompt_text.strip() == '' or
                    prompt_text.lower().strip().startswith('negative')
                )
                
                if is_positive and not is_negative:
                    prompt_info = {
                        'text': prompt_text,
                        'node_id': node_id,
                        'node_type': node_type,
                        'title': node.get('title', 'Untitled'),
                        'source': 'workflow'
                    }
                    
                    positive_prompts.append(prompt_info)
                    processed_nodes.add(node_id)
    
    return positive_prompts

def extract_positive_from_prompt_data(prompt_data: Dict, processed_nodes: set) -> List[Dict]:
    """Extract positive prompts from prompt data structure"""
    positive_prompts = []
    
    for key, value in prompt_data.items():
        if isinstance(value, dict):
            class_type = value.get('class_type', '')
            
            # Skip if already processed
            if key in processed_nodes:
                continue
            
            if class_type == 'CLIPTextEncode':
                inputs = value.get('inputs', {})
                
                # Look for text input
                text_content = ""
                if 'text' in inputs:
                    text_content = inputs['text']
                elif 'prompt' in inputs:
                    text_content = inputs['prompt']
                
                if text_content and text_content.strip():
                    # Only include if it looks like a positive prompt
                    is_negative = (
                        text_content.strip() == '' or
                        'negative' in str(text_content).lower()[:50]
                    )
                    
                    if not is_negative:
                        prompt_info = {
                            'text': text_content,
                            'node_id': key,
                            'class_type': class_type,
                            'title': f"Node {key}",
                            'source': 'prompt_data'
                        }
                        
                        positive_prompts.append(prompt_info)
                        processed_nodes.add(key)
    
    return positive_prompts

def print_positive_prompts(result: Dict[str, Any], prompt_only: bool = False, prompt_only_json: bool = False):
    """Print only the positive prompts"""
    positive_prompts = result.get('positive_prompts', [])

    if prompt_only_json:
        # This case is handled in main for aggregating all prompts
        return

    if prompt_only:
        for prompt_info in positive_prompts:
            print(prompt_info['text'])
        return

    print("=" * 80)
    print("POSITIVE PROMPTS EXTRACTION")
    print("=" * 80)
    
    file_info = result.get('file_info', {})
    print(f"\nFile: {file_info.get('filename', 'Unknown')}")
    print(f"Image Size: {file_info.get('size', 'Unknown')}")
    
    if positive_prompts:
        print(f"\n🟢 POSITIVE PROMPTS ({len(positive_prompts)} found):")
        print("-" * 60)
        
        for i, prompt_info in enumerate(positive_prompts, 1):
            print(f"\n#{i} - {prompt_info.get('title', 'Untitled')} (Node: {prompt_info.get('node_id', 'Unknown')})")
            print(f"Type: {prompt_info.get('node_type', prompt_info.get('class_type', 'Unknown'))}")
            print(f"Text: {prompt_info['text']}")
    else:
        print("\n❌ No positive prompts found in this image")


def save_positive_prompts(result: Dict[str, Any], output_path: str, format_type: str = 'txt'):
    """Save only positive prompts to file"""
    try:
        positive_prompts = result.get('positive_prompts', [])
        
        if not positive_prompts:
            print("No positive prompts to save")
            return
        
        if format_type.lower() == 'txt':
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("ComfyUI Positive Prompts\n")
                f.write("=" * 30 + "\n\n")
                
                for i, prompt_info in enumerate(positive_prompts, 1):
                    if len(positive_prompts) > 1:
                        f.write(f"Prompt {i} - {prompt_info.get('title', 'Untitled')}:\n")
                        f.write("-" * 40 + "\n")
                    f.write(f"{prompt_info['text']}\n")
                    if i < len(positive_prompts):
                        f.write("\n")
        
        elif format_type.lower() == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Positive prompts saved to: {output_path}")
        
    except Exception as e:
        print(f"✗ Error saving prompts: {e}")

def main():
    """Main function"""
    args = sys.argv[1:]
    if not args or '--help' in args:
        print("ComfyUI Positive Prompt Extractor")
        print("Usage: python comfyprompt_extractor.py <files_or_dirs...|wildcards> [options]")
        print("\nThis script extracts positive prompts from ComfyUI-generated PNG files.")
        print("It can process individual files, directories, or wildcard patterns.")
        print("\nOptions:")
        print("  --prompt-only       Extract the prompt text only, without any other information.")
        print("  --prompt-only-json  Extract the prompt text only, in JSON format.")
        print("  --save-txt          Save prompts to a text file for each image.")
        print("  --save-json         Save prompts to a JSON file for each image.")
        print("  --output <dir>      Specify an output directory for the saved files.")
        print("  --help              Show this help message.")
        print("\nExamples:")
        print("  - Process a single image:")
        print("    python comfyprompt_extractor.py my_image.png")
        print("\n  - Process all PNGs in a directory:")
        print("    python comfyprompt_extractor.py /path/to/images/")
        print("\n  - Process PNGs using a wildcard and save to text:")
        print("    python comfyprompt_extractor.py images/*.png --save-txt")
        print("\n  - Process multiple inputs and save to a specific output directory:")
        print("    python comfyprompt_extractor.py image1.png /path/to/more_images/ --save-json --output /path/to/prompts/")
        return

    paths = [arg for arg in args if not arg.startswith('--')]
    options = [arg for arg in args if arg.startswith('--')]

    if not paths:
        print("✗ Error: No input files, directories, or patterns specified.")
        print("Use --help for usage instructions.")
        return

    files_to_process = set()
    for path_arg in paths:
        # If path is a directory, search for PNGs inside it
        if os.path.isdir(path_arg):
            search_pattern = os.path.join(path_arg, '**', '*.png')
            found_files = glob.glob(search_pattern, recursive=True)
            for f in found_files:
                files_to_process.add(f)
        # Otherwise, treat it as a glob pattern (which also works for single files)
        else:
            found_files = glob.glob(path_arg, recursive=True)
            for f in found_files:
                 if os.path.isfile(f) and f.lower().endswith('.png'):
                    files_to_process.add(f)

    files_to_process = sorted(list(files_to_process))

    if not files_to_process:
        print("No PNG files found matching the specified paths/patterns.")
        return
    
    prompt_only = '--prompt-only' in options
    prompt_only_json = '--prompt-only-json' in options

    if not prompt_only and not prompt_only_json:
        print(f"Found {len(files_to_process)} PNG files to process.")

    # Get save options
    save_txt = '--save-txt' in options
    save_json = '--save-json' in options
    
    output_dir = None
    if '--output' in options:
        try:
            # Find the value associated with --output
            output_dir_index = -1
            for i, arg in enumerate(args):
                if arg == '--output':
                    output_dir_index = i + 1
                    break
            
            if output_dir_index != -1 and output_dir_index < len(args) and not args[output_dir_index].startswith('--'):
                output_dir = args[output_dir_index]
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                    print(f"Created output directory: {output_dir}")
            else:
                print("✗ Error: --output flag requires a directory path argument.")
                return
        except Exception as e:
            print(f"Error parsing --output argument: {e}")
            return

    all_prompts = []
    for file_path in files_to_process:
        try:
            result = extract_positive_prompts_only(file_path)
            
            if prompt_only_json:
                for prompt_info in result.get('positive_prompts', []):
                    all_prompts.append(prompt_info['text'])
                continue

            print_positive_prompts(result, prompt_only)
            
            if not result.get('positive_prompts'):
                continue

            # Determine output path
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            
            def get_output_path(extension):
                if output_dir:
                    return os.path.join(output_dir, f"{base_name}_positive_prompts.{extension}")
                # Place the output file next to the input file
                return f"{os.path.splitext(file_path)[0]}_positive_prompts.{extension}"

            if save_txt:
                save_positive_prompts(result, get_output_path('txt'), 'txt')
            
            if save_json:
                save_positive_prompts(result, get_output_path('json'), 'json')

            # Interactive save only for single files when no save flag is present
            if len(files_to_process) == 1 and not (save_txt or save_json):
                if not prompt_only:
                    print("\n" + "="*60)
                    choice = input("Save positive prompts? (t)ext, (j)son, (n)o: ").lower()
                    if choice == 't':
                        save_positive_prompts(result, get_output_path('txt'), 'txt')
                    elif choice == 'j':
                        save_positive_prompts(result, get_output_path('json'), 'json')

        except Exception as e:
            print(f"✗ Error processing {os.path.basename(file_path)}: {e}")

    if prompt_only_json:
        print(json.dumps(all_prompts, indent=2))


if __name__ == "__main__":
    main()
