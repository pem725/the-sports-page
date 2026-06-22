#!/usr/bin/env python3
"""Inline The Sports Page design-system styles into an issue's body HTML so it
renders correctly in email (where the page's <head><style> is unavailable).

Pure stdlib, no dependencies -- safe for the unattended autopublish runner.
Maps the fixed set of issue classes to inline styles, flattens the CSS-grid
containers (which every email client ignores) to stacked styled blocks, and
gives the scorecard table real cell/row styling (tables are email-native).

Public API: inline_for_email(body_html) -> str
"""
import re

# design-system palette (resolved from the issue :root vars)
INK, CREAM, AGED = '#1a1208', '#f5f0e8', '#e0d8c5'
RUST, STEEL, GOLD = '#b83a1e', '#2c4a6e', '#c9962a'
MUTED, DIV, CARD, GREEN = '#6b5e4a', '#c8b99a', '#ede5d2', '#2a6e3f'

# class -> inline style. Applied to any element carrying the class.
CLASS_STYLES = {
    'hed':    f'font-family:Georgia,"Times New Roman",serif;font-size:26px;font-weight:bold;line-height:1.2;margin:0 0 8px;color:{INK}',
    'deck':   f'font-style:italic;color:{MUTED};border-left:3px solid {RUST};padding-left:12px;margin:12px 0 18px;font-size:17px;line-height:1.5',
    'byline': f'font-family:monospace;font-size:11px;letter-spacing:1px;color:{MUTED};text-transform:uppercase;margin-bottom:18px',
    'sh':     f'font-size:18px;font-weight:bold;text-transform:uppercase;letter-spacing:.5px;border-bottom:2px solid {RUST};padding-bottom:4px;margin:28px 0 12px;color:{INK}',
    'intro':  f'background:{CARD};border-left:4px solid {STEEL};padding:14px 18px;margin:0 0 22px;font-size:16px;line-height:1.6',
    'pull':   f'border-top:2px solid {INK};border-bottom:2px solid {INK};padding:14px 0;margin:22px 0;text-align:center',
    'box':    f'background:{STEEL};color:#dce8f5;padding:18px 22px;margin:22px 0',
    'green-box': f'background:{GREEN}',
    'stat-row':  'margin:0 0 22px',
    'sc':     f'border:1px solid {DIV};background:{CARD};padding:12px;text-align:center;margin-bottom:6px',
    'issue-list': 'list-style:none;padding:0;margin:0 0 22px',
    'two-col':   'margin:18px 0',
}
# descendant rules: (container_class, child_tag) -> style
DESCENDANT = {
    ('box', 'h3'): 'color:#ffffff;font-size:17px;font-weight:bold;margin:0 0 10px',
    ('box', 'p'):  'color:#c8daed;font-size:15px;line-height:1.6;margin:0 0 10px',
    ('pull', 'p'): f'font-size:19px;font-weight:bold;font-style:italic;color:{STEEL};line-height:1.45;margin:0',
    ('pull', 'cite'): f'font-family:monospace;font-size:11px;color:{MUTED};display:block;margin-top:8px',
    ('sc', 'v'):  'font-size:28px;font-weight:bold;line-height:1;display:block',  # class="v"
    ('sc', 'l'):  f'font-family:monospace;font-size:11px;letter-spacing:1px;text-transform:uppercase;color:{MUTED};display:block;margin-top:4px',  # class="l"
    ('issue-list', 'li'): f'padding:8px 0;border-bottom:1px solid {DIV};font-size:15px;line-height:1.6',
}
TH = f'font-family:monospace;font-size:11px;letter-spacing:1px;text-transform:uppercase;color:{MUTED};border-bottom:2px solid {INK};padding:6px 8px;text-align:left'
TD = f'padding:7px 8px;border-bottom:1px solid {DIV};vertical-align:top'
ROW_BG = {'hl': '#e0f0e8', 'match': '#fff3d6', 'worse': '#fef0ec'}
FOOTER = f'border-top:3px double {INK};padding-top:10px;margin-top:28px;font-family:monospace;font-size:11px;color:{MUTED}'


def _merge_style(opentag, style):
    """Add/append an inline style to a single opening-tag string."""
    if re.search(r'\bstyle="', opentag):
        return re.sub(r'style="([^"]*)"', lambda m: f'style="{m.group(1)};{style}"', opentag, count=1)
    return opentag[:-1] + f' style="{style}">'


def _apply_class(html, cls, style):
    pat = re.compile(r'<\w+\b[^>]*\bclass="[^"]*\b' + re.escape(cls) + r'\b[^"]*"[^>]*>')
    return pat.sub(lambda m: _merge_style(m.group(0), style), html)


def _style_tables(html):
    """Give every <table class="rec"> real cell/row styling for email."""
    def do(m):
        tbl = m.group(0)
        tbl = re.sub(r'<th\b[^>]*>', lambda x: _merge_style(x.group(0), TH), tbl)
        # base td style everywhere
        tbl = re.sub(r'<td\b[^>]*>', lambda x: _merge_style(x.group(0), TD), tbl)
        tbl = _merge_style(tbl.split('>', 1)[0] + '>',
                           f'width:100%;border-collapse:collapse;font-size:14px;margin:16px 0') + tbl.split('>', 1)[1]
        # row-class background tints -> apply to that row's cells
        def row_repl(rm):
            row = rm.group(0)
            for klass, bg in ROW_BG.items():
                if re.search(r'class="[^"]*\b' + klass + r'\b', rm.group(0).split('>', 1)[0]):
                    row = re.sub(r'(<td\b[^>]*style="[^"]*)"', rf'\1;background:{bg}"', row)
                    break
            return row
        tbl = re.sub(r'<tr\b[^>]*>.*?</tr>', row_repl, tbl, flags=re.DOTALL)
        return tbl
    return re.sub(r'<table\b[^>]*\bclass="[^"]*\brec\b[^"]*"[^>]*>.*?</table>', do, html, flags=re.DOTALL)


def _style_descendants(html):
    for (cont, child), style in DESCENDANT.items():
        def do(m, child=child, style=style):
            block = m.group(0)
            if child in ('v', 'l'):   # class-named children (stat cards)
                return _apply_class(block, child, style)
            return re.sub(r'<' + child + r'\b[^>]*>',
                          lambda x: _merge_style(x.group(0), style), block)
        # match the container element's whole subtree (non-nesting containers here)
        html = re.sub(r'<\w+\b[^>]*\bclass="[^"]*\b' + re.escape(cont) + r'\b[^"]*"[^>]*>.*?</\w+>',
                      do, html, flags=re.DOTALL)
    return html


def inline_for_email(body_html):
    html = body_html
    html = _style_tables(html)              # tables first (before generic td/li rules)
    html = _style_descendants(html)         # box p/h3, pull p/cite, sc v/l, list li
    for cls, style in CLASS_STYLES.items():
        html = _apply_class(html, cls, style)
    html = _apply_class(html, 'footer', FOOTER)
    # wrap in an email-safe container with the broadsheet base font
    wrap = (f'<div style="max-width:640px;margin:0 auto;'
            f'font-family:Georgia,\'Times New Roman\',serif;color:{INK};'
            f'font-size:16px;line-height:1.6">')
    return wrap + html + '</div>'


if __name__ == '__main__':
    import sys
    print(inline_for_email(open(sys.argv[1], encoding='utf-8').read()))
