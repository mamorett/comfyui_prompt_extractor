import json
import sys
import os
from PIL import Image
from typing import Dict, Any, Optional

def extract_comfyui_workflow(file_path: str) -> Dict[str, Any]:
    """
    Extract ComfyUI workflow and prompt data from PNG metadata
    
    Args:
        file_path: Path to the PNG file
        
    Returns:
        Dictionary containing workflow data
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
                'comfyui_data': {}
            }
            
            # Look for ComfyUI specific keys
            comfyui_keys = ['workflow', 'prompt', 'Workflow', 'Prompt']
            
            for key in metadata:
                if key in comfyui_keys:
                    try:
                        # Try to parse as JSON
                        parsed_data = json.loads(metadata[key])
                        result['comfyui_data'][key.lower()] = parsed_data
                    except json.JSONDecodeError:
                        # If not JSON, store as string
                        result['comfyui_data'][key.lower()] = metadata[key]
                elif 'comfy' in key.lower() or 'workflow' in key.lower():
                    # Catch any other ComfyUI-related keys
                    try:
                        parsed_data = json.loads(metadata[key])
                        result['comfyui_data'][key] = parsed_data
                    except json.JSONDecodeError:
                        result['comfyui_data'][key] = metadata[key]
            
            return result
            
    except Exception as e:
        raise Exception(f"Error reading PNG file: {e}")

def save_workflow_json(workflow_data: Dict[str, Any], output_path: str):
    """Save workflow data to JSON file"""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(workflow_data, f, indent=2, ensure_ascii=False)
        print(f"✓ Workflow saved to: {output_path}")
    except Exception as e:
        print(f"✗ Error saving workflow: {e}")

def save_workflow_only(workflow_data: Dict[str, Any], output_path: str):
    """Save only the workflow part (for direct import to ComfyUI)"""
    try:
        if 'workflow' in workflow_data.get('comfyui_data', {}):
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(workflow_data['comfyui_data']['workflow'], f, indent=2, ensure_ascii=False)
            print(f"✓ Workflow-only file saved to: {output_path}")
        else:
            print("✗ No workflow data found to save")
    except Exception as e:
        print(f"✗ Error saving workflow-only file: {e}")

def print_workflow_summary(workflow_data: Dict[str, Any]):
    """Print a summary of the extracted workflow"""
    print("=" * 60)
    print("COMFYUI WORKFLOW EXTRACTION RESULTS")
    print("=" * 60)
    
    # File info
    file_info = workflow_data.get('file_info', {})
    print(f"\nFile: {file_info.get('filename', 'Unknown')}")
    print(f"Image Size: {file_info.get('size', 'Unknown')}")
    print(f"Color Mode: {file_info.get('mode', 'Unknown')}")
    
    # ComfyUI data
    comfyui_data = workflow_data.get('comfyui_data', {})
    
    if not comfyui_data:
        print("\n✗ No ComfyUI workflow data found in this PNG file")
        return
    
    print(f"\n✓ Found ComfyUI data with {len(comfyui_data)} key(s):")
    
    for key, value in comfyui_data.items():
        print(f"\n📋 {key.upper()}:")
        
        if isinstance(value, dict):
            if key == 'workflow':
                # Analyze workflow structure
                nodes = value.get('nodes', [])
                print(f"  - Nodes: {len(nodes)}")
                
                if nodes:
                    node_types = {}
                    for node in nodes:
                        node_type = node.get('type', 'Unknown')
                        node_types[node_type] = node_types.get(node_type, 0) + 1
                    
                    print("  - Node types:")
                    for node_type, count in sorted(node_types.items()):
                        print(f"    • {node_type}: {count}")
                
                # Check for other workflow properties
                for prop in ['links', 'groups', 'config']:
                    if prop in value:
                        if isinstance(value[prop], list):
                            print(f"  - {prop.capitalize()}: {len(value[prop])}")
                        else:
                            print(f"  - {prop.capitalize()}: Present")
            
            elif key == 'prompt':
                # Analyze prompt structure
                print(f"  - Prompt entries: {len(value)}")
                
                # Look for common ComfyUI node types in prompt
                node_classes = set()
                for prompt_key, prompt_value in value.items():
                    if isinstance(prompt_value, dict) and 'class_type' in prompt_value:
                        node_classes.add(prompt_value['class_type'])
                
                if node_classes:
                    print("  - Node classes used:")
                    for node_class in sorted(node_classes):
                        print(f"    • {node_class}")
            
            else:
                print(f"  - Type: Dictionary with {len(value)} keys")
        
        elif isinstance(value, list):
            print(f"  - Type: List with {len(value)} items")
        
        else:
            print(f"  - Type: {type(value).__name__}")
            if isinstance(value, str) and len(value) > 100:
                print(f"  - Content: {value[:100]}...")
            else:
                print(f"  - Content: {value}")

def main():
    """Main function to handle command line usage"""
    if len(sys.argv) < 2:
        print("ComfyUI Workflow Extractor")
        print("Usage: python comfyui_extractor.py <png_file> [options]")
        print("\nOptions:")
        print("  --save-all     Save complete metadata to JSON")
        print("  --save-workflow Save only workflow data to JSON")
        print("  --output <path> Specify output file path")
        print("\nExample:")
        print("  python comfyui_extractor.py image.png --save-workflow")
        return
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"✗ File not found: {file_path}")
        return
    
    try:
        # Extract workflow data
        workflow_data = extract_comfyui_workflow(file_path)
        
        # Print summary
        print_workflow_summary(workflow_data)
        
        # Handle save options
        base_name = os.path.splitext(file_path)[0]
        
        if '--save-all' in sys.argv:
            output_path = f"{base_name}_complete_metadata.json"
            if '--output' in sys.argv:
                idx = sys.argv.index('--output')
                if idx + 1 < len(sys.argv):
                    output_path = sys.argv[idx + 1]
            save_workflow_json(workflow_data, output_path)
        
        if '--save-workflow' in sys.argv:
            output_path = f"{base_name}_workflow.json"
            if '--output' in sys.argv and '--save-all' not in sys.argv:
                idx = sys.argv.index('--output')
                if idx + 1 < len(sys.argv):
                    output_path = sys.argv[idx + 1]
            save_workflow_only(workflow_data, output_path)
        
        # Interactive mode if no save options specified
        if '--save-all' not in sys.argv and '--save-workflow' not in sys.argv:
            if workflow_data.get('comfyui_data'):
                print("\n" + "="*60)
                choice = input("Save workflow data? (a)ll metadata, (w)orkflow only, (n)o: ").lower()
                
                if choice == 'a':
                    output_path = f"{base_name}_complete_metadata.json"
                    save_workflow_json(workflow_data, output_path)
                elif choice == 'w':
                    output_path = f"{base_name}_workflow.json"
                    save_workflow_only(workflow_data, output_path)
    
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    main()

