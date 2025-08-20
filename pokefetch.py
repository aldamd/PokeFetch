#!/usr/bin/env python3

import re
from collections import Counter
import json


class PokeFastFetch:
    def __init__(self, offset: int, cached_path: str, ff_config_path: str) -> None:
        self._offset = offset
        self._cached_path = cached_path
        self._ff_config_path = ff_config_path

        self._pokemon = None
        self._pokemon_lines = None
        self._ff_lines = 0
        self._results_map = None
        self._color_fmt = None
        self._extract_colors()

        self._ff_config = {}
        self._read_ff_config()

        self._write_ff_config()

    @staticmethod
    def _quantize_color(rgb: tuple, step: int = 8) -> tuple:
        return tuple((c // step) * step for c in rgb)

    def _extract_colors(self) -> None:
        with open(self._cached_path) as f:
            pokemon = f.read().strip()
            pokemon_lines = len(pokemon.split("\n"))
        ff_lines = pokemon_lines + OFFSET

        pattern = r"(?:38|48);2;(\d{1,3});(\d{1,3});(\d{1,3})"
        results = re.findall(pattern, pokemon)
        results = [tuple(map(int, c)) for c in results]
        results = [
            (r, g, b)
            for (r, g, b) in results
            if not (all(c < 90 for c in (r, g, b)) or all(c > 180 for c in (r, g, b)))
        ]
        if len(results) == 0:
            raise ValueError("ANSII parsing failed, zero results found")

        binned = [self._quantize_color(c) for c in results]
        results_map = Counter(binned)
        r, g, b = results_map.most_common(1)[0][0]
        color_fmt = f"38;2;{r};{g};{b}"

        self._pokemon = pokemon
        self._pokemon_lines = pokemon_lines
        self._ff_lines = ff_lines
        self._results_map = results_map
        self._color_fmt = color_fmt

    def _read_ff_config(self) -> None:
        with open(self._ff_config_path) as f:
            self._ff_config = json.load(f)
        self._ff_config["modules"] = ["break", "title"]

    def _write_ff_config(self) -> None:
        modules = [
            {
                "type": "users",
                "key": "users ",
                "keyColor": self._color_fmt,
            },
            {
                "type": "de",
                "key": "de    ",
                "keyColor": self._color_fmt,
            },
            {
                "type": "shell",
                "key": "shell ",
                "keyColor": self._color_fmt,
            },
            {
                "type": "terminal",
                "key": "term  ",
                "keyColor": self._color_fmt,
            },
            "break",
            {
                "type": "dns",
                "key": "dns   ",
                "keyColor": self._color_fmt,
            },
            {
                "type": "localip",
                "key": "ipv4  ",
                "keyColor": self._color_fmt,
                "format": "{ifname}: {ipv4}",
            },
            {
                "type": "wifi",
                "key": "wifi  ",
                "keyColor": self._color_fmt,
                "format": "{ssid} ({signal-quality}) - {protocol}",
            },
            "break",
            {
                "type": "battery",
                "key": "bat   ",
                "keyColor": self._color_fmt,
                "format": "{capacity} [{status}] ({cycle-count})",
            },
            {
                "type": "disk",
                "key": "disk  ",
                "keyColor": self._color_fmt,
            },
            {
                "type": "memory",
                "key": "memory",
                "keyColor": self._color_fmt,
            },
            {
                "type": "gpu",
                "key": "gpu   ",
                "keyColor": self._color_fmt,
            },
            {
                "type": "cpu",
                "key": "cpu   ",
                "keyColor": self._color_fmt,
            },
            "break",
            {
                "type": "uptime",
                "format": "{?days}{days}d {?}{hours}h {minutes}m",
                "key": "uptime",
                "keyColor": self._color_fmt,
            },
            {
                "type": "packages",
                "key": "pkgs  ",
                "keyColor": self._color_fmt,
            },
            {
                "type": "host",
                "key": "host  ",
                "format": "{vendor} {family}",
                "keyColor": self._color_fmt,
            },
            {
                "type": "kernel",
                "key": "kernel",
                "keyColor": self._color_fmt,
            },
            {
                "type": "os",
                "key": "os    ",
                "keyColor": self._color_fmt,
            },
        ]

        if self._ff_config.get("display", {}).get("color", {}):
            self._ff_config["display"]["color"]["title"] = self._color_fmt
        self._ff_config["display"]["color"]["title"]

        for i in range(self._ff_lines):
            try:
                module = modules.pop()
                if self._ff_lines - i <= 2 and module == "break":
                    while module == "break":
                        module = modules.pop()
                self._ff_config["modules"].append(module)
            except IndexError:
                break
        self._ff_config["modules"].append("break")

        with open(self._ff_config_path, "w") as f:
            json.dump(self._ff_config, f, indent=1)


if __name__ == "__main__":
    HOMEDIR = r"/home/aldamd"
    OFFSET = -3  # offset from fastfetch config preamble to module entries
    CACHED_PATH = rf"{HOMEDIR}/.cache/pokemon.txt"
    FF_CONFIG_PATH = rf"{HOMEDIR}/.config/fastfetch/config.jsonc"
    PokeFastFetch(OFFSET, CACHED_PATH, FF_CONFIG_PATH)
