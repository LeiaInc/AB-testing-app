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
import shutil
import time
import winreg
from win32api import GetFileVersionInfo

# --- Helper functions for version extraction ---

def get_registry_path(key_path):
    """Get path from Windows registry"""
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
        value, _ = winreg.QueryValueEx(key, "")
        winreg.CloseKey(key)
        return value
    except FileNotFoundError:
        return None

def get_exe_version(path):
    """Get file version from executable"""
    if not path or not os.path.exists(path):
        return "not found"
    try:
        info = GetFileVersionInfo(path, "\\")
        ms = info["FileVersionMS"]
        ls = info["FileVersionLS"]
        return f"{ms >> 16}.{ms & 0xFFFF}.{ls >> 16}.{ls & 0xFFFF}"
    except Exception:
        return "unknown"

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
        
        # Algorithm option sets for multivariate testing
        self.mv_algorithm_sets = {
            "Set B: BlinkEye+Algo1, BlinkEye+NoStab, MediaPipe+NoStab": [
                ("BLINKEYE", 1),   # BLINKEYE, Algorithm 1
                ("BLINKEYE", 3),   # BLINKEYE, No stabilization
                ("MEDIAPIPE", 3),  # MEDIAPIPE, No stabilization
            ],
            "Set A: BlinkEye+Algo1, BlinkEye+Algo2, MediaPipe+Algo2": [
                ("BLINKEYE", 1),   # BLINKEYE, Algorithm 1
                ("BLINKEYE", 2),   # BLINKEYE, Algorithm 2
                ("MEDIAPIPE", 2),  # MEDIAPIPE, Algorithm 2
            ],
        }
        
        # Track algorithm set usage
        self.mv_initial_algo_set = None
        self.mv_algo_set_changed = False
        
        # Recording state
        self.recording = False
        
        # Try to extract device info, fall back to saved/default for product code
        self.device_info = self.extract_device_info()
        if self.device_info and self.device_info.get('product_code'):
            self.product_code = self.device_info['product_code']
            self.save_product_code(self.product_code)
        else:
            self.product_code = self.load_product_code()
            self.device_info = None
        
        # Build INI file path
        self.update_ini_path()
        
        # Check if running as admin
        self.is_admin = self.check_admin()
        
        # Create session folder and log session info
        self.session_folder = self.create_session_folder()
        self.log_session_info()
        
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
        
        # Device info frame
        device_frame = ttk.LabelFrame(left_frame, text="Device Info", padding="10")
        device_frame.grid(row=0, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
        if self.device_info:
            sr_service_version = self.device_info.get('sr_service_version', 'N/A')
            eyetracker_version = self.device_info.get('eyetracker_version', 'N/A')
            lens_version = self.device_info.get('lens_version', 'N/A')
            lens_serial = self.device_info.get('lens_serial', 'N/A')
            sr_serial = self.device_info.get('sr_serial', 'N/A')
            product_code = self.device_info.get('product_code', 'N/A')
            
            ttk.Label(device_frame, text=f"SR Service:    {sr_service_version}", font=("Consolas", 9)).grid(row=0, column=0, sticky=tk.W, pady=2)
            ttk.Label(device_frame, text=f"Eye Tracker:   {eyetracker_version}", font=("Consolas", 9)).grid(row=1, column=0, sticky=tk.W, pady=2)
            ttk.Label(device_frame, text=f"Lens version:  {lens_version}", font=("Consolas", 9)).grid(row=2, column=0, sticky=tk.W, pady=2)
            ttk.Label(device_frame, text=f"Lens serial:   {lens_serial}", font=("Consolas", 9)).grid(row=3, column=0, sticky=tk.W, pady=2)
            ttk.Label(device_frame, text=f"SR serial:     {sr_serial}", font=("Consolas", 9)).grid(row=4, column=0, sticky=tk.W, pady=2)
            ttk.Label(device_frame, text=f"Product code:  {product_code}", font=("Consolas", 9, 'bold')).grid(row=5, column=0, sticky=tk.W, pady=2)
        else:
            ttk.Label(device_frame, text=f"Product code:  {self.product_code} (from settings)", 
                     font=("Consolas", 9)).grid(row=0, column=0, sticky=tk.W, pady=2)
            ttk.Label(device_frame, text="Device not detected - using saved value", 
                     font=("Arial", 8), foreground="orange").grid(row=1, column=0, sticky=tk.W, pady=2)
        
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
        
        # === RECORDING FRAME ===
        recording_frame = ttk.LabelFrame(left_frame, text="Recording", padding="10")
        recording_frame.grid(row=7, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
        self.recording_button = ttk.Button(recording_frame, text="Start recording", 
                                           command=self.toggle_recording)
        self.recording_button.grid(row=0, column=0, pady=5, ipadx=10, ipady=5)
        
        # Recording status label
        self.recording_status_label = ttk.Label(recording_frame, text="Recording: Off", 
                                                font=("Arial", 9), foreground="gray")
        self.recording_status_label.grid(row=1, column=0, pady=5)
        
        # === EYE STABILIZATION FRAME ===
        stab_frame = ttk.LabelFrame(left_frame, text="Eye Stabilization", padding="10")
        stab_frame.grid(row=8, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
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
        
        # Algorithm set selection (with warning)
        algo_set_frame = ttk.Frame(mv_frame)
        algo_set_frame.grid(row=5, column=0, pady=10)
        
        ttk.Label(algo_set_frame, text="Algorithm Set:", font=('Arial', 9)).pack(side=tk.LEFT, padx=(0, 5))
        self.mv_algo_set_var = tk.StringVar()
        self.mv_algo_set_combo = ttk.Combobox(algo_set_frame, textvariable=self.mv_algo_set_var,
                                              values=list(self.mv_algorithm_sets.keys()),
                                              state='readonly', width=45)
        self.mv_algo_set_combo.current(0)  # Set B (new) as default
        self.mv_algo_set_combo.pack(side=tk.LEFT)
        self.mv_algo_set_combo.bind('<<ComboboxSelected>>', self.on_algo_set_changed)
        
        ttk.Label(algo_set_frame, text="⚠ Do not change", font=('Arial', 9, 'bold'), 
                  foreground='red').pack(side=tk.LEFT, padx=(10, 0))
        
        # Allow recording checkbox
        self.mv_allow_recording = tk.BooleanVar(value=False)
        self.mv_recording_checkbox = ttk.Checkbutton(mv_frame, text="Allow recording during testing",
                                                     variable=self.mv_allow_recording)
        self.mv_recording_checkbox.grid(row=6, column=0, pady=10)
        
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
        
        # Set up close handler to clean up recording
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def on_close(self):
        """Handle application close - cleanup recording state"""
        self.remove_recording_from_ini()
        self.root.destroy()
    
    def toggle_recording(self):
        """Toggle recording state"""
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
        
        if not self.recording:
            # Start recording
            if self.set_recording(True):
                self.recording = True
                self.recording_button.config(text="Stop recording", state='disabled')
                self.recording_status_label.config(text="Recording: On", foreground="red")
                # Re-enable button after 2 seconds
                self.root.after(2000, self.enable_stop_button)
        else:
            # Stop recording
            if self.set_recording(False):
                self.recording = False
                self.recording_button.config(text="Start recording")
                self.recording_status_label.config(text="Recording: Off", foreground="gray")
                # Copy the latest recording
                self.copy_latest_recording()
    
    def copy_latest_recording(self):
        """Copy the latest recording folder to session folder"""
        source_dir = r"C:\ProgramData\Simulated Reality\Eye Tracker\Recordings"
        dest_base = os.path.join(self.session_folder, "Recordings")
        
        if not os.path.exists(source_dir):
            messagebox.showwarning("Warning", f"Recording source folder not found:\n{source_dir}")
            return
        
        # Find the latest recording folder (format: 2026-06-26___14_06_47)
        try:
            folders = [f for f in os.listdir(source_dir) 
                      if os.path.isdir(os.path.join(source_dir, f))]
            
            if not folders:
                messagebox.showwarning("Warning", "No recording folders found.")
                return
            
            # Sort by folder name (timestamp format allows alphabetical sorting)
            folders.sort(reverse=True)
            latest_folder = folders[0]
            
            source_path = os.path.join(source_dir, latest_folder)
            
            # Create destination directory if it doesn't exist
            if not os.path.exists(dest_base):
                os.makedirs(dest_base)
            
            dest_path = os.path.join(dest_base, latest_folder)
            
            # Copy the folder
            if os.path.exists(dest_path):
                shutil.rmtree(dest_path)  # Remove if already exists
            
            shutil.copytree(source_path, dest_path)
            
            messagebox.showinfo("Recording Saved", 
                              f"Recording copied to:\n{dest_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy recording:\n{str(e)}")
    
    def enable_stop_button(self):
        """Re-enable the stop recording button after delay"""
        if self.recording:  # Only if still recording
            self.recording_button.config(state='normal')
    
    def set_recording(self, state):
        """Set recording parameter in INI file"""
        config = self.read_ini()
        if config is None:
            return False
        
        section = 'Recorder'
        
        # Create section if it doesn't exist
        if not config.has_section(section):
            config.add_section(section)
        
        # Set recording value
        config.set(section, 'record', 'true' if state else 'false')
        
        return self.write_ini(config)
    
    def remove_recording_from_ini(self):
        """Remove recording parameter from INI file on app close"""
        config = self.read_ini()
        if config is None:
            return False
        
        section = 'Recorder'
        
        if config.has_section(section) and config.has_option(section, 'record'):
            config.remove_option(section, 'record')
            # If section is now empty, remove it
            if len(config.options(section)) == 0:
                config.remove_section(section)
            return self.write_ini(config)
        
        return True
    
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
    
    def create_session_folder(self):
        """Create a session folder with timestamp for logging all data"""
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        session_name = f"session_{timestamp}"
        session_path = os.path.join(self.get_executable_dir(), session_name)
        
        try:
            os.makedirs(session_path, exist_ok=True)
        except Exception as e:
            # Fall back to executable dir if can't create folder
            session_path = self.get_executable_dir()
        
        return session_path
    
    def log_session_info(self):
        """Log session information including device info and software versions"""
        info_path = os.path.join(self.session_folder, "session_info.txt")
        
        try:
            with open(info_path, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("MULTIVARIATE TESTING SESSION INFO\n")
                f.write("=" * 60 + "\n\n")
                
                f.write(f"Session started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Session folder: {self.session_folder}\n\n")
                
                f.write("-" * 40 + "\n")
                f.write("SOFTWARE VERSIONS\n")
                f.write("-" * 40 + "\n")
                
                if self.device_info:
                    f.write(f"SR Service version:    {self.device_info.get('sr_service_version', 'N/A')}\n")
                    f.write(f"Eye Tracker version:   {self.device_info.get('eyetracker_version', 'N/A')}\n")
                    f.write(f"Lens version:          {self.device_info.get('lens_version', 'N/A')}\n")
                else:
                    f.write("Device not detected - versions unavailable\n")
                
                f.write("\n")
                f.write("-" * 40 + "\n")
                f.write("DEVICE INFO\n")
                f.write("-" * 40 + "\n")
                
                if self.device_info:
                    f.write(f"Lens serial:           {self.device_info.get('lens_serial', 'N/A')}\n")
                    f.write(f"SR serial:             {self.device_info.get('sr_serial', 'N/A')}\n")
                    f.write(f"Product code:          {self.device_info.get('product_code', 'N/A')}\n")
                else:
                    f.write(f"Product code:          {self.product_code} (from settings)\n")
                    f.write("Device not connected or SR Service not running\n")
                
                f.write("\n")
                f.write("-" * 40 + "\n")
                f.write("SYSTEM INFO\n")
                f.write("-" * 40 + "\n")
                f.write(f"Running as admin:      {self.is_admin}\n")
                f.write(f"Config file:           {self.ini_path}\n")
                f.write("\n")
                f.write("=" * 60 + "\n")
                
        except Exception as e:
            pass  # Don't fail if we can't write session info
    
    def log_algo_set_info(self):
        """Append algorithm set usage info to session info file"""
        info_path = os.path.join(self.session_folder, "session_info.txt")
        
        try:
            with open(info_path, 'a', encoding='utf-8') as f:
                f.write("\n")
                f.write("-" * 40 + "\n")
                f.write(f"MULTIVARIATE TEST {self.active_test_number} - ALGORITHM SET\n")
                f.write("-" * 40 + "\n")
                f.write(f"Completed at:          {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Initial set:           {self.mv_initial_algo_set}\n")
                f.write(f"Final set:             {self.mv_algo_set_var.get()}\n")
                f.write(f"Set changed:           {'YES - WARNING!' if self.mv_algo_set_changed else 'No'}\n")
                f.write("\n")
        except Exception as e:
            pass  # Don't fail if we can't write
    
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
    
    def extract_device_info(self):
        """Extract device info from connected device using SR SDK"""
        try:
            SR_BIN = r"C:\Program Files\LeiaSR\Platform\bin"
            
            # Get SR Service and Eye Tracker versions from registry
            sr_service_dir = get_registry_path(r"SOFTWARE\Dimenco\Simulated Reality")
            eyetracker_dir = get_registry_path(r"SOFTWARE\Dimenco\Eye Tracker")
            
            sr_service_exe = os.path.join(sr_service_dir, "bin", "SRService.exe") if sr_service_dir else None
            if sr_service_exe and not os.path.exists(sr_service_exe):
                sr_service_exe = os.path.join(sr_service_dir, "bin", "srserver.exe")
            
            eyetracker_exe = os.path.join(eyetracker_dir, "bin", "SREyeTracker.exe") if eyetracker_dir else None
            if eyetracker_exe and not os.path.exists(eyetracker_exe):
                eyetracker_exe = os.path.join(eyetracker_dir, "bin", "DimencoEyeTracker.exe")
            
            sr_service_version = get_exe_version(sr_service_exe)
            eyetracker_version = get_exe_version(eyetracker_exe)
            
            # Load SR SDK
            core = ctypes.CDLL(os.path.join(SR_BIN, "SimulatedRealityCore.dll"))
            disp = ctypes.CDLL(os.path.join(SR_BIN, "SimulatedRealityDisplays.dll"))
            
            core.newSRContextLensPreference.restype = ctypes.c_void_p
            core.newSRContextLensPreference.argtypes = [ctypes.c_bool]
            context = core.newSRContextLensPreference(False)
            
            if not context:
                return None  # SR Service not running
            
            disp.createSwitchableLensHintAdmin.restype = ctypes.c_void_p
            disp.createSwitchableLensHintAdmin.argtypes = [ctypes.c_void_p]
            lens_admin = disp.createSwitchableLensHintAdmin(context)
            
            core.initializeSRContext.argtypes = [ctypes.c_void_p]
            core.initializeSRContext(context)
            
            time.sleep(0.5)
            
            # Get lens version
            disp.getVersion.restype = ctypes.c_char_p
            disp.getVersion.argtypes = [ctypes.c_void_p]
            lens_version = disp.getVersion(lens_admin).decode()
            
            # Get lens serial
            disp.getSerialNumber.restype = ctypes.c_char_p
            disp.getSerialNumber.argtypes = [ctypes.c_void_p]
            lens_serial = disp.getSerialNumber(lens_admin).decode()
            
            # Get SR serial
            disp.getAdditionalSerialNumber.restype = ctypes.c_char_p
            disp.getAdditionalSerialNumber.argtypes = [ctypes.c_void_p, ctypes.c_uint8]
            sr_serial = disp.getAdditionalSerialNumber(lens_admin, 4).decode()
            
            # Check if serial is empty (all null chars or empty string)
            if all(c == '\x00' for c in sr_serial) or sr_serial == '':
                sr_serial = "Not set"
                product_code = None
            else:
                # Extract product code (characters 8-10 of serial number)
                product_code = sr_serial[8:10] if len(sr_serial) > 9 else None
            
            return {
                'sr_service_version': sr_service_version,
                'eyetracker_version': eyetracker_version,
                'lens_version': lens_version,
                'lens_serial': lens_serial,
                'sr_serial': sr_serial,
                'product_code': product_code
            }
        except Exception as e:
            # If extraction fails, return None to fall back to saved/default value
            return None
    
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
            'algorithm_set': self.mv_algo_set_var.get(),
            'set_changed_during_session': self.mv_algo_set_changed,
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
    
    def on_algo_set_changed(self, event=None):
        """Called when the algorithm set combobox selection changes"""
        if self.mv_testing_mode and self.mv_initial_algo_set is not None:
            current_set = self.mv_algo_set_var.get()
            if current_set != self.mv_initial_algo_set:
                self.mv_algo_set_changed = True
    
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
            
            # Disable algorithm set dropdown during testing
            self.mv_algo_set_combo.config(state='disabled')
            
            # Update UI - disable other buttons and update active button
            buttons = {1: self.mv_button, 2: self.mv_button2}
            for num, btn in buttons.items():
                if num == test_number:
                    btn.config(text=f"Exit multivariate testing {num}")
                else:
                    btn.config(state='disabled')
            
            self.status_label.config(text="Current: Hidden (MV Testing)", foreground="purple")
            self.stab_status_label.config(text="Current: Hidden (MV Testing)", foreground="purple")
            
            # Start recording if checkbox is checked
            if self.mv_allow_recording.get():
                self.set_recording(True)
                self.recording = True
                self.recording_button.config(text="Stop recording", state='disabled')
                self.recording_status_label.config(text="Recording: On", foreground="red")
            
            # Start test sequence
            self.start_mv_test_sequence()
        else:
            # Exiting multivariate testing mode
            self.mv_testing_mode = False
            
            # Stop recording if it was started for testing
            if self.recording and self.mv_allow_recording.get():
                self.set_recording(False)
                self.recording = False
                self.recording_button.config(text="Start recording", state='normal')
                self.recording_status_label.config(text="Recording: Off", foreground="gray")
                self.copy_latest_recording()
            
            # Update UI - re-enable all buttons
            self.mv_button.config(text="Start multivariate testing 1", state='normal')
            self.mv_button2.config(text="Start multivariate testing 2", state='normal')
            self.mv_algo_set_combo.config(state='readonly')
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
        
        # Track algorithm set at start of testing
        self.mv_initial_algo_set = self.mv_algo_set_var.get()
        self.mv_algo_set_changed = False
        
        # Show test UI
        self.mv_field_frame.grid(row=8, column=0, pady=10)
        self.mv_feedback_frame.pack_forget()
        
        # Show first test
        self.show_next_mv_test()
    
    def show_next_mv_test(self):
        """Display the next test instruction for multivariate testing"""
        if self.mv_current_test_idx >= len(self.mv_tests):
            # All tests completed
            self.finish_mv_testing()
            return
        
        # Get algorithm options from selected set
        selected_set = self.mv_algo_set_var.get()
        mv_options = self.mv_algorithm_sets.get(selected_set, list(self.mv_algorithm_sets.values())[0])
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
        # Stop recording if it was started for testing
        if self.recording and self.mv_allow_recording.get():
            self.set_recording(False)
            self.recording = False
            self.recording_button.config(text="Start recording", state='normal')
            self.recording_status_label.config(text="Recording: Off", foreground="gray")
            self.copy_latest_recording()
        
        # Save results to CSV in session folder
        log_filename = f"multivariate_testing_{self.active_test_number}_results.csv"
        log_path = os.path.join(self.session_folder, log_filename)
        
        try:
            with open(log_path, 'w', newline='', encoding='utf-8') as f:
                if self.mv_test_results:
                    fieldnames = self.mv_test_results[0].keys()
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(self.mv_test_results)
            
            # Log algorithm set info to session info file
            self.log_algo_set_info()
            
            messagebox.showinfo("Multivariate Testing Complete", 
                              f"All tests completed!\n\nResults saved to:\n{self.session_folder}\\{log_filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save results:\n{str(e)}")
        
        # Exit multivariate testing mode
        self.mv_testing_mode = False
        self.mv_button.config(text="Start multivariate testing 1", state='normal')
        self.mv_button2.config(text="Start multivariate testing 2", state='normal')
        self.mv_algo_set_combo.config(state='readonly')
        self.mv_field_frame.grid_remove()
        self.update_status()

# Create and run GUI
if __name__ == "__main__":
    root = tk.Tk()
    app = MultivariateSwitcherGUI(root)
    root.mainloop()
