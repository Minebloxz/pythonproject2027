
import sys
import pygame
import numpy as np
import sympy as sp

# Initialize Pygame
pygame.init()

# Window Dimensions & Setup
WIDTH, HEIGHT = 1050, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Master Interactive Integral Calculator with Infinity")
clock = pygame.time.Clock()

# --- MODERN COLOR PALETTE ---
BG_COLOR = (18, 18, 24)
CARD_BG = (28, 28, 38)
PANEL_BG = (38, 38, 52)
TEXT_COLOR = (240, 240, 245)
TEXT_MUTED = (160, 160, 175)
ACCENT_COLOR = (0, 180, 216)
ACCENT_HOVER = (72, 202, 228)
SUCCESS_COLOR = (46, 196, 182)
HIGHLIGHT_COLOR = (255, 107, 107)
GRAPH_BG = (22, 22, 30)
GRID_COLOR = (50, 50, 68)
BTN_BG = (48, 48, 66)
BTN_HOVER = (68, 68, 90)
DANGER_BG = (140, 45, 55)
DANGER_HOVER = (180, 60, 70)

# Safe Linux-compatible fonts
FONT_SM = pygame.font.SysFont("Arial", 15)
FONT_MD = pygame.font.SysFont("Arial", 17, bold=True)
FONT_LG = pygame.font.SysFont("Arial", 22, bold=True)
FONT_TITLE = pygame.font.SysFont("Arial", 26, bold=True)

# Application States
STATE_MENU = 1
STATE_INPUT_FUNC = 2
STATE_INPUT_LOWER = 3
STATE_INPUT_UPPER = 4
STATE_RESULT = 5

current_state = STATE_MENU
calc_type = None  # 1 for Indefinite, 2 for Definite
user_input_str = ""
func_expr = None
indef_result_expr = None
lower_limit_val = 0.0
upper_limit_val = 0.0
result_text = ""
numeric_val = None


class Button:
  def __init__(self, x, y, w, h, text, action_value, bg=BTN_BG, hover_bg=BTN_HOVER):
    self.rect = pygame.Rect(x, y, w, h)
    self.text = text
    self.action_value = action_value
    self.bg = bg
    self.hover_bg = hover_bg

  def draw(self, surface):
    mouse_pos = pygame.mouse.get_pos()
    is_hovered = self.rect.collidepoint(mouse_pos)
    current_bg = self.hover_bg if is_hovered else self.bg
    pygame.draw.rect(surface, current_bg, self.rect, border_radius=8)
    pygame.draw.rect(surface, ACCENT_COLOR if is_hovered else (70, 70, 95), self.rect, 2, border_radius=8)

    txt_surf = FONT_MD.render(self.text, True, TEXT_COLOR)
    txt_rect = txt_surf.get_rect(center=self.rect.center)
    surface.blit(txt_surf, txt_rect)

  def is_clicked(self, event):
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
      return self.rect.collidepoint(event.pos)
    return False


# --- KEYPAD SETUP (Includes 'oo' for Infinity) ---
keypad_buttons = [
    # Row 1: Advanced Functions
    Button(40, 260, 75, 42, "sin", "sin("),
    Button(120, 260, 75, 42, "cos", "cos("),
    Button(200, 260, 75, 42, "tan", "tan("),
    Button(280, 260, 75, 42, "sqrt", "sqrt("),
    Button(360, 260, 75, 42, "log", "log("),
    Button(440, 260, 75, 42, "ln", "log("),
    
    # Row 2: Functions & Constants (Added 'oo' button here)
    Button(40, 310, 75, 42, "exp", "exp("),
    Button(120, 310, 75, 42, "abs", "Abs("),
    Button(200, 310, 75, 42, "pi", "pi"),
    Button(280, 310, 75, 42, "E", "E"),
    Button(360, 310, 75, 42, "oo", "oo"),      # Infinity Button
    Button(440, 310, 75, 42, "-oo", "-oo"),    # Negative Infinity Button

    # Row 3: Numbers & Operators
    Button(40, 365, 75, 42, "7", "7"),
    Button(120, 365, 75, 42, "8", "8"),
    Button(200, 365, 75, 42, "9", "9"),
    Button(280, 365, 75, 42, "/", "/"),
    Button(360, 365, 75, 42, "(", "("),
    Button(440, 365, 75, 42, ")", ")"),

    # Row 4
    Button(40, 415, 75, 42, "4", "4"),
    Button(120, 415, 75, 42, "5", "5"),
    Button(200, 415, 75, 42, "6", "6"),
    Button(280, 415, 75, 42, "*", "*"),
    Button(360, 415, 75, 42, "x", "x"),
    Button(440, 415, 75, 42, "**3", "**3"),

    # Row 5
    Button(40, 465, 75, 42, "1", "1"),
    Button(120, 465, 75, 42, "2", "2"),
    Button(200, 465, 75, 42, "3", "3"),
    Button(280, 465, 75, 42, "-", "-"),
    Button(360, 465, 75, 42, "+", "+"),
    Button(440, 465, 75, 42, "**2", "**2"),

    # Row 6
    Button(40, 515, 75, 42, "0", "0"),
    Button(120, 515, 75, 42, ".", "."),
    Button(200, 515, 155, 42, "C", "CLEAR", (100, 40, 50), (140, 50, 60)),
    Button(360, 515, 155, 42, "Back", "BACK", (80, 60, 40), (110, 80, 50)),
]

submit_btn = Button(40, 575, 475, 50, "Calculate Integral", "SUBMIT", ACCENT_COLOR, ACCENT_HOVER)

# Menu Buttons
menu_btn_indef = Button(325, 240, 400, 55, "1. Indefinite Integral", 1, PANEL_BG, BTN_HOVER)
menu_btn_def = Button(325, 315, 400, 55, "2. Definite Integral", 2, PANEL_BG, BTN_HOVER)
menu_btn_exit = Button(325, 390, 400, 55, "Exit Program", "EXIT", DANGER_BG, DANGER_HOVER)


def reset_inputs():
  global user_input_str
  user_input_str = ""


def handle_input_action(action):
  global user_input_str
  if action == "CLEAR":
    user_input_str = ""
  elif action == "BACK":
    user_input_str = user_input_str[:-1]
  else:
    user_input_str += action


def parse_limit_val(s):
  s_clean = s.strip().lower()
  if s_clean in ["oo", "inf", "infinity"]:
    return sp.oo
  elif s_clean in ["-oo", "-inf", "-infinity"]:
    return -sp.oo
  else:
    return sp.sympify(s_clean)


def draw_graph(surface, expr, lower, upper, is_indefinite=False, indef_expr=None):
  gx, gy, gw, gh = 540, 140, 480, 480
  pygame.draw.rect(surface, GRAPH_BG, (gx, gy, gw, gh), border_radius=12)
  pygame.draw.rect(surface, GRID_COLOR, (gx, gy, gw, gh), 2, border_radius=12)

  x = sp.Symbol("x")
  try:
    f_lambd = sp.lambdify(x, expr, "numpy")
    if is_indefinite and indef_expr:
      F_lambd = sp.lambdify(x, indef_expr, "numpy")
  except Exception:
    return

  # Handle plotting window boundaries gracefully if limits are infinite
  if is_indefinite:
    x_min, x_max = -6.0, 6.0
  else:
    low_f = float(lower.evalf()) if lower.is_number and not lower.has(sp.oo) and not lower.has(-sp.oo) else None
    upp_f = float(upper.evalf()) if upper.is_number and not upper.has(sp.oo) and not upper.has(-sp.oo) else None

    if low_f is not None and upp_f is not None:
      span = upp_f - low_f
      margin = span * 0.4 if span != 0 else 3.0
      x_min, x_max = low_f - margin, upp_f + margin
    elif low_f is not None:
      x_min, x_max = low_f - 2, low_f + 10
    elif upp_f is not None:
      x_min, x_max = upp_f - 10, upp_f + 2
    else:
      x_min, x_max = -10.0, 10.0

  x_vals = np.linspace(x_min, x_max, 400)
  try:
    y_vals = f_lambd(x_vals)
    if isinstance(y_vals, (int, float, np.number)):
      y_vals = np.full_like(x_vals, y_vals)
  except Exception:
    return

  y_min, y_max = np.nanmin(y_vals), np.nanmax(y_vals)
  if is_indefinite and indef_expr:
    try:
      y_vals_F = F_lambd(x_vals)
      if isinstance(y_vals_F, (int, float, np.number)):
        y_vals_F = np.full_like(x_vals, y_vals_F)
      y_min = min(y_min, np.nanmin(y_vals_F))
      y_max = max(y_max, np.nanmax(y_vals_F))
    except Exception:
      pass

  y_span = y_max - y_min if y_max != y_min else 2.0
  y_min -= y_span * 0.2
  y_max += y_span * 0.2

  def to_pixel(mx, my):
    px = gx + (mx - x_min) / (x_max - x_min) * gw
    py = gy + gh - (my - y_min) / (y_max - y_min) * gh
    return int(px), int(py)

  # Grid axes
  zero_x, zero_y = to_pixel(0, 0)
  if gy <= zero_y <= gy + gh:
    pygame.draw.line(surface, GRID_COLOR, (gx, zero_y), (gx + gw, zero_y), 1)
  if gx <= zero_x <= gx + gw:
    pygame.draw.line(surface, GRID_COLOR, (zero_x, gy), (zero_x, gy + gh), 1)

  # Shading area for finite portion of definite integral
  if not is_indefinite:
    l_plot = low_f if low_f is not None else x_min
    u_plot = upp_f if upp_f is not None else x_max
    shade_x = np.linspace(max(l_plot, x_min), min(u_plot, x_max), 150)
    try:
      shade_y = f_lambd(shade_x)
      if isinstance(shade_y, (int, float, np.number)):
        shade_y = np.full_like(shade_x, shade_y)

      points = [to_pixel(shade_x[0], 0)]
      for mx, my in zip(shade_x, shade_y):
        if not np.isnan(my) and np.isfinite(my):
          points.append(to_pixel(mx, my))
      points.append(to_pixel(shade_x[-1], 0))

      if len(points) > 2:
        shade_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.polygon(shade_surf, (0, 180, 216, 70), points)
        surface.blit(shade_surf, (0, 0))
    except Exception:
      pass

  # Draw Curve f(x)
  pixel_points = []
  for mx, my in zip(x_vals, y_vals):
    if not np.isnan(my) and np.isfinite(my):
      px, py = to_pixel(mx, my)
      if gy <= py <= gy + gh:
        pixel_points.append((px, py))

  if len(pixel_points) > 1:
    pygame.draw.aalines(surface, (72, 202, 228), False, pixel_points)

  # Draw Antiderivative Curve F(x) if Indefinite
  if is_indefinite and indef_expr:
    pixel_points_F = []
    try:
      for mx, my in zip(x_vals, y_vals_F):
        if not np.isnan(my) and np.isfinite(my):
          px, py = to_pixel(mx, my)
          if gy <= py <= gy + gh:
            pixel_points_F.append((px, py))
      if len(pixel_points_F) > 1:
        pygame.draw.aalines(surface, SUCCESS_COLOR, False, pixel_points_F)
    except Exception:
      pass

  # Limit markers for finite limits
  if not is_indefinite:
    if low_f is not None and x_min <= low_f <= x_max:
      lx, _ = to_pixel(low_f, 0)
      pygame.draw.line(surface, HIGHLIGHT_COLOR, (lx, gy), (lx, gy + gh), 2)
    if upp_f is not None and x_min <= upp_f <= x_max:
      ux, _ = to_pixel(upp_f, 0)
      pygame.draw.line(surface, SUCCESS_COLOR, (ux, gy), (ux, gy + gh), 2)


# --- MAIN EVENT LOOP ---
while True:
  screen.fill(BG_COLOR)

  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      pygame.quit()
      sys.exit()

    elif event.type == pygame.KEYDOWN:
      if event.key == pygame.K_ESCAPE:
        pygame.quit()
        sys.exit()

      if current_state in [STATE_INPUT_FUNC, STATE_INPUT_LOWER, STATE_INPUT_UPPER]:
        if event.key == pygame.K_RETURN:
          x = sp.Symbol("x")
          if current_state == STATE_INPUT_FUNC:
            try:
              func_expr = sp.sympify(user_input_str)
              if calc_type == 1:
                res = sp.integrate(func_expr, x)
                if isinstance(res, sp.Integral):
                  result_text = "Result: Not possible symbolically"
                  indef_result_expr = None
                else:
                  result_text = f"∫ f(x) dx = {res} + C"
                  indef_result_expr = res
                current_state = STATE_RESULT
              else:
                current_state = STATE_INPUT_LOWER
                reset_inputs()
            except Exception:
              result_text = "Parsing Error! Try again."
          elif current_state == STATE_INPUT_LOWER:
            try:
              lower_limit_val = parse_limit_val(user_input_str)
              current_state = STATE_INPUT_UPPER
              reset_inputs()
            except Exception:
              pass
          elif current_state == STATE_INPUT_UPPER:
            try:
              upper_limit_val = parse_limit_val(user_input_str)
              exact_ans = sp.integrate(func_expr, (x, lower_limit_val, upper_limit_val))
              numeric_val = float(exact_ans.evalf())
              result_text = f"Area: {numeric_val:.4f} sq. units"
              current_state = STATE_RESULT
            except Exception:
              result_text = "Error evaluating limits or improper integral."
        elif event.key == pygame.K_BACKSPACE:
          user_input_str = user_input_str[:-1]
        else:
          user_input_str += event.unicode

      elif current_state == STATE_RESULT:
        if event.key == pygame.K_r or event.key == pygame.K_RETURN:
          current_state = STATE_MENU
          reset_inputs()

    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
      if current_state == STATE_MENU:
        if menu_btn_indef.is_clicked(event):
          calc_type = 1
          current_state = STATE_INPUT_FUNC
          reset_inputs()
        elif menu_btn_def.is_clicked(event):
          calc_type = 2
          current_state = STATE_INPUT_FUNC
          reset_inputs()
        elif menu_btn_exit.is_clicked(event):
          pygame.quit()
          sys.exit()

      elif current_state in [STATE_INPUT_FUNC, STATE_INPUT_LOWER, STATE_INPUT_UPPER]:
        for btn in keypad_buttons:
          if btn.is_clicked(event):
            handle_input_action(btn.action_value)
        if submit_btn.is_clicked(event):
          x = sp.Symbol("x")
          if current_state == STATE_INPUT_FUNC:
            try:
              func_expr = sp.sympify(user_input_str)
              if calc_type == 1:
                res = sp.integrate(func_expr, x)
                if isinstance(res, sp.Integral):
                  result_text = "Result: Not possible symbolically"
                  indef_result_expr = None
                else:
                  result_text = f"∫ f(x) dx = {res} + C"
                  indef_result_expr = res
                current_state = STATE_RESULT
              else:
                current_state = STATE_INPUT_LOWER
                reset_inputs()
            except Exception:
              result_text = "Parsing Error!"
          elif current_state == STATE_INPUT_LOWER:
            try:
              lower_limit_val = parse_limit_val(user_input_str)
              current_state = STATE_INPUT_UPPER
              reset_inputs()
            except Exception:
              pass
          elif current_state == STATE_INPUT_UPPER:
            try:
              upper_limit_val = parse_limit_val(user_input_str)
              exact_ans = sp.integrate(func_expr, (x, lower_limit_val, upper_limit_val))
              numeric_val = float(exact_ans.evalf())
              result_text = f"Area: {numeric_val:.4f} sq. units"
              current_state = STATE_RESULT
            except Exception:
              result_text = "Error evaluating limits or improper integral."

  # --- RENDERING UI ---
  if current_state == STATE_MENU:
    title = FONT_TITLE.render("MASTER INTEGRAL CALCULATOR", True, TEXT_COLOR)
    screen.blit(title, title.get_rect(center=(WIDTH / 2, 130)))
    
    subtitle = FONT_SM.render("Choose an option or exit below", True, TEXT_MUTED)
    screen.blit(subtitle, subtitle.get_rect(center=(WIDTH / 2, 175)))

    menu_btn_indef.draw(screen)
    menu_btn_def.draw(screen)
    menu_btn_exit.draw(screen)

  elif current_state in [STATE_INPUT_FUNC, STATE_INPUT_LOWER, STATE_INPUT_UPPER]:
    mode_title = "Indefinite Integral" if calc_type == 1 else "Definite Integral"
    t_surf = FONT_LG.render(f"Mode: {mode_title}", True, ACCENT_COLOR)
    screen.blit(t_surf, (40, 25))

    if current_state == STATE_INPUT_FUNC:
      prompt_text = "Enter function f(x):"
    elif current_state == STATE_INPUT_LOWER:
      prompt_text = f"Function: {func_expr}  |  Enter Lower Limit (a):"
    else:
      prompt_text = f"Function: {func_expr}  |  Limits: [{lower_limit_val}, b]  |  Enter Upper Limit (b):"

    p_surf = FONT_MD.render(prompt_text, True, TEXT_MUTED)
    screen.blit(p_surf, (40, 65))

    pygame.draw.rect(screen, CARD_BG, (40, 100, 475, 55), border_radius=10)
    pygame.draw.rect(screen, ACCENT_COLOR, (40, 100, 475, 55), 2, border_radius=10)
    
    disp_surf = FONT_LG.render(user_input_str + "_", True, TEXT_COLOR)
    screen.blit(disp_surf, (55, 113))

    for btn in keypad_buttons:
      btn.draw(screen)
    submit_btn.draw(screen)

    hint = FONT_SM.render("Tip: Click keypad buttons (like 'oo') or type them manually.", True, TEXT_MUTED)
    screen.blit(hint, (40, 640))

  elif current_state == STATE_RESULT:
    res_title = FONT_TITLE.render("Calculation Result", True, SUCCESS_COLOR)
    screen.blit(res_title, (40, 25))

    pygame.draw.rect(screen, CARD_BG, (40, 70, 970, 60), border_radius=10)
    pygame.draw.rect(screen, (70, 70, 95), (40, 70, 970, 60), 2, border_radius=10)
    
    res_surf = FONT_MD.render(result_text, True, TEXT_COLOR)
    screen.blit(res_surf, (55, 88))

    if calc_type == 1 and indef_result_expr:
      draw_graph(screen, func_expr, 0, 0, is_indefinite=True, indef_expr=indef_result_expr)
      
      pygame.draw.rect(screen, CARD_BG, (40, 580, 460, 85), border_radius=10)
      l_title = FONT_SM.render("Graph Legend:", True, TEXT_COLOR)
      screen.blit(l_title, (55, 590))
      c_line = FONT_SM.render("— Function f(x) (Cyan)", True, (72, 202, 228))
      screen.blit(c_line, (55, 615))
      f_line = FONT_SM.render("— Antiderivative F(x) (Green)", True, SUCCESS_COLOR)
      screen.blit(f_line, (55, 635))

    elif calc_type == 2:
      draw_graph(screen, func_expr, lower_limit_val, upper_limit_val, is_indefinite=False)

      pygame.draw.rect(screen, CARD_BG, (40, 580, 460, 85), border_radius=10)
      l_title = FONT_SM.render("Graph Legend:", True, TEXT_COLOR)
      screen.blit(l_title, (55, 590))
      c_line = FONT_SM.render("— Function Curve f(x)", True, (72, 202, 228))
      screen.blit(c_line, (55, 615))
      l_line = FONT_SM.render("| Lower Limit (Red)  | Upper Limit (Green)", True, TEXT_MUTED)
      screen.blit(l_line, (55, 635))

    restart_msg = FONT_MD.render("Press 'R' or ENTER to return to Menu", True, ACCENT_HOVER)
    screen.blit(restart_msg, (40, 680))

  pygame.display.flip()
  clock.tick(60)
