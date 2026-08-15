"""Shared Plotly theming so every chart in the app looks like it belongs to
the same product instead of each page styling its own — and flips with the
dark/light toggle since colors are read live, never imported statically."""
from utils.theme import get_colors


def apply_dark_theme(fig, height=300, show_legend=True):
    """Name kept for backward compatibility across the app — it now applies
    whichever theme (dark or light) is currently active."""
    c = get_colors()
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=c["text_dim"], family="Inter, sans-serif", size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                    bgcolor="rgba(0,0,0,0)") if show_legend else dict(visible=False),
        xaxis=dict(gridcolor=c["border"], zerolinecolor=c["border"]),
        yaxis=dict(gridcolor=c["border"], zerolinecolor=c["border"]),
        hoverlabel=dict(bgcolor=c["bg_card_alt"], font_color=c["text"]),
    )
    return fig


def get_chart_colorway():
    c = get_colors()
    return [c["primary"], c["success"], c["accent"], c["danger"], c["warning"], c["primary_dark"]]


class _ColorwayProxy(list):
    """Makes CHART_COLORWAY usable both as a static-looking import (for
    existing `from utils.charts import CHART_COLORWAY` call sites) and as
    something that re-reads the live theme on every access, by overriding
    the sequence protocol to defer to get_chart_colorway()."""
    def __getitem__(self, item):
        return get_chart_colorway()[item]

    def __iter__(self):
        return iter(get_chart_colorway())

    def __len__(self):
        return len(get_chart_colorway())


CHART_COLORWAY = _ColorwayProxy()
