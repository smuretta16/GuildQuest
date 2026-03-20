"""
guildquest_gui.py  —  GuildQuest Adventure Management System (redesigned)
Dark fantasy theme, sidebar navigation, polished Mini-Adventures tab.
Run:  python guildquest_gui.py
"""

import tkinter as tk
from tkinter import ttk, messagebox

from guildquest import (
    Campaign, Character, GuildQuestGame, Item, Permission,
    PlayerProfile, QuestEvent, Rarity, Realm, Theme,
    TimeDisplay, User, Visibility, WorldTime, save_profiles,
)
from game_context import GameContext
from relic_hunt import RelicHunt
from escort_mission import EscortMission, PYGAME_AVAILABLE
from mini_adventure import GameResult

BG       = "#0f0f1a"
PANEL    = "#16213e"
SIDEBAR  = "#0a0a14"
ACCENT   = "#7c4dff"
ACCENT2  = "#00bcd4"
GOLD     = "#ffd54f"
RED      = "#ef5350"
GREEN    = "#66bb6a"
TEXT     = "#e8eaf6"
TEXT_DIM = "#7986cb"
BORDER   = "#1e2a4a"
ENTRY_BG = "#1a1f35"
BTN_BG   = "#1e2a4a"
BTN_HOV  = "#2a3a5e"

FT       = ("Segoe UI", 20, "bold")
FH2      = ("Segoe UI", 13, "bold")
FB       = ("Segoe UI", 10)
FM       = ("Consolas", 10)
FS       = ("Segoe UI", 9)

#  Widget helpers 

def _lbl(p, text, font=FB, fg=TEXT, bg=PANEL, **kw):
    return tk.Label(p, text=text, font=font, fg=fg, bg=bg, **kw)

def _ent(p, var, width=24):
    return tk.Entry(p, textvariable=var, width=width,
                    bg=ENTRY_BG, fg=TEXT, insertbackground=TEXT,
                    relief="flat", bd=4, font=FB)

def _cbo(p, var, values=(), width=22):
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("D.TCombobox", fieldbackground=ENTRY_BG,
                    background=ENTRY_BG, foreground=TEXT,
                    selectbackground=ACCENT, arrowcolor=TEXT_DIM)
    return ttk.Combobox(p, textvariable=var, values=values,
                        state="readonly", width=width,
                        style="D.TCombobox", font=FB)

def _btn(p, text, cmd, width=16, color=ACCENT):
    b = tk.Button(p, text=text, command=cmd, width=width,
                  bg=color, fg="white", activebackground=BTN_HOV,
                  activeforeground="white", relief="flat", bd=0,
                  font=("Segoe UI", 10, "bold"), cursor="hand2",
                  padx=8, pady=5)
    b.bind("<Enter>", lambda e: b.config(bg=BTN_HOV))
    b.bind("<Leave>", lambda e: b.config(bg=color))
    return b

def _slist(p, height=8):
    lb = tk.Listbox(p, height=height, bg=ENTRY_BG, fg=TEXT,
                    selectbackground=ACCENT, selectforeground="white",
                    relief="flat", bd=0, font=FM,
                    activestyle="none", highlightthickness=0)
    sb = tk.Scrollbar(p, orient="vertical", command=lb.yview,
                      bg=PANEL, troughcolor=PANEL, width=10)
    lb.configure(yscrollcommand=sb.set)
    lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    sb.pack(side=tk.RIGHT, fill=tk.Y)
    return lb

def _card(p, title=""):
    outer = tk.Frame(p, bg=PANEL)
    if title:
        tk.Label(outer, text=f"  {title}",
                 font=("Segoe UI", 10, "bold"),
                 fg=ACCENT2, bg=PANEL).pack(anchor="w", pady=(6, 0))
        tk.Frame(outer, height=1, bg=BORDER).pack(fill=tk.X, pady=4)
    inner = tk.Frame(outer, bg=PANEL)
    inner.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)
    return outer, inner



# Relic Hunt game window


CELL = 50
GS   = 10

class RelicHuntWindow(tk.Toplevel):
    P1K = {"w":"W","a":"A","s":"S","d":"D"}
    P2K = {"Up":"W","Down":"S","Left":"A","Right":"D"}

    def __init__(self, parent, game, p1, p2, on_close=None):
        super().__init__(parent)
        self.title("⚔ Relic Hunt")
        self.resizable(False, False)
        self.configure(bg=BG)
        self._game = game
        self._p1 = p1
        self._p2 = p2
        self._on_close = on_close
        self._engine = RelicHunt()
        ctx = GameContext(clock=game.clock, realms=game.realms)
        self._engine.init(ctx, p1, p2)
        self._build()
        self._draw()
        self._bind()
        self.update_idletasks()
        sw,sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"+{(sw-self.winfo_width())//2}+{(sh-self.winfo_height())//2}")
        self.protocol("WM_DELETE_WINDOW", self._quit)
        self.focus_set()

    def _build(self):
        p1n, p2n = self._p1.character_name, self._p2.character_name
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill=tk.X, padx=16, pady=(12,4))
        tk.Label(hdr, text="⚔  RELIC HUNT  ⚔",
                 font=("Segoe UI",17,"bold"), bg=BG, fg=GOLD).pack()
        tk.Label(hdr, text="First to collect 5 relics wins!",
                 font=FS, bg=BG, fg=TEXT_DIM).pack()

        sf = tk.Frame(self, bg=BG)
        sf.pack(fill=tk.X, padx=20, pady=6)
        self._s1 = tk.StringVar(value=f"🔵 {p1n}  0/5")
        self._s2 = tk.StringVar(value=f"🔴 {p2n}  0/5")
        for sv, fg in ((self._s1,"#4fc3f7"),(self._s2,"#ef5350")):
            b = tk.Frame(sf, bg=PANEL, padx=10, pady=6)
            b.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=4)
            tk.Label(b, textvariable=sv, font=("Segoe UI",12,"bold"),
                     bg=PANEL, fg=fg).pack()

        self._cv = tk.Canvas(self, width=GS*CELL, height=GS*CELL,
                             bg="#111827", highlightthickness=2,
                             highlightbackground=ACCENT)
        self._cv.pack(padx=20, pady=8)

        self._status = tk.StringVar(value=f"🔵 {p1n}'s turn  (W A S D)")
        tk.Label(self, textvariable=self._status,
                 font=("Segoe UI",11,"bold"), bg=BG, fg=TEXT).pack()
        tk.Label(self,
                 text=f"  🔵 {p1n}: W A S D     🔴 {p2n}: ↑ ↓ ← →     ◆ = relic",
                 font=FS, bg=BG, fg=TEXT_DIM).pack(pady=(2,10))

    def _draw(self):
        c = self._cv
        c.delete("all")
        p1r,p1c = self._engine._pos[0]
        p2r,p2c = self._engine._pos[1]
        for r in range(GS):
            for col in range(GS):
                x1,y1 = col*CELL, r*CELL
                x2,y2 = x1+CELL, y1+CELL
                cx,cy = x1+CELL//2, y1+CELL//2
                c.create_rectangle(x1,y1,x2,y2, fill="#111827", outline="#1e2a4a")
                if (r,col)==(p1r,p1c):
                    c.create_oval(x1+5,y1+5,x2-5,y2-5, fill="#4fc3f7", outline="white",width=2)
                    c.create_text(cx,cy,text="1",font=("Segoe UI",13,"bold"),fill="white")
                elif (r,col)==(p2r,p2c):
                    c.create_oval(x1+5,y1+5,x2-5,y2-5, fill="#ef5350", outline="white",width=2)
                    c.create_text(cx,cy,text="2",font=("Segoe UI",13,"bold"),fill="white")
                elif self._engine._grid[r][col]:
                    pts=[cx,y1+10,x2-10,cy,cx,y2-10,x1+10,cy]
                    c.create_polygon(pts, fill=GOLD, outline="#fff8e1")
        s = self._engine._scores
        p1n,p2n = self._p1.character_name, self._p2.character_name
        self._s1.set(f"🔵 {p1n}  {s[0]}/5")
        self._s2.set(f"🔴 {p2n}  {s[1]}/5")
        if not self._engine.is_over():
            if self._engine._current_player==0:
                self._status.set(f"🔵 {p1n}'s turn  (W A S D)")
            else:
                self._status.set(f"🔴 {p2n}'s turn  (↑ ↓ ← →)")

    def _bind(self):
        for k in ("w","a","s","d"): self.bind(f"<KeyPress-{k}>", self._key)
        for k in ("Up","Down","Left","Right"): self.bind(f"<KeyPress-{k}>", self._key)

    def _key(self, event):
        if self._engine.is_over(): return
        k = event.keysym
        if k in self.P1K:   pidx,d = 1, self.P1K[k]
        elif k in self.P2K: pidx,d = 2, self.P2K[k]
        else: return
        fb = self._engine.handle_input(pidx, d)
        if "not yours" in fb:
            self._status.set(f"⚠  {fb}")
            self.after(700, self._restore_status)
            return
        self._engine.advance_turn()
        self._draw()
        if self._engine.is_over(): self._game_over()

    def _restore_status(self):
        if self._engine.is_over(): return
        p1n,p2n = self._p1.character_name, self._p2.character_name
        if self._engine._current_player==0:
            self._status.set(f"🔵 {p1n}'s turn  (W A S D)")
        else:
            self._status.set(f"🔴 {p2n}'s turn  (↑ ↓ ← →)")

    def _game_over(self):
        result = self._engine.get_outcome()
        p1n,p2n = self._p1.character_name, self._p2.character_name
        if result==GameResult.PLAYER1_WIN:
            msg=f"🏆  {p1n} wins!"
            self._engine.on_player_win(self._p1)
            self._engine.on_player_loss(self._p2)
        elif result==GameResult.PLAYER2_WIN:
            msg=f"🏆  {p2n} wins!"
            self._engine.on_player_win(self._p2)
            self._engine.on_player_loss(self._p1)
        else:
            msg="🤝  It's a tie!"
        self._p1.record_quest("Relic Hunt")
        self._p2.record_quest("Relic Hunt")
        save_profiles(self._game.users)
        self._status.set(msg)
        self._draw()
        cx,cy = GS*CELL//2, GS*CELL//2
        self._cv.create_rectangle(cx-170,cy-40,cx+170,cy+40,
                                  fill="#0f0f1a",outline=GREEN,width=3)
        self._cv.create_text(cx,cy,text=msg,
                             font=("Segoe UI",17,"bold"),fill=GREEN)
        bf = tk.Frame(self, bg=BG)
        bf.pack(pady=10)
        _btn(bf,"▶ Play Again",self._replay,width=14).pack(side=tk.LEFT,padx=8)
        _btn(bf,"✕ Close",self._quit,width=14,color="#37474f").pack(side=tk.LEFT,padx=8)

    def _replay(self):
        for w in self.winfo_children(): w.destroy()
        self._engine.reset()
        ctx = GameContext(clock=self._game.clock, realms=self._game.realms)
        self._engine.init(ctx, self._p1, self._p2)
        self._build(); self._draw(); self._bind(); self.focus_set()

    def _quit(self):
        save_profiles(self._game.users)
        if self._on_close: self._on_close()
        self.destroy()



# Main Application


class GuildQuestGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("GuildQuest — Adventure Management System")
        self.root.configure(bg=BG)
        self.root.minsize(1100, 680)
        self.game = GuildQuestGame()
        self._pages: dict[str, tk.Frame] = {}
        self._nav:   dict[str, tuple]    = {}
        self._build_layout()
        self._build_sidebar()
        self._build_all_pages()
        self._show("dashboard")

    #  Layout 

    def _build_layout(self):
        self._sb = tk.Frame(self.root, bg=SIDEBAR, width=195)
        self._sb.pack(side=tk.LEFT, fill=tk.Y)
        self._sb.pack_propagate(False)
        self._ct = tk.Frame(self.root, bg=BG)
        self._ct.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    #  Sidebar 

    def _build_sidebar(self):
        sb = self._sb
        lf = tk.Frame(sb, bg=SIDEBAR, pady=16)
        lf.pack(fill=tk.X)
        tk.Label(lf,text="⚔",font=("Segoe UI",26),bg=SIDEBAR,fg=GOLD).pack()
        tk.Label(lf,text="GuildQuest",font=("Segoe UI",13,"bold"),bg=SIDEBAR,fg=TEXT).pack()
        tk.Label(lf,text="Adventure System",font=FS,bg=SIDEBAR,fg=TEXT_DIM).pack()
        tk.Frame(sb,height=1,bg=BORDER).pack(fill=tk.X,pady=6)

        self._tw = tk.StringVar()
        self._rw = tk.StringVar()
        tk.Label(sb,textvariable=self._tw,font=("Consolas",9),bg=SIDEBAR,fg=ACCENT2).pack(pady=(4,0))
        tk.Label(sb,textvariable=self._rw,font=FS,bg=SIDEBAR,fg=TEXT_DIM).pack()
        tk.Frame(sb,height=1,bg=BORDER).pack(fill=tk.X,pady=6)

        items = [
            ("dashboard",  "🏠","Dashboard"),
            ("miniadv",    "🎮","Mini-Adventures"),
            ("campaigns",  "📜","Campaigns"),
            ("events",     "⏱","Quest Events"),
            ("characters", "🧙","Characters"),
            ("realms",     "🌍","Realms"),
            ("users",      "👤","Users"),
            ("profiles",   "📊","Player Profiles"),
            ("settings",   "⚙","Settings"),
        ]
        for pid,icon,text in items:
            self._navbtn(sb, pid, icon, text)

        tk.Frame(sb,height=1,bg=BORDER).pack(fill=tk.X,pady=6)
        self._uw = tk.StringVar()
        tk.Label(sb,text="Active User",font=FS,bg=SIDEBAR,fg=TEXT_DIM).pack()
        tk.Label(sb,textvariable=self._uw,font=("Segoe UI",10,"bold"),bg=SIDEBAR,fg=ACCENT2).pack(pady=(0,12))
        self._update_sb()

    def _navbtn(self, parent, pid, icon, text):
        f = tk.Frame(parent, bg=SIDEBAR, cursor="hand2")
        f.pack(fill=tk.X)
        lbl = tk.Label(f, text=f"  {icon}  {text}",
                       font=FB, bg=SIDEBAR, fg=TEXT, anchor="w", pady=9, padx=4)
        lbl.pack(fill=tk.X)
        ind = tk.Frame(f, width=4, bg=SIDEBAR)
        ind.place(relx=0, rely=0, relheight=1)

        def click(): self._show(pid)
        def enter(e):
            if self._nav.get("_active") != pid:
                lbl.config(bg=BTN_BG); f.config(bg=BTN_BG)
        def leave(e):
            if self._nav.get("_active") != pid:
                lbl.config(bg=SIDEBAR); f.config(bg=SIDEBAR)

        f.bind("<Enter>", enter); f.bind("<Leave>", leave)
        lbl.bind("<Button-1>", lambda e: click())
        f.bind("<Button-1>",   lambda e: click())
        self._nav[pid] = (f, lbl, ind)

    def _show(self, pid: str):
        old = self._nav.get("_active")
        if old and old in self._nav:
            f,lbl,ind = self._nav[old]
            f.config(bg=SIDEBAR); lbl.config(bg=SIDEBAR,fg=TEXT); ind.config(bg=SIDEBAR)
        self._nav["_active"] = pid
        if pid in self._nav:
            f,lbl,ind = self._nav[pid]
            f.config(bg=BTN_BG); lbl.config(bg=BTN_BG,fg=GOLD); ind.config(bg=ACCENT)
        for p,pg in self._pages.items(): pg.pack_forget()
        self._pages[pid].pack(fill=tk.BOTH, expand=True)
        self._refresh(pid)

    def _refresh(self, pid):
        self._update_sb()
        dispatch = {
            "dashboard":  self._ref_dashboard,
            "miniadv":    self._ref_miniadv,
            "campaigns":  self._ref_campaigns,
            "events":     self._ref_events,
            "characters": self._ref_characters,
            "realms":     self._ref_realms,
            "users":      self._ref_users,
            "profiles":   self._ref_profiles,
            "settings":   self._ref_settings,
        }
        if pid in dispatch: dispatch[pid]()

    def _update_sb(self):
        self._tw.set(f"🕐 {self.game.clock.now}")
        u = self.game.active_user
        r = self.game.realms.get(u.settings.current_realm_id)
        self._rw.set(f"🌍 {r.name if r else '—'}")
        self._uw.set(u.name)

    #  Page factory 

    def _page(self, pid, title, sub=""):
        pg = tk.Frame(self._ct, bg=BG)
        self._pages[pid] = pg
        hdr = tk.Frame(pg, bg=BG)
        hdr.pack(fill=tk.X, padx=24, pady=(20,0))
        tk.Label(hdr,text=title,font=FT,bg=BG,fg=TEXT).pack(anchor="w")
        if sub:
            tk.Label(hdr,text=sub,font=FS,bg=BG,fg=TEXT_DIM).pack(anchor="w")
        tk.Frame(pg,height=1,bg=BORDER).pack(fill=tk.X,padx=24,pady=10)
        return pg

    def _build_all_pages(self):
        self._build_dashboard()
        self._build_miniadv()
        self._build_campaigns()
        self._build_events()
        self._build_characters()
        self._build_realms()
        self._build_users()
        self._build_profiles()
        self._build_settings()

    
    # DASHBOARD
    

    def _build_dashboard(self):
        pg = self._page("dashboard","🏠  Dashboard","Overview of your GuildQuest world")
        body = tk.Frame(pg, bg=BG)
        body.pack(fill=tk.BOTH, expand=True, padx=24, pady=8)

        # Stat cards row
        sr = tk.Frame(body, bg=BG)
        sr.pack(fill=tk.X, pady=(0,16))
        self._dstats: dict[str,tk.StringVar] = {}
        for key,icon,lbl,col in [
            ("realms","🌍","Realms",ACCENT2),
            ("campaigns","📜","Campaigns",ACCENT),
            ("events","⏱","Events",GOLD),
            ("characters","🧙","Characters",GREEN),
        ]:
            f = tk.Frame(sr, bg=PANEL, padx=16, pady=12)
            f.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=6)
            tk.Label(f,text=icon,font=("Segoe UI",22),bg=PANEL,fg=col).pack()
            v = tk.StringVar(value="0")
            self._dstats[key] = v
            tk.Label(f,textvariable=v,font=("Segoe UI",20,"bold"),bg=PANEL,fg=col).pack()
            tk.Label(f,text=lbl,font=FS,bg=PANEL,fg=TEXT_DIM).pack()

        cols = tk.Frame(body, bg=BG)
        cols.pack(fill=tk.BOTH, expand=True)
        left = tk.Frame(cols, bg=BG)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0,8))
        right = tk.Frame(cols, bg=BG)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(8,0))

        oc,ic = _card(left,"📅  Upcoming Quest Events")
        oc.pack(fill=tk.BOTH, expand=True, pady=(0,12))
        lf = tk.Frame(ic, bg=PANEL); lf.pack(fill=tk.BOTH, expand=True)
        self._d_events = _slist(lf, 7)

        oc2,ic2 = _card(right,"🌍  Realms at a Glance")
        oc2.pack(fill=tk.BOTH, expand=True, pady=(0,12))
        lf2 = tk.Frame(ic2, bg=PANEL); lf2.pack(fill=tk.BOTH, expand=True)
        self._d_realms = _slist(lf2, 7)

        oc3,ic3 = _card(body,"⚡  Quick Actions")
        oc3.pack(fill=tk.X)
        qr = tk.Frame(ic3, bg=PANEL); qr.pack(fill=tk.X)
        _btn(qr,"🎮 Play Mini-Adventure",lambda:self._show("miniadv"),width=22).pack(side=tk.LEFT,padx=6,pady=4)
        _btn(qr,"📜 New Campaign",lambda:self._show("campaigns"),width=18,color="#37474f").pack(side=tk.LEFT,padx=6)
        _btn(qr,"⏩ Advance Time",self._quick_advance,width=16,color="#37474f").pack(side=tk.LEFT,padx=6)

    def _ref_dashboard(self):
        self._dstats["realms"].set(str(len(self.game.realms)))
        self._dstats["campaigns"].set(str(len(self.game.campaigns)))
        self._dstats["events"].set(str(len(self.game.events)))
        self._dstats["characters"].set(str(len(self.game.characters)))
        self._d_events.delete(0,tk.END)
        for e in sorted(self.game.events.values(),key=lambda e:e.start_time.total_minutes)[:14]:
            r = self.game.realms.get(e.realm_id)
            self._d_events.insert(tk.END,f"  {e.name}  ·  {r.name if r else '?'}  ·  {e.start_time}")
        self._d_realms.delete(0,tk.END)
        for r in sorted(self.game.realms.values(),key=lambda r:r.realm_id):
            off = f"+{r.minute_offset}m" if r.minute_offset>=0 else f"{r.minute_offset}m"
            self._d_realms.insert(tk.END,f"  {r.name}  ·  {off}  ·  {r.description[:38]}")

    def _quick_advance(self):
        top = tk.Toplevel(self.root)
        top.title("Advance Time"); top.configure(bg=BG); top.resizable(False,False)
        _lbl(top,"  Minutes to advance:",bg=BG).pack(padx=20,pady=(16,4),anchor="w")
        v = tk.StringVar()
        _ent(top,v,10).pack(padx=20,pady=4)
        def go():
            try:
                m=int(v.get())
                if m>0:
                    self.game.clock.advance_minutes(m)
                    self._update_sb(); self._ref_dashboard(); top.destroy()
            except ValueError: pass
        _btn(top,"Advance",go,10).pack(pady=10)

    
    # MINI-ADVENTURES
    

    def _build_miniadv(self):
        pg = self._page("miniadv","🎮  Mini-Adventures",
                        "Launch two-player adventures in the GuildQuest world")
        body = tk.Frame(pg, bg=BG)
        body.pack(fill=tk.BOTH, expand=True, padx=24, pady=8)
        left = tk.Frame(body, bg=BG)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0,12))
        right = tk.Frame(body, bg=BG)
        right.pack(side=tk.RIGHT, fill=tk.Y)

        oc,ic = _card(left,"🗺  Available Adventures")
        oc.pack(fill=tk.BOTH, expand=True, pady=(0,12))

        self._adv_sel = tk.IntVar(value=0)
        adventures = [
            ("⚔  Relic Hunt",
             "Competitive  |  Race to collect 5 relics on a 10×10 grid.\n"
             "Player 1: W A S D        Player 2: ↑ ↓ ← →"),
            ("🛡  Escort Across the Realm",
             "Co-op  |  Escort the NPC carrier to the goal before health runs out.\n"
             "Player 1: A D W (jump)   Player 2: ← → ↑ (jump)   Requires: pip install pygame"),
        ]
        for i,(name,desc) in enumerate(adventures):
            af = tk.Frame(ic, bg=PANEL, padx=12, pady=10, cursor="hand2")
            af.pack(fill=tk.X, pady=4)
            tk.Radiobutton(af,variable=self._adv_sel,value=i,
                           bg=PANEL,activebackground=PANEL,
                           selectcolor=ACCENT,fg=ACCENT).pack(side=tk.LEFT,padx=(0,8))
            nf = tk.Frame(af, bg=PANEL); nf.pack(side=tk.LEFT, fill=tk.X, expand=True)
            tk.Label(nf,text=name,font=("Segoe UI",11,"bold"),
                     bg=PANEL,fg=GOLD,anchor="w").pack(anchor="w")
            tk.Label(nf,text=desc,font=FS,bg=PANEL,fg=TEXT_DIM,
                     anchor="w",justify="left",wraplength=360).pack(anchor="w")
            af.bind("<Button-1>",lambda e,idx=i: self._adv_sel.set(idx))

        oc2,ic2 = _card(right,"👥  Select Players")
        oc2.pack(fill=tk.X, pady=(0,12))
        _lbl(ic2,"Player 1  (W A S D)",fg="#4fc3f7",bg=PANEL).pack(anchor="w",pady=(0,2))
        self._ap1 = tk.StringVar()
        self._ap1c = _cbo(ic2,self._ap1,width=26)
        self._ap1c.pack(anchor="w",pady=(0,10))
        _lbl(ic2,"Player 2  (Arrow Keys)",fg="#ef5350",bg=PANEL).pack(anchor="w",pady=(0,2))
        self._ap2 = tk.StringVar()
        self._ap2c = _cbo(ic2,self._ap2,width=26)
        self._ap2c.pack(anchor="w",pady=(0,6))
        _lbl(ic2,"Players need a saved profile  (Player Profiles page).",
             font=FS,fg=TEXT_DIM,bg=PANEL).pack(anchor="w",pady=(4,8))
        _btn(ic2,"▶  Launch Adventure",self._launch,width=24,color=ACCENT).pack(anchor="w",pady=6)

        oc3,ic3 = _card(right,"🏆  Recent Results")
        oc3.pack(fill=tk.BOTH, expand=True)
        lf = tk.Frame(ic3, bg=PANEL); lf.pack(fill=tk.BOTH, expand=True)
        self._res_list = _slist(lf, 7)

    def _ref_miniadv(self):
        users = [u for u in sorted(self.game.users.values(),key=lambda u:u.user_id)
                 if u.profile]
        vals = [f"{u.user_id}: {u.name}  ({u.profile.character_name})" for u in users]
        self._ap1c["values"] = vals
        self._ap2c["values"] = vals
        if vals and not self._ap1.get(): self._ap1.set(vals[0])
        if len(vals)>=2 and not self._ap2.get(): self._ap2.set(vals[1])

    def _launch(self):
        v1,v2 = self._ap1.get(), self._ap2.get()
        if not v1 or not v2:
            messagebox.showerror("Players Required",
                "Both players must be selected.\nCreate profiles in Player Profiles first."); return
        if v1==v2:
            messagebox.showerror("Different Players","Player 1 and 2 must be different."); return
        u1 = self.game.users.get(int(v1.split(":")[0]))
        u2 = self.game.users.get(int(v2.split(":")[0]))
        if not u1 or not u1.profile or not u2 or not u2.profile:
            messagebox.showerror("No Profile","Both players need a saved profile."); return
        idx = self._adv_sel.get()
        if idx==0:
            w = RelicHuntWindow(self.root,self.game,u1.profile,u2.profile,
                                on_close=self._adv_closed)
            w.grab_set()
        elif idx==1:
            self._launch_escort(u1.profile, u2.profile)

    def _adv_closed(self):
        self._ref_miniadv(); self._ref_profiles()
        self._res_list.delete(0,tk.END)
        for u in sorted(self.game.users.values(),key=lambda u:u.user_id):
            if u.profile:
                p=u.profile
                self._res_list.insert(0,
                    f"  {u.name} ({p.character_name})  W:{p.wins}  L:{p.losses}  Q:{p.quests_completed}")

    def _launch_escort(self, p1: PlayerProfile, p2: PlayerProfile):
        """Launch Escort Mission (pygame if available, otherwise Tkinter fallback)."""

        if PYGAME_AVAILABLE:
            prompt = (
                "Escort Across the Realm will open in a new Pygame window.\n"
                "The main GuildQuest window will be unresponsive while the game runs.\n\n"
                "Launch now?"
            )
        else:
            prompt = (
                "Pygame isn't installed, so Escort Across the Realm will run in a Tkinter window instead.\n"
                "Controls are the same.\n\n"
                "Launch now?"
            )

        if not messagebox.askyesno("Launch Escort Mission", prompt):
            return

        engine = EscortMission()
        from game_context import GameContext
        ctx = GameContext(clock=self.game.clock, realms=self.game.realms)
        engine.init(ctx, p1, p2)

        # Hide main window while pygame runs so they don't fight for focus
        self.root.withdraw()
        try:
            if PYGAME_AVAILABLE:
                result = engine.run_pygame_session()
            else:
                result = engine.run_tkinter_session(parent=self.root)
        finally:
            self.root.deiconify()
            from guildquest import save_profiles
            save_profiles(self.game.users)
            self._adv_closed()

        # Show outcome in a dialog
        p1n = p1.character_name
        p2n = p2.character_name
        from mini_adventure import GameResult
        if result == GameResult.COOPERATIVE_WIN:
            messagebox.showinfo("Mission Complete!",
                f"🏆 {p1n} & {p2n} successfully escorted the NPC!\n"
                "An Escort Medal was added to both inventories.")
        elif result == GameResult.COOPERATIVE_LOSS:
            messagebox.showinfo("Mission Failed",
                f"💀 {p1n} & {p2n} failed to protect the NPC.\nBetter luck next time!")
        else:
            messagebox.showinfo("Escort Mission", "Mission ended.")

    
    # CAMPAIGNS
    

    def _build_campaigns(self):
        pg = self._page("campaigns","📜  Campaigns","Create and manage quest campaigns")
        body = tk.Frame(pg,bg=BG); body.pack(fill=tk.BOTH,expand=True,padx=24,pady=8)
        left = tk.Frame(body,bg=BG); left.pack(side=tk.LEFT,fill=tk.BOTH,expand=True,padx=(0,12))
        right = tk.Frame(body,bg=BG); right.pack(side=tk.RIGHT,fill=tk.Y)

        oc,ic = _card(left,"📜  All Campaigns")
        oc.pack(fill=tk.BOTH,expand=True)
        lf=tk.Frame(ic,bg=PANEL); lf.pack(fill=tk.BOTH,expand=True)
        self._clist = _slist(lf,14)

        oc2,ic2 = _card(right,"➕  Create Campaign")
        oc2.pack(fill=tk.X,pady=(0,12))
        _lbl(ic2,"Name",bg=PANEL).pack(anchor="w")
        self._cname = tk.StringVar()
        _ent(ic2,self._cname).pack(anchor="w",pady=(2,8))
        _lbl(ic2,"Visibility",bg=PANEL).pack(anchor="w")
        self._cvis = tk.StringVar(value="PRIVATE")
        _cbo(ic2,self._cvis,["PUBLIC","PRIVATE"]).pack(anchor="w",pady=(2,8))
        _btn(ic2,"Create Campaign",self._create_camp,width=20).pack(anchor="w",pady=4)

        oc3,ic3 = _card(right,"🔗  Share Campaign")
        oc3.pack(fill=tk.X,pady=(0,12))
        _lbl(ic3,"Share with user",bg=PANEL).pack(anchor="w")
        self._shu = tk.StringVar()
        self._shuc = _cbo(ic3,self._shu,width=22)
        self._shuc.pack(anchor="w",pady=(2,8))
        _lbl(ic3,"Permission",bg=PANEL).pack(anchor="w")
        self._shp = tk.StringVar(value="VIEW")
        _cbo(ic3,self._shp,["VIEW","COLLABORATIVE"]).pack(anchor="w",pady=(2,8))
        _btn(ic3,"Share Selected",self._share_camp,width=20).pack(anchor="w",pady=4)

        _btn(right,"🗑  Delete Selected",self._del_camp,width=20,color="#c62828").pack(pady=8,anchor="w")

    def _ref_campaigns(self):
        self._clist.delete(0,tk.END)
        for c in self.game.list_visible_campaigns():
            _,ce,io = self.game.campaign_access(c)
            role = "owner" if io else ("editor" if ce else "viewer")
            vis = "🌐" if c.visibility==Visibility.PUBLIC else "🔒"
            self._clist.insert(tk.END,
                f"  {vis} [{c.campaign_id}] {c.name}  ·  {role}  ·  {len(c.event_ids)} events")
        others=[u for u in self.game.users.values() if u.user_id!=self.game.active_user_id]
        self._shuc["values"]=[f"{u.user_id}: {u.name}" for u in others]

    def _create_camp(self):
        n=self._cname.get().strip()
        if not n: messagebox.showerror("Validation","Name required."); return
        cid=self.game.next_campaign_id; self.game.next_campaign_id+=1
        self.game.campaigns[cid]=Campaign(cid,self.game.active_user_id,n,Visibility[self._cvis.get()])
        self._cname.set(""); self._ref_campaigns()

    def _del_camp(self):
        sel=self._clist.curselection()
        if not sel: return
        t=self._clist.get(sel[0])
        cid=int(t.split("[")[1].split("]")[0])
        c=self.game.campaigns.get(cid)
        if not c: return
        _,_,io=self.game.campaign_access(c)
        if not io: messagebox.showerror("Permission","Only owner can delete."); return
        if not messagebox.askyesno("Delete",f"Delete '{c.name}'?"): return
        for eid in c.event_ids: self.game.events.pop(eid,None)
        self.game.campaigns.pop(cid); self._ref_campaigns()

    def _share_camp(self):
        sel=self._clist.curselection()
        if not sel: messagebox.showerror("Select","Select a campaign first."); return
        t=self._clist.get(sel[0])
        cid=int(t.split("[")[1].split("]")[0])
        c=self.game.campaigns.get(cid)
        if not c: return
        _,_,io=self.game.campaign_access(c)
        if not io: messagebox.showerror("Permission","Only owner can share."); return
        uv=self._shu.get()
        if not uv: messagebox.showerror("Select","Select a user."); return
        uid=int(uv.split(":")[0])
        c.shares[uid]=Permission[self._shp.get()]
        messagebox.showinfo("Shared","Campaign shared.")

    
    # EVENTS
    

    def _build_events(self):
        pg = self._page("events","⏱  Quest Events","Schedule events across realms")
        body=tk.Frame(pg,bg=BG); body.pack(fill=tk.BOTH,expand=True,padx=24,pady=8)
        left=tk.Frame(body,bg=BG); left.pack(side=tk.LEFT,fill=tk.BOTH,expand=True,padx=(0,12))
        right=tk.Frame(body,bg=BG); right.pack(side=tk.RIGHT,fill=tk.Y)

        fb=tk.Frame(left,bg=BG); fb.pack(fill=tk.X,pady=(0,8))
        _lbl(fb,"Campaign:",fg=TEXT,bg=BG).pack(side=tk.LEFT,padx=(0,4))
        self._ecv=tk.StringVar()
        self._ecc=_cbo(fb,self._ecv,width=22); self._ecc.pack(side=tk.LEFT,padx=4)
        _lbl(fb,"Range:",fg=TEXT,bg=BG).pack(side=tk.LEFT,padx=(8,4))
        self._erv=tk.StringVar(value="ALL")
        _cbo(fb,self._erv,["DAY","WEEK","MONTH","YEAR","ALL"],8).pack(side=tk.LEFT)
        _btn(fb,"Refresh",self._ref_events,8,color="#37474f").pack(side=tk.LEFT,padx=8)

        oc,ic=_card(left,"📋  Events"); oc.pack(fill=tk.BOTH,expand=True)
        lf=tk.Frame(ic,bg=PANEL); lf.pack(fill=tk.BOTH,expand=True)
        self._elist=_slist(lf,14)

        oc2,ic2=_card(right,"➕  Add Quest Event"); oc2.pack(fill=tk.X)
        self._evars: dict[str,tk.StringVar]={}
        for ltext,key in [("Name","en"),("Start Day","ed"),("Start Hour","eh"),
                           ("Minute","em"),("Duration (min)","edu")]:
            _lbl(ic2,ltext,bg=PANEL).pack(anchor="w")
            v=tk.StringVar(); self._evars[key]=v
            _ent(ic2,v,22).pack(anchor="w",pady=(2,8))
        _lbl(ic2,"Realm",bg=PANEL).pack(anchor="w")
        self._erealm=tk.StringVar()
        self._erc=_cbo(ic2,self._erealm,width=22); self._erc.pack(anchor="w",pady=(2,8))
        _btn(ic2,"Add Event",self._add_event,20).pack(anchor="w",pady=6)

    def _ref_events(self):
        camps=self.game.list_visible_campaigns()
        ev_vals=[f"{c.campaign_id}: {c.name}" for c in camps]
        self._ecc["values"]=ev_vals
        if ev_vals and self._ecv.get() not in ev_vals: self._ecv.set(ev_vals[0])
        rv=[f"{r.realm_id}: {r.name}" for r in sorted(self.game.realms.values(),key=lambda r:r.realm_id)]
        self._erc["values"]=rv
        if rv and not self._erealm.get(): self._erealm.set(rv[0])
        self._elist.delete(0,tk.END)
        cv=self._ecv.get()
        if not cv: return
        cid=int(cv.split(":")[0])
        camp=self.game.campaigns.get(cid)
        if not camp: return
        rm={"DAY":24*60,"WEEK":7*24*60,"MONTH":30*24*60,"YEAR":365*24*60,"ALL":None}
        within=rm.get(self._erv.get())
        now=self.game.clock.now.total_minutes
        evs=[]
        for eid in camp.event_ids:
            e=self.game.events.get(eid)
            if not e: continue
            if within is not None:
                if e.start_time.total_minutes<now: continue
                if e.start_time.total_minutes>now+within: continue
            evs.append(e)
        evs.sort(key=lambda e:e.start_time.total_minutes)
        for e in evs:
            r=self.game.realms.get(e.realm_id)
            self._elist.insert(tk.END,
                f"  [{e.event_id}] {e.name}  ·  {r.name if r else '?'}  ·  {e.start_time} → {e.end_time}")

    def _add_event(self):
        cv=self._ecv.get()
        if not cv: messagebox.showerror("Validation","Select a campaign."); return
        cid=int(cv.split(":")[0])
        camp=self.game.campaigns.get(cid)
        if not camp: return
        _,ce,_=self.game.campaign_access(camp)
        if not ce: messagebox.showerror("Permission","No edit access."); return
        n=self._evars["en"].get().strip()
        if not n: messagebox.showerror("Validation","Name required."); return
        try:
            day=int(self._evars["ed"].get())
            hr=int(self._evars["eh"].get())
            mn=int(self._evars["em"].get())
            dur=int(self._evars["edu"].get())
        except ValueError:
            messagebox.showerror("Validation","Time fields must be numbers."); return
        if not(0<=hr<=23 and 0<=mn<=59 and dur>0):
            messagebox.showerror("Validation","Invalid time values."); return
        rv=self._erealm.get()
        if not rv: messagebox.showerror("Validation","Select a realm."); return
        rid=int(rv.split(":")[0])
        start=WorldTime(day,hr,mn); end=start.add_minutes(dur)
        eid=self.game.next_event_id; self.game.next_event_id+=1
        self.game.events[eid]=QuestEvent(eid,n,start,end,rid)
        camp.event_ids.append(eid)
        for k in("en","ed","eh","em","edu"): self._evars[k].set("")
        self._ref_events()

    
    # CHARACTERS
    

    def _build_characters(self):
        pg=self._page("characters","🧙  Characters","Manage your adventuring roster")
        body=tk.Frame(pg,bg=BG); body.pack(fill=tk.BOTH,expand=True,padx=24,pady=8)
        left=tk.Frame(body,bg=BG); left.pack(side=tk.LEFT,fill=tk.BOTH,expand=True,padx=(0,12))
        right=tk.Frame(body,bg=BG); right.pack(side=tk.RIGHT,fill=tk.Y)

        oc,ic=_card(left,"🧙  Roster"); oc.pack(fill=tk.BOTH,expand=True)
        lf=tk.Frame(ic,bg=PANEL); lf.pack(fill=tk.BOTH,expand=True)
        self._charlist=_slist(lf,14)

        oc2,ic2=_card(right,"➕  Add Character"); oc2.pack(fill=tk.X,pady=(0,12))
        _lbl(ic2,"Name",bg=PANEL).pack(anchor="w")
        self._chname=tk.StringVar()
        _ent(ic2,self._chname).pack(anchor="w",pady=(2,8))
        _lbl(ic2,"Class",bg=PANEL).pack(anchor="w")
        self._chcls=tk.StringVar()
        _cbo(ic2,self._chcls,["Warrior","Mage","Rogue","Cleric","Ranger","Paladin"]).pack(anchor="w",pady=(2,8))
        _btn(ic2,"Add Character",self._add_char,20).pack(anchor="w",pady=4)

        oc3,ic3=_card(right,"🎒  Add Item to Character"); oc3.pack(fill=tk.X)
        _lbl(ic3,"Character",bg=PANEL).pack(anchor="w")
        self._ichv=tk.StringVar()
        self._ichc=_cbo(ic3,self._ichv,width=22); self._ichc.pack(anchor="w",pady=(2,8))
        _lbl(ic3,"Item Name",bg=PANEL).pack(anchor="w")
        self._iname=tk.StringVar()
        _ent(ic3,self._iname).pack(anchor="w",pady=(2,8))
        _lbl(ic3,"Description",bg=PANEL).pack(anchor="w")
        self._idesc=tk.StringVar()
        _ent(ic3,self._idesc).pack(anchor="w",pady=(2,8))
        _lbl(ic3,"Rarity",bg=PANEL).pack(anchor="w")
        self._irar=tk.StringVar(value="COMMON")
        _cbo(ic3,self._irar,["COMMON","RARE","ULTRA_RARE","LEGENDARY"],22).pack(anchor="w",pady=(2,8))
        _btn(ic3,"Add Item",self._add_item,20).pack(anchor="w",pady=4)

    def _ref_characters(self):
        self._charlist.delete(0,tk.END)
        chars=sorted(self.game.characters.values(),key=lambda c:c.character_id)
        for c in chars:
            self._charlist.insert(tk.END,f"  [{c.character_id}] {c.name}  ·  {c.character_class}  ·  Lv{c.level}")
            for item in c.inventory:
                self._charlist.insert(tk.END,f"      🎒 {item.name}  [{item.rarity.value}]  {item.description}")
        cv=[f"{c.character_id}: {c.name}" for c in chars]
        self._ichc["values"]=cv
        if cv and not self._ichv.get(): self._ichv.set(cv[0])

    def _add_char(self):
        n=self._chname.get().strip(); cl=self._chcls.get().strip()
        if not n or not cl: messagebox.showerror("Validation","Name and class required."); return
        cid=self.game.next_character_id; self.game.next_character_id+=1
        self.game.characters[cid]=Character(cid,n,cl)
        self._chname.set(""); self._ref_characters()

    def _add_item(self):
        cv=self._ichv.get()
        if not cv: messagebox.showerror("Validation","Select a character."); return
        cid=int(cv.split(":")[0])
        char=self.game.characters.get(cid)
        if not char: return
        n=self._iname.get().strip()
        if not n: messagebox.showerror("Validation","Item name required."); return
        char.inventory.append(Item(n,self._idesc.get().strip(),Rarity[self._irar.get()]))
        self._iname.set(""); self._idesc.set(""); self._ref_characters()

    
    # REALMS
    

    def _build_realms(self):
        pg=self._page("realms","🌍  Realms","Explore and manage GuildQuest realms")
        body=tk.Frame(pg,bg=BG); body.pack(fill=tk.BOTH,expand=True,padx=24,pady=8)
        left=tk.Frame(body,bg=BG); left.pack(side=tk.LEFT,fill=tk.BOTH,expand=True,padx=(0,12))
        right=tk.Frame(body,bg=BG); right.pack(side=tk.RIGHT,fill=tk.Y)

        oc,ic=_card(left,"🌍  All Realms"); oc.pack(fill=tk.BOTH,expand=True)
        lf=tk.Frame(ic,bg=PANEL); lf.pack(fill=tk.BOTH,expand=True)
        self._rlist=_slist(lf,16)

        oc2,ic2=_card(right,"➕  Add Realm"); oc2.pack(fill=tk.X)
        _lbl(ic2,"Name",bg=PANEL).pack(anchor="w")
        self._rname=tk.StringVar()
        _ent(ic2,self._rname).pack(anchor="w",pady=(2,8))
        _lbl(ic2,"Description",bg=PANEL).pack(anchor="w")
        self._rdesc=tk.StringVar()
        _ent(ic2,self._rdesc).pack(anchor="w",pady=(2,8))
        _lbl(ic2,"Time Offset (minutes)",bg=PANEL).pack(anchor="w")
        self._roff=tk.StringVar(value="0")
        _ent(ic2,self._roff,10).pack(anchor="w",pady=(2,8))
        _btn(ic2,"Add Realm",self._add_realm,20).pack(anchor="w",pady=6)

    def _ref_realms(self):
        self._rlist.delete(0,tk.END)
        for r in sorted(self.game.realms.values(),key=lambda r:r.realm_id):
            off=f"+{r.minute_offset}m" if r.minute_offset>=0 else f"{r.minute_offset}m"
            self._rlist.insert(tk.END,f"  [{r.realm_id}] {r.name}  ·  offset {off}")
            self._rlist.insert(tk.END,f"      {r.description}")
            self._rlist.insert(tk.END,"")

    def _add_realm(self):
        n=self._rname.get().strip()
        if not n: messagebox.showerror("Validation","Name required."); return
        try: off=int(self._roff.get())
        except ValueError: messagebox.showerror("Validation","Offset must be a number."); return
        rid=self.game.next_realm_id; self.game.next_realm_id+=1
        self.game.realms[rid]=Realm(rid,n,self._rdesc.get().strip(),off)
        self._rname.set(""); self._rdesc.set(""); self._roff.set("0")
        self._ref_realms()

    
    # USERS
    

    def _build_users(self):
        pg=self._page("users","👤  Users","Switch active user or create a new one")
        body=tk.Frame(pg,bg=BG); body.pack(fill=tk.BOTH,expand=True,padx=24,pady=8)
        oc,ic=_card(body,"👥  User List"); oc.pack(fill=tk.BOTH,expand=True,pady=(0,12))
        lf=tk.Frame(ic,bg=PANEL); lf.pack(fill=tk.BOTH,expand=True)
        self._ulist=_slist(lf,10)
        row=tk.Frame(body,bg=BG); row.pack(fill=tk.X,pady=8)
        oc2,ic2=_card(row,"🔄  Switch User"); oc2.pack(side=tk.LEFT,fill=tk.X,expand=True,padx=(0,12))
        self._swv=tk.StringVar()
        self._swc=_cbo(ic2,self._swv,width=24); self._swc.pack(anchor="w",pady=(0,8))
        _btn(ic2,"Switch User",self._switch_user,18).pack(anchor="w")
        oc3,ic3=_card(row,"➕  Create User"); oc3.pack(side=tk.LEFT,fill=tk.X,expand=True)
        self._nuv=tk.StringVar()
        _ent(ic3,self._nuv).pack(anchor="w",pady=(0,8))
        _btn(ic3,"Create User",self._create_user,18).pack(anchor="w")

    def _ref_users(self):
        self._ulist.delete(0,tk.END)
        users=sorted(self.game.users.values(),key=lambda u:u.user_id)
        vals=[]
        for u in users:
            m="  ★" if u.user_id==self.game.active_user_id else "   "
            pi=f"  ({u.profile.character_name})" if u.profile else ""
            self._ulist.insert(tk.END,f"{m} [{u.user_id}] {u.name}{pi}")
            vals.append(f"{u.user_id}: {u.name}")
        self._swc["values"]=vals

    def _switch_user(self):
        v=self._swv.get()
        if not v: return
        uid=int(v.split(":")[0])
        if uid in self.game.users:
            self.game.active_user_id=uid
            self._update_sb(); self._ref_users()

    def _create_user(self):
        n=self._nuv.get().strip()
        if not n: messagebox.showerror("Validation","Name required."); return
        uid=self.game.next_user_id; self.game.next_user_id+=1
        self.game.users[uid]=User(uid,n)
        self._nuv.set(""); self._ref_users()

    
    # PLAYER PROFILES
    

    def _build_profiles(self):
        pg=self._page("profiles","📊  Player Profiles","Stats, quest history and profile management")
        body=tk.Frame(pg,bg=BG); body.pack(fill=tk.BOTH,expand=True,padx=24,pady=8)
        left=tk.Frame(body,bg=BG); left.pack(side=tk.LEFT,fill=tk.BOTH,expand=True,padx=(0,12))
        right=tk.Frame(body,bg=BG); right.pack(side=tk.RIGHT,fill=tk.Y)

        oc,ic=_card(left,"📊  Stats  (active user)"); oc.pack(fill=tk.X,pady=(0,12))
        self._ptxt=tk.Text(ic,height=7,bg=ENTRY_BG,fg=TEXT,font=FM,relief="flat",bd=0,state="disabled")
        self._ptxt.pack(fill=tk.X)

        oc2,ic2=_card(left,"📋  Quest History"); oc2.pack(fill=tk.BOTH,expand=True,pady=(0,12))
        lf=tk.Frame(ic2,bg=PANEL); lf.pack(fill=tk.BOTH,expand=True)
        self._pquests=_slist(lf,6)

        oc3,ic3=_card(left,"🎒  Inventory Snapshot"); oc3.pack(fill=tk.BOTH,expand=True)
        lf2=tk.Frame(ic3,bg=PANEL); lf2.pack(fill=tk.BOTH,expand=True)
        self._pinv=_slist(lf2,5)

        oc4,ic4=_card(right,"✏️  Create / Edit Profile"); oc4.pack(fill=tk.X)
        _lbl(ic4,"Character Name",bg=PANEL).pack(anchor="w")
        self._pcn=tk.StringVar()
        _ent(ic4,self._pcn).pack(anchor="w",pady=(2,8))
        _lbl(ic4,"Preferred Realm",bg=PANEL).pack(anchor="w")
        self._prv=tk.StringVar()
        self._prc=_cbo(ic4,self._prv,width=24); self._prc.pack(anchor="w",pady=(2,12))
        _btn(ic4,"💾 Save Profile",self._save_profile,20).pack(anchor="w")
        _lbl(ic4,"\nShowing profile for the active user.\nSwitch users on the Users page.",
             font=FS,fg=TEXT_DIM,bg=PANEL,justify="left").pack(anchor="w",pady=8)

    def _ref_profiles(self):
        u=self.game.active_user; p=u.profile
        rv=[f"{r.realm_id}: {r.name}" for r in sorted(self.game.realms.values(),key=lambda r:r.realm_id)]
        self._prc["values"]=rv
        self._ptxt.config(state="normal"); self._ptxt.delete("1.0",tk.END)
        if p:
            tot=p.wins+p.losses
            wr=f"{p.wins/tot:.0%}" if tot>0 else "N/A"
            self._ptxt.insert(tk.END,
                f"  Player      : {u.name}\n"
                f"  Character   : {p.character_name}\n"
                f"  Realm       : {p.preferred_realm}\n"
                f"  Wins        : {p.wins}    Losses : {p.losses}    Win Rate : {wr}\n"
                f"  Quests Done : {p.quests_completed}\n"
                f"  Achievements: {', '.join(p.achievements) or 'none'}\n")
            self._pcn.set(p.character_name)
            m=next((v for v in rv if v.split(": ",1)[1]==p.preferred_realm),"")
            self._prv.set(m)
        else:
            self._ptxt.insert(tk.END,f"  No profile yet for {u.name}.\n  Fill in the form and click Save.")
            self._pcn.set("")
            if rv: self._prv.set(rv[0])
        self._ptxt.config(state="disabled")
        self._pquests.delete(0,tk.END)
        if p and p.quest_history:
            for q in p.quest_history: self._pquests.insert(tk.END,f"  ✓  {q}")
        else:
            self._pquests.insert(tk.END,"  (no quests recorded yet)")
        self._pinv.delete(0,tk.END)
        if p and p.inventory_snapshot:
            for item in p.inventory_snapshot:
                self._pinv.insert(tk.END,f"  {item.name}  [{item.rarity.value}]  {item.description}")
        else:
            self._pinv.insert(tk.END,"  (no inventory snapshot)")

    def _save_profile(self):
        cn=self._pcn.get().strip(); rv=self._prv.get()
        if not cn: messagebox.showerror("Validation","Character name required."); return
        if not rv: messagebox.showerror("Validation","Select a preferred realm."); return
        pref=rv.split(": ",1)[1]; u=self.game.active_user
        if u.profile is None:
            u.profile=PlayerProfile(character_name=cn,preferred_realm=pref)
        else:
            u.profile.character_name=cn; u.profile.preferred_realm=pref
        save_profiles(self.game.users)
        self._ref_profiles(); self._ref_miniadv()
        messagebox.showinfo("Saved","Profile saved.")

    
    # SETTINGS
    

    def _build_settings(self):
        pg=self._page("settings","⚙  Settings","Display preferences and world time")
        body=tk.Frame(pg,bg=BG); body.pack(fill=tk.BOTH,expand=True,padx=24,pady=8)
        row=tk.Frame(body,bg=BG); row.pack(fill=tk.X)

        oc,ic=_card(row,"🎨  Display Preferences")
        oc.pack(side=tk.LEFT,fill=tk.X,expand=True,padx=(0,12))
        _lbl(ic,"Theme",bg=PANEL).pack(anchor="w")
        self._thv=tk.StringVar()
        _cbo(ic,self._thv,["CLASSIC","MODERN"]).pack(anchor="w",pady=(2,10))
        _lbl(ic,"Time Display",bg=PANEL).pack(anchor="w")
        self._tdv=tk.StringVar()
        _cbo(ic,self._tdv,["WORLDCLOCK","REALMLOCAL","BOTH"]).pack(anchor="w",pady=(2,10))
        _lbl(ic,"Current Realm",bg=PANEL).pack(anchor="w")
        self._srv=tk.StringVar()
        self._src=_cbo(ic,self._srv,width=24); self._src.pack(anchor="w",pady=(2,10))
        _btn(ic,"💾 Save Settings",self._save_settings,20).pack(anchor="w",pady=8)

        oc2,ic2=_card(row,"🕐  World Time")
        oc2.pack(side=tk.LEFT,fill=tk.X,expand=True)
        self._wtd=tk.StringVar()
        tk.Label(ic2,textvariable=self._wtd,font=("Consolas",18,"bold"),
                 bg=PANEL,fg=ACCENT2).pack(pady=8)
        _lbl(ic2,"Advance by (minutes):",bg=PANEL).pack(anchor="w")
        self._adv=tk.StringVar()
        _ent(ic2,self._adv,10).pack(anchor="w",pady=(2,8))
        _btn(ic2,"⏩ Advance Time",self._advance_time,20).pack(anchor="w")

    def _ref_settings(self):
        s=self.game.active_user.settings
        self._thv.set(s.theme.value); self._tdv.set(s.time_display.value)
        rv=[f"{r.realm_id}: {r.name}" for r in sorted(self.game.realms.values(),key=lambda r:r.realm_id)]
        self._src["values"]=rv
        cur=self.game.realms.get(s.current_realm_id)
        if cur: self._srv.set(f"{cur.realm_id}: {cur.name}")
        elif rv: self._srv.set(rv[0])
        self._wtd.set(str(self.game.clock.now))
        self._update_sb()

    def _save_settings(self):
        s=self.game.active_user.settings
        s.theme=Theme[self._thv.get()]; s.time_display=TimeDisplay[self._tdv.get()]
        rv=self._srv.get()
        if rv: s.current_realm_id=int(rv.split(":")[0])
        self._ref_settings(); messagebox.showinfo("Saved","Settings saved.")

    def _advance_time(self):
        try:
            m=int(self._adv.get())
            if m<=0: raise ValueError
        except ValueError:
            messagebox.showerror("Validation","Enter a positive number."); return
        self.game.clock.advance_minutes(m)
        self._adv.set(""); self._ref_settings(); self._update_sb()



# Entry point


def main():
    root = tk.Tk()
    root.geometry("1200x740")
    root.configure(bg=BG)
    GuildQuestGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
