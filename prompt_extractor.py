import json
import sys
import os
from PIL import Image
from typing import Dict, Any, Optional

def extract_positive_prompt(file_path: str) -> Optional[str]:
    """
    Extract the Positive Prompt from PNG metadata parameters key
    
    Args:
        file_path: Path to the PNG file
        
    Returns:
        String containing the positive prompt or None if not found
    """
    try:
        with Image.open(file_path) as img:
            if img.format != 'PNG':
                raise ValueError(f"File is not a PNG: {img.format}")
            
            metadata = img.info
            
            # Look specifically for parameters key
            if 'parameters' not in metadata:
                return None
            
            parameters_data = metadata['parameters']
            
            # Try to parse as JSON first
            try:
                parsed_params = json.loads(parameters_data)
                
                # If it's a dictionary, look for positive prompt keys
                if isinstance(parsed_params, dict):
                    # Try various possible key names for positive prompt
                    possible_keys = [
                        'Positive prompt',
                        'positive prompt', 
                        'Positive Prompt',
                        'positive_prompt',
                        'prompt',
                        'Prompt'
                    ]
                    
                    for key in possible_keys:
                        if key in parsed_params:
                            return parsed_params[key]
                
            except json.JSONDecodeError:
                # If not JSON, parse as text format
                pass
            
            # Parse as text format
            lines = parameters_data.split('\n')
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Look for "Positive prompt:" at the start of a line
                if line.lower().startswith('positive prompt:'):
                    # Extract everything after "Positive prompt:"
                    prompt_text = line.split(':', 1)[1].strip()
                    
                    # Check if the prompt continues on next lines
                    # (until we hit another parameter or empty line)
                    j = i + 1
                    while j < len(lines):
                        next_line = lines[j].strip()
                        
                        # Stop if we hit another parameter (contains :) or empty line
                        if ':' in next_line or not next_line:
                            break
                        
                        # Add continuation line
                        prompt_text += ' ' + next_line
                        j += 1
                    
                    return prompt_text
            
            return None
            
    except Exception as e:
        raise Exception(f"Error reading PNG file: {e}")

def extract_parameters_structure(file_path: str) -> Dict[str, Any]:
    """
    Extract the complete parameters structure for debugging
    
    Args:
        file_path: Path to the PNG file
        
    Returns:
        Dictionary containing parameters structure
    """
    try:
        with Image.open(file_path) as img:
            metadata = img.info
            result = {
                'file_info': {
                    'filename': os.path.basename(file_path),
                    'size': img.size,
                    'mode': img.mode
                },
                'parameters_found': False,
                'parameters_content': None,
                'all_keys': list(metadata.keys())
            }
            
            # Look for parameters key
            if 'parameters' in metadata:
                result['parameters_found'] = True
                parameters_data = metadata['parameters']
                
                try:
                    # Try to parse as JSON
                    parsed_data = json.loads(parameters_data)
                    result['parameters_content'] = {
                        'type': 'json',
                        'data': parsed_data
                    }
                except json.JSONDecodeError:
                    # Store as string
                    result['parameters_content'] = {
                        'type': 'string',
                        'data': parameters_data
                    }
            
            return result
            
    except Exception as e:
        raise Exception(f"Error reading PNG file: {e}")

def save_positive_prompt(prompt: str, output_path: str):
    """Save positive prompt to text file"""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(prompt)
        print(f"✓ Positive prompt saved to: {output_path}")
    except Exception as e:
        print(f"✗ Error saving positive prompt: {e}")

def print_extraction_results(file_path: str, positive_prompt: Optional[str]):
    """Print the extraction results"""
    print("=" * 60)
    print("PARAMETERS:POSITIVE PROMPT EXTRACTION")
    print("=" * 60)
    
    print(f"\nFile: {os.path.basename(file_path)}")
    
    if positive_prompt:
        print(f"\n✓ Positive Prompt Found:")
        print("-" * 40)
        print(positive_prompt)
        print("-" * 40)
        print(f"\nPrompt Length: {len(positive_prompt)} characters")
    else:
        print("\n✗ No positive prompt found in parameters")
        print("\nTip: Use --debug to see the parameters structure")

def print_debug_info(file_path: str):
    """Print parameters structure for debugging"""
    try:
        params_info = extract_parameters_structure(file_path)
        
        print("=" * 60)
        print("DEBUG: PARAMETERS STRUCTURE ANALYSIS")
        print("=" * 60)
        
        print(f"\nFile: {params_info['file_info']['filename']}")
        print(f"Parameters found: {params_info['parameters_found']}")
        
        print(f"\nAll available metadata keys ({len(params_info['all_keys'])}):")
        for key in params_info['all_keys']:
            print(f"  • {key}")
        
        if params_info['parameters_found']:
            print(f"\n✓ Parameters key found!")
            content = params_info['parameters_content']
            print(f"Parameters data type: {content['type']}")
            
            if content['type'] == 'json':
                print("\nParameters JSON structure:")
                print(json.dumps(content['data'], indent=2))
                
                # Analyze the structure
                if isinstance(content['data'], dict):
                    print(f"\nParameters contains {len(content['data'])} keys:")
                    for key in content['data'].keys():
                        print(f"  • {key}")
                        if 'positive' in key.lower() or key.lower() == 'prompt':
                            print(f"    ^ This looks like the positive prompt key!")
            
            else:
                print(f"\nParameters string content:")
                print("-" * 40)
                print(content['data'])
                print("-" * 40)
                
                # Analyze text structure
                lines = content['data'].split('\n')
                print(f"\nParameters contains {len(lines)} lines:")
                for i, line in enumerate(lines[:10]):  # Show first 10 lines
                    line_preview = line.strip()
                    if len(line_preview) > 60:
                        line_preview = line_preview[:60] + "..."
                    print(f"  {i+1}: {line_preview}")
                    if 'positive prompt' in line.lower():
                        print(f"      ^ Line {i+1} contains 'positive prompt'!")
                
                if len(lines) > 10:
                    print(f"  ... and {len(lines) - 10} more lines")
        
        else:
            print(f"\n✗ No 'parameters' key found in metadata")
    
    except Exception as e:
        print(f"✗ Debug error: {e}")

def main():
    """Main function to handle command line usage"""
    if len(sys.argv) < 2:
        print("Parameters:Positive Prompt Extractor")
        print("Usage: python prompt_extractor.py <png_file> [options]")
        print("\nOptions:")
        print("  --save         Save positive prompt to text file")
        print("  --output <path> Specify output file path")
        print("  --debug        Show parameters structure for debugging")
        print("\nExamples:")
        print("  python prompt_extractor.py image.png")
        print("  python prompt_extractor.py image.png --save")
        print("  python prompt_extractor.py image.png --debug")
        return
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"✗ File not found: {file_path}")
        return
    
    try:
        # Debug mode
        if '--debug' in sys.argv:
            print_debug_info(file_path)
            return
        
        # Extract positive prompt
        positive_prompt = extract_positive_prompt(file_path)
        
        # Print results
        print_extraction_results(file_path, positive_prompt)
        
        # Handle save option
        if '--save' in sys.argv and positive_prompt:
            base_name = os.path.splitext(file_path)[0]
            output_path = f"{base_name}_positive_prompt.txt"
            
            if '--output' in sys.argv:
                idx = sys.argv.index('--output')
                if idx + 1 < len(sys.argv):
                    output_path = sys.argv[idx + 1]
            
            save_positive_prompt(positive_prompt, output_path)
        
        # Interactive mode if no save option specified
        elif positive_prompt and '--save' not in sys.argv:
            print("\n" + "="*60)
            choice = input("Save positive prompt to file? (y/n): ").lower()
            
            if choice == 'y':
                base_name = os.path.splitext(file_path)[0]
                output_path = f"{base_name}_positive_prompt.txt"
                save_positive_prompt(positive_prompt, output_path)
    
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    main()
