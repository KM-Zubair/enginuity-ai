import streamlit as st

def card(title: str, body: str, muted: str | None = None):
    st.markdown(
        f"""
        <div class="eng-card">
          <h3>{title}</h3>
          <div>{body}</div>
          {f'<div class="eng-muted mt-2">{muted}</div>' if muted else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )

def button_row(primary: tuple[str,str] | None = None, ghost: tuple[str,str] | None = None):
    st.markdown('<div class="flex gap-2 mt-2">', unsafe_allow_html=True)
    if primary:
        label, href = primary
        st.markdown(f'<a class="eng-btn eng-btn-primary" href="{href}" target="_self">{label}</a>', unsafe_allow_html=True)
    if ghost:
        label, href = ghost
        st.markdown(f'<a class="eng-btn eng-btn-ghost" href="{href}" target="_self">{label}</a>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def section_card(title: str, body: str, muted: str | None = None):
    st.markdown(
        f"""
        <div class="eng-card">
          <h2 style="margin:0 0 .5rem 0">{title}</h2>
          <div>{body}</div>
          {f'<div class="eng-muted mt-2">{muted}</div>' if muted else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )

def feature_tile(title: str, desc: str, icon: str, href: str | None = None, disabled: bool = False):
    class_name = "tile disabled" if disabled else "tile"
    if href and not disabled:
        st.markdown(
            f"""
            <a class="{class_name}" href="{href}" target="_self" style="text-decoration:none; color:inherit;">
              <div class="icon">{icon}</div>
              <h3>{title}</h3>
              <p>{desc}</p>
            </a>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div class="{class_name}">
              <div class="icon">{icon}</div>
              <h3>{title}</h3>
              <p>{desc}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

def a11y_bar():
    # simple floating controls; increasing font-size via CSS variable would be fancier—
    # for now we expose Streamlit controls to toggle contrast/size later if you want.
    st.markdown(
        """
        <div class="a11y-bar">
          <span style="opacity:.85">A11y</span>
          <button onclick="document.body.style.zoom='110%'">A+</button>
          <button onclick="document.body.style.zoom='100%'">A</button>
          <button onclick="document.body.style.zoom='90%'">A-</button>
        </div>
        """,
        unsafe_allow_html=True,
    )
