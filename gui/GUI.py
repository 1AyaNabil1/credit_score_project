import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from db.users import get_all_users, get_user_by_id
from logic.calculator import calculate_iScore


class CreditScoreApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Credit Score Calculator")
        self.root.geometry("600x450")
        self.root.configure(bg="#f0f2f5")
        self.root.resizable(False, False)

        self.selected_user_id = None
        self.users = []

        self._init_main_window()
        self._load_users()

    def _init_main_window(self):
        # Title
        ttk.Label(
            self.root, text="Credit Score Dashboard", font=("Segoe UI", 16, "bold")
        ).pack(pady=10)

        # User selection
        ttk.Label(self.root, text="Select User:").pack(pady=5)
        self.user_combo = ttk.Combobox(self.root, state="readonly", width=40)
        self.user_combo.pack()
        self.user_combo.bind("<<ComboboxSelected>>", self._on_user_selected)

        # Buttons frame
        btn_frame = tk.Frame(self.root, bg="#f0f2f5")
        btn_frame.pack(pady=15)

        ttk.Button(
            btn_frame, text="Calculate iScore", command=self._calculate_score
        ).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Add User", command=self._add_user_popup).grid(
            row=0, column=1, padx=5
        )
        ttk.Button(btn_frame, text="Delete User", command=self._delete_user).grid(
            row=0, column=2, padx=5
        )
        ttk.Button(btn_frame, text="Refresh", command=self._refresh_users).grid(
            row=0, column=3, padx=5
        )

        # Score display panel
        self.result_label = tk.Label(
            self.root, text="", font=("Segoe UI", 12), bg="#f0f2f5", fg="#333"
        )
        self.result_label.pack(pady=15)

        # Status bar
        self.status = tk.Label(
            self.root,
            text="",
            font=("Segoe UI", 9),
            bg="#f0f2f5",
            anchor="w",
            relief="sunken",
        )
        self.status.pack(fill="x", side="bottom")

    def _load_users(self):
        self.users = get_all_users()
        self.user_combo["values"] = [
            f"{u['user_id']} - {u['full_name']}" for u in self.users
        ]
        self.user_combo.set("")

    def _on_user_selected(self, event):
        selected = self.user_combo.get()
        if selected:
            self.selected_user_id = int(selected.split(" - ")[0])
            self.status.config(text=f"Selected user ID: {self.selected_user_id}")

    def _calculate_score(self):
        if self.selected_user_id is None:
            messagebox.showwarning("Select User", "Please select a user first.")
            return

        score = calculate_iScore(self.selected_user_id)
        details = get_user_by_id(self.selected_user_id)
        display = (
            f"User: {details['full_name']} (ID: {details['user_id']})\n"
            f"National ID: {details['national_id']}\n"
            f"Calculated iScore: {score}"
        )
        self.result_label.config(text=display)
        self.status.config(text=f"iScore calculated for {details['full_name']}")

    def _add_user_popup(self):
        name = simpledialog.askstring("Add User", "Full name:")
        if not name:
            return
        nat_id = simpledialog.askstring("Add User", "National ID:")
        if not nat_id:
            return

        from db.connection import get_all_connections

        conns = get_all_connections()
        conn = conns["users"]
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(user_id) FROM users")
            max_id = cursor.fetchone()[0] or 0
            new_id = max_id + 1
            cursor.execute(
                "INSERT INTO users (user_id, full_name, national_id) VALUES (%s, %s, %s)",
                (new_id, name, nat_id),
            )
            conn.commit()
            messagebox.showinfo("Success", f"User '{name}' added.")
            self._refresh_users()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add user: {e}")
        finally:
            cursor.close()
            conn.close()

    def _delete_user(self):
        if self.selected_user_id is None:
            messagebox.showwarning("Delete User", "No user selected.")
            return

        confirm = messagebox.askyesno(
            "Delete User",
            f"Are you sure you want to delete user ID {self.selected_user_id}?",
        )
        if not confirm:
            return

        from db.connection import get_all_connections

        conns = get_all_connections()
        conn = conns["users"]
        try:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM users WHERE user_id = %s", (self.selected_user_id,)
            )
            conn.commit()
            messagebox.showinfo("Deleted", f"User ID {self.selected_user_id} deleted.")
            self._refresh_users()
            self.result_label.config(text="")
            self.selected_user_id = None
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete user: {e}")
        finally:
            cursor.close()
            conn.close()

    def _refresh_users(self):
        self._load_users()
        self.result_label.config(text="")
        self.status.config(text="User list refreshed.")
        self.selected_user_id = None


# Entry point
def launch_gui():
    root = tk.Tk()
    CreditScoreApp(root)
    root.mainloop()
