import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class CSVViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CSV Viewer with Charts")

        self.df = None

        # Buttons
        self.load_button = tk.Button(root, text="Load CSV", command=self.load_csv)
        self.load_button.pack(pady=5)

        self.show_chart_button = tk.Button(root, text="Show Chart", command=self.show_chart)
        self.show_chart_button.pack(pady=5)

        self.search_label = tk.Label(root, text="Search:")
        self.search_label.pack(pady=5)

        self.search_entry = tk.Entry(root)
        self.search_entry.pack(pady=5)

        self.search_button = tk.Button(root, text="Search", command=self.search_data)
        self.search_button.pack(pady=5)

        # Table
        self.text = tk.Text(root, height=20, width=100)
        self.text.pack(pady=10)

    def load_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if file_path:
            try:
                self.df = pd.read_csv(file_path)
                self.show_data(self.df)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load CSV:\n{e}")

    def show_data(self, df):
        self.text.delete("1.0", tk.END)
        self.text.insert(tk.END, df.to_string())

    def show_chart(self):
        if self.df is not None:
            try:
                fig, ax = plt.subplots(figsize=(6, 4))
                self.df.hist(ax=ax)
                plt.tight_layout()

                chart_window = tk.Toplevel(self.root)
                chart_window.title("Chart")

                canvas = FigureCanvasTkAgg(fig, master=chart_window)
                canvas.draw()
                canvas.get_tk_widget().pack()

            except Exception as e:
                messagebox.showerror("Error", f"Failed to generate chart:\n{e}")
        else:
            messagebox.showwarning("Warning", "Please load a CSV first!")

    def search_data(self):
        if self.df is not None:
            query = self.search_entry.get().lower()
            if query:
                filtered = self.df[self.df.apply(lambda row: row.astype(str).str.lower().str.contains(query).any(), axis=1)]
                self.show_data(filtered)
            else:
                self.show_data(self.df)
        else:
            messagebox.showwarning("Warning", "Please load a CSV first!")

if __name__ == "__main__":
    root = tk.Tk()
    app = CSVViewerApp(root)
    root.mainloop()
