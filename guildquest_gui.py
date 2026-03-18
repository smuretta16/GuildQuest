import tkinter as tk
from tkinter import ttk, messagebox

from guildquest import (
    Campaign,
    Character,
    GuildQuestGame,
    Item,
    Permission,
    PlayerProfile,
    QuestEvent,
    Rarity,
    Realm,
    Theme,
    TimeDisplay,
    User,
    Visibility,
    WorldTime,
    save_profiles,
)


class GuildQuestGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("GuildQuest")
        self.game = GuildQuestGame()

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.tab_users = ttk.Frame(self.notebook)
        self.tab_campaigns = ttk.Frame(self.notebook)
        self.tab_events = ttk.Frame(self.notebook)
        self.tab_characters = ttk.Frame(self.notebook)
        self.tab_realms = ttk.Frame(self.notebook)
        self.tab_profiles = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_users, text="Users / Settings")
        self.notebook.add(self.tab_campaigns, text="Campaigns")
        self.notebook.add(self.tab_events, text="Quest Events")
        self.notebook.add(self.tab_characters, text="Characters")
        self.notebook.add(self.tab_realms, text="Realms")
        self.notebook.add(self.tab_profiles, text="Player Profile")

        self._build_users_tab()
        self._build_campaigns_tab()
        self._build_events_tab()
        self._build_characters_tab()
        self._build_realms_tab()
        self._build_profiles_tab()

        self._refresh_all()

    def _refresh_all(self) -> None:
        self._refresh_users()
        self._refresh_campaigns()
        self._refresh_events()
        self._refresh_characters()
        self._refresh_realms()
        self._refresh_settings()
        self._refresh_profiles()

    def _build_users_tab(self) -> None:
        frame = self.tab_users

        user_box = ttk.LabelFrame(frame, text="Active User")
        user_box.pack(fill=tk.X, padx=8, pady=6)

        self.active_user_var = tk.StringVar()
        self.user_combo = ttk.Combobox(user_box, textvariable=self.active_user_var, state="readonly")
        self.user_combo.pack(side=tk.LEFT, padx=8, pady=6)
        ttk.Button(user_box, text="Switch", command=self._switch_user).pack(side=tk.LEFT, padx=4)

        create_box = ttk.LabelFrame(frame, text="Create User")
        create_box.pack(fill=tk.X, padx=8, pady=6)
        self.new_user_name = tk.StringVar()
        ttk.Entry(create_box, textvariable=self.new_user_name, width=30).pack(side=tk.LEFT, padx=8, pady=6)
        ttk.Button(create_box, text="Create", command=self._create_user).pack(side=tk.LEFT, padx=4)

        settings_box = ttk.LabelFrame(frame, text="Settings")
        settings_box.pack(fill=tk.X, padx=8, pady=6)

        self.theme_var = tk.StringVar()
        self.time_display_var = tk.StringVar()
        self.current_realm_var = tk.StringVar()

        ttk.Label(settings_box, text="Theme").grid(row=0, column=0, sticky="w", padx=6, pady=4)
        self.theme_combo = ttk.Combobox(settings_box, textvariable=self.theme_var, state="readonly")
        self.theme_combo.grid(row=0, column=1, sticky="w", padx=6, pady=4)

        ttk.Label(settings_box, text="Time display").grid(row=1, column=0, sticky="w", padx=6, pady=4)
        self.time_display_combo = ttk.Combobox(settings_box, textvariable=self.time_display_var, state="readonly")
        self.time_display_combo.grid(row=1, column=1, sticky="w", padx=6, pady=4)

        ttk.Label(settings_box, text="Current realm").grid(row=2, column=0, sticky="w", padx=6, pady=4)
        self.current_realm_combo = ttk.Combobox(settings_box, textvariable=self.current_realm_var, state="readonly")
        self.current_realm_combo.grid(row=2, column=1, sticky="w", padx=6, pady=4)

        ttk.Button(settings_box, text="Save Settings", command=self._save_settings).grid(
            row=3, column=0, columnspan=2, sticky="w", padx=6, pady=6
        )

        time_box = ttk.LabelFrame(frame, text="World Time")
        time_box.pack(fill=tk.X, padx=8, pady=6)
        self.world_time_label = ttk.Label(time_box, text="")
        self.world_time_label.pack(side=tk.LEFT, padx=8, pady=6)
        self.advance_minutes_var = tk.StringVar()
        ttk.Entry(time_box, textvariable=self.advance_minutes_var, width=8).pack(side=tk.LEFT, padx=6)
        ttk.Button(time_box, text="Advance", command=self._advance_time).pack(side=tk.LEFT, padx=4)

    def _build_campaigns_tab(self) -> None:
        frame = self.tab_campaigns

        list_box = ttk.LabelFrame(frame, text="Campaigns")
        list_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=6)

        self.campaign_list = tk.Listbox(list_box, height=12)
        self.campaign_list.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        control_box = ttk.Frame(frame)
        control_box.pack(side=tk.RIGHT, fill=tk.Y, padx=8, pady=6)

        create_box = ttk.LabelFrame(control_box, text="Create Campaign")
        create_box.pack(fill=tk.X, pady=6)

        self.campaign_name_var = tk.StringVar()
        self.campaign_visibility_var = tk.StringVar()
        ttk.Label(create_box, text="Name").grid(row=0, column=0, sticky="w", padx=6, pady=4)
        ttk.Entry(create_box, textvariable=self.campaign_name_var, width=22).grid(
            row=0, column=1, padx=6, pady=4
        )
        ttk.Label(create_box, text="Visibility").grid(row=1, column=0, sticky="w", padx=6, pady=4)
        self.campaign_visibility_combo = ttk.Combobox(
            create_box, textvariable=self.campaign_visibility_var, state="readonly", width=20
        )
        self.campaign_visibility_combo.grid(row=1, column=1, padx=6, pady=4)
        ttk.Button(create_box, text="Create", command=self._create_campaign).grid(
            row=2, column=0, columnspan=2, padx=6, pady=6, sticky="w"
        )

        ttk.Button(control_box, text="Delete Selected", command=self._delete_campaign).pack(fill=tk.X, pady=4)

        share_box = ttk.LabelFrame(control_box, text="Share Campaign")
        share_box.pack(fill=tk.X, pady=6)
        self.share_user_var = tk.StringVar()
        self.share_perm_var = tk.StringVar()
        ttk.Label(share_box, text="User").grid(row=0, column=0, sticky="w", padx=6, pady=4)
        self.share_user_combo = ttk.Combobox(share_box, textvariable=self.share_user_var, state="readonly")
        self.share_user_combo.grid(row=0, column=1, padx=6, pady=4)
        ttk.Label(share_box, text="Permission").grid(row=1, column=0, sticky="w", padx=6, pady=4)
        self.share_perm_combo = ttk.Combobox(share_box, textvariable=self.share_perm_var, state="readonly")
        self.share_perm_combo.grid(row=1, column=1, padx=6, pady=4)
        ttk.Button(share_box, text="Share", command=self._share_campaign).grid(
            row=2, column=0, columnspan=2, padx=6, pady=6, sticky="w"
        )

    def _build_events_tab(self) -> None:
        frame = self.tab_events

        top = ttk.Frame(frame)
        top.pack(fill=tk.X, padx=8, pady=6)

        ttk.Label(top, text="Campaign").pack(side=tk.LEFT, padx=4)
        self.event_campaign_var = tk.StringVar()
        self.event_campaign_combo = ttk.Combobox(top, textvariable=self.event_campaign_var, state="readonly")
        self.event_campaign_combo.pack(side=tk.LEFT, padx=4)

        ttk.Label(top, text="View Range").pack(side=tk.LEFT, padx=4)
        self.event_range_var = tk.StringVar()
        self.event_range_combo = ttk.Combobox(top, textvariable=self.event_range_var, state="readonly")
        self.event_range_combo.pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="Refresh", command=self._refresh_events).pack(side=tk.LEFT, padx=6)

        self.event_list = tk.Listbox(frame, height=12)
        self.event_list.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)

        add_box = ttk.LabelFrame(frame, text="Add Quest Event")
        add_box.pack(fill=tk.X, padx=8, pady=6)

        self.event_name_var = tk.StringVar()
        self.event_day_var = tk.StringVar()
        self.event_hour_var = tk.StringVar()
        self.event_minute_var = tk.StringVar()
        self.event_duration_var = tk.StringVar()
        self.event_realm_var = tk.StringVar()

        ttk.Label(add_box, text="Name").grid(row=0, column=0, sticky="w", padx=6, pady=4)
        ttk.Entry(add_box, textvariable=self.event_name_var, width=26).grid(row=0, column=1, padx=6, pady=4)
        ttk.Label(add_box, text="Day").grid(row=0, column=2, sticky="w", padx=6, pady=4)
        ttk.Entry(add_box, textvariable=self.event_day_var, width=6).grid(row=0, column=3, padx=6, pady=4)
        ttk.Label(add_box, text="Hour").grid(row=1, column=0, sticky="w", padx=6, pady=4)
        ttk.Entry(add_box, textvariable=self.event_hour_var, width=6).grid(row=1, column=1, padx=6, pady=4)
        ttk.Label(add_box, text="Minute").grid(row=1, column=2, sticky="w", padx=6, pady=4)
        ttk.Entry(add_box, textvariable=self.event_minute_var, width=6).grid(row=1, column=3, padx=6, pady=4)
        ttk.Label(add_box, text="Duration (min)").grid(row=2, column=0, sticky="w", padx=6, pady=4)
        ttk.Entry(add_box, textvariable=self.event_duration_var, width=10).grid(row=2, column=1, padx=6, pady=4)
        ttk.Label(add_box, text="Realm").grid(row=2, column=2, sticky="w", padx=6, pady=4)
        self.event_realm_combo = ttk.Combobox(add_box, textvariable=self.event_realm_var, state="readonly")
        self.event_realm_combo.grid(row=2, column=3, padx=6, pady=4)

        ttk.Button(add_box, text="Add Event", command=self._add_event).grid(
            row=3, column=0, columnspan=4, padx=6, pady=6, sticky="w"
        )

    def _build_characters_tab(self) -> None:
        frame = self.tab_characters

        list_box = ttk.LabelFrame(frame, text="Characters")
        list_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=6)
        self.character_list = tk.Listbox(list_box, height=12)
        self.character_list.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        control_box = ttk.Frame(frame)
        control_box.pack(side=tk.RIGHT, fill=tk.Y, padx=8, pady=6)

        create_box = ttk.LabelFrame(control_box, text="Add Character")
        create_box.pack(fill=tk.X, pady=6)
        self.character_name_var = tk.StringVar()
        self.character_class_var = tk.StringVar()
        ttk.Label(create_box, text="Name").grid(row=0, column=0, sticky="w", padx=6, pady=4)
        ttk.Entry(create_box, textvariable=self.character_name_var, width=20).grid(
            row=0, column=1, padx=6, pady=4
        )
        ttk.Label(create_box, text="Class").grid(row=1, column=0, sticky="w", padx=6, pady=4)
        ttk.Entry(create_box, textvariable=self.character_class_var, width=20).grid(
            row=1, column=1, padx=6, pady=4
        )
        ttk.Button(create_box, text="Create", command=self._add_character).grid(
            row=2, column=0, columnspan=2, padx=6, pady=6, sticky="w"
        )

        item_box = ttk.LabelFrame(control_box, text="Add Item")
        item_box.pack(fill=tk.X, pady=6)
        self.item_character_var = tk.StringVar()
        self.item_name_var = tk.StringVar()
        self.item_desc_var = tk.StringVar()
        self.item_rarity_var = tk.StringVar()

        ttk.Label(item_box, text="Character").grid(row=0, column=0, sticky="w", padx=6, pady=4)
        self.item_character_combo = ttk.Combobox(item_box, textvariable=self.item_character_var, state="readonly")
        self.item_character_combo.grid(row=0, column=1, padx=6, pady=4)
        ttk.Label(item_box, text="Item").grid(row=1, column=0, sticky="w", padx=6, pady=4)
        ttk.Entry(item_box, textvariable=self.item_name_var, width=20).grid(row=1, column=1, padx=6, pady=4)
        ttk.Label(item_box, text="Description").grid(row=2, column=0, sticky="w", padx=6, pady=4)
        ttk.Entry(item_box, textvariable=self.item_desc_var, width=20).grid(row=2, column=1, padx=6, pady=4)
        ttk.Label(item_box, text="Rarity").grid(row=3, column=0, sticky="w", padx=6, pady=4)
        self.item_rarity_combo = ttk.Combobox(item_box, textvariable=self.item_rarity_var, state="readonly")
        self.item_rarity_combo.grid(row=3, column=1, padx=6, pady=4)
        ttk.Button(item_box, text="Add Item", command=self._add_item).grid(
            row=4, column=0, columnspan=2, padx=6, pady=6, sticky="w"
        )

    def _build_realms_tab(self) -> None:
        frame = self.tab_realms
        list_box = ttk.LabelFrame(frame, text="Realms")
        list_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=6)
        self.realm_list = tk.Listbox(list_box, height=12)
        self.realm_list.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        control_box = ttk.Frame(frame)
        control_box.pack(side=tk.RIGHT, fill=tk.Y, padx=8, pady=6)

        add_box = ttk.LabelFrame(control_box, text="Add Realm")
        add_box.pack(fill=tk.X, pady=6)
        self.realm_name_var = tk.StringVar()
        self.realm_desc_var = tk.StringVar()
        self.realm_offset_var = tk.StringVar()
        ttk.Label(add_box, text="Name").grid(row=0, column=0, sticky="w", padx=6, pady=4)
        ttk.Entry(add_box, textvariable=self.realm_name_var, width=20).grid(row=0, column=1, padx=6, pady=4)
        ttk.Label(add_box, text="Description").grid(row=1, column=0, sticky="w", padx=6, pady=4)
        ttk.Entry(add_box, textvariable=self.realm_desc_var, width=20).grid(row=1, column=1, padx=6, pady=4)
        ttk.Label(add_box, text="Offset (min)").grid(row=2, column=0, sticky="w", padx=6, pady=4)
        ttk.Entry(add_box, textvariable=self.realm_offset_var, width=10).grid(row=2, column=1, padx=6, pady=4)
        ttk.Button(add_box, text="Add Realm", command=self._add_realm).grid(
            row=3, column=0, columnspan=2, padx=6, pady=6, sticky="w"
        )

    def _refresh_users(self) -> None:
        users = sorted(self.game.users.values(), key=lambda u: u.user_id)
        values = [f"{u.user_id}: {u.name}" for u in users]
        self.user_combo["values"] = values
        active = self.game.active_user
        self.active_user_var.set(f"{active.user_id}: {active.name}")

        share_targets = [u for u in users if u.user_id != self.game.active_user_id]
        self.share_user_combo["values"] = [f"{u.user_id}: {u.name}" for u in share_targets]

    def _refresh_settings(self) -> None:
        settings = self.game.active_user.settings
        self.theme_combo["values"] = [t.value for t in Theme]
        self.time_display_combo["values"] = [t.value for t in TimeDisplay]
        self.current_realm_combo["values"] = [
            f"{r.realm_id}: {r.name}" for r in sorted(self.game.realms.values(), key=lambda r: r.realm_id)
        ]
        self.theme_var.set(settings.theme.value)
        self.time_display_var.set(settings.time_display.value)
        current = self.game.realms.get(settings.current_realm_id)
        if current:
            self.current_realm_var.set(f"{current.realm_id}: {current.name}")
        elif self.current_realm_combo["values"]:
            self.current_realm_var.set(self.current_realm_combo["values"][0])
        else:
            self.current_realm_var.set("")
        self.world_time_label.config(text=f"World time: {self.game.clock.now}")

    def _refresh_campaigns(self) -> None:
        self.campaign_list.delete(0, tk.END)
        for c in self.game.list_visible_campaigns():
            _, can_edit, is_owner = self.game.campaign_access(c)
            role = "owner" if is_owner else ("editor" if can_edit else "viewer")
            self.campaign_list.insert(tk.END, f"[{c.campaign_id}] {c.name} ({c.visibility}, {role})")

        self.campaign_visibility_combo["values"] = [v.value for v in Visibility]
        self.campaign_visibility_var.set(Visibility.PRIVATE.value)
        self.share_perm_combo["values"] = [p.value for p in Permission]
        if not self.share_perm_var.get():
            self.share_perm_var.set(Permission.VIEW.value)

        campaigns = self.game.list_visible_campaigns()
        event_values = [f"{c.campaign_id}: {c.name}" for c in campaigns]
        self.event_campaign_combo["values"] = event_values
        if event_values:
            if self.event_campaign_var.get() not in event_values:
                self.event_campaign_var.set(event_values[0])
        else:
            self.event_campaign_var.set("")

    def _refresh_events(self) -> None:
        self.event_list.delete(0, tk.END)
        self.event_range_combo["values"] = ["DAY", "WEEK", "MONTH", "YEAR", "ALL"]
        if not self.event_range_var.get():
            self.event_range_var.set("ALL")

        campaigns = self.game.list_visible_campaigns()
        if campaigns:
            self.event_campaign_combo["values"] = [f"{c.campaign_id}: {c.name}" for c in campaigns]
            if self.event_campaign_var.get() not in self.event_campaign_combo["values"]:
                self.event_campaign_var.set(self.event_campaign_combo["values"][0])
        else:
            self.event_campaign_combo["values"] = []
            self.event_campaign_var.set("")
            return

        campaign_id = self._selected_campaign_id(self.event_campaign_var.get())
        campaign = self.game.campaigns.get(campaign_id)
        if campaign is None:
            return

        range_map = {
            "DAY": 24 * 60,
            "WEEK": 7 * 24 * 60,
            "MONTH": 30 * 24 * 60,
            "YEAR": 365 * 24 * 60,
            "ALL": None,
        }
        within = range_map[self.event_range_var.get()]

        now_total = self.game.clock.now.total_minutes
        events = []
        for eid in campaign.event_ids:
            event = self.game.events.get(eid)
            if event is None:
                continue
            if within is not None:
                if event.start_time.total_minutes < now_total:
                    continue
                if event.start_time.total_minutes > now_total + within:
                    continue
            events.append(event)

        events.sort(key=lambda e: e.start_time.total_minutes)
        for e in events:
            realm = self.game.realms.get(e.realm_id)
            realm_name = realm.name if realm else "Unknown"
            start = self.game.format_time_for_user(e.start_time, e.realm_id)
            end = self.game.format_time_for_user(e.end_time, e.realm_id)
            self.event_list.insert(
                tk.END, f"[{e.event_id}] {e.name} | {realm_name} | {start} -> {end}"
            )

        self.event_realm_combo["values"] = [
            f"{r.realm_id}: {r.name}" for r in sorted(self.game.realms.values(), key=lambda r: r.realm_id)
        ]
        if self.event_realm_combo["values"] and not self.event_realm_var.get():
            self.event_realm_var.set(self.event_realm_combo["values"][0])

    def _refresh_characters(self) -> None:
        self.character_list.delete(0, tk.END)
        characters = sorted(self.game.characters.values(), key=lambda c: c.character_id)
        for c in characters:
            items = ", ".join([f"{i.name}({i.rarity})" for i in c.inventory]) if c.inventory else "(empty)"
            self.character_list.insert(
                tk.END, f"[{c.character_id}] {c.name} ({c.character_class}) | Items: {items}"
            )

        self.item_character_combo["values"] = [f"{c.character_id}: {c.name}" for c in characters]
        self.item_rarity_combo["values"] = [r.value for r in Rarity]
        if characters and not self.item_character_var.get():
            self.item_character_var.set(self.item_character_combo["values"][0])
        if not self.item_rarity_var.get():
            self.item_rarity_var.set(Rarity.COMMON.value)

    def _refresh_realms(self) -> None:
        self.realm_list.delete(0, tk.END)
        for r in sorted(self.game.realms.values(), key=lambda r: r.realm_id):
            self.realm_list.insert(tk.END, f"[{r.realm_id}] {r.name} (offset {r.minute_offset:+}m)")

    def _switch_user(self) -> None:
        value = self.active_user_var.get()
        if not value:
            return
        user_id = int(value.split(":", 1)[0])
        if user_id in self.game.users:
            self.game.active_user_id = user_id
            self._refresh_all()

    def _create_user(self) -> None:
        name = self.new_user_name.get().strip()
        if not name:
            messagebox.showerror("Validation", "User name is required.")
            return
        self.game.users[self.game.next_user_id] = User(self.game.next_user_id, name)
        self.game.next_user_id += 1
        self.new_user_name.set("")
        self._refresh_all()

    def _save_settings(self) -> None:
        settings = self.game.active_user.settings
        settings.theme = Theme[self.theme_var.get()]
        settings.time_display = TimeDisplay[self.time_display_var.get()]
        if self.current_realm_var.get():
            settings.current_realm_id = int(self.current_realm_var.get().split(":", 1)[0])
        self._refresh_settings()

    def _advance_time(self) -> None:
        raw = self.advance_minutes_var.get().strip()
        if not raw:
            return
        try:
            minutes = int(raw)
        except ValueError:
            messagebox.showerror("Validation", "Advance minutes must be a number.")
            return
        if minutes <= 0:
            messagebox.showerror("Validation", "Advance minutes must be > 0.")
            return
        self.game.clock.advance_minutes(minutes)
        self.advance_minutes_var.set("")
        self._refresh_events()
        self._refresh_settings()

    def _create_campaign(self) -> None:
        name = self.campaign_name_var.get().strip()
        if not name:
            messagebox.showerror("Validation", "Campaign name is required.")
            return
        visibility = Visibility[self.campaign_visibility_var.get()]
        campaign_id = self.game.next_campaign_id
        self.game.next_campaign_id += 1
        self.game.campaigns[campaign_id] = Campaign(
            campaign_id, self.game.active_user_id, name, visibility
        )
        self.campaign_name_var.set("")
        self._refresh_campaigns()
        self._refresh_events()

    def _selected_campaign_id(self, value: str) -> int:
        return int(value.split(":", 1)[0]) if value else -1

    def _delete_campaign(self) -> None:
        idxs = self.campaign_list.curselection()
        if not idxs:
            return
        text = self.campaign_list.get(idxs[0])
        cid = int(text.split("]", 1)[0].lstrip("["))
        campaign = self.game.campaigns.get(cid)
        if campaign is None:
            return
        _, _, is_owner = self.game.campaign_access(campaign)
        if not is_owner:
            messagebox.showerror("Permission", "Only the owner can delete a campaign.")
            return
        if not messagebox.askyesno("Delete", f"Delete campaign '{campaign.name}'?"):
            return
        for eid in campaign.event_ids:
            self.game.events.pop(eid, None)
        self.game.campaigns.pop(campaign.campaign_id, None)
        self._refresh_all()

    def _share_campaign(self) -> None:
        idxs = self.campaign_list.curselection()
        if not idxs:
            return
        text = self.campaign_list.get(idxs[0])
        cid = int(text.split("]", 1)[0].lstrip("["))
        campaign = self.game.campaigns.get(cid)
        if campaign is None:
            return
        _, _, is_owner = self.game.campaign_access(campaign)
        if not is_owner:
            messagebox.showerror("Permission", "Only the owner can share a campaign.")
            return

        user_value = self.share_user_var.get()
        if not user_value:
            messagebox.showerror("Validation", "Select a user to share with.")
            return
        user_id = int(user_value.split(":", 1)[0])
        if not self.share_perm_var.get():
            messagebox.showerror("Validation", "Select a permission level.")
            return
        perm = Permission[self.share_perm_var.get()]
        campaign.shares[user_id] = perm
        self._refresh_campaigns()

    def _add_event(self) -> None:
        campaign_value = self.event_campaign_var.get()
        if not campaign_value:
            messagebox.showerror("Validation", "Select a campaign.")
            return
        campaign = self.game.campaigns.get(self._selected_campaign_id(campaign_value))
        if campaign is None:
            return
        _, can_edit, _ = self.game.campaign_access(campaign)
        if not can_edit:
            messagebox.showerror("Permission", "You do not have edit access for this campaign.")
            return

        name = self.event_name_var.get().strip()
        if not name:
            messagebox.showerror("Validation", "Event name is required.")
            return

        try:
            day = int(self.event_day_var.get())
            hour = int(self.event_hour_var.get())
            minute = int(self.event_minute_var.get())
            duration = int(self.event_duration_var.get())
        except ValueError:
            messagebox.showerror("Validation", "Day/hour/minute/duration must be numbers.")
            return

        if day < 0 or hour < 0 or hour > 23 or minute < 0 or minute > 59 or duration <= 0:
            messagebox.showerror("Validation", "Please enter valid time values.")
            return

        realm_value = self.event_realm_var.get()
        if not realm_value:
            messagebox.showerror("Validation", "Select a realm.")
            return
        realm_id = int(realm_value.split(":", 1)[0])

        start = WorldTime(day, hour, minute)
        end = start.add_minutes(duration)
        event_id = self.game.next_event_id
        self.game.next_event_id += 1
        self.game.events[event_id] = QuestEvent(event_id, name, start, end, realm_id)
        campaign.event_ids.append(event_id)

        self.event_name_var.set("")
        self.event_day_var.set("")
        self.event_hour_var.set("")
        self.event_minute_var.set("")
        self.event_duration_var.set("")
        self._refresh_events()

    def _add_character(self) -> None:
        name = self.character_name_var.get().strip()
        char_class = self.character_class_var.get().strip()
        if not name or not char_class:
            messagebox.showerror("Validation", "Character name and class are required.")
            return
        cid = self.game.next_character_id
        self.game.next_character_id += 1
        self.game.characters[cid] = Character(cid, name, char_class)
        self.character_name_var.set("")
        self.character_class_var.set("")
        self._refresh_characters()

    def _add_item(self) -> None:
        character_value = self.item_character_var.get()
        if not character_value:
            messagebox.showerror("Validation", "Select a character.")
            return
        char_id = int(character_value.split(":", 1)[0])
        character = self.game.characters.get(char_id)
        if character is None:
            return

        name = self.item_name_var.get().strip()
        desc = self.item_desc_var.get().strip()
        if not name:
            messagebox.showerror("Validation", "Item name is required.")
            return

        rarity = Rarity[self.item_rarity_var.get()]
        character.inventory.append(Item(name, desc, rarity))
        self.item_name_var.set("")
        self.item_desc_var.set("")
        self._refresh_characters()

    def _build_profiles_tab(self) -> None:
        frame = self.tab_profiles

        # ── Left: read-only profile display ──────────────────────────────
        display = ttk.Frame(frame)
        display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=6)

        stats_box = ttk.LabelFrame(display, text="Stats")
        stats_box.pack(fill=tk.X, pady=(0, 6))

        self.profile_stats_text = tk.Text(stats_box, height=7, state="disabled", wrap="word")
        self.profile_stats_text.pack(fill=tk.X, padx=6, pady=6)

        history_box = ttk.LabelFrame(display, text="Quest History")
        history_box.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

        self.profile_quest_list = tk.Listbox(history_box, height=6)
        self.profile_quest_list.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        snapshot_box = ttk.LabelFrame(display, text="Inventory Snapshot")
        snapshot_box.pack(fill=tk.BOTH, expand=True)

        self.profile_inventory_list = tk.Listbox(snapshot_box, height=5)
        self.profile_inventory_list.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # ── Right: create/edit form ───────────────────────────────────────
        edit_box = ttk.LabelFrame(frame, text="Create / Edit Profile")
        edit_box.pack(side=tk.RIGHT, fill=tk.Y, padx=8, pady=6)

        self.profile_char_name_var = tk.StringVar()
        self.profile_realm_var = tk.StringVar()

        ttk.Label(edit_box, text="Character Name").grid(row=0, column=0, sticky="w", padx=6, pady=4)
        ttk.Entry(edit_box, textvariable=self.profile_char_name_var, width=22).grid(
            row=0, column=1, padx=6, pady=4
        )

        ttk.Label(edit_box, text="Preferred Realm").grid(row=1, column=0, sticky="w", padx=6, pady=4)
        self.profile_realm_combo = ttk.Combobox(
            edit_box, textvariable=self.profile_realm_var, state="readonly", width=20
        )
        self.profile_realm_combo.grid(row=1, column=1, padx=6, pady=4)

        ttk.Button(edit_box, text="Save Profile", command=self._save_profile).grid(
            row=2, column=0, columnspan=2, padx=6, pady=8, sticky="w"
        )

        ttk.Separator(edit_box, orient="horizontal").grid(
            row=3, column=0, columnspan=2, sticky="ew", padx=6, pady=4
        )
        ttk.Label(edit_box, text="Active user's profile is shown on the left.",
                  wraplength=180, foreground="gray").grid(
            row=4, column=0, columnspan=2, padx=6, pady=4, sticky="w"
        )

    def _refresh_profiles(self) -> None:
        user = self.game.active_user
        p = user.profile

        # Update realm dropdown
        realm_values = [
            f"{r.realm_id}: {r.name}"
            for r in sorted(self.game.realms.values(), key=lambda r: r.realm_id)
        ]
        self.profile_realm_combo["values"] = realm_values

        # Stats text
        self.profile_stats_text.config(state="normal")
        self.profile_stats_text.delete("1.0", tk.END)
        if p:
            total = p.wins + p.losses
            win_rate = f"{p.wins / total:.0%}" if total > 0 else "N/A"
            stats = (
                f"Player     : {user.name}\n"
                f"Character  : {p.character_name}\n"
                f"Realm      : {p.preferred_realm}\n"
                f"Wins       : {p.wins}   Losses: {p.losses}   Win Rate: {win_rate}\n"
                f"Quests     : {p.quests_completed}\n"
                f"Achievements: {', '.join(p.achievements) if p.achievements else 'none'}"
            )
            self.profile_stats_text.insert(tk.END, stats)
            # Pre-fill the edit form with current values
            self.profile_char_name_var.set(p.character_name)
            matching = next(
                (v for v in realm_values if v.split(": ", 1)[1] == p.preferred_realm), ""
            )
            self.profile_realm_var.set(matching)
        else:
            self.profile_stats_text.insert(tk.END, f"No profile yet for {user.name}.\nFill in the form and click Save Profile.")
            self.profile_char_name_var.set("")
            if realm_values:
                self.profile_realm_var.set(realm_values[0])
        self.profile_stats_text.config(state="disabled")

        # Quest history
        self.profile_quest_list.delete(0, tk.END)
        if p and p.quest_history:
            for quest in p.quest_history:
                self.profile_quest_list.insert(tk.END, quest)
        else:
            self.profile_quest_list.insert(tk.END, "(no quests recorded yet)")

        # Inventory snapshot
        self.profile_inventory_list.delete(0, tk.END)
        if p and p.inventory_snapshot:
            for item in p.inventory_snapshot:
                self.profile_inventory_list.insert(tk.END, f"{item.name}  [{item.rarity.value}]  {item.description}")
        else:
            self.profile_inventory_list.insert(tk.END, "(no inventory snapshot yet)")

    def _save_profile(self) -> None:
        char_name = self.profile_char_name_var.get().strip()
        realm_value = self.profile_realm_var.get()
        if not char_name:
            messagebox.showerror("Validation", "Character name is required.")
            return
        if not realm_value:
            messagebox.showerror("Validation", "Select a preferred realm.")
            return
        preferred_realm = realm_value.split(": ", 1)[1]

        user = self.game.active_user
        if user.profile is None:
            user.profile = PlayerProfile(
                character_name=char_name,
                preferred_realm=preferred_realm,
            )
        else:
            user.profile.character_name = char_name
            user.profile.preferred_realm = preferred_realm

        save_profiles(self.game.users)
        self._refresh_profiles()
        messagebox.showinfo("Profile", "Profile saved.")

    def _add_realm(self) -> None:
        name = self.realm_name_var.get().strip()
        desc = self.realm_desc_var.get().strip()
        try:
            offset = int(self.realm_offset_var.get())
        except ValueError:
            messagebox.showerror("Validation", "Offset must be a number.")
            return
        if not name:
            messagebox.showerror("Validation", "Realm name is required.")
            return
        rid = self.game.next_realm_id
        self.game.next_realm_id += 1
        self.game.realms[rid] = Realm(rid, name, desc, offset)
        self.realm_name_var.set("")
        self.realm_desc_var.set("")
        self.realm_offset_var.set("")
        self._refresh_realms()
        self._refresh_events()
        self._refresh_settings()


def main() -> None:
    root = tk.Tk()
    root.geometry("980x620")
    GuildQuestGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
