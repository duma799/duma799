#!/usr/bin/env python3
"""Generate a neofetch-style SVG card for GitHub profile."""

import os
import json
from datetime import date
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError

GITHUB_USERNAME = "duma799"
BIRTHDAY = date(2008, 7, 27)

# Colors (Tokyo Night)
BG = "#1a1b27"
LABEL = "#e0af68"
VALUE = "#a9b1d6"
BLUE = "#70a5fd"
GREEN = "#9ece6a"
PURPLE = "#bf91f3"

# Static info
STATIC_INFO = {
    "OS": "MacOS 26, Arch Linux",
    "IDE": "Neovim, VSCode, PyCharm",
}

LANGUAGES = {
    "Languages.Programming": "Python, Lua, Bash, C++",
    "Languages.Computer": "JSON, SQL",
    "Languages.Real": "English, Russian",
}

HOBBIES = {
    "Hobbies.Software": "Ricing",
    "Hobbies.General": "Billiard",
}

CONTACTS = {
    "Email": "gptduma@gmail.com",
    "GitHub": "duma799",
    "Reddit": "duma799",
    "Telegram": "duma799",
    "Instagram": "_duma799",
}

PALETTE_COLORS = [BLUE, GREEN, LABEL, PURPLE, VALUE, "#f7768e"]


def fetch_github_stats():
    """Fetch stats from GitHub GraphQL API."""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("No GITHUB_TOKEN set, using placeholder stats")
        return {"repos": 0, "stars": 0, "commits": 0, "followers": 0}

    query = """
    {
      user(login: "%s") {
        followers { totalCount }
        repositories(first: 100, ownerAffiliations: OWNER) {
          totalCount
          nodes { stargazerCount }
          pageInfo { hasNextPage endCursor }
        }
        contributionsCollection {
          totalCommitContributions
          restrictedContributionsCount
        }
      }
    }
    """ % GITHUB_USERNAME

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    req = Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query}).encode(),
        headers=headers,
    )

    try:
        with urlopen(req) as resp:
            data = json.loads(resp.read())["data"]["user"]
    except (URLError, KeyError) as e:
        print(f"GitHub API error: {e}, using placeholder stats")
        return {"repos": 0, "stars": 0, "commits": 0, "followers": 0}

    stars = sum(n["stargazerCount"] for n in data["repositories"]["nodes"])
    contribs = data["contributionsCollection"]
    commits = contribs["totalCommitContributions"] + contribs["restrictedContributionsCount"]

    return {
        "repos": data["repositories"]["totalCount"],
        "stars": stars,
        "commits": commits,
        "followers": data["followers"]["totalCount"],
    }


def calculate_uptime():
    """Calculate age from birthday."""
    today = date.today()
    years = today.year - BIRTHDAY.year
    months = today.month - BIRTHDAY.month
    days = today.day - BIRTHDAY.day

    if days < 0:
        months -= 1
        # Get days in previous month
        prev_month = today.month - 1 if today.month > 1 else 12
        prev_year = today.year if today.month > 1 else today.year - 1
        from calendar import monthrange
        days += monthrange(prev_year, prev_month)[1]

    if months < 0:
        years -= 1
        months += 12

    return f"{years} years, {months} months, {days} days"


def escape_xml(text):
    """Escape special XML characters."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_svg():
    """Build the neofetch SVG."""
    script_dir = Path(__file__).parent
    art_file = script_dir / "ascii_art.txt"

    if not art_file.exists():
        raise FileNotFoundError(f"ASCII art file not found: {art_file}")

    ascii_lines = art_file.read_text().rstrip("\n").split("\n")
    stats = fetch_github_stats()
    uptime = calculate_uptime()

    # SVG dimensions
    width = 1050
    height = 520
    font_size = 13
    line_height = 17
    art_x = 15
    info_x = 520
    start_y = 35

    # Build info lines as (label, value) tuples or special markers
    info_lines = []
    info_lines.append(("header", f"{GITHUB_USERNAME}@github"))
    info_lines.append(("separator", ""))

    # System info
    for label, value in STATIC_INFO.items():
        info_lines.append(("field", label, value))
    info_lines.append(("field", "Uptime", uptime))
    info_lines.append(("blank", ""))

    # Languages
    for label, value in LANGUAGES.items():
        info_lines.append(("field", label, value))
    info_lines.append(("blank", ""))

    # Hobbies
    for label, value in HOBBIES.items():
        info_lines.append(("field", label, value))
    info_lines.append(("blank", ""))

    # Contact section
    info_lines.append(("section", "Contact"))
    for label, value in CONTACTS.items():
        info_lines.append(("field", label, value))
    info_lines.append(("blank", ""))

    # GitHub Stats section
    info_lines.append(("section", "GitHub Stats"))
    info_lines.append(("stats_row", "Repos", str(stats["repos"]), "Stars", str(stats["stars"])))
    info_lines.append(("stats_row", "Commits", str(stats["commits"]), "Followers", str(stats["followers"])))
    info_lines.append(("blank", ""))

    # Color palette
    info_lines.append(("palette", ""))

    # Calculate max label width for dot padding
    max_label_len = 22  # "Languages.Programming" is the longest

    # Build SVG text elements
    text_elements = []

    # ASCII art
    for i, line in enumerate(ascii_lines):
        y = start_y + i * line_height
        escaped = escape_xml(line)
        text_elements.append(
            f'  <text x="{art_x}" y="{y}" fill="{BLUE}">{escaped}</text>'
        )

    # Info lines
    y = start_y
    for line in info_lines:
        kind = line[0]

        if kind == "header":
            name = line[1]
            user_part, host_part = name.split("@")
            text_elements.append(
                f'  <text x="{info_x}" y="{y}">'
                f'<tspan fill="{BLUE}">{escape_xml(user_part)}</tspan>'
                f'<tspan fill="{VALUE}">@</tspan>'
                f'<tspan fill="{BLUE}">{escape_xml(host_part)}</tspan>'
                f'</text>'
            )
        elif kind == "separator":
            sep = "─" * 36
            text_elements.append(
                f'  <text x="{info_x}" y="{y}" fill="{BLUE}">{sep}</text>'
            )
        elif kind == "field":
            label = line[1]
            value = line[2]
            dots_len = max_label_len - len(label)
            dots = " " + "." * max(dots_len, 2) + " "
            text_elements.append(
                f'  <text x="{info_x}" y="{y}">'
                f'<tspan fill="{LABEL}">{escape_xml(label)}</tspan>'
                f'<tspan fill="{VALUE}">{escape_xml(dots)}{escape_xml(value)}</tspan>'
                f'</text>'
            )
        elif kind == "section":
            title = line[1]
            sep_len = 30 - len(title)
            sep = "── " + title + " " + "─" * sep_len
            text_elements.append(
                f'  <text x="{info_x}" y="{y}" fill="{BLUE}">{escape_xml(sep)}</text>'
            )
        elif kind == "stats_row":
            l1, v1, l2, v2 = line[1], line[2], line[3], line[4]
            dots1_len = max_label_len - len(l1)
            dots1 = " " + "." * max(dots1_len, 2) + " "
            text_elements.append(
                f'  <text x="{info_x}" y="{y}">'
                f'<tspan fill="{LABEL}">{escape_xml(l1)}</tspan>'
                f'<tspan fill="{VALUE}">{escape_xml(dots1)}</tspan>'
                f'<tspan fill="{GREEN}">{escape_xml(v1)}</tspan>'
                f'<tspan fill="{VALUE}">  |  </tspan>'
                f'<tspan fill="{LABEL}">{escape_xml(l2)}</tspan>'
                f'<tspan fill="{VALUE}">: </tspan>'
                f'<tspan fill="{GREEN}">{escape_xml(v2)}</tspan>'
                f'</text>'
            )
        elif kind == "palette":
            palette_parts = []
            for color in PALETTE_COLORS:
                palette_parts.append(
                    f'<tspan fill="{color}">██</tspan><tspan fill="{BG}"> </tspan>'
                )
            text_elements.append(
                f'  <text x="{info_x}" y="{y}">{"".join(palette_parts)}</text>'
            )
        elif kind == "blank":
            pass  # just advance y

        y += line_height

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <style>
    text {{
      font-family: 'Courier New', 'Courier', monospace;
      font-size: {font_size}px;
      white-space: pre;
    }}
  </style>
  <rect width="{width}" height="{height}" rx="10" fill="{BG}"/>
{chr(10).join(text_elements)}
</svg>"""

    return svg


def main():
    svg = build_svg()
    out_path = Path(__file__).parent.parent / "profile" / "neofetch.svg"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(svg)
    print(f"Generated {out_path}")


if __name__ == "__main__":
    main()
