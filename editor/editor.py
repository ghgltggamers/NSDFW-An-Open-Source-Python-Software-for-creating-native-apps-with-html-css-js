import os
import json
import webbrowser
import http.server
import socketserver
import tkinter as tk
from tkinter import simpledialog, filedialog, messagebox
from tkinter import scrolledtext
import subprocess
import threading
import shutil

from project_manager.project_manager import ProjectManager

class HTTPServerThread(threading.Thread):
    def __init__(self, server_address, handler_class):
        super().__init__()
        self.server = http.server.HTTPServer(server_address, handler_class)
        self.should_stop = threading.Event()

    def run(self):
        while not self.should_stop.is_set():
            self.server.handle_request()

    def stop(self):
        self.should_stop.set()
        self.server.server_close()

class Editor:
    def __init__(self, root):
        self.root = root
        self.root.title("NSDFW - Native Software Deployer From Web")
        
        # Set the window icon
        self.set_icon("app_icon.png")

        # Initialize Project Manager
        self.project_manager = ProjectManager()
        self.current_project_path = None
        self.current_file_path = None

        # Initialize HTTP server variables
        self.http_server_thread = None

        # Project List Frame
        self.project_frame = tk.Frame(root, width=200, bg='lightgrey')
        self.project_frame.pack(side=tk.LEFT, fill=tk.Y)

        self.project_listbox = tk.Listbox(self.project_frame)
        self.project_listbox.pack(fill=tk.Y)
        self.project_listbox.bind('<<ListboxSelect>>', self.on_project_select)

        # File Browser
        self.file_browser = tk.Listbox(root, width=30)
        self.file_browser.pack(side=tk.LEFT, fill=tk.Y)
        self.file_browser.bind('<<ListboxSelect>>', self.on_file_select)

        # Text Editor
        self.text_editor = tk.Text(root, wrap='word')
        self.text_editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Console
        self.console = scrolledtext.ScrolledText(root, height=10)
        self.console.pack(side=tk.BOTTOM, fill=tk.X)

        # File Info Label
        self.file_info_label = tk.Label(root, text="No file open", bg='lightgrey')
        self.file_info_label.pack(side=tk.TOP, fill=tk.X)
        self.file_info_label.bind("<Button-1>", self.show_file_menu)

        # Top Buttons
        self.create_buttons()

        # Load Projects
        self.load_projects()

        # Keyboard shortcuts
        self.root.bind('<Control-s>', self.save_file_shortcut)

    def set_icon(self, icon_path):
        """Set the window icon."""
        if os.path.exists(icon_path):
            self.root.iconphoto(True, tk.PhotoImage(file=icon_path))
        else:
            print(f"Icon file '{icon_path}' not found.")

    def create_buttons(self):
        button_frame = tk.Frame(self.root)
        button_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        buttons = [
            ("Open", self.open_file),
            ("Save", self.save_file),
            ("New", self.create_file),
            ("Delete", self.delete_file),
            ("+ New", self.create_project),
            ("- Project", self.delete_project),
            ("Run", self.run_file),
            ("Export", self.export_project),
            ("Stop Server", self.stop_server)  # Added Stop Server button
        ]

        for index, (text, command) in enumerate(buttons):
            row = index // 3
            column = index % 3
            button = tk.Button(button_frame, text=text, command=command)
            button.grid(row=row, column=column, padx=5, pady=5, sticky="ew")

    def create_menu(self):
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Save", command=self.save_file)
        menu.add_command(label="Delete", command=self.delete_file)
        menu.add_command(label="Run", command=self.run_file)
        return menu

    def show_file_menu(self, event):
        if self.current_file_path:
            menu = self.create_menu()
            try:
                menu.post(event.x_root, event.y_root)
            finally:
                menu.grab_release()

    def open_file(self):
        filepath = filedialog.askopenfilename()
        if filepath:
            with open(filepath, 'r') as file:
                content = file.read()
                self.text_editor.delete(1.0, tk.END)
                self.text_editor.insert(tk.END, content)
                self.current_file_path = filepath
                self.update_file_info()

    def save_file(self):
        if self.current_file_path:
            with open(self.current_file_path, 'w') as file:
                content = self.text_editor.get(1.0, tk.END)
                file.write(content)
        else:
            filepath = filedialog.asksaveasfilename(defaultextension=".html",
                                                    filetypes=[("HTML files", "*.html"),
                                                               ("CSS files", "*.css"),
                                                               ("JavaScript files", "*.js"),
                                                               ("All files", "*.*")])
            if filepath:
                content = self.text_editor.get(1.0, tk.END)
                with open(filepath, 'w') as file:
                    file.write(content)
                self.current_file_path = filepath
                self.update_file_info()

    def save_file_shortcut(self, event=None):
        self.save_file()

    def create_file(self):
        if self.current_project_path:
            filename = simpledialog.askstring("File Name", "Enter new file name:")
            if filename:
                filepath = os.path.join(self.current_project_path, 'assets', filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with open(filepath, 'w') as file:
                    pass
                self.load_files()
                self.current_file_path = filepath
                self.update_file_info()
        else:
            messagebox.showwarning("No Project Loaded", "Please load a project before creating a file.")

    def delete_file(self):
        if self.current_file_path:
            os.remove(self.current_file_path)
            self.text_editor.delete(1.0, tk.END)
            self.load_files()
            self.current_file_path = None
            self.update_file_info()
        else:
            messagebox.showwarning("No File Open", "Please open a file to delete.")

    def run_file(self):
        if self.current_file_path:
            webbrowser.open(f'file://{self.current_file_path}')
        else:
            messagebox.showwarning("No File Open", "Please open a file to run.")

    def load_files(self):
        self.file_browser.delete(0, tk.END)
        if self.current_project_path:
            assets_path = os.path.join(self.current_project_path, 'assets')
            for root, dirs, files in os.walk(assets_path):
                for name in files:
                    self.file_browser.insert(tk.END, os.path.relpath(os.path.join(root, name), assets_path))

    def update_file_info(self):
        if self.current_file_path:
            file_name = os.path.basename(self.current_file_path)
            self.file_info_label.config(text=file_name)
        else:
            self.file_info_label.config(text="No file open")

    def create_project(self):
        name = simpledialog.askstring("Project Name", "Enter project name:")
        path = filedialog.askdirectory(title="Select Project Path")
        package_name = simpledialog.askstring("Package Name", "Enter package name (e.g., com.example.app):")

        if name and path and package_name:
            project_path = os.path.join(path, name)
            if not os.path.exists(project_path):
                os.makedirs(project_path)
                assets_path = os.path.join(project_path, 'assets')
                os.makedirs(assets_path)

                # Create meta file
                meta_file_path = os.path.join(project_path, 'project.meta.json')
                meta_data = {
                    "name": name,
                    "path": project_path,
                    "package_name": package_name
                }
                with open(meta_file_path, 'w') as meta_file:
                    json.dump(meta_data, meta_file, indent=4)
                
                # Create boilerplate files in assets directory
                with open(os.path.join(assets_path, 'index.html'), 'w') as file:
                    file.write("<!DOCTYPE html>\n<html>\n<head>\n<title>Project</title>\n<link rel='stylesheet' href='style.css'>\n</head>\n<body>\n<h1>Hello, World!</h1>\n<script src='script.js'></script>\n</body>\n</html>")
                
                with open(os.path.join(assets_path, 'style.css'), 'w') as file:
                    file.write("body { font-family: Arial, sans-serif; }")
                
                with open(os.path.join(assets_path, 'script.js'), 'w') as file:
                    file.write("console.log('Hello, World!');")

                # Update project.json
                self.project_manager.add_project(name, project_path)

                messagebox.showinfo("Success", "Project created successfully!")
                self.load_projects()
            else:
                messagebox.showerror("Error", "Project path already exists.")
        else:
            messagebox.showwarning("Input Error", "All fields are required.")

    def delete_project(self):
        selected_project = self.project_listbox.curselection()
        if selected_project:
            project_name = self.project_listbox.get(selected_project[0])
            project_path = self.project_manager.get_project_path(project_name)
            if project_path:
                shutil.rmtree(project_path)
                self.project_manager.remove_project(project_name)
                self.load_projects()
                self.text_editor.delete(1.0, tk.END)
                self.current_file_path = None
                self.update_file_info()
                messagebox.showinfo("Success", "Project deleted successfully!")
            else:
                messagebox.showwarning("Error", "Project path not found.")
        else:
            messagebox.showwarning("No Selection", "Select a project to delete.")

    def load_projects(self):
        self.project_listbox.delete(0, tk.END)
        projects = self.project_manager.get_projects()
        for project_name in projects:
            self.project_listbox.insert(tk.END, project_name)

    def on_project_select(self, event):
        selected_project = self.project_listbox.curselection()
        if selected_project:
            self.current_project_path = self.project_manager.get_project_path(self.project_listbox.get(selected_project[0]))
            self.load_files()

    def on_file_select(self, event):
        selected_file = self.file_browser.curselection()
        if selected_file:
            file_path = os.path.join(self.current_project_path, 'assets', self.file_browser.get(selected_file[0]))
            if os.path.exists(file_path):
                with open(file_path, 'r') as file:
                    content = file.read()
                    self.text_editor.delete(1.0, tk.END)
                    self.text_editor.insert(tk.END, content)
                    self.current_file_path = file_path
                    self.update_file_info()

    def stop_server(self):
        if self.http_server_thread:
            self.http_server_thread.stop()
            self.http_server_thread.join()
            self.http_server_thread = None
            messagebox.showinfo("Server", "Server stopped successfully.")

    def export_project(self):
        if self.current_project_path:
            webkit_version = simpledialog.askstring("WebKit2GTK Version", "Enter WebKit2GTK version (e.g., 4.0 or 4.1):")
            if webkit_version:
                project_name = simpledialog.askstring("Project Name", "Enter the project name:")
                if project_name:
                    cpp_source_code = f"""
#include <gtk/gtk.h>
#include <webkit2/webkit2.h>
#include <glib.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

// Function to get the directory of the executable
char* get_executable_directory() {{
    static char path[1024];
    ssize_t len = readlink("/proc/self/exe", path, sizeof(path) - 1);
    if (len != -1) {{
        path[len] = '\\0';
        char* last_slash = strrchr(path, '/');
        if (last_slash) {{
            *(last_slash + 1) = '\\0';
        }}
        return path;
    }}
    return NULL;
}}

// Function to get the path to the index.html file
char* get_index_file_path() {{
    static char index_path[1024];
    char* exe_dir = get_executable_directory();
    if (exe_dir) {{
        snprintf(index_path, sizeof(index_path), "%sindex.html", exe_dir);
        return index_path;
    }}
    return NULL;
}}

static void activate(GtkApplication* app, gpointer user_data) {{
    GtkWidget *window;
    GtkWidget *web_view;
    GtkWidget *icon;
    char* index_path = get_index_file_path();

    if (!index_path) {{
        g_printerr("Failed to get index.html path\\n");
        return;
    }}

    window = gtk_application_window_new(app);
    gtk_window_set_title(GTK_WINDOW(window), "{project_name}");
    gtk_window_set_default_size(GTK_WINDOW(window), 800, 600);
    gtk_window_set_position(GTK_WINDOW(window), GTK_WIN_POS_CENTER);

    // Load and set the application icon
    GdkPixbuf *pixbuf = gdk_pixbuf_new_from_file("app_icon.png", NULL);
    if (pixbuf) {{
        gtk_window_set_icon(GTK_WINDOW(window), pixbuf);
        g_object_unref(pixbuf);
    }} else {{
        g_printerr("Failed to load app_icon.png\\n");
    }}

    web_view = webkit_web_view_new();
    gtk_container_add(GTK_CONTAINER(window), web_view);

    webkit_web_view_load_uri(WEBKIT_WEB_VIEW(web_view), g_strdup_printf("file://%s", index_path));

    gtk_widget_show_all(window);
}}

int main(int argc, char *argv[]) {{
    GtkApplication *app;
    int status;

    app = gtk_application_new("com.example.app", G_APPLICATION_DEFAULT_FLAGS);
    g_signal_connect(app, "activate", G_CALLBACK(activate), NULL);
    status = g_application_run(G_APPLICATION(app), argc, argv);
    g_object_unref(app);

    return status;
}}
"""
                    cpp_file_path = os.path.join(self.current_project_path, "main.cpp")
                    with open(cpp_file_path, 'w') as cpp_file:
                        cpp_file.write(cpp_source_code)

                    # Move the icon file to the project directory
                    icon_file_path = os.path.join(self.current_project_path, "app_icon.png")
                    shutil.copy("app_icon.png", icon_file_path)

                    compile_command = f"g++ -o {os.path.join(self.current_project_path, 'assets', 'app')} {cpp_file_path} `pkg-config --cflags --libs gtk+-3.0 webkit2gtk-{webkit_version}`"
                    print("Compiling with command:", compile_command)
                    try:
                        subprocess.run(compile_command, shell=True, check=True)
                        os.remove(cpp_file_path)  # Delete main.cpp after compilation
                        messagebox.showinfo("Export", "Project exported successfully!")
                    except subprocess.CalledProcessError as e:
                        messagebox.showerror("Error", f"Compilation failed: {e}")
                else:
                    messagebox.showwarning("Project Name", "Please provide a valid project name.")
            else:
                messagebox.showwarning("WebKit2GTK Version", "Please provide a valid WebKit2GTK version.")
        else:
            messagebox.showwarning("No Project Loaded", "Please load a project before exporting.")

if __name__ == "__main__":
    root = tk.Tk()
    editor = Editor(root)
    root.mainloop()
