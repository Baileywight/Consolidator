import wx
import os

def generate_directory_tree(root_path, output_filename, excluded_folders=None):
    """
    Generate a text representation of the directory structure.
    
    Args:
        root_path: The root directory to start from
        output_filename: The name of the output file to exclude from the tree
        excluded_folders: Set of folder paths to exclude from the tree
    
    Returns:
        String representation of the directory tree
    """
    if excluded_folders is None:
        excluded_folders = set()
    
    tree_lines = ["Directory Structure:"]
    
    def _add_to_tree(path, prefix=""):
        # Skip if this path is in excluded folders
        if path in excluded_folders:
            return
            
        try:
            entries = sorted(os.listdir(path))
        except PermissionError:
            return
        
        # Filter out the output file and hidden files/folders
        filtered_entries = [entry for entry in entries 
                           if entry != output_filename 
                           and not entry.startswith('.')]
        
        # Further filter out excluded subdirectories
        final_entries = []
        for entry in filtered_entries:
            entry_path = os.path.join(path, entry)
            if not (os.path.isdir(entry_path) and entry_path in excluded_folders):
                final_entries.append(entry)
        
        for i, entry in enumerate(final_entries):
            is_last = i == len(final_entries) - 1
            entry_path = os.path.join(path, entry)
            
            # Choose the correct prefix characters
            if is_last:
                connector = "└── "
                new_prefix = prefix + "    "
            else:
                connector = "├── "
                new_prefix = prefix + "│   "
                
            # Add the entry to the tree
            tree_lines.append(f"{prefix}{connector}{os.path.basename(entry_path)}")
            
            # Recursively process directories (if not excluded)
            if os.path.isdir(entry_path) and entry_path not in excluded_folders:
                _add_to_tree(entry_path, new_prefix)
    
    _add_to_tree(root_path)
    return "\n".join(tree_lines)

def consolidate_files(folder_path, output_filename="consolidated_code.txt", include_subdirs=False, include_tree=False, excluded_folders=None):
    """
    Consolidates text from all files in a folder into a single output file.
    Args:
        folder_path: The path to the folder containing the files.
        output_filename: The name of the output file (default: "consolidated_code.txt").
        include_subdirs: Whether to include files from subdirectories (default: False).
        include_tree: Whether to include directory structure tree in output (default: False).
        excluded_folders: Set of folder paths to exclude from consolidation (default: None).
    """
    if excluded_folders is None:
        excluded_folders = set()
    
    output_path = os.path.join(folder_path, output_filename)
    files_processed = 0
    
    try:
        with open(output_path, "w", encoding="utf-8") as outfile:
            # Add directory tree if requested
            if include_tree:
                tree = generate_directory_tree(folder_path, output_filename, excluded_folders)
                outfile.write(tree + "\n\n")
                outfile.write("=" * 50 + "\n\n")
            
            if include_subdirs:
                # Walk through directory and subdirectories
                for root, dirs, files in os.walk(folder_path):
                    # Skip if current directory is excluded
                    if root in excluded_folders:
                        dirs.clear()  # Don't descend into subdirectories
                        continue
                    
                    # Remove excluded directories from dirs list to prevent os.walk from entering them
                    dirs[:] = [d for d in dirs if os.path.join(root, d) not in excluded_folders]
                    
                    for filename in files:
                        if filename != output_filename:  # Avoid the output file itself
                            filepath = os.path.join(root, filename)
                            # Get relative path from the root folder for cleaner display
                            rel_path = os.path.relpath(filepath, folder_path)
                            
                            try:
                                with open(filepath, "r", encoding="utf-8") as infile:
                                    outfile.write(f"======= {rel_path} =======\n")
                                    outfile.write(infile.read() + "\n\n")
                                    files_processed += 1
                            except UnicodeDecodeError:
                                print(f"Warning: Skipping file {rel_path} due to encoding issues.")
                            except Exception as e:
                                print(f"Error processing file {rel_path}: {e}")
            else:
                # Original behavior - only process files in the top directory
                for filename in os.listdir(folder_path):
                    filepath = os.path.join(folder_path, filename)
                    if os.path.isfile(filepath) and filename != output_filename:
                        try:
                            with open(filepath, "r", encoding="utf-8") as infile:
                                outfile.write(f"======= {filename} =======\n")
                                outfile.write(infile.read() + "\n\n")
                                files_processed += 1
                        except UnicodeDecodeError:
                            print(f"Warning: Skipping file {filename} due to encoding issues.")
                        except Exception as e:
                            print(f"Error processing file {filename}: {e}")
        
        print(f"Consolidated code written to: {output_path}")
        return output_path, files_processed
    except Exception as e:
        print(f"Error: {e}")
        raise e

class CodeConsolidatorFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Code Consolidator", size=(650, 400))
        
        # Create a panel
        panel = wx.Panel(self)
        
        # Create the main sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Folder path row
        folder_sizer = wx.BoxSizer(wx.HORIZONTAL)
        folder_label = wx.StaticText(panel, label="Folder Path:")
        self.folder_path_ctrl = wx.TextCtrl(panel, size=(350, -1))
        browse_button = wx.Button(panel, label="Browse")
        browse_button.Bind(wx.EVT_BUTTON, self.browse_folder)
        
        folder_sizer.Add(folder_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        folder_sizer.Add(self.folder_path_ctrl, 1, wx.ALL | wx.EXPAND, 5)
        folder_sizer.Add(browse_button, 0, wx.ALL, 5)
        
        # Output filename row
        output_sizer = wx.BoxSizer(wx.HORIZONTAL)
        output_label = wx.StaticText(panel, label="Output File:")
        self.output_file_ctrl = wx.TextCtrl(panel, value="consolidated_code.txt")
        
        output_sizer.Add(output_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        output_sizer.Add(self.output_file_ctrl, 1, wx.ALL | wx.EXPAND, 5)
        
        # Excluded folders section
        excluded_label = wx.StaticText(panel, label="Excluded Folders:")
        
        # Excluded folders list with scrollbar
        self.excluded_folders_list = wx.ListCtrl(panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.excluded_folders_list.AppendColumn("Excluded Folder Paths", width=580)
        self.excluded_folders_list.SetMinSize((580, 100))
        
        # Buttons for managing excluded folders
        exclude_buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        add_exclude_button = wx.Button(panel, label="Add Folder to Exclude")
        remove_exclude_button = wx.Button(panel, label="Remove Selected")
        clear_exclude_button = wx.Button(panel, label="Clear All")
        
        add_exclude_button.Bind(wx.EVT_BUTTON, self.add_excluded_folder)
        remove_exclude_button.Bind(wx.EVT_BUTTON, self.remove_excluded_folder)
        clear_exclude_button.Bind(wx.EVT_BUTTON, self.clear_excluded_folders)
        
        exclude_buttons_sizer.Add(add_exclude_button, 0, wx.ALL, 5)
        exclude_buttons_sizer.Add(remove_exclude_button, 0, wx.ALL, 5)
        exclude_buttons_sizer.Add(clear_exclude_button, 0, wx.ALL, 5)
        
        # Options row
        options_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.include_subdirs_checkbox = wx.CheckBox(panel, label="Include subdirectories")
        self.include_tree_checkbox = wx.CheckBox(panel, label="Include directory tree")
        options_sizer.Add(self.include_subdirs_checkbox, 0, wx.ALL, 5)
        options_sizer.Add(self.include_tree_checkbox, 0, wx.ALL, 5)
        
        # Consolidate button
        consolidate_button = wx.Button(panel, label="Consolidate")
        consolidate_button.Bind(wx.EVT_BUTTON, self.consolidate_button_clicked)
        
        # Result text
        self.result_text = wx.StaticText(panel, label="")
        
        # Store excluded folders
        self.excluded_folders = set()
        
        # Add all elements to the main sizer in the correct order
        main_sizer.Add(folder_sizer, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(output_sizer, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(excluded_label, 0, wx.ALL, 5)
        main_sizer.Add(self.excluded_folders_list, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(exclude_buttons_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        main_sizer.Add(options_sizer, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(consolidate_button, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        main_sizer.Add(self.result_text, 0, wx.EXPAND | wx.ALL, 5)
        
        # Set the panel's sizer
        panel.SetSizer(main_sizer)
        
        # Center the window
        self.Centre()
        
    def browse_folder(self, event):
        with wx.DirDialog(self, "Choose a directory", style=wx.DD_DEFAULT_STYLE) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self.folder_path_ctrl.SetValue(dlg.GetPath())
    
    def add_excluded_folder(self, event):
        """Add a folder to the exclusion list using a directory dialog."""
        root_folder = self.folder_path_ctrl.GetValue()
        
        if not root_folder:
            wx.MessageBox("Please select a root folder first.", "No Root Folder", 
                         wx.OK | wx.ICON_WARNING)
            return
        
        # Start the dialog from the root folder if it exists
        default_path = root_folder if os.path.exists(root_folder) else ""
        
        with wx.DirDialog(self, "Select folder to exclude from consolidation", 
                         defaultPath=default_path, style=wx.DD_DEFAULT_STYLE) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                selected_folder = dlg.GetPath()
                
                # Normalize paths for consistent comparison
                root_folder_norm = os.path.normpath(root_folder)
                selected_folder_norm = os.path.normpath(selected_folder)
                
                # Validate that the selected folder is within the root folder
                if not selected_folder_norm.startswith(root_folder_norm):
                    wx.MessageBox(
                        "Selected folder must be within the root consolidation folder.",
                        "Invalid Selection", wx.OK | wx.ICON_WARNING
                    )
                    return
                
                # Check if already excluded
                if selected_folder_norm in self.excluded_folders:
                    wx.MessageBox(
                        "This folder is already in the exclusion list.",
                        "Already Excluded", wx.OK | wx.ICON_INFORMATION
                    )
                    return
                
                # Add to exclusion list
                self.excluded_folders.add(selected_folder_norm)
                self.update_excluded_folders_display()
    
    def remove_excluded_folder(self, event):
        """Remove the selected folder from the exclusion list."""
        selected = self.excluded_folders_list.GetFirstSelected()
        if selected == -1:
            wx.MessageBox("Please select a folder to remove.", "No Selection", 
                         wx.OK | wx.ICON_WARNING)
            return
        
        # Get the folder path from the list
        folder_path = self.excluded_folders_list.GetItemText(selected)
        
        # Remove from set and update display
        self.excluded_folders.discard(folder_path)
        self.update_excluded_folders_display()
    
    def clear_excluded_folders(self, event):
        """Clear all excluded folders."""
        if self.excluded_folders:
            result = wx.MessageBox(
                "Are you sure you want to clear all excluded folders?",
                "Confirm Clear", wx.YES_NO | wx.ICON_QUESTION
            )
            if result == wx.YES:
                self.excluded_folders.clear()
                self.update_excluded_folders_display()
    
    def update_excluded_folders_display(self):
        """Update the list control showing excluded folders."""
        # Clear the list
        self.excluded_folders_list.DeleteAllItems()
        
        # Add all excluded folders
        for folder_path in sorted(self.excluded_folders):
            index = self.excluded_folders_list.InsertItem(self.excluded_folders_list.GetItemCount(), folder_path)
        
        # Update the layout
        self.Layout()
    
    def consolidate_button_clicked(self, event):
        folder_path = self.folder_path_ctrl.GetValue()
        output_filename = self.output_file_ctrl.GetValue()
        include_subdirs = self.include_subdirs_checkbox.GetValue()
        include_tree = self.include_tree_checkbox.GetValue()
        
        if not folder_path:
            self.result_text.SetLabel("Please select a folder.")
            self.result_text.SetForegroundColour(wx.Colour(255, 0, 0))  # Red color
            self.Layout()
            return
            
        if not output_filename:
            self.result_text.SetLabel("Please specify an output filename.")
            self.result_text.SetForegroundColour(wx.Colour(255, 0, 0))  # Red color
            self.Layout()
            return
        
        try:
            output_path, files_processed = consolidate_files(
                folder_path, 
                output_filename, 
                include_subdirs,
                include_tree,
                self.excluded_folders
            )
            
            excluded_info = f" (excluded {len(self.excluded_folders)} folders)" if self.excluded_folders else ""
            self.result_text.SetLabel(
                f"Consolidated {files_processed} files to: {output_path}{excluded_info}"
            )
            self.result_text.SetForegroundColour(wx.Colour(0, 128, 0))  # Green color
        except Exception as e:
            self.result_text.SetLabel(f"Error: {str(e)}")
            self.result_text.SetForegroundColour(wx.Colour(255, 0, 0))  # Red color
        
        # Refresh to update layout after changing text
        self.Layout()

if __name__ == "__main__":
    app = wx.App()
    frame = CodeConsolidatorFrame()
    frame.Show()
    app.MainLoop()