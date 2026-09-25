"""Hand-drawn stroke icon set. No emojis anywhere in the chrome."""
_GOLD = "#c9a227"

def _svg(inner, size=22, color=_GOLD, sw=1.8):
    return (
        f"<svg width='{size}' height='{size}' viewBox='0 0 24 24' fill='none' "
        f"stroke='{color}' stroke-width='{sw}' stroke-linecap='round' stroke-linejoin='round' "
        f"style='vertical-align:-4px'>{inner}</svg>"
    )

def star(size=22, color=_GOLD):
    return _svg("<path d='M12 2l2.9 6.6 7.1.6-5.4 4.7 1.6 7-6.2-3.7-6.2 3.7 1.6-7L2 9.2l7.1-.6z'/>",
                size, color)

def moon(size=22, color=_GOLD):
    return _svg("<path d='M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8z'/>", size, color)

def shield(size=22, color=_GOLD):
    return _svg("<path d='M12 22s8-3.6 8-10V5l-8-3-8 3v7c0 6.4 8 10 8 10z'/>"
                "<path d='M9 12l2 2 4-4'/>", size, color)

def chart(size=22, color=_GOLD):
    return _svg("<path d='M3 3v18h18'/><path d='M7 15l4-6 4 3 5-8'/>", size, color)

def clock(size=22, color=_GOLD):
    return _svg("<circle cx='12' cy='12' r='9'/><path d='M12 7v5l3 3'/>", size, color)

def book(size=22, color=_GOLD):
    return _svg("<path d='M4 19.5A2.5 2.5 0 0 1 6.5 17H20V4H6.5A2.5 2.5 0 0 0 4 6.5v13z'/>"
                "<path d='M4 19.5A2.5 2.5 0 0 0 6.5 22H20v-5'/>", size, color)

def check(size=22, color=_GOLD):
    return _svg("<path d='M20 6L9 17l-5-5'/>", size, color)

def arrow(size=22, color=_GOLD):
    return _svg("<path d='M5 12h14'/><path d='M13 6l6 6-6 6'/>", size, color)

def quote(size=22, color=_GOLD):
    return _svg("<path d='M10 11H6a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v7a4 4 0 0 1-4 4'/>"
                "<path d='M20 11h-4a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v7a4 4 0 0 1-4 4'/>",
                size, color)

def spark(size=22, color=_GOLD):
    return _svg("<path d='M12 3v4M12 17v4M3 12h4M17 12h4M5.6 5.6l2.8 2.8M15.6 15.6l2.8 2.8M5.6 18.4l2.8-2.8M15.6 8.4l2.8-2.8'/>",
                size, color)

def dice(size=22, color=_GOLD):
    return _svg("<rect x='3' y='3' width='18' height='18' rx='4'/>"
                "<circle cx='8.5' cy='8.5' r='1.2' fill='" + color + "'/>"
                "<circle cx='15.5' cy='15.5' r='1.2' fill='" + color + "'/>"
                "<circle cx='15.5' cy='8.5' r='1.2' fill='" + color + "'/>"
                "<circle cx='8.5' cy='15.5' r='1.2' fill='" + color + "'/>", size, color)

def pin(size=22, color=_GOLD):
    return _svg("<path d='M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 1 1 16 0z'/>"
                "<circle cx='12' cy='10' r='3'/>", size, color)

def chat(size=22, color=_GOLD):
    return _svg("<path d='M21 12a8 8 0 0 1-8 8H4l2-3a8 8 0 1 1 15-5z'/>", size, color)
