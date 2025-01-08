import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import time
import socket



def send_request_login(request):
    str = ""
    server_address = ('localhost', 1234)

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client_socket.connect(server_address)
        client_socket.send(request.encode())
        response = client_socket.recv(1024).decode()
        str = response
        process_response(response)
    except ConnectionRefusedError:
        messagebox.showerror("Connection Error", "Connection refused. Make sure the server is running.")
    finally:
        client_socket.close()
        return str


def send_request(request):
    server_address = ('localhost', 1234)

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client_socket.connect(server_address)
        client_socket.send(request.encode())
        response = client_socket.recv(1024).decode()
        if response:
            process_response(response)
    except ConnectionRefusedError:
        messagebox.showerror("Connection Error", "Connection refused. Make sure the server is running.")
    finally:
        client_socket.close()


def process_response(response):
    messagebox.showinfo("Server Response", response)


class Disk:
    def __init__(self, color, width):
        self.color = color
        self.width = width


class HanoiTowerApp:
    def __init__(self, login):
        self.crntClientLogin = login
        self.hours = 0
        self.minutes = 0
        self.seconds = 0

        self.master = tk.Tk()
        self.master.title("Ханойська вежа")
        self.master.state("zoomed")  
        self.master.config(background="#3e2723")  

        self.canvas = tk.Canvas(self.master, background="#f7f2c6")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.button = tk.Button(self.master, text="Старт", command=self.start_game, background="#cfd8dc", fg="black", font=("Helvetica", 14, "bold"))
        self.button.pack(pady=10)

        self.timer_label = tk.Label(self.master, text="00:00:00", background="#f0f0f0", font=("Helvetica", 16, "bold"))
        self.timer_label.pack(pady=10)

        self.button_exit = tk.Button(self.master, text="Вихід із гри", command=self.exit_game, background="#e57373", fg="white", font=("Helvetica", 14, "bold"))
        self.button_exit.pack(pady=10)

        self.green = Disk('#79aee0', 150)
        self.blue = Disk('#50f283', 130)
        self.yellow = Disk('#d0a6f2', 100)
        self.purple = Disk('#f1f772', 80)
        self.red = Disk('#db5a5a', 50)

        self.towers = [[self.green, self.blue, self.yellow, self.purple], [], []]
        self.chosenDisk = None
        self.start_time = None
        self.timer_running = False

        self.master.bind('<Configure>', self.resize)
        self.tower_positions = []

    def start_game(self):
     if not self.timer_running:
        self.canvas.bind('<Button-1>', self.left_click)
        # Переміщаємо всі диски на перший стрижень
        self.towers = [[self.green, self.blue, self.yellow, self.purple], [], []]
        self.chosenDisk = None
        self.fromTower = None

        # Оновлюємо  відображення стрижнів
        self.update_tower_positions()
        self.draw_towers()

        # Скиндаємо таймер
        self.start_time = time.time()
        self.hours, self.minutes, self.seconds = 0, 0, 0
        self.timer_label.config(text="00:00:00")
        self.timer_running = True
        self.master.after(1000, self.update_timer)


    def exit_game(self):
        self.master.destroy() 
        login_window()

    def update_timer(self):
        if self.start_time is not None:
            current_time = time.time() - self.start_time
            self.hours = int(current_time / 3600)
            self.minutes = int((current_time % 3600) / 60)
            self.seconds = int(current_time % 60)
            timer_text = f"{self.hours:02}:{self.minutes:02}:{self.seconds:02}"
            self.timer_label.config(text=timer_text)
            self.master.after(1000, self.update_timer)

    def update_tower_positions(self):
        canvas_width = self.canvas.winfo_width()
        self.tower_positions = [
            canvas_width * 0.2,
            canvas_width * 0.5,
            canvas_width * 0.8
        ]

    def draw_towers(self):
        self.canvas.delete("all")

        base_y = self.canvas.winfo_height() * 0.8
        tower_width = 30
        tower_height = self.canvas.winfo_height() * 0.6
        disk_height = 40

        for x in self.tower_positions:
            self.canvas.create_rectangle(x - tower_width / 2, base_y - tower_height,
                                         x + tower_width / 2, base_y, fill="gray")

        for i, tower in enumerate(self.towers):
            tower_x = self.tower_positions[i]
            current_y = base_y
            for disk in tower:
                self.canvas.create_rectangle(tower_x - disk.width, current_y - disk_height,
                                             tower_x + disk.width, current_y, fill=disk.color)
                current_y -= disk_height

    def left_click(self, event):
        x = event.x
        if not self.chosenDisk:
            self.fromTower = self.get_tower_from_coordinates(x)
            if self.fromTower is not None and self.towers[self.fromTower]:
                self.chosenDisk = self.towers[self.fromTower].pop()
        else:
            toTower = self.get_tower_from_coordinates(x)
            if toTower is not None and self.is_valid_move(toTower):
                self.towers[toTower].append(self.chosenDisk)
                if self.has_player_won():
                    self.stop_timer()

                    request = f"end {self.crntClientLogin} {self.hours} {self.minutes} {self.seconds}"
                    send_request(request)

            else:
                self.towers[self.fromTower].append(self.chosenDisk)
            self.chosenDisk = None
            self.fromTower = None

        self.draw_towers()

    def get_tower_from_coordinates(self, x):
        for i, position in enumerate(self.tower_positions):
            if abs(x - position) < self.canvas.winfo_width() * 0.1:
                return i
        return None

    def is_valid_move(self, toTower):
        for disk in self.towers[toTower]:
            if disk.width < self.chosenDisk.width:
                return False
        return True

    def has_player_won(self):
        return len(self.towers[1]) == 5 or len(self.towers[2]) == 5

    def stop_timer(self):
        self.start_time = None
        self.timer_running = False

    def resize(self, event):
        self.update_tower_positions()
        self.draw_towers()

    def run(self):
        self.master.mainloop()


def create_account_window():
    def register():
        username = username_entry.get()
        password = password_entry.get()
        request = f"reg {username} {password}"
        send_request(request)

    root = tk.Tk()
    root.title("Реєстрація")
    root.state("normal")  
    root.config(background="#3e2723")  

    header_label = tk.Label(
        root,
        text="Реєстрація нового користувача",
        background="#3e2723",
        foreground="#ffffff",
        font=("Helvetica", 24, "bold"),
        pady=20
    )
    header_label.pack()

    content_frame = ttk.Frame(root, padding=50, style="TFrame")
    content_frame.pack(fill="both", expand=True)

   
    style = ttk.Style()
    style.configure("TLabel", background="#3e2723", foreground="#ffffff", font=("Helvetica", 16))
    style.configure("TButton", font=("Helvetica", 14), padding=10)
    style.map("TButton", background=[("active", "#37474F")], foreground=[("active", "#ffffff")])
    style.configure("TEntry", font=("Helvetica", 14), padding=10, width=30, relief="solid", background="#ffffff")
    style.configure("TFrame", background="#f7f2c6")  

    username_label = ttk.Label(content_frame, text="Ім'я користувача:")
    username_label.pack(pady=10)
    username_entry = ttk.Entry(content_frame, style="TEntry")
    username_entry.pack(pady=10)

    password_label = ttk.Label(content_frame, text="Пароль:")
    password_label.pack(pady=10)
    password_entry = ttk.Entry(content_frame, show="*", style="TEntry")
    password_entry.pack(pady=10)

    register_button = ttk.Button(content_frame, text="Зареєструватися", command=register)
    register_button.pack(pady=20)

    footer_label = tk.Label(
        root,
        text=" © 2024",
        background="#3e2723",
        foreground="#b0bec5",
        font=("Helvetica", 12),
        pady=20
    )
    footer_label.pack(side="bottom")

    root.mainloop()

def login_window():
    def login(crnt_window):
        username = username_entry.get()
        password = password_entry.get()
        
        request = f"log {username} {password}"
        str = send_request_login(request)

        if str == "Login was successful!":
         crnt_window.destroy()
         app = HanoiTowerApp(username)
         messagebox.showinfo("Welcome!", f"Welcome {username}! Good Luck!")
         app.run()
         login_window()

    def create_account():
        create_account_window()

    root = tk.Tk()
    root.title("Вхід")
    root.state("zoomed")  
    root.config(background="#3e2723")  

    
    header_label = tk.Label(
        root,
        text="Ласкаво просимо! Увійдіть до системи",
        background="#3e2723",
        foreground="#ffffff",
        font=("Helvetica", 24, "bold"),
        pady=20
    )
    header_label.pack()

    
    content_frame = ttk.Frame(root, padding=50, style="TFrame")
    content_frame.pack(fill="both", expand=True)

    
    style = ttk.Style()
    style.configure("TLabel", background="#3e2723", foreground="#ffffff", font=("Helvetica", 16))
    style.configure("TButton", font=("Helvetica", 14), padding=10)
    style.map("TButton", background=[("active", "#37474F")], foreground=[("active", "#ffffff")])
    style.configure("TFrame", background="#f7f2c6") 

    username_label = ttk.Label(content_frame, text="Ім'я користувача:")
    username_label.pack(pady=10)
    username_entry = ttk.Entry(content_frame, font=("Helvetica", 14), width=30)
    username_entry.pack(pady=10)

    password_label = ttk.Label(content_frame, text="Пароль:")
    password_label.pack(pady=10)
    password_entry = ttk.Entry(content_frame, show="*", font=("Helvetica", 14), width=30)
    password_entry.pack(pady=10)

    login_button = ttk.Button(content_frame, text="Увійти", command=lambda: login(root))
    login_button.pack(pady=20)

    create_account_button = ttk.Button(content_frame, text="Немає облікового запису?", command=create_account)
    create_account_button.pack(pady=10)

   
    footer_label = tk.Label(
        root,
        text=" © 2025",
        background="#3e2723",
        foreground="#b0bec5",
        font=("Helvetica", 12),
        pady=20
    )
    footer_label.pack(side="bottom")

    root.mainloop()

if __name__ == '__main__':
    login_window()