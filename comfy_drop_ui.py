import json
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk
import pyperclip
from typing import Dict, Any, List, Optional
import threading
import glob

# Try to import tkinterdnd2 for drag and drop
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False

class ComfyUIPromptExtractorUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ComfyUI Positive Prompt Extractor")
        self.root.geometry("900x700")
        self.root.configure(bg='#f0f0f0')
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="ComfyUI Positive Prompt Extractor", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # File selection section
        file_frame = ttk.LabelFrame(main_frame, text="Select ComfyUI PNG File(s)", padding="10")
        file_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        
        # File path display
        self.file_path_var = tk.StringVar()
        self.file_path_var.set("No file selected")
        
        ttk.Label(file_frame, text="File(s):").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.file_label = ttk.Label(file_frame, textvariable=self.file_path_var, 
                                   foreground='gray', font=('Arial', 9))
        self.file_label.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # Browse buttons frame
        browse_frame = ttk.Frame(file_frame)
        browse_frame.grid(row=0, column=2, padx=(5, 0))
        
        self.browse_file_btn = ttk.Button(browse_frame, text="Browse File", command=self.browse_file)
        self.browse_file_btn.grid(row=0, column=0, padx=(0, 2))
        
        self.browse_folder_btn = ttk.Button(browse_frame, text="Browse Folder", command=self.browse_folder)
        self.browse_folder_btn.grid(row=0, column=1)
        
        # Drop zone
        drop_text = "Drag & Drop PNG file(s) or folder here" if HAS_DND else "Click here to select PNG file(s)"
        if not HAS_DND:
            drop_text += "\n(Install tkinterdnd2 for drag & drop: pip install tkinterdnd2)"
        
        self.drop_frame = tk.Frame(file_frame, bg='#e8e8e8', relief='ridge', bd=2, height=100)
        self.drop_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        self.drop_frame.grid_propagate(False)
        
        self.drop_label = tk.Label(self.drop_frame, text=drop_text, 
                                  bg='#e8e8e8', fg='gray', font=('Arial', 10),
                                  justify='center')
        self.drop_label.place(relx=0.5, rely=0.5, anchor='center')
        
        # Setup drag and drop if available
        if HAS_DND:
            self.drop_frame.drop_target_register(DND_FILES)
            self.drop_frame.dnd_bind('<<Drop>>', self.on_drop)
            self.drop_frame.dnd_bind('<<DragEnter>>', self.on_drag_enter)
            self.drop_frame.dnd_bind('<<DragLeave>>', self.on_drag_leave)
        else:
            # Fallback to click
            self.drop_frame.bind('<Button-1>', self.browse_file)
            self.drop_label.bind('<Button-1>', self.browse_file)
        
        # Results section
        results_frame = ttk.LabelFrame(main_frame, text="Extracted Positive Prompts", padding="10")
        results_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        # Text area for prompts with tabs
        self.notebook = ttk.Notebook(results_frame)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Main prompts tab
        self.prompts_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.prompts_frame, text="Prompts")
        
        self.prompts_frame.columnconfigure(0, weight=1)
        self.prompts_frame.rowconfigure(0, weight=1)
        
        self.prompt_text = scrolledtext.ScrolledText(self.prompts_frame, wrap=tk.WORD, 
                                                    height=15, font=('Arial', 10))
        self.prompt_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Summary tab
        self.summary_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.summary_frame, text="Summary")
        
        self.summary_frame.columnconfigure(0, weight=1)
        self.summary_frame.rowconfigure(0, weight=1)
        
        self.summary_text = scrolledtext.ScrolledText(self.summary_frame, wrap=tk.WORD, 
                                                     height=15, font=('Arial', 10))
        self.summary_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Buttons frame
        buttons_frame = ttk.Frame(results_frame)
        buttons_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        buttons_frame.columnconfigure(0, weight=1)
        
        # Status and buttons
        self.status_var = tk.StringVar()
        status_text = "Ready - Drag & drop or select ComfyUI PNG file(s)" if HAS_DND else "Ready - Select ComfyUI PNG file(s) to extract prompts"
        self.status_var.set(status_text)
        
        self.status_label = ttk.Label(buttons_frame, textvariable=self.status_var, 
                                     foreground='gray', font=('Arial', 9))
        self.status_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        # Button frame
        btn_frame = ttk.Frame(buttons_frame)
        btn_frame.grid(row=1, column=0, sticky=tk.E)
        
        self.copy_btn = ttk.Button(btn_frame, text="Copy All Prompts", 
                                  command=self.copy_to_clipboard, state='disabled')
        self.copy_btn.grid(row=0, column=0, padx=(0, 5))
        
        self.copy_first_btn = ttk.Button(btn_frame, text="Copy First Prompt", 
                                        command=self.copy_first_prompt, state='disabled')
        self.copy_first_btn.grid(row=0, column=1, padx=(0, 5))
        
        self.save_btn = ttk.Button(btn_frame, text="Save to File", 
                                  command=self.save_to_file, state='disabled')
        self.save_btn.grid(row=0, column=2, padx=(0, 5))
        
        self.clear_btn = ttk.Button(btn_frame, text="Clear", command=self.clear_results)
        self.clear_btn.grid(row=0, column=3)
        
        # Progress bar (hidden by default)
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 5))
        self.progress.grid_remove()  # Hide initially
        
        # Store current results
        self.current_results = []
        self.current_files = []
    
    def on_drop(self, event):
        """Handle file drop event"""
        files = self.root.tk.splitlist(event.data)
        if files:
            self.load_files(files)
        
        # Reset drop zone appearance
        self.drop_frame.configure(bg='#e8e8e8')
        self.drop_label.configure(bg='#e8e8e8', fg='gray')
    
    def on_drag_enter(self, event):
        """Handle drag enter event"""
        self.drop_frame.configure(bg='#d0f0d0')  # Light green
        self.drop_label.configure(bg='#d0f0d0', fg='#006600', text="Drop PNG file(s) or folder here!")
    
    def on_drag_leave(self, event):
        """Handle drag leave event"""
        self.drop_frame.configure(bg='#e8e8e8')
        self.drop_label.configure(bg='#e8e8e8', fg='gray', text="Drag & Drop PNG file(s) or folder here")
        
    def browse_file(self, event=None):
        """Open file dialog to select PNG file(s)"""
        file_paths = filedialog.askopenfilenames(
            title="Select ComfyUI PNG File(s)",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        
        if file_paths:
            self.load_files(list(file_paths))
    
    def browse_folder(self):
        """Open folder dialog to select directory with PNG files"""
        folder_path = filedialog.askdirectory(title="Select Folder with ComfyUI PNG Files")
        
        if folder_path:
            # Find all PNG files in the folder
            png_files = glob.glob(os.path.join(folder_path, "**", "*.png"), recursive=True)
            if png_files:
                self.load_files(png_files)
            else:
                messagebox.showinfo("No Files", "No PNG files found in the selected folder.")
    
    def load_files(self, file_paths):
        """Load and process the selected files"""
        # Filter for PNG files and existing files
        valid_files = []
        for file_path in file_paths:
            if os.path.isdir(file_path):
                # If it's a directory, find PNG files in it
                png_files = glob.glob(os.path.join(file_path, "**", "*.png"), recursive=True)
                valid_files.extend(png_files)
            elif os.path.exists(file_path) and file_path.lower().endswith('.png'):
                valid_files.append(file_path)
        
        if not valid_files:
            messagebox.showwarning("Warning", "No valid PNG files found")
            return
        
        # Update UI
        if len(valid_files) == 1:
            self.file_path_var.set(os.path.basename(valid_files[0]))
        else:
            self.file_path_var.set(f"{len(valid_files)} PNG files selected")
        
        self.status_var.set("Processing...")
        self.progress.grid()
        self.progress.start()
        
        # Disable buttons during processing
        self.browse_file_btn.configure(state='disabled')
        self.browse_folder_btn.configure(state='disabled')
        self.copy_btn.configure(state='disabled')
        self.copy_first_btn.configure(state='disabled')
        self.save_btn.configure(state='disabled')
        
        # Process files in separate thread to avoid UI freezing
        thread = threading.Thread(target=self.extract_prompts_thread, args=(valid_files,))
        thread.daemon = True
        thread.start()
    
    def extract_prompts_thread(self, file_paths):
        """Extract prompts in separate thread"""
        try:
            results = []
            for file_path in file_paths:
                result = self.extract_positive_prompts_only(file_path)
                results.append(result)
            
            # Update UI in main thread
            self.root.after(0, self.update_results, results, file_paths)
        except Exception as e:
            self.root.after(0, self.show_error, str(e))
    
    def extract_positive_prompts_only(self, file_path: str) -> Dict[str, Any]:
        """Extract only positive prompts from ComfyUI PNG metadata"""
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
                        prompts = self.extract_positive_from_workflow(workflow_data, processed_nodes)
                        result['positive_prompts'].extend(prompts)
                    except json.JSONDecodeError as e:
                        print(f"Warning: Could not parse workflow JSON: {e}")
                
                # Only check prompt data if we didn't find anything in workflow
                if not result['positive_prompts'] and 'prompt' in metadata:
                    try:
                        prompt_data = json.loads(metadata['prompt'])
                        prompts = self.extract_positive_from_prompt_data(prompt_data, processed_nodes)
                        result['positive_prompts'].extend(prompts)
                    except json.JSONDecodeError as e:
                        print(f"Warning: Could not parse prompt JSON: {e}")
                
                return result
                
        except Exception as e:
            raise Exception(f"Error reading PNG file: {e}")
    
    def extract_positive_from_workflow(self, workflow_data: Dict, processed_nodes: set) -> List[Dict]:
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
    
    def extract_positive_from_prompt_data(self, prompt_data: Dict, processed_nodes: set) -> List[Dict]:
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
    
    def update_results(self, results, file_paths):
        """Update UI with extraction results"""
        # Stop progress bar
        self.progress.stop()
        self.progress.grid_remove()
        
        # Re-enable buttons
        self.browse_file_btn.configure(state='normal')
        self.browse_folder_btn.configure(state='normal')
        
        # Store results
        self.current_results = results
        self.current_files = file_paths
        
        # Clear previous content
        self.prompt_text.delete(1.0, tk.END)
        self.summary_text.delete(1.0, tk.END)
        
        total_prompts = 0
        files_with_prompts = 0
        all_prompt_texts = []
        
        # Process results
        for i, result in enumerate(results):
            file_info = result.get('file_info', {})
            positive_prompts = result.get('positive_prompts', [])
            
            if positive_prompts:
                files_with_prompts += 1
                total_prompts += len(positive_prompts)
                
                # Add to main prompts display
                if len(results) > 1:
                    self.prompt_text.insert(tk.END, f"=== {file_info.get('filename', 'Unknown')} ===\n")
                
                for j, prompt_info in enumerate(positive_prompts, 1):
                    if len(positive_prompts) > 1:
                        self.prompt_text.insert(tk.END, f"\nPrompt {j} - {prompt_info.get('title', 'Untitled')}:\n")
                        self.prompt_text.insert(tk.END, "-" * 40 + "\n")
                    
                    prompt_text = prompt_info['text']
                    self.prompt_text.insert(tk.END, f"{prompt_text}\n")
                    all_prompt_texts.append(prompt_text)
                    
                    if j < len(positive_prompts):
                        self.prompt_text.insert(tk.END, "\n")
                
                if i < len(results) - 1:
                    self.prompt_text.insert(tk.END, "\n" + "="*60 + "\n\n")
        
        # Update summary
        self.summary_text.insert(tk.END, f"EXTRACTION SUMMARY\n")
        self.summary_text.insert(tk.END, f"="*50 + "\n\n")
        self.summary_text.insert(tk.END, f"Files processed: {len(results)}\n")
        self.summary_text.insert(tk.END, f"Files with prompts: {files_with_prompts}\n")
        self.summary_text.insert(tk.END, f"Total positive prompts found: {total_prompts}\n\n")
        
        if files_with_prompts == 0:
            self.summary_text.insert(tk.END, "No positive prompts found in any files.\n")
            self.summary_text.insert(tk.END, "Make sure the PNG files contain ComfyUI workflow metadata.")
        else:
            self.summary_text.insert(tk.END, "FILES WITH PROMPTS:\n")
            self.summary_text.insert(tk.END, "-" * 30 + "\n")
            
            for result in results:
                positive_prompts = result.get('positive_prompts', [])
                if positive_prompts:
                    filename = result.get('file_info', {}).get('filename', 'Unknown')
                    self.summary_text.insert(tk.END, f"• {filename} ({len(positive_prompts)} prompts)\n")
        
        # Update status and enable buttons
        if total_prompts > 0:
            self.status_var.set(f"✓ Extracted {total_prompts} positive prompts from {files_with_prompts} files")
            self.copy_btn.configure(state='normal')
            self.copy_first_btn.configure(state='normal')
            self.save_btn.configure(state='normal')
            
            # Store all prompts for copying
            self.all_prompt_texts = all_prompt_texts
        else:
            self.status_var.set("✗ No positive prompts found")
            self.all_prompt_texts = []
    
    def show_error(self, error_message):
        """Show error message"""
        self.progress.stop()
        self.progress.grid_remove()
        self.browse_file_btn.configure(state='normal')
        self.browse_folder_btn.configure(state='normal')
        
        self.status_var.set(f"✗ Error: {error_message}")
        messagebox.showerror("Error", f"Failed to process file(s):\n{error_message}")
    
    def copy_to_clipboard(self):
        """Copy all prompts to clipboard"""
        if hasattr(self, 'all_prompt_texts') and self.all_prompt_texts:
            try:
                # Join all prompts with double newlines
                all_text = '\n\n'.join(self.all_prompt_texts)
                pyperclip.copy(all_text)
                self.status_var.set(f"✓ All {len(self.all_prompt_texts)} prompts copied to clipboard!")
                
                # Reset status after 3 seconds
                self.root.after(3000, lambda: self.status_var.set("Ready"))
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to copy to clipboard:\n{e}")
    
    def copy_first_prompt(self):
        """Copy first prompt to clipboard"""
        if hasattr(self, 'all_prompt_texts') and self.all_prompt_texts:
            try:
                pyperclip.copy(self.all_prompt_texts[0])
                self.status_var.set("✓ First prompt copied to clipboard!")
                
                # Reset status after 3 seconds
                self.root.after(3000, lambda: self.status_var.set("Ready"))
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to copy to clipboard:\n{e}")
    
    def save_to_file(self):
        """Save prompts to text file"""
        if hasattr(self, 'all_prompt_texts') and self.all_prompt_texts:
            # Default filename
            if len(self.current_files) == 1:
                base_name = os.path.splitext(os.path.basename(self.current_files[0]))[0]
                default_name = f"{base_name}_positive_prompts.txt"
            else:
                default_name = "comfyui_positive_prompts.txt"
            
            file_path = filedialog.asksaveasfilename(
                title="Save Positive Prompts",
                defaultextension=".txt",
                initialfilename=default_name,
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            
            if file_path:
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write("ComfyUI Positive Prompts\n")
                        f.write("=" * 30 + "\n\n")
                        
                        for i, prompt_text in enumerate(self.all_prompt_texts, 1):
                            if len(self.all_prompt_texts) > 1:
                                f.write(f"Prompt {i}:\n")
                                f.write("-" * 20 + "\n")
                            f.write(f"{prompt_text}\n")
                            if i < len(self.all_prompt_texts):
                                f.write("\n")
                    
                    self.status_var.set(f"✓ Prompts saved to {os.path.basename(file_path)}")
                    
                    # Reset status after 3 seconds
                    self.root.after(3000, lambda: self.status_var.set("Ready"))
                    
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save file:\n{e}")
    
    def clear_results(self):
        """Clear all results"""
        self.prompt_text.delete(1.0, tk.END)
        self.summary_text.delete(1.0, tk.END)
        self.file_path_var.set("No file selected")
        status_text = "Ready - Drag & drop or select ComfyUI PNG file(s)" if HAS_DND else "Ready - Select ComfyUI PNG file(s) to extract prompts"
        self.status_var.set(status_text)
        self.copy_btn.configure(state='disabled')
        self.copy_first_btn.configure(state='disabled')
        self.save_btn.configure(state='disabled')
        self.current_results = []
        self.current_files = []
        if hasattr(self, 'all_prompt_texts'):
            self.all_prompt_texts = []

def main():
    # Check if required packages are available
    missing_packages = []
    
    try:
        import pyperclip
    except ImportError:
        missing_packages.append('pyperclip')
    
    try:
        from PIL import Image
    except ImportError:
        missing_packages.append('Pillow')
    
    # Check for drag and drop support
    if not HAS_DND:
        print("Note: For drag & drop functionality, install tkinterdnd2:")
        print("pip install tkinterdnd2")
        missing_packages.append('tkinterdnd2')
    
    if missing_packages:
        print("Installing required packages:", ', '.join(missing_packages))
        import subprocess
        import sys
        for package in missing_packages:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            except subprocess.CalledProcessError:
                print(f"Failed to install {package}. You may need to install it manually.")
        
        print("Please restart the application to use drag & drop functionality.")
    
    # Use TkinterDnD root if available, otherwise regular Tk
    if HAS_DND:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    
    app = ComfyUIPromptExtractorUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
