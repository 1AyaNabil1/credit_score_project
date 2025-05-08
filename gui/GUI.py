import tkinter as tk
from tkinter import ttk, messagebox
from db.users import get_all_users, get_user_by_id
from logic.calculator import calculate_iScore


def launch_gui():
    root = tk.Tk()
    app = CreditScoreApp(root)
    root.mainloop()


class CreditScoreApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Credit Score Calculator")
        self.root.geometry("600x400")
        self.root.configure(bg="#f0f2f5")

        self.selected_user_id = None
        self.users = []

        self._init_main_window()
        self._load_users()

    def _init_main_window(self):
        # Labels, dropdown, buttons, results panel
        pass

    def _load_users(self):
        # Call get_all_users and populate dropdown
        pass

    def _on_user_selected(self, event):
        # Save selected user_id
        pass

    def _calculate_score(self):
        # Call calculate_iScore, show results
        pass

    def _add_user_popup(self):
        # Popup form to add user
        pass

    def _delete_user(self):
        # Delete selected user
        pass

    def _refresh_users(self):
        # Reload user list in dropdown
        pass
