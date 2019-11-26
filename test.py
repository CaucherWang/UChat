import tkinter as tk


def hit_login():
    return True


def hit_register():
    return True


class LoginPage:
    def __init__(self, main_window):
        self.root = main_window
        self.canvas = tk.Frame(main_window, width=800, height=600)
        self.canvas.grid()
        self.canvas.pack_propagate(0)

        self.welcomeBar = tk.Label(self.canvas, text='Welcome to UChat', bg='grey', fg='pink', font=('Consolas', 22),
                                   width=30, height=2)
        self.welcomeBar.pack()
        tk.Label(self.canvas, text='User name:', font=('Arial', 14)).place(x=180, y=170)
        tk.Label(self.canvas, text='Password:', font=('Arial', 14)).place(x=180, y=210)
        var_usr_name = tk.StringVar()
        tk.Entry(self.canvas, textvariable=var_usr_name, show=None, font=('Arial', 14)).place(x=280, y=175)
        var_usr_pwd = tk.StringVar()
        tk.Entry(self.canvas, show='*', textvariable=var_usr_pwd, font=('Arial', 14)).place(x=280, y=215)

        tk.Button(self.canvas, text='登陆', font=('STFangsong', 18), width=10, height=1,
                  command=hit_login).place(x=280, y=250)
        tk.Button(self.canvas, text='注册', font=('STFangsong', 18), width=10, height=1,
                  command=hit_register).place(x=450, y=250)

class 
window = tk.Tk()
window.title('UChat_v1.0')
window.geometry('800x600')
LoginPage(window)
window.mainloop()
