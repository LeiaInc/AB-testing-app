import tkinter as tk
from tkinter import ttk, messagebox
import configparser
import os
import sys
import ctypes
import random
import pandas as pd
from datetime import datetime
import csv

class ToolTip:
    """Create a tooltip for a given widget"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind('<Enter>', self.show_tooltip)
        self.widget.bind('<Leave>', self.hide_tooltip)
    
    def show_tooltip(self, event=None):
        x, y, _, _ = self.widget.bbox('insert') if hasattr(self.widget, 'bbox') else (0, 0, 0, 0)
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f'+{x}+{y}')
        
        label = tk.Label(self.tooltip, text=self.text, justify=tk.LEFT,
                        background='#ffffe0', relief='solid', borderwidth=1,
                        font=('Arial', 9), padx=5, pady=5)
        label.pack()
    
    def hide_tooltip(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

class MultivariateSwitcherGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Eye Tracker Multivariate Testing")
        self.root.geometry("850x750")
        
        # Settings file for saving product code
        self.settings_file = os.path.join(self.get_executable_dir(), "multivariate_switcher_settings.ini")
        
        # Multivariate testing mode flag
        self.mv_testing_mode = False
        self.mv_tests = []
        self.mv_current_test_idx = 0
        self.mv_current_repetition = 0
        self.mv_total_repetitions = 10
        self.mv_test_results = []
        self.active_test_number = 1  # Track which test button was clicked (1, 2, or 3)
        
        # Load product code from settings
        self.product_code = self.load_product_code()
        
        # Build INI file path
        self.update_ini_path()
        
        # Check if running as admin
        self.is_admin = self.check_admin()
        
        # Eye Stabilization algorithm configurations
        self.stab_algo_configs = {
            1: {
                'enabled': 'true',
                'algoID': '1'
            },
            2: {
                'enabled': 'true',
                'algoID': '2'
            },
            3: {
                'enabled': 'false'
            }
        }
        
        # Create main frame
        main_frame = ttk.Frame(root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Left frame for switcher
        left_frame = ttk.LabelFrame(main_frame, text="Algorithm Switcher", padding="15")
        left_frame.grid(row=0, column=0, padx=10, pady=10, sticky=(tk.N, tk.S, tk.W, tk.E))
        
        # Right frame for Multivariate testing
        mv_frame = ttk.LabelFrame(main_frame, text="Multivariate Testing", padding="15")
        mv_frame.grid(row=0, column=1, padx=10, pady=10, sticky=(tk.N, tk.S, tk.W, tk.E))
        
        # === LEFT FRAME: Switcher Controls ===
        
        # Product code frame
        product_frame = ttk.Frame(left_frame)
        product_frame.grid(row=0, column=0, columnspan=2, pady=10)
        
        ttk.Label(product_frame, text="Product Code:", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        
        self.product_code_var = tk.StringVar(value=self.product_code)
        product_entry = ttk.Entry(product_frame, textvariable=self.product_code_var, width=10)
        product_entry.pack(side=tk.LEFT, padx=5)
        
        apply_button = ttk.Button(product_frame, text="Apply", command=self.apply_product_code)
        apply_button.pack(side=tk.LEFT, padx=5)
        
        # Current status label
        self.status_label = ttk.Label(left_frame, text="Current: Unknown", 
                                      font=("Arial", 12))
        self.status_label.grid(row=1, column=0, columnspan=2, pady=10)
        
        # Admin status label
        admin_text = "Running as Administrator ✓" if self.is_admin else "⚠ Not running as Administrator"
        admin_color = "green" if self.is_admin else "red"
        self.admin_label = ttk.Label(left_frame, text=admin_text, 
                                     font=("Arial", 9), foreground=admin_color)
        self.admin_label.grid(row=2, column=0, columnspan=2, pady=5)
        
        # Switch button
        self.switch_button = ttk.Button(left_frame, text="Switch Algorithm", 
                                       command=self.switch_algorithm)
        self.switch_button.grid(row=3, column=0, columnspan=2, pady=20, ipadx=20, ipady=10)
        
        # Restart as admin button (only show if not admin)
        if not self.is_admin:
            self.admin_button = ttk.Button(left_frame, text="Restart as Administrator", 
                                          command=self.restart_as_admin)
            self.admin_button.grid(row=4, column=0, columnspan=2, pady=5)
        
        # Info label
        info_label = ttk.Label(left_frame, text="Toggles between MEDIAPIPE and BLINKEYE", 
                              font=("Arial", 9), foreground="gray")
        info_label.grid(row=5, column=0, columnspan=2, pady=5)
        
        # File path label
        path_label = ttk.Label(left_frame, text=f"Config: ...\\{self.product_code}\\ft_user.ini", 
                              font=("Arial", 8), foreground="gray")
        path_label.grid(row=6, column=0, columnspan=2, pady=5)
        self.path_label = path_label
        
        # === EYE STABILIZATION FRAME ===
        stab_frame = ttk.LabelFrame(left_frame, text="Eye Stabilization", padding="10")
        stab_frame.grid(row=7, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
        self.selected_stab_algo = tk.IntVar(value=1)
        
        stab_algo1_radio = ttk.Radiobutton(stab_frame, text="Algorithm 1", 
                                           variable=self.selected_stab_algo, value=1)
        stab_algo1_radio.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        stab_algo2_radio = ttk.Radiobutton(stab_frame, text="Algorithm 2", 
                                           variable=self.selected_stab_algo, value=2)
        stab_algo2_radio.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        stab_algo3_radio = ttk.Radiobutton(stab_frame, text="No stabilization", 
                                           variable=self.selected_stab_algo, value=3)
        stab_algo3_radio.grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        
        stab_apply_button = ttk.Button(stab_frame, text="Apply", 
                                       command=self.apply_stabilization)
        stab_apply_button.grid(row=1, column=0, columnspan=3, pady=10)
        
        # Stabilization status label
        self.stab_status_label = ttk.Label(stab_frame, text="Current: Unknown", 
                                           font=("Arial", 9), foreground="gray")
        self.stab_status_label.grid(row=2, column=0, columnspan=3, pady=5)
        
        # === MULTIVARIATE TESTING FRAME ===
        
        # Multivariate Testing description
        mv_desc_label = ttk.Label(mv_frame, 
                                 text="In the following two sets of tests the application is randomly\nselecting between 3 different configuration settings of the eye tracker.\n\nPress \"Start multivariate testing 1\" to complete the first set of tests.\nOnce completed press \"Start multivariate testing 2\" to complete\nthe second set of tests.\n\nFor the first set use \"Leia Player\" while for the second set\nof tests use \"Leia Viewer\" as 3D application.", 
                                 font=('Arial', 9), foreground='gray', justify=tk.LEFT)
        mv_desc_label.grid(row=0, column=0, pady=10)
        
        # Leia Player instruction with bold
        lp_instruction_frame = ttk.Frame(mv_frame)
        lp_instruction_frame.grid(row=1, column=0, pady=5)
        
        ttk.Label(lp_instruction_frame, text="Use ", font=('Arial', 10)).pack(side=tk.LEFT)
        ttk.Label(lp_instruction_frame, text="Leia Player", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        ttk.Label(lp_instruction_frame, text=" app for testing", font=('Arial', 10)).pack(side=tk.LEFT)
        
        # Multivariate Testing button 1
        self.mv_button = ttk.Button(mv_frame, text="Start multivariate testing 1", 
                                   command=lambda: self.toggle_mv_testing(1))
        self.mv_button.grid(row=2, column=0, pady=10, ipadx=20, ipady=10)
        
        # Leia Viewer instruction for test 2
        lp_instruction_frame2 = ttk.Frame(mv_frame)
        lp_instruction_frame2.grid(row=3, column=0, pady=(15, 5))
        
        ttk.Label(lp_instruction_frame2, text="Use ", font=('Arial', 10)).pack(side=tk.LEFT)
        ttk.Label(lp_instruction_frame2, text="Leia Viewer", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        ttk.Label(lp_instruction_frame2, text=" app for testing", font=('Arial', 10)).pack(side=tk.LEFT)
        
        # Multivariate Testing button 2
        self.mv_button2 = ttk.Button(mv_frame, text="Start multivariate testing 2", 
                                    command=lambda: self.toggle_mv_testing(2))
        self.mv_button2.grid(row=4, column=0, pady=10, ipadx=20, ipady=10)
        
        # Multivariate Testing status field (initially hidden)
        self.mv_field_frame = ttk.Frame(mv_frame)
        
        # Test name label
        self.mv_test_name_label = ttk.Label(self.mv_field_frame, text="", 
                                           font=('Arial', 12, 'bold'), foreground='blue')
        self.mv_test_name_label.pack(pady=10)
        
        # Instruction label
        self.mv_instruction_label = ttk.Label(self.mv_field_frame, text="", 
                                             font=('Arial', 10, 'italic'), foreground='black',
                                             wraplength=280, justify=tk.CENTER)
        self.mv_instruction_label.pack(pady=10)
        
        # Repetition counter label
        self.mv_repetition_label = ttk.Label(self.mv_field_frame, text="", 
                                            font=('Arial', 16), foreground='gray')
        self.mv_repetition_label.pack(pady=2)
        
        # Progress bar
        self.mv_progress_bar = ttk.Progressbar(self.mv_field_frame, mode='determinate', 
                                              length=250, maximum=10)
        self.mv_progress_bar.pack(pady=5)
        
        # Completed button frame
        self.mv_completed_frame = ttk.Frame(self.mv_field_frame)
        self.mv_completed_button = ttk.Button(self.mv_completed_frame, text="I've completed this instruction", 
                                             command=self.on_mv_test_completed)
        self.mv_completed_button.pack(pady=10)
        
        # Feedback frame
        self.mv_feedback_frame = ttk.Frame(self.mv_field_frame)
        
        self.mv_feedback_question = ttk.Label(self.mv_feedback_frame,
                                             text="Compared to previous:",
                                             font=('Arial', 10))
        self.mv_feedback_question.pack(pady=5)
        
        mv_feedback_buttons_frame = ttk.Frame(self.mv_feedback_frame)
        mv_feedback_buttons_frame.pack(pady=5)
        
        self.mv_worse_button = ttk.Button(mv_feedback_buttons_frame, text="Worse",
                                         command=lambda: self.record_mv_feedback_with_comment("Worse"))
        self.mv_worse_button.pack(side=tk.LEFT, padx=5)
        
        self.mv_same_button = ttk.Button(mv_feedback_buttons_frame, text="No difference",
                                        command=lambda: self.record_mv_feedback_with_comment("No difference"))
        self.mv_same_button.pack(side=tk.LEFT, padx=5)
        
        self.mv_better_button = ttk.Button(mv_feedback_buttons_frame, text="Better",
                                          command=lambda: self.record_mv_feedback_with_comment("Better"))
        self.mv_better_button.pack(side=tk.LEFT, padx=5)
        
        # Additional comments label and input
        self.mv_comments_label = ttk.Label(self.mv_feedback_frame, text="Additional comments (optional):", font=('Arial', 9))
        self.mv_comments_label.pack(pady=(10, 2))
        self.mv_comments_entry = ttk.Entry(self.mv_feedback_frame, width=40)
        self.mv_comments_entry.pack(pady=(0, 2))
        self.mv_comments_desc = ttk.Label(self.mv_feedback_frame, text="You can provide extra feedback here.", font=('Arial', 8), foreground='gray')
        self.mv_comments_desc.pack(pady=(0, 10))
        
        # Load and display current value
        self.update_status()
    
    def get_executable_dir(self):
        """Get the directory where the executable is located (for saving files)"""
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            return os.path.dirname(sys.executable)
        else:
            # Running as script
            return os.path.dirname(os.path.abspath(__file__))
    
    def get_resource_dir(self):
        """Get the directory where bundled resources are located (for loading files)"""
        if getattr(sys, 'frozen', False):
            # Running as compiled executable - use PyInstaller's temp folder
            return sys._MEIPASS
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
        
        # Update status to show current algorithm for this product code
        self.update_status()
        
        # Check if file exists
        if not os.path.exists(self.ini_path):
            messagebox.showwarning("Warning", f"Product code updated to: {new_code}\n\nNote: Config file not found at:\n{self.ini_path}")
        else:
            messagebox.showinfo("Success", f"Product code updated to: {new_code}")
    
    def read_ini(self):
        """Read the INI file and return ConfigParser object"""
        if not os.path.exists(self.ini_path):
            messagebox.showerror("Error", f"INI file not found:\n{self.ini_path}")
            return None
        
        config = configparser.ConfigParser()
        
        # Try different encodings and methods
        encodings = ['utf-8-sig', 'utf-8', 'utf-16', 'cp1252', 'latin-1']
        
        for encoding in encodings:
            try:
                config.read(self.ini_path, encoding=encoding)
                # Verify config was read (has sections)
                if config.sections() or config.defaults():
                    return config
            except UnicodeDecodeError:
                continue
            except configparser.Error as e:
                # Invalid INI format with this encoding, try next
                continue
            except Exception as e:
                continue
        
        # If all encodings fail, show detailed error
        try:
            # Try to read file content for diagnostic info
            with open(self.ini_path, 'rb') as f:
                content = f.read(500)  # Read first 500 bytes
            hex_preview = content[:100].hex()
            messagebox.showerror("Error", 
                f"Failed to read INI file with any encoding.\n\n"
                f"File: {self.ini_path}\n"
                f"First bytes (hex): {hex_preview}\n\n"
                f"The file may be corrupted or in an unsupported format.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read INI file:\n{str(e)}")
        
        return None
    
    def write_ini(self, config):
        """Write ConfigParser object back to INI file"""
        try:
            # Use UTF-8 without BOM for better compatibility
            with open(self.ini_path, 'w', encoding='utf-8') as configfile:
                config.write(configfile)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to write INI file:\n{str(e)}")
            return False
    
    def get_current_algo(self):
        """Get current EyeTracker algorithm value"""
        config = self.read_ini()
        if config is None:
            return None
        
        # Try to find EyeTracker in any section
        for section in config.sections():
            if config.has_option(section, 'EyeTracker'):
                return config.get(section, 'EyeTracker')
        
        # If not found in any section, assume it's in DEFAULT or no section
        if config.has_option('DEFAULT', 'EyeTracker'):
            return config.get('DEFAULT', 'EyeTracker')
        
        return None
    
    def set_algo(self, new_value):
        """Set EyeTracker algorithm value"""
        config = self.read_ini()
        if config is None:
            return False
        
        # Try to find and update EyeTracker in any section
        found = False
        for section in config.sections():
            if config.has_option(section, 'EyeTracker'):
                config.set(section, 'EyeTracker', new_value)
                found = True
                break
        
        # If not found in any section, try DEFAULT
        if not found:
            if config.has_option('DEFAULT', 'EyeTracker'):
                config.set('DEFAULT', 'EyeTracker', new_value)
                found = True
        
        # If still not found, add it to DEFAULT section
        if not found:
            config.set('DEFAULT', 'EyeTracker', new_value)
        
        return self.write_ini(config)
    
    def update_status(self):
        """Update the status label with current algorithm"""
        if self.mv_testing_mode:
            self.status_label.config(text="Current: Hidden (MV Testing)", foreground="purple")
            self.stab_status_label.config(text="Current: Hidden (MV Testing)", foreground="purple")
            return
        
        current = self.get_current_algo()
        if current:
            self.status_label.config(text=f"Current: {current}", foreground="blue")
        else:
            self.status_label.config(text="Current: Not found in INI", foreground="red")
        
        # Update stabilization status
        self.update_stab_status()
    
    def update_stab_status(self):
        """Update the stabilization status label"""
        current_stab = self.get_current_stabilization()
        if current_stab:
            self.stab_status_label.config(text=f"Current: {current_stab}", foreground="blue")
            # Update radio button selection based on current settings
            if current_stab == "Algorithm 1":
                self.selected_stab_algo.set(1)
            elif current_stab == "Algorithm 2":
                self.selected_stab_algo.set(2)
            elif current_stab == "No stabilization":
                self.selected_stab_algo.set(3)
        else:
            self.stab_status_label.config(text="Current: Unknown", foreground="gray")
    
    def get_current_stabilization(self):
        """Get current eye stabilization algorithm from INI"""
        config = self.read_ini()
        if config is None:
            return None
        
        section = 'EyeStabilizationParams'
        if not config.has_section(section):
            return None
        
        # Read current values
        enabled = config.get(section, 'enabled', fallback='true').lower()
        algo_id = config.get(section, 'algoID', fallback=None)
        
        # Determine which algorithm is active
        if enabled == 'false':
            return "No stabilization"
        elif algo_id == '1':
            return "Algorithm 1"
        elif algo_id == '2':
            return "Algorithm 2"
        else:
            return f"Custom (algoID={algo_id})"
    
    def apply_stabilization(self):
        """Apply selected stabilization algorithm to INI file"""
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
            return
        
        section = 'EyeStabilizationParams'
        
        # Create section if it doesn't exist
        if not config.has_section(section):
            config.add_section(section)
        
        # Get selected algorithm config
        algo_num = self.selected_stab_algo.get()
        algo_config = self.stab_algo_configs[algo_num]
        
        # Set all parameters
        for key, value in algo_config.items():
            config.set(section, key, value)
        
        # Write back to file
        if self.write_ini(config):
            algo_names = {1: "Algorithm 1", 2: "Algorithm 2", 3: "No stabilization"}
            messagebox.showinfo("Success", f"Eye Stabilization set to: {algo_names[algo_num]}")
            self.update_stab_status()
        else:
            messagebox.showerror("Error", "Failed to update INI file")
    
    def set_stabilization(self, algo_num):
        """Set stabilization algorithm by number (1, 2, or 3 for no stabilization)"""
        config = self.read_ini()
        if config is None:
            return False
        
        section = 'EyeStabilizationParams'
        
        # Create section if it doesn't exist
        if not config.has_section(section):
            config.add_section(section)
        
        # Get algorithm config
        algo_config = self.stab_algo_configs[algo_num]
        
        # Set all parameters
        for key, value in algo_config.items():
            config.set(section, key, value)
        
        return self.write_ini(config)
    
    def switch_algorithm(self):
        """Toggle between MEDIAPIPE and BLINKEYE"""
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
        
        current = self.get_current_algo()
        
        if current is None:
            messagebox.showwarning("Warning", "EyeTracker parameter not found in INI file")
            return
        
        # Toggle the value
        if current.upper() == "MEDIAPIPE":
            new_value = "BLINKEYE"
        elif current.upper() == "BLINKEYE":
            new_value = "MEDIAPIPE"
        else:
            # If it's neither, default to MEDIAPIPE
            response = messagebox.askyesno(
                "Unknown Value", 
                f"Current value is '{current}'.\nSwitch to MEDIAPIPE?",
                icon='question'
            )
            new_value = "MEDIAPIPE" if response else "BLINKEYE"
        
        # Update the INI file
        if self.set_algo(new_value):
            self.update_status()
            messagebox.showinfo("Success", f"Algorithm switched to: {new_value}")
        else:
            messagebox.showerror("Error", "Failed to update INI file")
    
    # === MULTIVARIATE TESTING METHODS ===
    
    def record_mv_feedback_with_comment(self, feedback):
        """Record user feedback with additional comments for multivariate testing"""
        comment = self.mv_comments_entry.get().strip()
        self.mv_comments_entry.delete(0, tk.END)
        self.record_mv_feedback(feedback, comment)
    
    def record_mv_feedback(self, feedback, comment=None):
        """Record user feedback and move to next test in multivariate testing"""
        test = self.mv_tests[self.mv_current_test_idx]
        
        # Get current settings from INI
        current_algo = self.get_current_algo()
        current_stab = self.get_current_stabilization()
        
        # Record result
        result = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'test_name': test['name'],
            'instruction': test['instruction'],
            'repetition': self.mv_current_repetition + 1,
            'algorithm': current_algo,
            'stabilization': current_stab,
            'feedback': feedback,
            'comments': comment if comment is not None else ""
        }
        self.mv_test_results.append(result)
        
        # Move to next repetition
        self.mv_current_repetition += 1
        
        if self.mv_current_repetition >= self.mv_total_repetitions:
            # Move to next test
            self.mv_current_test_idx += 1
            self.mv_current_repetition = 0
        
        # Hide feedback frame
        self.mv_feedback_frame.pack_forget()
        
        # Show next test
        self.show_next_mv_test()
        
        # Load and display current value
        self.update_status()
    
    def toggle_mv_testing(self, test_number=1):
        """Toggle Multivariate testing mode"""
        if not self.mv_testing_mode:
            # Entering multivariate testing mode
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
            
            # Load tests from Excel
            if not self.load_mv_tests_from_excel(test_number):
                return
            
            # Enter multivariate testing mode
            self.mv_testing_mode = True
            self.active_test_number = test_number
            
            # Update UI - disable other buttons and update active button
            buttons = {1: self.mv_button, 2: self.mv_button2}
            for num, btn in buttons.items():
                if num == test_number:
                    btn.config(text=f"Exit multivariate testing {num}")
                else:
                    btn.config(state='disabled')
            
            self.status_label.config(text="Current: Hidden (MV Testing)", foreground="purple")
            self.stab_status_label.config(text="Current: Hidden (MV Testing)", foreground="purple")
            
            # Start test sequence
            self.start_mv_test_sequence()
        else:
            # Exiting multivariate testing mode
            self.mv_testing_mode = False
            
            # Update UI - re-enable all buttons
            self.mv_button.config(text="Start multivariate testing 1", state='normal')
            self.mv_button2.config(text="Start multivariate testing 2", state='normal')
            self.mv_field_frame.grid_remove()
            self.update_status()
            
            messagebox.showinfo("Multivariate Testing", "Multivariate Testing mode deactivated.")
    
    def load_mv_tests_from_excel(self, test_number=1):
        """Load tests from Excel for multivariate testing"""
        # Use get_resource_dir for bundled resources (sys._MEIPASS in frozen mode)
        resource_dir = self.get_resource_dir()
        
        # Use different instruction files for each test
        instruction_files = {
            1: "instructions_mvt_1.xlsx",
            2: "instructions_mvt_2.xlsx"
        }
        filename = instruction_files.get(test_number, "instructions_mvt_1.xlsx")
        excel_path = os.path.join(resource_dir, "abtesting_instructions", filename)
        
        self.mv_tests = []
        if os.path.exists(excel_path):
            try:
                df = pd.read_excel(excel_path)
                if 'Test Name' in df.columns and 'Instruction' in df.columns:
                    for _, row in df.iterrows():
                        self.mv_tests.append({
                            'name': str(row['Test Name']),
                            'instruction': str(row['Instruction'])
                        })
                if len(self.mv_tests) == 0:
                    messagebox.showerror("Error", f"No tests found in {filename}")
                    return False
                return True
            except Exception as e:
                messagebox.showerror("Error", f"Failed to read {filename}:\n{str(e)}\nUsing default instructions.")
        else:
            messagebox.showerror("Error", f"Instructions file not found:\n{excel_path}\nUsing default instructions.")
        
        # Fallback: hardcoded instructions
        self.mv_tests = [
            {'name': 'Test 1', 'instruction': 'Follow the dot with your eyes.'},
            {'name': 'Test 2', 'instruction': 'Look left and right quickly.'},
            {'name': 'Test 3', 'instruction': 'Blink three times.'},
            {'name': 'Test 4', 'instruction': 'Focus on the center for 5 seconds.'}
        ]
        return True
    
    def start_mv_test_sequence(self):
        """Start the multivariate testing sequence"""
        self.mv_current_test_idx = 0
        self.mv_current_repetition = 0
        self.mv_test_results = []
        
        # Show test UI
        self.mv_field_frame.grid(row=7, column=0, pady=10)
        self.mv_feedback_frame.pack_forget()
        
        # Show first test
        self.show_next_mv_test()
    
    def show_next_mv_test(self):
        """Display the next test instruction for multivariate testing"""
        if self.mv_current_test_idx >= len(self.mv_tests):
            # All tests completed
            self.finish_mv_testing()
            return
        
        # Both tests use the same algorithm options
        mv_options = [
            ("BLINKEYE", 1),   # BLINKEYE, Algorithm 1
            ("BLINKEYE", 2),   # BLINKEYE, Algorithm 2
            ("MEDIAPIPE", 2),  # MEDIAPIPE, Algorithm 2
        ]
        selected_algo, selected_stab = random.choice(mv_options)
        
        if not self.set_algo(selected_algo):
            messagebox.showerror("Error", "Failed to set algorithm")
            return
        
        if not self.set_stabilization(selected_stab):
            messagebox.showerror("Error", "Failed to set stabilization")
            return
        
        test = self.mv_tests[self.mv_current_test_idx]
        
        # Update progress
        self.mv_progress_bar['value'] = self.mv_current_repetition
        
        # Update test display
        self.mv_test_name_label.config(text=test['name'])
        self.mv_repetition_label.config(text=f"Repetition {self.mv_current_repetition + 1} of {self.mv_total_repetitions}")
        self.mv_instruction_label.config(text=test['instruction'])
        
        # First repetition: show completed button; subsequent repetitions: show feedback directly
        if self.mv_current_repetition == 0:
            self.mv_feedback_frame.pack_forget()
            self.mv_completed_frame.pack(pady=10)
        else:
            self.mv_completed_frame.pack_forget()
            self.mv_feedback_frame.pack(pady=10)
    
    def on_mv_test_completed(self):
        """Called when user confirms they completed the test (first repetition only) in multivariate testing"""
        self.mv_completed_frame.pack_forget()
        self.record_mv_feedback("N/A (First)")
    
    def finish_mv_testing(self):
        """Complete multivariate testing and save results"""
        # Save results to CSV with test number in filename
        log_filename = f"multivariate_testing_{self.active_test_number}_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        log_path = os.path.join(self.get_executable_dir(), log_filename)
        
        try:
            with open(log_path, 'w', newline='', encoding='utf-8') as f:
                if self.mv_test_results:
                    fieldnames = self.mv_test_results[0].keys()
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(self.mv_test_results)
            
            messagebox.showinfo("Multivariate Testing Complete", 
                              f"All tests completed!\n\nResults saved to:\n{log_filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save results:\n{str(e)}")
        
        # Exit multivariate testing mode
        self.mv_testing_mode = False
        self.mv_button.config(text="Start multivariate testing 1", state='normal')
        self.mv_button2.config(text="Start multivariate testing 2", state='normal')
        self.mv_field_frame.grid_remove()
        self.update_status()

# Create and run GUI
if __name__ == "__main__":
    root = tk.Tk()
    app = MultivariateSwitcherGUI(root)
    root.mainloop()
