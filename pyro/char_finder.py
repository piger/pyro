import click
import tdl
import tcod
import better_exceptions

FG = (255, 255, 255)
BG = (8, 8, 8)
HIGHLIGHT = (112, 219, 147)


def get_char(col, row):
    col = col + 1
    row = row + 1
    i = row - 1
    if row < 0:
        row = 0
    result = ((i * 16) + col) - 1
    return result


@click.command()
def char_finder():
    w_display = 16
    h_display = 16
    w_info = 15
    h_info = 16
    margin = 1
    w = w_display + w_info + margin
    h = 16

    highlight = (0, 0)

    tdl.set_font("mononoki_16-19.png", columns=16, rows=16, greyscale=True, altLayout=False)
    tdl.set_fps(30)
    root = tdl.init(w, h, title="char picker")
    display = tdl.Console(w_display, h_display)
    info = tdl.Console(w_info, h_info)
    display.set_colors(FG, BG)
    info.set_colors(FG, BG)

    running = True

    while running:
        display.clear()
        info.clear()

        c = 0
        for y in range(0, 16):
            for x in range(0, 16):
                color = FG
                if highlight == (x, y):
                    color = HIGHLIGHT
                display.draw_char(x, y, c, fg=color)
                c += 1

        for event in tdl.event.get():
            if event.type == "KEYDOWN":
                running = False
                break
            elif event.type == "MOUSEDOWN":
                print(event.cell)
                highlight = event.cell

        info.draw_str(0, 0, "cell: %dx%d" % highlight)
        info.draw_str(0, 1, "char: %d" % get_char(*highlight))

        root.blit(display, 0, 0, 16, 16, 0, 0)
        root.blit(info, w_display + margin, 0, w_info, h_info, 0, 0)
        tdl.flush()
