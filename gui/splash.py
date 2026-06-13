from __future__ import annotations

import math
import platform
import random
import tkinter as tk

# ── Renkler ──────────────────────────────────────────────────
_BG     = "#050810"
_ACCENT = "#10b981"   # emerald
_CYAN   = "#06b6d4"   # cyan
_PURPLE = "#8b5cf6"   # mor
_TEXT   = "#e2eaf6"
_DIM    = "#3a5570"
_BORDER = "#1a2840"
_FONT   = "Segoe UI" if platform.system() == "Windows" else "Inter"

_W, _H   = 500, 320
_VERSION = "v1.0"

# Gradient bar segmentleri: emerald → cyan → purple
_GRAD = ["#10b981", "#0aab8a", "#08bba8", "#06b6d4",
         "#4990d4", "#7b6ed4", "#8b5cf6"]


class SplashScreen:
    """
    Premium animasyonlu splash ekranı.
    SplashScreen().run()  →  blocking, biter bitmez App() başlatılır.
    """

    def __init__(self) -> None:
        self._root = tk.Tk()
        self._root.overrideredirect(True)
        self._root.configure(bg=_BORDER)
        self._root.attributes("-topmost", True)
        self._root.attributes("-alpha", 0.0)

        sw = self._root.winfo_screenwidth()
        sh = self._root.winfo_screenheight()
        x  = (sw - _W) // 2
        y  = (sh - _H) // 2 - 20
        self._root.geometry(f"{_W}x{_H}+{x}+{y}")

        self._alpha   = 0.0
        self._tick    = 0
        self._bar_pct = 0.0
        self._done    = False

        self._build()

    # ── Build ─────────────────────────────────────────────────

    def _build(self) -> None:
        outer = tk.Frame(self._root, bg=_BORDER, padx=1, pady=1)
        outer.pack(fill="both", expand=True)
        inner = tk.Frame(outer, bg=_BG)
        inner.pack(fill="both", expand=True)

        W, H = _W - 2, _H - 2
        cv = tk.Canvas(inner, width=W, height=H, bg=_BG, highlightthickness=0)
        cv.pack()
        self._cv = cv
        self._CW, self._CH = W, H

        # ── 1. Arka plan: merkezi radyal parıltı ──────────────
        cx, cy_glow = W // 2, H // 2
        for i in range(20):
            t  = 1 - i / 20
            r  = 50 + i * 20
            v  = int(t * 14)
            col = f"#{v//4:02x}{v:02x}{v * 2:02x}"   # mavimsi parıltı
            cv.create_oval(cx - r, cy_glow - r, cx + r, cy_glow + r,
                           fill=col, outline="")

        # ── 2. Arka plan ızgara (subtle tech grid) ────────────
        for x in range(0, W + 1, 40):
            cv.create_line(x, 0, x, H, fill="#0a1428", width=1)
        for y in range(0, H + 1, 40):
            cv.create_line(0, y, W, y, fill="#0a1428", width=1)

        # ── 3. Parçacıklar ────────────────────────────────────
        colors = [_ACCENT] * 5 + [_CYAN] * 4 + [_PURPLE] * 3 + ["#ffffff"] * 2
        self._particles: list[dict] = []
        for _ in range(28):
            px = random.randint(5, W - 5)
            py = random.randint(-H, H)
            r  = random.uniform(1.0, 2.8)
            sp = random.uniform(0.2, 0.9)
            col = random.choice(colors)
            pid = cv.create_oval(px - r, py - r, px + r, py + r,
                                 fill=col, outline="")
            self._particles.append(dict(id=pid, x=px, y=py, r=r,
                                        speed=sp, color=col))

        # ── 4. Nabız halkaları (logo etrafı) ──────────────────
        cx_logo, cy_logo = W // 2, 110
        self._rings: list[dict] = []
        for i in range(3):
            rid = cv.create_oval(0, 0, 0, 0, outline="", width=1)
            self._rings.append(dict(id=rid, phase=i / 3.0))

        # ── 5. Logo glow katmanları ────────────────────────────
        for i in range(8):
            r  = 52 + i * 5
            g  = max(0, int(0x20 * (1 - i / 8)))
            b  = max(0, int(0x10 * (1 - i / 8)))
            col = f"#00{g:02x}{b:02x}"
            cv.create_oval(cx_logo - r, cy_logo - r,
                           cx_logo + r, cy_logo + r,
                           fill=col, outline="")

        # Logo dış çember
        cv.create_oval(cx_logo - 46, cy_logo - 46,
                       cx_logo + 46, cy_logo + 46,
                       fill="#061a12", outline=_ACCENT, width=2)
        # Logo iç çember
        cv.create_oval(cx_logo - 33, cy_logo - 33,
                       cx_logo + 33, cy_logo + 33,
                       fill="#0a2d1e", outline="")
        # "B" harfi
        cv.create_text(cx_logo, cy_logo + 1, text="B",
                       font=(_FONT, 24, "bold"), fill=_ACCENT)

        # Dönen parlaklık ışığı (arc)
        self._shine_id = cv.create_arc(
            cx_logo - 46, cy_logo - 46,
            cx_logo + 46, cy_logo + 46,
            start=0, extent=50,
            outline="#ffffff", width=2, style="arc",
        )
        self._cx_logo = cx_logo
        self._cy_logo = cy_logo

        # ── 6. Metinler ───────────────────────────────────────
        cv.create_text(W // 2, cy_logo + 62,
                       text="BLACKBOARD SYNC",
                       font=(_FONT, 17, "bold"), fill=_TEXT)
        cv.create_text(W // 2, cy_logo + 82,
                       text="Istinye Üniversitesi  ·  Ders Materyali İndirici",
                       font=(_FONT, 10), fill=_DIM)

        # ── 7. Alt alan ───────────────────────────────────────
        sep_y = H - 52
        cv.create_line(20, sep_y, W - 20, sep_y, fill=_BORDER)

        cv.create_text(24, H - 16, text=_VERSION,
                       font=(_FONT, 9), fill=_DIM, anchor="w")
        self._status_id = cv.create_text(
            W - 24, H - 16, text="Başlatılıyor...",
            font=(_FONT, 9), fill=_DIM, anchor="e",
        )

        # ── 8. Gradient progress bar ──────────────────────────
        bx1, bby = 20, sep_y + 10
        bx2, bby2 = W - 20, sep_y + 17
        cv.create_rectangle(bx1, bby, bx2, bby2, fill=_BORDER, outline="")

        n  = len(_GRAD)
        sw = (bx2 - bx1) / n
        self._bar_segs: list[int] = []
        for i, col in enumerate(_GRAD):
            x1 = bx1 + i * sw
            sid = cv.create_rectangle(x1, bby, x1, bby2,
                                      fill=col, outline="")
            self._bar_segs.append(sid)

        # Shimmer (bar üstünde kayan parlak bant)
        self._shimmer_id = cv.create_rectangle(
            bx1, bby, bx1, bby2, fill="#ccfff0", outline="",
        )

        self._bx1, self._bx2 = bx1, bx2
        self._bby, self._bby2 = bby, bby2
        self._seg_w = sw

    # ── Animasyon döngüsü ─────────────────────────────────────

    def _animate(self) -> None:
        cv  = self._cv
        t   = self._tick
        W, H = self._CW, self._CH

        # Parçacıklar
        for p in self._particles:
            p["y"] -= p["speed"]
            if p["y"] < -8:
                p["y"] = H + 8
                p["x"] = random.randint(5, W - 5)
            r = p["r"]
            cv.coords(p["id"], p["x"] - r, p["y"] - r,
                                p["x"] + r, p["y"] + r)

        # Nabız halkaları
        for ring in self._rings:
            phase = ((t * 0.016) + ring["phase"]) % 1.0
            r     = 46 + phase * 64
            fade  = 1.0 - phase
            cx, cy = self._cx_logo, self._cy_logo
            cv.coords(ring["id"], cx - r, cy - r, cx + r, cy + r)
            g   = int(0x98 * fade * 0.55)
            b   = int(0x81 * fade * 0.4)
            rv  = int(0x10 * fade * 0.2)
            col = f"#{rv:02x}{g:02x}{b:02x}"
            cv.itemconfigure(ring["id"],
                             outline=col,
                             width=max(1, int(2.5 * fade)))

        # Dönen parlaklık (logo üstünde)
        angle = (t * 3.5) % 360
        cv.itemconfigure(self._shine_id, start=angle)

        # Gradient bar doldurma
        if self._bar_pct < 1.0:
            self._bar_pct = min(1.0, self._bar_pct + 0.008)
            fill_x = self._bx1 + (self._bx2 - self._bx1) * self._bar_pct
            for i, sid in enumerate(self._bar_segs):
                x1 = self._bx1 + i * self._seg_w
                x2 = self._bx1 + (i + 1) * self._seg_w
                fx = min(fill_x, x2)
                cv.coords(sid, x1, self._bby, max(x1, fx), self._bby2)

            # Shimmer — fill noktasının 12px gerisinde kayan bant
            sh  = max(self._bx1, fill_x - 14)
            sh2 = min(fill_x + 3, self._bx2)
            cv.coords(self._shimmer_id, sh, self._bby, sh2, self._bby2)

            pct = int(self._bar_pct * 100)
            if pct < 100:
                cv.itemconfigure(self._status_id, text=f"% {pct}")
            else:
                cv.coords(self._shimmer_id, 0, 0, 0, 0)   # gizle
                cv.itemconfigure(self._status_id,
                                 text="Hazır  ✓", fill=_ACCENT)
                if not self._done:
                    self._done = True
                    self._root.after(320, self._fade_out)

        self._tick += 1
        self._root.after(28, self._animate)

    # ── Fade ──────────────────────────────────────────────────

    def _fade_in(self) -> None:
        self._alpha = min(1.0, self._alpha + 0.07)
        self._root.attributes("-alpha", self._alpha)
        if self._alpha < 1.0:
            self._root.after(14, self._fade_in)
        else:
            self._animate()

    def _fade_out(self) -> None:
        self._alpha = max(0.0, self._alpha - 0.07)
        self._root.attributes("-alpha", self._alpha)
        if self._alpha > 0:
            self._root.after(14, self._fade_out)
        else:
            self._root.destroy()

    # ── Public ────────────────────────────────────────────────

    def run(self) -> None:
        self._root.after(60, self._fade_in)
        self._root.mainloop()
