import math
import sqlite3
import sys

try:
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.patches import Polygon
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

# ==========================================
# 1. DATABASE SETUP
# ==========================================
def init_db():
    conn = sqlite3.connect("lpp_optimizer.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS problems (
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, 
        objective TEXT, p REAL, q REAL, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS constraints (
        id INTEGER PRIMARY KEY AUTOINCREMENT, problem_id INTEGER, 
        a REAL, b REAL, sign TEXT, k REAL)''')
    conn.commit()
    conn.close()

def save_problem(title, objective, p, q, constraints):
    conn = sqlite3.connect("lpp_optimizer.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO problems (title, objective, p, q) VALUES (?, ?, ?, ?)", (title, objective, p, q))
    pid = cursor.lastrowid
    for a, b, sign, k in constraints:
        cursor.execute("INSERT INTO constraints (problem_id, a, b, sign, k) VALUES (?, ?, ?, ?, ?)", (pid, a, b, sign, k))
    conn.commit()
    conn.close()

# ==========================================
# 2. LPP SOLVER ENGINE (Corner Point Method)
# ==========================================
def intersect(c1, c2):
    a1, b1, _, k1 = c1
    a2, b2, _, k2 = c2
    d = a1 * b2 - a2 * b1
    if abs(d) < 1e-9: return None
    return ((k1 * b2 - k2 * b1) / d, (a1 * k2 - a2 * k1) / d)

def is_feasible(pt, constraints):
    x, y = pt
    for a, b, sign, k in constraints:
        v = a * x + b * y
        if sign == "<=" and v > k + 1e-7: return False
        if sign == ">=" and v < k - 1e-7: return False
        if sign == "=" and abs(v - k) > 1e-7: return False
    return True

def solve_lpp(objective, p_coef, q_coef, constraints):
    full_c = list(constraints) + [(1, 0, ">=", 0), (0, 1, ">=", 0)]
    points = []
    n = len(full_c)
    
    for i in range(n):
        for j in range(i + 1, n):
            pt = intersect(full_c[i], full_c[j])
            if pt:
                rnd = (round(pt[0], 5), round(pt[1], 5))
                if is_feasible(rnd, full_c):
                    if not any(math.isclose(rnd[0], ex[0], abs_tol=1e-4) and 
                               math.isclose(rnd[1], ex[1], abs_tol=1e-4) for ex in points):
                        points.append(rnd)

    if not points:
        return {"status": "No Feasible Solution", "points": [], "optimal": None}

    evaluated = [(pt, p_coef * pt[0] + q_coef * pt[1]) for pt in points]
    optimal = max(evaluated, key=lambda x: x[1]) if objective.upper() == "MAX" else min(evaluated, key=lambda x: x[1])
    return {"status": "Success", "points": evaluated, "optimal": optimal}

# ==========================================
# 3. GRAPH VISUALIZATION & SHADING
# ==========================================
def sort_polygon(pts):
    if not pts: return []
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    return sorted(pts, key=lambda p: math.atan2(p[1] - cy, p[0] - cx))

def plot_feasible_region(constraints, points, optimal_pt):
    if not HAS_MATPLOTLIB:
        print("\n[Note] Matplotlib not installed. Run 'pip install matplotlib numpy'.")
        return

    plt.figure(figsize=(8, 8))
    pts_only = [p[0] for p in points]
    max_x = max([p[0] for p in pts_only] + [10]) * 1.4
    max_y = max([p[1] for p in pts_only] + [10]) * 1.4
    
    x = np.linspace(0, max_x, 400)
    for a, b, sign, k in constraints:
        if b != 0:
            plt.plot(x, (k - a * x) / b, label=f"{a}x + {b}y {sign} {k}")
        else:
            plt.axvline(x=k/a, label=f"x {sign} {k/a}")

    # Shade Feasible Polygon Region
    if len(pts_only) >= 3:
        poly_pts = sort_polygon(pts_only)
        plt.gca().add_patch(Polygon(poly_pts, color='skyblue', alpha=0.4, label='Feasible Region'))

    # Mark Corner Points & Optimal Point
    plt.scatter([p[0] for p in pts_only], [p[1] for p in pts_only], color="red", zorder=5)
    if optimal_pt:
        opt_x, opt_y = optimal_pt[0]
        plt.scatter([opt_x], [opt_y], color="gold", s=220, marker="*", zorder=6, label=f"Optimal ({opt_x}, {opt_y})")

    plt.xlim(0, max_x)
    plt.ylim(0, max_y)
    plt.xlabel("Variable x")
    plt.ylabel("Variable y")
    plt.title("LPP Feasible Region & Corner Points")
    plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    print("\n📊 Displaying graph window...")
    plt.show()

# ==========================================
# 4. TEMPLATES & CLI
# ==========================================
def display_results(title, obj, p, q, constraints, result):
    print("\n" + "="*50 + f"\n PROBLEM: {title}\n Objective: {obj} Z = {p}x + {q}y\n" + "="*50)
    if result["status"] == "No Feasible Solution":
        print("❌ No feasible solution found."); return

    print(f"{'Corner Point':<18} | {'Z Value':<10}")
    print("-" * 32)
    for pt, z in result["points"]:
        print(f"{str(pt):<18} | {z:<10.2f}{' <-- OPTIMAL' if pt == result['optimal'][0] else ''}")

    opt_pt, opt_z = result["optimal"]
    print(f"\n✅ Optimal Solution: x = {opt_pt[0]}, y = {opt_pt[1]} | Max/Min Z = {opt_z:.2f}")
    save_problem(title, obj, p, q, constraints)
    
    if input("\nDisplay graph visualization? (y/n): ").strip().lower() == 'y':
        plot_feasible_region(constraints, result["points"], result["optimal"])

def main_menu():
    init_db()
    while True:
        print("\n==============================\n    LPP OPTIMIZER TOOLKIT     \n==============================")
        print("1. Solve Custom LPP\n2. Factory Template (Max Profit)\n3. Investment Template\n4. View History\n5. Exit")
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == '1':
            title = input("Title: "); obj = input("Objective (MAX/MIN): ").upper()
            p = float(input("Coefficient p: ")); q = float(input("Coefficient q: "))
            constraints = []
            print("Enter constraints as 'a b sign k' (e.g. 2 1 <= 100). Type 'done':")
            while True:
                line = input("> ").strip()
                if line.lower() == 'done': break
                parts = line.split()
                if len(parts) == 4: constraints.append((float(parts[0]), float(parts[1]), parts[2], float(parts[3])))
            display_results(title, obj, p, q, constraints, solve_lpp(obj, p, q, constraints))
        elif choice == '2':
            constraints = [(2, 1, "<=", 100), (1, 1, "<=", 80)]
            display_results("Factory Production", "MAX", 40, 30, constraints, solve_lpp("MAX", 40, 30, constraints))
        elif choice == '3':
            constraints = [(1, 1, "<=", 100000), (0, 1, "<=", 60000), (1, 0, ">=", 10000)]
            display_results("Investment Portfolio", "MAX", 0.08, 0.15, constraints, solve_lpp("MAX", 0.08, 0.15, constraints))
        elif choice == '4':
            conn = sqlite3.connect("lpp_optimizer.db"); rows = conn.cursor().execute("SELECT title, objective, p, q FROM problems").fetchall(); conn.close()
            print("\n--- History ---")
            for r in rows: print(f"Title: {r[0]} | Obj: {r[1]} (Z = {r[2]}x + {r[3]}y)")
        elif choice == '5':
            sys.exit(0)

if __name__ == "__main__":
    main_menu()
