import json
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk
import pyperclip
from typing import Optional
import threading

# Try to import tkinterdnd2 for drag and drop
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False

class PromptExtractorUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PNG Positive Prompt Extractor")
        self.root.geometry("800x600")
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
        title_label = ttk.Label(main_frame, text="PNG Positive Prompt Extractor", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # File selection section
        file_frame = ttk.LabelFrame(main_frame, text="Select PNG File", padding="10")
        file_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        
        # File path display
        self.file_path_var = tk.StringVar()
        self.file_path_var.set("No file selected")
        
        ttk.Label(file_frame, text="File:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.file_label = ttk.Label(file_frame, textvariable=self.file_path_var, 
                                   foreground='gray', font=('Arial', 9))
        self.file_label.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # Browse button
        self.browse_btn = ttk.Button(file_frame, text="Browse", command=self.browse_file)
        self.browse_btn.grid(row=0, column=2, padx=(5, 0))
        
        # Drop zone
        drop_text = "Drag & Drop PNG file here" if HAS_DND else "Click here to select PNG file"
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
        results_frame = ttk.LabelFrame(main_frame, text="Extracted Positive Prompt", padding="10")
        results_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        # Text area for prompt
        self.prompt_text = scrolledtext.ScrolledText(results_frame, wrap=tk.WORD, 
                                                    height=15, font=('Arial', 10))
        self.prompt_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Buttons frame
        buttons_frame = ttk.Frame(results_frame)
        buttons_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        buttons_frame.columnconfigure(0, weight=1)
        
        # Status and buttons
        self.status_var = tk.StringVar()
        status_text = "Ready - Drag & drop or select a PNG file" if HAS_DND else "Ready - Select a PNG file to extract prompt"
        self.status_var.set(status_text)
        
        self.status_label = ttk.Label(buttons_frame, textvariable=self.status_var, 
                                     foreground='gray', font=('Arial', 9))
        self.status_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        # Button frame
        btn_frame = ttk.Frame(buttons_frame)
        btn_frame.grid(row=1, column=0, sticky=tk.E)
        
        self.copy_btn = ttk.Button(btn_frame, text="Copy to Clipboard", 
                                  command=self.copy_to_clipboard, state='disabled')
        self.copy_btn.grid(row=0, column=0, padx=(0, 5))
        
        self.save_btn = ttk.Button(btn_frame, text="Save to File", 
                                  command=self.save_to_file, state='disabled')
        self.save_btn.grid(row=0, column=1, padx=(0, 5))
        
        self.clear_btn = ttk.Button(btn_frame, text="Clear", command=self.clear_results)
        self.clear_btn.grid(row=0, column=2)
        
        # Progress bar (hidden by default)
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 5))
        self.progress.grid_remove()  # Hide initially
    
    def on_drop(self, event):
        """Handle file drop event"""
        files = self.root.tk.splitlist(event.data)
        if files:
            file_path = files[0]  # Take the first file
            self.load_file(file_path)
        
        # Reset drop zone appearance
        self.drop_frame.configure(bg='#e8e8e8')
        self.drop_label.configure(bg='#e8e8e8', fg='gray')
    
    def on_drag_enter(self, event):
        """Handle drag enter event"""
        self.drop_frame.configure(bg='#d0f0d0')  # Light green
        self.drop_label.configure(bg='#d0f0d0', fg='#006600', text="Drop PNG file here!")
    
    def on_drag_leave(self, event):
        """Handle drag leave event"""
        self.drop_frame.configure(bg='#e8e8e8')
        self.drop_label.configure(bg='#e8e8e8', fg='gray', text="Drag & Drop PNG file here")
        
    def browse_file(self, event=None):
        """Open file dialog to select PNG file"""
        file_path = filedialog.askopenfilename(
            title="Select PNG File",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        
        if file_path:
            self.load_file(file_path)
    
    def load_file(self, file_path):
        """Load and process the selected file"""
        if not os.path.exists(file_path):
            messagebox.showerror("Error", f"File not found: {file_path}")
            return
        
        if not file_path.lower().endswith('.png'):
            messagebox.showwarning("Warning", "Please select a PNG file")
            return
        
        # Update UI
        self.file_path_var.set(os.path.basename(file_path))
        self.status_var.set("Processing...")
        self.progress.grid()
        self.progress.start()
        
        # Disable buttons during processing
        self.browse_btn.configure(state='disabled')
        self.copy_btn.configure(state='disabled')
        self.save_btn.configure(state='disabled')
        
        # Process file in separate thread to avoid UI freezing
        thread = threading.Thread(target=self.extract_prompt_thread, args=(file_path,))
        thread.daemon = True
        thread.start()
    
    def extract_prompt_thread(self, file_path):
        """Extract prompt in separate thread"""
        try:
            prompt = self.extract_positive_prompt(file_path)
            # Update UI in main thread
            self.root.after(0, self.update_results, prompt, file_path)
        except Exception as e:
            self.root.after(0, self.show_error, str(e))
    
    def extract_positive_prompt(self, file_path: str) -> Optional[str]:
        """Extract the Positive Prompt from PNG metadata parameters key"""
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
                    pass
                
                # Parse as text format
                lines = parameters_data.split('\n')
                
                for i, line in enumerate(lines):
                    line = line.strip()
                    
                    if line.lower().startswith('positive prompt:'):
                        prompt_text = line.split(':', 1)[1].strip()
                        
                        # Check if the prompt continues on next lines
                        j = i + 1
                        while j < len(lines):
                            next_line = lines[j].strip()
                            
                            if ':' in next_line or not next_line:
                                break
                            
                            prompt_text += ' ' + next_line
                            j += 1
                        
                        return prompt_text
                
                return None
                
        except Exception as e:
            raise Exception(f"Error reading PNG file: {e}")
    
    def update_results(self, prompt, file_path):
        """Update UI with extraction results"""
        # Stop progress bar
        self.progress.stop()
        self.progress.grid_remove()
        
        # Re-enable buttons
        self.browse_btn.configure(state='normal')
        
        if prompt:
            # Display prompt
            self.prompt_text.delete(1.0, tk.END)
            self.prompt_text.insert(1.0, prompt)
            
            # Update status
            self.status_var.set(f"✓ Prompt extracted successfully ({len(prompt)} characters)")
            
            # Enable action buttons
            self.copy_btn.configure(state='normal')
            self.save_btn.configure(state='normal')
            
            # Store current prompt for actions
            self.current_prompt = prompt
            self.current_file_path = file_path
            
        else:
            self.prompt_text.delete(1.0, tk.END)
            self.prompt_text.insert(1.0, "No positive prompt found in this PNG file.\n\n"
                                         "Make sure the PNG contains 'parameters' metadata with a 'Positive prompt' field.")
            
            self.status_var.set("✗ No positive prompt found")
            self.current_prompt = None
    
    def show_error(self, error_message):
        """Show error message"""
        self.progress.stop()
        self.progress.grid_remove()
        self.browse_btn.configure(state='normal')
        
        self.status_var.set(f"✗ Error: {error_message}")
        messagebox.showerror("Error", f"Failed to process file:\n{error_message}")
    
    def copy_to_clipboard(self):
        """Copy prompt to clipboard"""
        if hasattr(self, 'current_prompt') and self.current_prompt:
            try:
                pyperclip.copy(self.current_prompt)
                self.status_var.set("✓ Prompt copied to clipboard!")
                
                # Reset status after 3 seconds
                self.root.after(3000, lambda: self.status_var.set("Ready"))
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to copy to clipboard:\n{e}")
    
    def save_to_file(self):
        """Save prompt to text file"""
        if hasattr(self, 'current_prompt') and self.current_prompt:
            # Default filename based on original PNG
            default_name = "positive_prompt.txt"
            if hasattr(self, 'current_file_path'):
                base_name = os.path.splitext(os.path.basename(self.current_file_path))[0]
                default_name = f"{base_name}_positive_prompt.txt"
            
            file_path = filedialog.asksaveasfilename(
                title="Save Positive Prompt",
                defaultextension=".txt",
                initialfilename=default_name,
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            
            if file_path:
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(self.current_prompt)
                    
                    self.status_var.set(f"✓ Prompt saved to {os.path.basename(file_path)}")
                    
                    # Reset status after 3 seconds
                    self.root.after(3000, lambda: self.status_var.set("Ready"))
                    
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save file:\n{e}")
    
    def clear_results(self):
        """Clear all results"""
        self.prompt_text.delete(1.0, tk.END)
        self.file_path_var.set("No file selected")
        status_text = "Ready - Drag & drop or select a PNG file" if HAS_DND else "Ready - Select a PNG file to extract prompt"
        self.status_var.set(status_text)
        self.copy_btn.configure(state='disabled')
        self.save_btn.configure(state='disabled')
        if hasattr(self, 'current_prompt'):
            self.current_prompt = None

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
    
    app = PromptExtractorUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
