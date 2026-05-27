import tkinter as tk
from tkinter import ttk, messagebox
import configparser
import os
import sys
import ctypes

class StabilizationSwitcherGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Eye Stabilization Algorithm Switcher")
        self.root.geometry("600x700")
        
        # Settings file for saving product code
        self.settings_file = os.path.join(self.get_executable_dir(), "stabilization_switcher_settings.ini")
        
        # Load product code from settings
        self.product_code = self.load_product_code()
        
        # Build INI file path
        self.update_ini_path()
        
        # Check if running as admin
        self.is_admin = self.check_admin()
        
        # Algorithm configurations
        self.algo_configs = {
            1: {
                'enabled': 'true',
                'factor': '0.95',
                'maxDistError_percentage': '5',
                'useAverage': 'false',
                'useRotation': 'true',
                'stabilizeLandmarks': 'true'
            },
            2: {
                'enabled': 'true',
                'factor': '0.85',
                'maxDistError_percentage': '0.2',
                'useAverage': 'false',
                'useRotation': 'true',
                'stabilizeLandmarks': 'true'
            }
        }
        
        # Create main frame
        main_frame = ttk.Frame(root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Product code frame
        product_frame = ttk.LabelFrame(main_frame, text="Configuration", padding="15")
        product_frame.grid(row=0, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
        ttk.Label(product_frame, text="Product Code:", font=("Arial", 10)).grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.product_code_var = tk.StringVar(value=self.product_code)
        product_entry = ttk.Entry(product_frame, textvariable=self.product_code_var, width=10)
        product_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        apply_button = ttk.Button(product_frame, text="Apply", command=self.apply_product_code)
        apply_button.grid(row=0, column=2, padx=5, pady=5)
        
        # File path label
        self.path_label = ttk.Label(product_frame, text=f"Config: ...\\{self.product_code}\\ft_user.ini", 
                                    font=("Arial", 8), foreground="gray")
        self.path_label.grid(row=1, column=0, columnspan=3, pady=5, sticky=tk.W)
        
        # Admin status label
        admin_text = "Running as Administrator ✓" if self.is_admin else "⚠ Not running as Administrator"
        admin_color = "green" if self.is_admin else "red"
        self.admin_label = ttk.Label(product_frame, text=admin_text, 
                                     font=("Arial", 9), foreground=admin_color)
        self.admin_label.grid(row=2, column=0, columnspan=3, pady=5, sticky=tk.W)
        
        # Restart as admin button (only show if not admin)
        if not self.is_admin:
            self.admin_button = ttk.Button(product_frame, text="Restart as Administrator", 
                                          command=self.restart_as_admin)
            self.admin_button.grid(row=3, column=0, columnspan=3, pady=5)
        
        # Algorithm selection frame
        algo_frame = ttk.LabelFrame(main_frame, text="Algorithm Selection", padding="15")
        algo_frame.grid(row=1, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
        self.selected_algo = tk.IntVar(value=1)
        
        algo1_radio = ttk.Radiobutton(algo_frame, text="Algorithm 1", 
                                     variable=self.selected_algo, value=1,
                                     command=self.on_algo_selected)
        algo1_radio.grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
        
        algo2_radio = ttk.Radiobutton(algo_frame, text="Algorithm 2", 
                                     variable=self.selected_algo, value=2,
                                     command=self.on_algo_selected)
        algo2_radio.grid(row=0, column=1, padx=10, pady=5, sticky=tk.W)
        
        load_current_button = ttk.Button(algo_frame, text="Load Current Settings", 
                                        command=self.load_current_settings)
        load_current_button.grid(row=0, column=2, padx=10, pady=5)
        
        # Parameters frame
        params_frame = ttk.LabelFrame(main_frame, text="Parameters", padding="15")
        params_frame.grid(row=2, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
        # Create parameter entries
        self.param_vars = {}
        param_labels = {
            'enabled': 'Enabled:',
            'factor': 'Factor:',
            'maxDistError_percentage': 'Max Dist Error %:',
            'useAverage': 'Use Average:',
            'useRotation': 'Use Rotation:',
            'stabilizeLandmarks': 'Stabilize Landmarks:'
        }
        
        row = 0
        for key, label in param_labels.items():
            ttk.Label(params_frame, text=label, font=("Arial", 10)).grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
            
            var = tk.StringVar()
            self.param_vars[key] = var
            entry = ttk.Entry(params_frame, textvariable=var, width=20)
            entry.grid(row=row, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))
            
            row += 1
        
        # Load defaults button
        load_defaults_button = ttk.Button(params_frame, text="Load Algorithm Defaults", 
                                         command=self.load_defaults)
        load_defaults_button.grid(row=row, column=0, columnspan=2, pady=10)
        
        # Current status frame
        status_frame = ttk.LabelFrame(main_frame, text="Current INI Status", padding="15")
        status_frame.grid(row=3, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.status_text = tk.Text(status_frame, height=10, width=60, font=("Courier", 9))
        self.status_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar = ttk.Scrollbar(status_frame, orient=tk.VERTICAL, command=self.status_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.status_text.config(yscrollcommand=scrollbar.set)
        
        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        apply_all_button = ttk.Button(button_frame, text="Apply Settings to INI", 
                                     command=self.apply_settings, style='Accent.TButton')
        apply_all_button.pack(side=tk.LEFT, padx=10, ipadx=20, ipady=5)
        
        refresh_button = ttk.Button(button_frame, text="Refresh Status", 
                                   command=self.update_status)
        refresh_button.pack(side=tk.LEFT, padx=10)
        
        # Initialize with defaults
        self.load_defaults()
        self.update_status()
    
    def get_executable_dir(self):
        """Get the directory where the executable is located (for saving files)"""
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            return os.path.dirname(sys.executable)
        else:
            # Running as script
            return os.path.dirname(os.path.abspath(__file__))
    
    def check_admin(self):
        """Check if running with administrator privileges"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    def restart_as_admin(self):
        """Restart the program with administrator privileges"""
        try:
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                script = sys.executable
            else:
                # Running as script
                script = os.path.abspath(__file__)
            
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, f'"{script}"', None, 1
            )
            self.root.quit()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to restart as administrator:\n{str(e)}")
    
    def load_product_code(self):
        """Load product code from settings file"""
        if os.path.exists(self.settings_file):
            config = configparser.ConfigParser()
            try:
                config.read(self.settings_file)
                if config.has_option('Settings', 'ProductCode'):
                    return config.get('Settings', 'ProductCode')
            except:
                pass
        return "BC"  # Default value
    
    def save_product_code(self, code):
        """Save product code to settings file"""
        config = configparser.ConfigParser()
        config['Settings'] = {'ProductCode': code}
        try:
            with open(self.settings_file, 'w') as f:
                config.write(f)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings:\n{str(e)}")
            return False
    
    def update_ini_path(self):
        """Update the INI file path based on product code"""
        self.ini_path = rf"C:\Program Files\LeiaSR\Tracker\products\{self.product_code}\ft_user.ini"
    
    def apply_product_code(self):
        """Apply new product code and update path"""
        new_code = self.product_code_var.get().strip()
        if not new_code:
            messagebox.showwarning("Warning", "Product code cannot be empty")
            return
        
        self.product_code = new_code
        self.update_ini_path()
        self.save_product_code(new_code)
        
        # Update path label
        self.path_label.config(text=f"Config: ...\\{self.product_code}\\ft_user.ini")
        
        # Update status
        self.update_status()
        
        # Check if file exists
        if not os.path.exists(self.ini_path):
            messagebox.showwarning("Warning", f"Product code updated to: {new_code}\n\nNote: Config file not found at:\n{self.ini_path}")
        else:
            messagebox.showinfo("Success", f"Product code updated to: {new_code}")
    
    def read_ini(self):
        """Read the INI file and return ConfigParser object"""
        if not os.path.exists(self.ini_path):
            return None
        
        config = configparser.ConfigParser()
        
        # Try different encodings
        encodings = ['utf-8-sig', 'utf-8', 'utf-16', 'cp1252', 'latin-1']
        
        for encoding in encodings:
            try:
                config.read(self.ini_path, encoding=encoding)
                if config.sections() or config.defaults():
                    return config
            except:
                continue
        
        return None
    
    def write_ini(self, config):
        """Write ConfigParser object back to INI file"""
        try:
            with open(self.ini_path, 'w', encoding='utf-8') as configfile:
                config.write(configfile)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to write INI file:\n{str(e)}")
            return False
    
    def on_algo_selected(self):
        """Called when algorithm radio button is selected"""
        # Auto-load defaults when switching algorithms
        self.load_defaults()
    
    def load_defaults(self):
        """Load default parameters for the selected algorithm"""
        algo_num = self.selected_algo.get()
        config = self.algo_configs[algo_num]
        
        for key, value in config.items():
            if key in self.param_vars:
                self.param_vars[key].set(value)
    
    def load_current_settings(self):
        """Load current settings from INI file"""
        config = self.read_ini()
        if config is None:
            messagebox.showerror("Error", f"INI file not found or cannot be read:\n{self.ini_path}")
            return
        
        section = 'EyeStabilizationParams'
        if not config.has_section(section):
            messagebox.showwarning("Warning", f"Section [{section}] not found in INI file")
            return
        
        # Load parameters from INI
        for key in self.param_vars.keys():
            if config.has_option(section, key):
                value = config.get(section, key)
                self.param_vars[key].set(value)
        
        messagebox.showinfo("Success", "Current settings loaded from INI file")
        self.update_status()
    
    def apply_settings(self):
        """Apply current parameter settings to INI file"""
        if not self.is_admin:
            response = messagebox.askyesno(
                "Administrator Required", 
                "Administrator privileges are required to modify files in Program Files.\n\n"
                "Would you like to restart the program as Administrator?",
                icon='warning'
            )
            if response:
                self.restart_as_admin()
            return
        
        config = self.read_ini()
        if config is None:
            messagebox.showerror("Error", f"INI file not found:\n{self.ini_path}")
            return
        
        section = 'EyeStabilizationParams'
        
        # Create section if it doesn't exist
        if not config.has_section(section):
            config.add_section(section)
        
        # Set all parameters
        for key, var in self.param_vars.items():
            value = var.get().strip()
            if value:
                config.set(section, key, value)
        
        # Write to file
        if self.write_ini(config):
            self.update_status()
            algo_num = self.selected_algo.get()
            messagebox.showinfo("Success", f"Settings applied successfully!\n\nAlgorithm {algo_num} parameters have been written to:\n{self.ini_path}")
    
    def update_status(self):
        """Update the status display with current INI file content"""
        self.status_text.delete('1.0', tk.END)
        
        config = self.read_ini()
        if config is None:
            self.status_text.insert('1.0', f"INI file not found:\n{self.ini_path}")
            return
        
        section = 'EyeStabilizationParams'
        if not config.has_section(section):
            self.status_text.insert('1.0', f"Section [{section}] not found in INI file")
            return
        
        # Display current settings
        output = f"[{section}]\n"
        for key in self.param_vars.keys():
            if config.has_option(section, key):
                value = config.get(section, key)
                output += f"{key} = {value}\n"
        
        self.status_text.insert('1.0', output)

# Create and run GUI
if __name__ == "__main__":
    root = tk.Tk()
    app = StabilizationSwitcherGUI(root)
    root.mainloop()
