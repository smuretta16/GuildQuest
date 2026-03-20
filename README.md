# GuildQuest

Combined implementation based on:
- Sonja_Muretta_GUILDQUEST
- ThangNguyen_GUILDQUEST

## Run (GUI)

```bash
python3 guildquest_gui.py
```

## Included features

### Thang
- Add quest event (with realm selection)
- View campaign events
- Add item to character
- Delete campaign
- View characters

### Sonja
- Campaign features (create/manage visibility/access)
- Create campaign
- Views (day/week/month/year + all)
- Sharing (campaign permissions: VIEW/COLLABORATIVE)
- Settings (theme/time display/current realm)
- Advance world time

## How to play
1. Start the game with `python3 guildquest.py` (CLI) or `python3 guildquest_gui.py` (GUI).
2. In the main menu, use numbers to choose actions (`0` exits).
3. Go to `1. Users` to switch active user or create a new one.
4. Create a campaign from `2. Create campaign`.
5. Add realms with `5. Add realm` (optional) and add quest events with `3. Add quest event`.
6. Use `4. View campaign events` or `10. Views` to see events by time range.
7. Create characters with `6. Add character`, then use `7. Add item to character`.
8. Use `11. Share campaign` to share with another user (VIEW or COLLABORATIVE).
9. Customize display in `12. Settings` and move game time with `13. Advance world time`.

## Notes
- In-memory data only (no database yet)
- Seeded users, realms, campaigns, and events are included at startup
- CLI menu driven
- GUI uses `tkinter` (standard Python library)
