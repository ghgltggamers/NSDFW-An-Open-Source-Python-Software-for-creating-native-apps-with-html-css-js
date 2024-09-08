# project_manager/project_manager.py

import json
import os

class ProjectManager:
    def __init__(self, data_file='projects.json'):
        self.data_file = data_file
        self.projects = self.load_projects()

    def load_projects(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as file:
                return json.load(file)
        else:
            return {}

    def save_projects(self):
        with open(self.data_file, 'w') as file:
            json.dump(self.projects, file, indent=4)

    def get_projects(self):
        return list(self.projects.keys())

    def get_project_path(self, name):
        return self.projects.get(name, {}).get('path')

    def add_project(self, name, path):
        self.projects[name] = {'path': path}
        self.save_projects()

    def remove_project(self, name):
        if name in self.projects:
            del self.projects[name]
            self.save_projects()
