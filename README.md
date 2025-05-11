# 💳 Credit Score Dashboard (iScore)

A smart, stylish Python-based GUI application to **calculate and visualize credit scores (iScore)** using data distributed across multiple relational databases. Built with `customtkinter`, `matplotlib`, and MySQL, this system offers a polished user experience, color-coded analytics, and full CRUD support.

---

## 🚀 Features

- 📊 **Modern Gauge Chart** (matplotlib): Live rendering of user iScore as a half-donut arc with color-coded performance bands.
- 🎨 **Beautiful Flutter-inspired UI**: Light pink theme with rounded buttons and intuitive icons.
- 👤 Add / Delete users directly from the GUI with instant refresh.
- 💾 Export scores and ratings to CSV for external use.
- 🔒 Private fields protected — national IDs are hidden from public views.
- ✅ Fully synced with a distributed database structure (users, payments, debt, history, mix).
- 🔁 Live user list refresh after updates.
- 🖱️ GUI built with `customtkinter` for a mobile-like desktop experience.

---

## 🏗️ Architecture

```
credit_score_project/
├── db/
│   └── connection.py, users.py, ...
├── logic/
│   └── calculator.py
├── gui/
│   └── GUI.py ← main app window
│   └── gui_run.py ← entrypoint script
├── resources/
│   └── icon and button images
├── requirements.txt
├── README.md
└── main.py
```

---

## 🧠 iScore Calculation Logic

Each user’s credit score is calculated based on weighted inputs from:

| Metric          | Weight  | Data Source (DB)    |
|-----------------|---------|---------------------|
| Payment History | 35%     | `payments_db`       |
| Credit Usage    | 30%     | `debt_db`           |
| Credit History  | 20%     | `history_db`        |
| Credit Mix      | 15%     | `mix_reference_db`  |

---

## 🖥️ Installation & Usage

### 1. Clone the repository

```bash
git clone https://github.com/1AyaNabil1/credit_score_project.git
cd credit_score_project
```

### 2. Setup environment

Using Conda:
```bash
conda create -n credit_env python=3.10
conda activate credit_env
pip install -r requirements.txt
```

### 3. Configure MySQL databases

Ensure these databases are running locally:
- `users_db`
- `payments_db`
- `debt_db`
- `history_db`
- `mix_reference_db`

Update credentials in `db/connection.py` if needed.

### 4. Launch GUI

```bash
python gui/gui_run.py
```

---

## 📂 Export Format

Exported `.csv` file includes:

- User ID
- Full Name
- Calculated iScore
- Score Band (e.g. Poor, Good)

---

## 🎨 Screenshots

| Dashboard Preview |
|-------------------|
| ![Preview](https://github.com/1AyaNabil1/credit_score_project/blob/main/img/img2.png) |

---

## 🤝 Contributing

Pull requests are welcome. For major changes, open an issue first to discuss the roadmap.

---

## 📄 License

MIT License — free to use, share, and adapt.

---

## 💡 Credits

Developed by the Aya Nabil @ Alexandria University
