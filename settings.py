import json
import os
from copy import deepcopy


DEFAULT_CUSTOM_THEME = {
    "window_bg": "#11151b",
    "surface_bg": "#1a2029",
    "card_bg": "#202836",
    "border": "#3a4861",
    "text": "#e7edf5",
    "muted_text": "#aab6c8",
    "button_bg": "#2a3448",
    "button_hover": "#364865",
    "input_bg": "#121821",
    "list_bg": "#0f141b",
    "accent": "#2f7de1",
    "accent_hover": "#3b8cf0",
    "arrow": "#9fb3cf",
    "selection_bg": "#2b4468",
}

DEFAULT_SHORTCUTS = {
    "toggle_panel": "Ctrl+T",
    "refresh": "F5",
    "select_all": "Ctrl+A",
    "delete_checked": "Delete",
    "toggle_theme": "Ctrl+Shift+T",
    "export_markdown": "Ctrl+Shift+M",
}

DEFAULT_SETTINGS = {
    "theme_mode": "dark",
    "custom_theme": deepcopy(DEFAULT_CUSTOM_THEME),
    "shortcuts": deepcopy(DEFAULT_SHORTCUTS),
    "background_mode": False,
    "realtime_save_enabled": False,
    "realtime_save_dir": "",
}


class SettingsManager:
    def __init__(self, base_dir):
        self.path = os.path.join(base_dir, "user_settings.json")
        self.data = self._load()

    def _load(self):
        if not os.path.exists(self.path):
            return deepcopy(DEFAULT_SETTINGS)
        try:
            with open(self.path, "r", encoding="utf-8") as fp:
                loaded = json.load(fp)
            if not isinstance(loaded, dict):
                return deepcopy(DEFAULT_SETTINGS)
            merged = deepcopy(DEFAULT_SETTINGS)
            merged.update({k: v for k, v in loaded.items() if k in merged})
            if not isinstance(merged.get("custom_theme"), dict):
                merged["custom_theme"] = deepcopy(DEFAULT_CUSTOM_THEME)
            else:
                custom_theme = deepcopy(DEFAULT_CUSTOM_THEME)
                custom_theme.update(merged["custom_theme"])
                merged["custom_theme"] = custom_theme
            if not isinstance(merged.get("shortcuts"), dict):
                merged["shortcuts"] = deepcopy(DEFAULT_SHORTCUTS)
            else:
                shortcuts = deepcopy(DEFAULT_SHORTCUTS)
                shortcuts.update(
                    {k: str(v) for k, v in merged["shortcuts"].items() if k in DEFAULT_SHORTCUTS}
                )
                merged["shortcuts"] = shortcuts
            theme_mode = str(merged.get("theme_mode", "dark"))
            if theme_mode not in ("dark", "light", "custom"):
                merged["theme_mode"] = "dark"
            merged["background_mode"] = bool(merged.get("background_mode", False))
            merged["realtime_save_enabled"] = bool(merged.get("realtime_save_enabled", False))
            realtime_save_dir = merged.get("realtime_save_dir", "")
            merged["realtime_save_dir"] = str(realtime_save_dir).strip()
            return merged
        except (OSError, json.JSONDecodeError):
            return deepcopy(DEFAULT_SETTINGS)

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        temp_path = f"{self.path}.tmp"
        try:
            with open(temp_path, "w", encoding="utf-8") as fp:
                json.dump(self.data, fp, ensure_ascii=False, indent=2)
                fp.flush()
                os.fsync(fp.fileno())
            os.replace(temp_path, self.path)
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    def get_theme_mode(self):
        return self.data.get("theme_mode", "dark")

    def set_theme_mode(self, mode):
        self.data["theme_mode"] = mode if mode in ("dark", "light", "custom") else "dark"
        self.save()

    def get_custom_theme(self):
        custom_theme = deepcopy(DEFAULT_CUSTOM_THEME)
        custom_theme.update(self.data.get("custom_theme", {}))
        return custom_theme

    def set_custom_theme(self, palette):
        base = deepcopy(DEFAULT_CUSTOM_THEME)
        if isinstance(palette, dict):
            for key in base:
                if key in palette:
                    base[key] = str(palette[key])
        self.data["custom_theme"] = base
        self.save()

    def get_shortcuts(self):
        shortcuts = deepcopy(DEFAULT_SHORTCUTS)
        shortcuts.update(self.data.get("shortcuts", {}))
        return {k: str(v) for k, v in shortcuts.items()}

    def set_shortcuts(self, mapping):
        shortcuts = deepcopy(DEFAULT_SHORTCUTS)
        if isinstance(mapping, dict):
            for key in shortcuts:
                if key in mapping:
                    shortcuts[key] = str(mapping[key]).strip()
        self.data["shortcuts"] = shortcuts
        self.save()

    def get_background_mode(self):
        return bool(self.data.get("background_mode", False))

    def set_background_mode(self, enabled):
        self.data["background_mode"] = bool(enabled)
        self.save()

    def get_realtime_save_enabled(self):
        return bool(self.data.get("realtime_save_enabled", False))

    def set_realtime_save_enabled(self, enabled):
        self.data["realtime_save_enabled"] = bool(enabled)
        self.save()

    def get_realtime_save_dir(self):
        return str(self.data.get("realtime_save_dir", "")).strip()

    def set_realtime_save_dir(self, directory):
        self.data["realtime_save_dir"] = str(directory or "").strip()
        self.save()
