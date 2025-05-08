import customtkinter as ctk
from tkinter import messagebox, simpledialog, filedialog
from db.users import get_all_users, get_user_by_id
from logic.calculator import calculate_iScore
from PIL import Image
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Wedge
import os
import csv

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
        base = "resources"
        self.icons["calculate"] = ctk.CTkImage(
            Image.open(os.path.join(base, "Calculate_iScore.png")), size=(20, 20)
        )
        self.icons["add"] = ctk.CTkImage(
            Image.open(os.path.join(base, "Add_User.png")), size=(20, 20)
        )
        self.icons["delete"] = ctk.CTkImage(
            Image.open(os.path.join(base, "Delete_User.png")), size=(20, 20)
        )
        self.icons["export"] = ctk.CTkImage(
            Image.open(os.path.join(base, "Export_CSV.png")), size=(20, 20)
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
        self.users = get_all_users()
        values = [f"{u['user_id']} - {u['full_name']}" for u in self.users]
        self.user_combo.configure(values=values)
        if values:
            self.user_combo.set("Select a user")

    def on_user_selected(self, choice):
        self.selected_user_id = int(choice.split(" - ")[0])

    def calculate_score(self):
        if not self.selected_user_id:
            messagebox.showwarning("Missing", "Please select a user.")
            return

        score = calculate_iScore(self.selected_user_id)
        details = get_user_by_id(self.selected_user_id)
        band, color = self.interpret_score(score)

        self.result_label.configure(
            text=f"{details['full_name']} → Score: {score:.2f} — {band}",
            text_color=color,
        )
        self.render_gauge(score, color)
        self.status.configure(text=f"iScore calculated for {details['full_name']}")

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
        name = simpledialog.askstring("Add User", "Full name:")
        if not name:
            return
        nid = simpledialog.askstring("Add User", "National ID:")
        if not nid:
            return

        from db.connection import get_all_connections

        conn = get_all_connections()["users"]
        try:
            cur = conn.cursor()
            cur.execute("SELECT MAX(user_id) FROM users")
            max_id = cur.fetchone()[0] or 0
            new_id = max_id + 1
            cur.execute(
                "INSERT INTO users (user_id, full_name, national_id) VALUES (%s, %s, %s)",
                (new_id, name, nid),
            )
            conn.commit()
            messagebox.showinfo("Success", f"User {name} added.")
            self.load_users()
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            cur.close()
            conn.close()

    def delete_user(self):
        if not self.selected_user_id:
            messagebox.showwarning(
                "Select a user first", "You must choose a user to delete."
            )
            return

        from db.connection import get_all_connections

        conn = get_all_connections()["users"]
        try:
            confirm = messagebox.askyesno(
                "Delete?", f"Delete user ID {self.selected_user_id}?"
            )
            if not confirm:
                return
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM users WHERE user_id = %s", (self.selected_user_id,)
            )
            conn.commit()
            messagebox.showinfo("Deleted", "User deleted.")
            self.load_users()
            self.result_label.configure(text="")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            cur.close()
            conn.close()

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
        if score < 580:
            return "Poor", "#e53935"
        elif score < 670:
            return "Fair", "#fb8c00"
        elif score < 740:
            return "Good", "#b8860b"
        elif score < 800:
            return "Very Good", "#43a047"
        else:
            return "Excellent", "#1e88e5"


def launch_gui():
    app = CreditScoreApp()
    app.mainloop()
