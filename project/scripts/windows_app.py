"""
Windows GUI Application for Research Paper Processing Pipeline.
Cross-platform compatible (Windows, macOS, Linux).
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import sys
import os
from pathlib import Path
import json
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

class PipelineGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Research Paper Processing Pipeline")
        self.root.geometry("900x700")
        
        # Variables
        self.papers_dir = tk.StringVar(value="project/papers")
        self.output_dir = tk.StringVar(value="project/outputs")
        self.provider = tk.StringVar(value="anthropic")
        self.cloud_provider = tk.StringVar(value="local")
        self.workers = tk.IntVar(value=5)
        self.use_langchain = tk.BooleanVar(value=False)
        self.check_pubmed = tk.BooleanVar(value=False)
        self.pubmed_query = tk.StringVar(value="")
        self.email = tk.StringVar(value="")
        self.anthropic_key = tk.StringVar(value=os.environ.get('ANTHROPIC_API_KEY', ''))
        self.openai_key = tk.StringVar(value=os.environ.get('OPENAI_API_KEY', ''))
        
        self.processing = False
        
        self.setup_ui()
    
    def setup_ui(self):
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Tab 1: Configuration
        config_frame = ttk.Frame(notebook)
        notebook.add(config_frame, text='Configuration')
        self.setup_config_tab(config_frame)
        
        # Tab 2: PubMed
        pubmed_frame = ttk.Frame(notebook)
        notebook.add(pubmed_frame, text='PubMed Check')
        self.setup_pubmed_tab(pubmed_frame)
        
        # Tab 3: Log
        log_frame = ttk.Frame(notebook)
        notebook.add(log_frame, text='Processing Log')
        self.setup_log_tab(log_frame)
        
        # Bottom buttons
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill='x', padx=10, pady=10)
        
        self.start_button = ttk.Button(
            button_frame, 
            text="Start Processing", 
            command=self.start_processing,
            style='Accent.TButton'
        )
        self.start_button.pack(side='left', padx=5)
        
        self.stop_button = ttk.Button(
            button_frame,
            text="Stop",
            command=self.stop_processing,
            state='disabled'
        )
        self.stop_button.pack(side='left', padx=5)
        
        ttk.Button(
            button_frame,
            text="Exit",
            command=self.root.quit
        ).pack(side='right', padx=5)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(
            self.root,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        status_bar.pack(side='bottom', fill='x')
    
    def setup_config_tab(self, parent):
        # Directories section
        dir_frame = ttk.LabelFrame(parent, text="Directories", padding=10)
        dir_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(dir_frame, text="Papers Directory:").grid(row=0, column=0, sticky='w', pady=5)
        ttk.Entry(dir_frame, textvariable=self.papers_dir, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(dir_frame, text="Browse", command=self.browse_papers_dir).grid(row=0, column=2)
        
        ttk.Label(dir_frame, text="Output Directory:").grid(row=1, column=0, sticky='w', pady=5)
        ttk.Entry(dir_frame, textvariable=self.output_dir, width=50).grid(row=1, column=1, padx=5)
        ttk.Button(dir_frame, text="Browse", command=self.browse_output_dir).grid(row=1, column=2)
        
        # API Configuration
        api_frame = ttk.LabelFrame(parent, text="API Configuration", padding=10)
        api_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(api_frame, text="AI Provider:").grid(row=0, column=0, sticky='w', pady=5)
        provider_combo = ttk.Combobox(
            api_frame,
            textvariable=self.provider,
            values=['anthropic', 'openai'],
            state='readonly',
            width=20
        )
        provider_combo.grid(row=0, column=1, sticky='w', padx=5)
        
        ttk.Label(api_frame, text="Anthropic API Key:").grid(row=1, column=0, sticky='w', pady=5)
        ttk.Entry(api_frame, textvariable=self.anthropic_key, width=50, show='*').grid(row=1, column=1, padx=5)
        
        ttk.Label(api_frame, text="OpenAI API Key:").grid(row=2, column=0, sticky='w', pady=5)
        ttk.Entry(api_frame, textvariable=self.openai_key, width=50, show='*').grid(row=2, column=1, padx=5)
        
        # Cloud Configuration
        cloud_frame = ttk.LabelFrame(parent, text="Cloud Storage", padding=10)
        cloud_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(cloud_frame, text="Storage Provider:").grid(row=0, column=0, sticky='w', pady=5)
        cloud_combo = ttk.Combobox(
            cloud_frame,
            textvariable=self.cloud_provider,
            values=['local', 'aws', 'azure'],
            state='readonly',
            width=20
        )
        cloud_combo.grid(row=0, column=1, sticky='w', padx=5)
        
        # Processing Options
        options_frame = ttk.LabelFrame(parent, text="Processing Options", padding=10)
        options_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(options_frame, text="Parallel Workers:").grid(row=0, column=0, sticky='w', pady=5)
        ttk.Spinbox(options_frame, from_=1, to=20, textvariable=self.workers, width=10).grid(row=0, column=1, sticky='w', padx=5)
        
        ttk.Checkbutton(
            options_frame,
            text="Use LangChain (structured extraction)",
            variable=self.use_langchain
        ).grid(row=1, column=0, columnspan=2, sticky='w', pady=5)
    
    def setup_pubmed_tab(self, parent):
        info_label = ttk.Label(
            parent,
            text="Check PubMed for new papers before processing",
            font=('Arial', 10, 'bold')
        )
        info_label.pack(pady=10)
        
        check_frame = ttk.Frame(parent)
        check_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Checkbutton(
            check_frame,
            text="Check PubMed for new papers",
            variable=self.check_pubmed
        ).pack(anchor='w', pady=5)
        
        ttk.Label(check_frame, text="Search Query:").pack(anchor='w', pady=5)
        ttk.Entry(check_frame, textvariable=self.pubmed_query, width=60).pack(fill='x', pady=5)
        
        ttk.Label(
            check_frame,
            text='Example: "cancer biomarkers" or "BRCA1 breast cancer"',
            font=('Arial', 8, 'italic')
        ).pack(anchor='w')
        
        ttk.Label(check_frame, text="Email for notifications:").pack(anchor='w', pady=(15, 5))
        ttk.Entry(check_frame, textvariable=self.email, width=60).pack(fill='x', pady=5)
        
        ttk.Label(
            check_frame,
            text="Note: Email notifications require SMTP configuration in environment variables",
            font=('Arial', 8, 'italic'),
            foreground='gray'
        ).pack(anchor='w', pady=5)
    
    def setup_log_tab(self, parent):
        self.log_text = scrolledtext.ScrolledText(
            parent,
            wrap=tk.WORD,
            width=80,
            height=30,
            font=('Courier', 9)
        )
        self.log_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Add tags for colored output
        self.log_text.tag_config('success', foreground='green')
        self.log_text.tag_config('error', foreground='red')
        self.log_text.tag_config('warning', foreground='orange')
        self.log_text.tag_config('info', foreground='blue')
    
    def browse_papers_dir(self):
        directory = filedialog.askdirectory(initialdir=self.papers_dir.get())
        if directory:
            self.papers_dir.set(directory)
    
    def browse_output_dir(self):
        directory = filedialog.askdirectory(initialdir=self.output_dir.get())
        if directory:
            self.output_dir.set(directory)
    
    def log(self, message, tag='info'):
        """Add message to log with timestamp"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n", tag)
        self.log_text.see(tk.END)
        self.root.update()
    
    def start_processing(self):
        # Validate inputs
        if not Path(self.papers_dir.get()).exists():
            messagebox.showerror("Error", "Papers directory does not exist!")
            return
        
        provider = self.provider.get()
        if provider == 'anthropic' and not self.anthropic_key.get():
            messagebox.showerror("Error", "Anthropic API key is required!")
            return
        
        if provider == 'openai' and not self.openai_key.get():
            messagebox.showerror("Error", "OpenAI API key is required!")
            return
        
        if self.check_pubmed.get() and not self.pubmed_query.get():
            messagebox.showwarning("Warning", "PubMed check enabled but no query provided!")
        
        # Disable start button
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.processing = True
        
        # Clear log
        self.log_text.delete(1.0, tk.END)
        
        # Set environment variables
        os.environ['ANTHROPIC_API_KEY'] = self.anthropic_key.get()
        os.environ['OPENAI_API_KEY'] = self.openai_key.get()
        
        # Start processing in separate thread
        thread = threading.Thread(target=self.run_pipeline, daemon=True)
        thread.start()
    
    def stop_processing(self):
        self.processing = False
        self.log("Stopping processing...", 'warning')
    
    def run_pipeline(self):
        """Run the processing pipeline"""
        try:
            self.status_var.set("Processing...")
            self.log("Starting pipeline...", 'info')
            
            # Import process_papers
            from process_papers import main
            
            # Redirect stdout to log
            import io
            from contextlib import redirect_stdout
            
            log_stream = io.StringIO()
            
            with redirect_stdout(log_stream):
                main(
                    papers_dir=self.papers_dir.get(),
                    output_dir=self.output_dir.get(),
                    max_workers=self.workers.get(),
                    provider=self.provider.get(),
                    use_langchain=self.use_langchain.get(),
                    check_pubmed=self.check_pubmed.get(),
                    pubmed_query=self.pubmed_query.get(),
                    user_email=self.email.get(),
                    cloud_provider=self.cloud_provider.get()
                )
            
            # Display output
            output = log_stream.getvalue()
            for line in output.split('\n'):
                if line.strip():
                    if '✓' in line or 'success' in line.lower():
                        self.log(line, 'success')
                    elif '✗' in line or 'error' in line.lower() or 'failed' in line.lower():
                        self.log(line, 'error')
                    elif 'warning' in line.lower():
                        self.log(line, 'warning')
                    else:
                        self.log(line, 'info')
            
            self.status_var.set("Processing complete!")
            self.log("Pipeline completed successfully!", 'success')
            messagebox.showinfo("Success", "Processing completed successfully!")
            
        except Exception as e:
            self.log(f"Error: {str(e)}", 'error')
            self.status_var.set("Error occurred")
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")
        
        finally:
            self.start_button.config(state='normal')
            self.stop_button.config(state='disabled')
            self.processing = False

def main():
    root = tk.Tk()
    app = PipelineGUI(root)
    root.mainloop()

if __name__ == '__main__':
    main()