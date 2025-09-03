# scientific_calculator.py
"""
Scientific Calculator — single-file Tkinter app.
Safe expression evaluation via AST + math functions.
Features:
 - Basic ops: + - * / % ** parentheses
 - Scientific: sin, cos, tan, asin, acos, atan, log, ln, sqrt, exp, factorial
 - Memory (M+, M-, MR, MC), history, keyboard support
 - Clear / backspace / +/- toggle
"""

import math, ast, operator, tkinter as tk
from tkinter import messagebox, simpledialog

# Allowed names mapped to math functions/constants
SAFE_FUNCS = {
    'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
    'asin': math.asin, 'acos': math.acos, 'atan': math.atan,
    'sinh': math.sinh, 'cosh': math.cosh, 'tanh': math.tanh,
    'log': lambda x, b=10: math.log(x, b) if b!=None else math.log10(x),
    'ln': math.log,
    'sqrt': math.sqrt, 'exp': math.exp, 'pow': pow,
    'abs': abs, 'fact': math.factorial, 'factorial': math.factorial,
    'pi': math.pi, 'e': math.e
}

# Allowed AST nodes
ALLOWED_NODES = {
    ast.Expression, ast.UnaryOp, ast.BinOp, ast.Call, ast.Name,
    ast.Load, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod,
    ast.USub, ast.UAdd, ast.Num, ast.Tuple
}

def safe_eval(expr):
    """
    Parse expr into AST and evaluate with a restricted environment.
    Supports function calls from SAFE_FUNCS and numeric operations.
    """
    expr = expr.replace('^', '**')
    node = ast.parse(expr, mode='eval')
    for n in ast.walk(node):
        if not isinstance(n, tuple(ALLOWED_NODES)):
            raise ValueError(f"Disallowed expression: {type(n).__name__}")
        # Prevent name attributes other than allowed funcs/constants
        if isinstance(n, ast.Name) and n.id not in SAFE_FUNCS and not n.id.isidentifier():
            raise ValueError(f"Unknown identifier: {n.id}")

    def _eval(n):
        if isinstance(n, ast.Expression):
            return _eval(n.body)
        if isinstance(n, ast.Num):
            return n.n
        if isinstance(n, ast.UnaryOp):
            val = _eval(n.operand)
            return -val if isinstance(n.op, ast.USub) else +val
        if isinstance(n, ast.BinOp):
            a = _eval(n.left); b = _eval(n.right)
            if isinstance(n.op, ast.Add): return operator.add(a, b)
            if isinstance(n.op, ast.Sub): return operator.sub(a, b)
            if isinstance(n.op, ast.Mult): return operator.mul(a, b)
            if isinstance(n.op, ast.Div): return operator.truediv(a, b)
            if isinstance(n.op, ast.Pow): return operator.pow(a, b)
            if isinstance(n.op, ast.Mod): return operator.mod(a, b)
        if isinstance(n, ast.Call):
            func = n.func
            if isinstance(func, ast.Name) and func.id in SAFE_FUNCS:
                args = [_eval(a) for a in n.args]
                return SAFE_FUNCS[func.id](*args)
            raise ValueError(f"Unsafe call: {ast.dump(func)}")
        if isinstance(n, ast.Name):
            if n.id in SAFE_FUNCS:
                val = SAFE_FUNCS[n.id]
                if callable(val):
                    raise ValueError(f"Function {n.id} needs arguments")
                return val
        if isinstance(n, ast.Tuple):
            return tuple(_eval(elt) for elt in n.elts)
        raise ValueError("Unsupported expression")
    return _eval(node)

# GUI
class SciCalc(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Scientific Calculator")
        self.geometry("420x560")
        self.resizable(False, False)
        self.memory = 0.0
        self.history = []
        self._build_ui()
        self.bind_keys()

    def _build_ui(self):
        self.display = tk.Entry(self, font=("Consolas", 20), bd=4, relief=tk.RIDGE, justify='right')
        self.display.insert(0, "0")
        self.display.grid(row=0, column=0, columnspan=6, sticky="nsew", padx=6, pady=6, ipady=10)

        btns = [
            ('MC',1,0),('MR',1,1),('M+',1,2),('M-',1,3),('Hist',1,4),('C',1,5),
            ('7',2,0),('8',2,1),('9',2,2),('/',2,3),('^',2,4),('<-',2,5),
            ('4',3,0),('5',3,1),('6',3,2),('*',3,3),('(',3,4),(')',3,5),
            ('1',4,0),('2',4,1),('3',4,2),('-',4,3),('pi',4,4),('e',4,5),
            ('0',5,0),('.',5,1),('%',5,2),('+',5,3),('±',5,4),('=',5,5),
            ('sin',6,0),('cos',6,1),('tan',6,2),('ln',6,3),('log',6,4),('sqrt',6,5),
            ('asin',7,0),('acos',7,1),('atan',7,2),('fact',7,3),('exp',7,4),('pow',7,5),
        ]
        for (text,r,c) in btns:
            cmd = lambda t=text: self.on_button(t)
            tk.Button(self, text=text, width=6, height=2, command=cmd, font=("Arial",12)).grid(row=r, column=c, padx=4, pady=4)

    def bind_keys(self):
        for k in "0123456789.+-*/()%":
            self.bind(k, lambda e, ch=k: self.insert_text(ch))
        self.bind('<Return>', lambda e: self.on_button('='))
        self.bind('<BackSpace>', lambda e: self.on_button('<-'))
        self.bind('<Escape>', lambda e: self.on_button('C'))

    def insert_text(self, s):
        cur = self.display.get()
        if cur == "0": self.display.delete(0, tk.END); cur = ""
        self.display.insert(tk.END, s)

    def on_button(self, key):
        if key == 'C':
            self.display.delete(0, tk.END); self.display.insert(0, "0")
        elif key == '<-':
            cur = self.display.get()
            if len(cur) <= 1:
                self.display.delete(0, tk.END); self.display.insert(0, "0")
            else:
                self.display.delete(len(cur)-1, tk.END)
        elif key == '=':
            expr = self.display.get()
            try:
                result = safe_eval(expr)
                self.history.append((expr, result))
                self.display.delete(0, tk.END); self.display.insert(0, str(result))
            except Exception as e:
                messagebox.showerror("Error", f"Could not evaluate: {e}")
        elif key == '±':
            cur = self.display.get()
            if cur.startswith('-'):
                self.display.delete(0); self.display.insert(0, cur[1:])
            else:
                self.display.delete(0, tk.END); self.display.insert(0, '-' + cur)
        elif key in ('M+', 'M-', 'MR', 'MC'):
            try:
                if key == 'M+':
                    self.memory += float(self.display.get())
                elif key == 'M-':
                    self.memory -= float(self.display.get())
                elif key == 'MR':
                    self.display.delete(0, tk.END); self.display.insert(0, str(self.memory))
                elif key == 'MC':
                    self.memory = 0.0
            except:
                messagebox.showinfo("Memory", "Memory operation failed")
        elif key == 'Hist':
            self.show_history()
        else:
            # insert function or character
            if key in SAFE_FUNCS and callable(SAFE_FUNCS[key]):
                self.insert_text(f"{key}(")
            else:
                self.insert_text(key)

    def show_history(self):
        if not self.history:
            messagebox.showinfo("History", "No history yet.")
            return
        s = "\n".join(f"{i+1}: {expr} = {res}" for i,(expr,res) in enumerate(self.history[-20:]))
        dlg = tk.Toplevel(self)
        dlg.title("History")
        tk.Text(dlg, width=50, height=20).pack(padx=8,pady=8)
        txt = dlg.children[list(dlg.children.keys())[0]]
        txt.insert('1.0', s); txt.config(state='disabled')

if __name__ == "__main__":
    SciCalc().mainloop()
