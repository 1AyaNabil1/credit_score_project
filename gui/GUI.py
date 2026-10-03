import customtkinter as ctk
from tkinter import messagebox, simpledialog, filedialog
from db import users as user_db
from db.connection import DatabaseError
from logic.calculator import calculate_iScore, score_user
from logic.scoring import InvalidRecordError, score_band
from logic.validation import ValidationError
from PIL import Image
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Wedge
from pathlib import Path
import csv

# Icons ship with the project, so find them relative to this file rather than
# the current working directory.
RESOURCES_DIR = Path(__file__).resolve().parent.parent / "resources"

BAND_COLORS = {
    "Poor": "#e53935",
    "Fair": "#fb8c00",
    "Good": "#b8860b",
    "Very Good": "#43a047",
    "Excellent": "#1e88e5",
}

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class CreditScoreApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("iScore Dashboard")
        self.geometry("900x680")
        self.resizable(True, True)
        self.configure(fg_color="#ffe6f0")  # light pink background

        self.selected_user_id = None
        self.users = []

        self.icons = {}
        self.load_icons()

        self.build_ui()
        self.load_users()

    def load_icons(self):
        files = {
            "calculate": "Calculate_iScore.png",
            "add": "Add_User.png",
            "delete": "Delete_User.png",
            "export": "Export_CSV.png",
        }
        for key, filename in files.items():
            self.icons[key] = ctk.CTkImage(
                Image.open(RESOURCES_DIR / filename), size=(20, 20)
            )

    def build_ui(self):
        self.header = ctk.CTkLabel(
            self,
            text="Credit Score Dashboard 💖",
            font=("Segoe UI", 24, "bold"),
            text_color="#d81b60",
        )
        self.header.pack(pady=20)

        self.user_combo = ctk.CTkComboBox(
            self, width=300, state="readonly", command=self.on_user_selected
        )
        self.user_combo.pack(pady=10)

        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(pady=15)

        self.calc_btn = ctk.CTkButton(
            self.btn_frame,
            text="Calculate iScore",
            image=self.icons["calculate"],
            command=self.calculate_score,
            corner_radius=20,
            fg_color="#f48fb1",
            text_color="white",
            compound="left",
            width=150,
        )
        self.calc_btn.grid(row=0, column=0, padx=8)

        self.add_btn = ctk.CTkButton(
            self.btn_frame,
            text="Add User",
            image=self.icons["add"],
            command=self.add_user_popup,
            corner_radius=20,
            fg_color="#ce93d8",
            text_color="white",
            compound="left",
            width=120,
        )
        self.add_btn.grid(row=0, column=1, padx=8)

        self.delete_btn = ctk.CTkButton(
            self.btn_frame,
            text="Delete User",
            image=self.icons["delete"],
            command=self.delete_user,
            corner_radius=20,
            fg_color="#ef9a9a",
            text_color="white",
            compound="left",
            width=130,
        )
        self.delete_btn.grid(row=0, column=2, padx=8)

        self.export_btn = ctk.CTkButton(
            self.btn_frame,
            text="Export CSV",
            image=self.icons["export"],
            command=self.export_csv,
            corner_radius=20,
            fg_color="#81d4fa",
            text_color="white",
            compound="left",
            width=130,
        )
        self.export_btn.grid(row=0, column=3, padx=8)

        self.result_label = ctk.CTkLabel(self, text="", font=("Segoe UI", 16, "bold"))
        self.result_label.pack(pady=15)

        self.chart_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.chart_frame.pack()

        self.status = ctk.CTkLabel(
            self, text="", font=("Segoe UI", 12), text_color="#888888"
        )
        self.status.pack(pady=5)

    def load_users(self):
        try:
            self.users = user_db.get_all_users()
        except DatabaseError as e:
            self.users = []
            messagebox.showerror("Database error", str(e))
        values = [f"{u['user_id']} - {u['full_name']}" for u in self.users]
        self.user_combo.configure(values=values)
        # The list was rebuilt, so forget the old selection instead of acting
        # on a user the combo box no longer shows.
        self.selected_user_id = None
        self.user_combo.set("Select a user" if values else "No users found")

    def on_user_selected(self, choice):
        self.selected_user_id = int(choice.split(" - ")[0])

    def clear_result(self):
        self.result_label.configure(text="")
        self.status.configure(text="")
        for widget in self.chart_frame.winfo_children():
            widget.destroy()

    def calculate_score(self):
        if self.selected_user_id is None:
            messagebox.showwarning("Missing", "Please select a user.")
            return

        try:
            details = user_db.get_user_by_id(self.selected_user_id)
            if details is None:
                messagebox.showwarning("Not found", "That user no longer exists.")
                self.load_users()
                self.clear_result()
                return
            result = score_user(self.selected_user_id)
        except (DatabaseError, InvalidRecordError) as e:
            messagebox.showerror("Could not calculate iScore", str(e))
            return

        score = result.iscore
        band, color = self.interpret_score(score)
        self.result_label.configure(
            text=f"{details['full_name']} → Score: {score:.2f} — {band}",
            text_color=color,
        )
        self.render_gauge(score, color)
        status = f"iScore calculated for {details['full_name']}"
        if result.missing:
            status += f" (no data for {', '.join(result.missing)}; counted as 0)"
        self.status.configure(text=status)

    def render_gauge(self, score, color):
        for widget in self.chart_frame.winfo_children():
            widget.destroy()

        # Setup figure and axis
        fig, ax = plt.subplots(figsize=(5, 2.5), subplot_kw={"aspect": "equal"})
        fig.patch.set_facecolor("#ffe6f0")
        ax.set_facecolor("#ffe6f0")
        ax.axis("off")

        # Gauge range
        background = Wedge(
            center=(0, 0), r=1, theta1=0, theta2=180, width=0.3, facecolor="#eeeeee"
        )
        ax.add_patch(background)

        # Calculate percentage and arc
        percent = max(0, min((score - 300) / 550, 1))
        theta2 = 180 * percent
        arc = Wedge(
            center=(0, 0), r=1, theta1=0, theta2=theta2, width=0.3, facecolor=color
        )
        ax.add_patch(arc)

        # Score in center
        ax.text(
            0,
            -0.1,
            f"{int(score)}",
            fontsize=22,
            ha="center",
            va="center",
            fontweight="bold",
            color=color,
        )

        # Hide all spines and ticks
        ax.set_xlim(-1.2, 1.2)
        ax.set_ylim(-0.2, 1.2)

        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack()
        plt.close(fig)

    def add_user_popup(self):
        name = simpledialog.askstring("Add User", "Full name:", parent=self)
        if name is None:
            return
        nid = simpledialog.askstring("Add User", "National ID:", parent=self)
        if nid is None:
            return

        try:
            new_id = user_db.add_user(name, nid)
        except ValidationError as e:
            messagebox.showwarning("Invalid input", str(e))
            return
        except DatabaseError as e:
            messagebox.showerror("Error", str(e))
            return
        messagebox.showinfo("Success", f"User added with ID {new_id}.")
        self.load_users()

    def delete_user(self):
        if self.selected_user_id is None:
            messagebox.showwarning(
                "Select a user first", "You must choose a user to delete."
            )
            return

        user_id = self.selected_user_id
        confirm = messagebox.askyesno(
            "Delete?", f"Delete user ID {user_id} and all of their credit records?"
        )
        if not confirm:
            return
        try:
            deleted = user_db.delete_user(user_id)
        except DatabaseError as e:
            messagebox.showerror("Error", str(e))
            return
        if deleted:
            messagebox.showinfo("Deleted", "User deleted.")
        else:
            messagebox.showwarning("Not found", "That user was already deleted.")
        self.load_users()
        self.clear_result()

    def export_csv(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv")
        if not file_path:
            return

        try:
            with open(file_path, mode="w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["User ID", "Full Name", "Score", "Band"])
                for u in self.users:
                    score = calculate_iScore(u["user_id"])
                    band, _ = self.interpret_score(score)
                    writer.writerow([u["user_id"], u["full_name"], score, band])
            messagebox.showinfo("Exported", "CSV exported successfully.")
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))

    def interpret_score(self, score):
        band = score_band(score)
        return band, BAND_COLORS[band]


def launch_gui():
    app = CreditScoreApp()
    app.mainloop()
