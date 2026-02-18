import time
import streamlit as st


def should_refresh(key: str = "last_poll", interval_seconds: int = 3) -> bool:
    now = time.time()
    last = st.session_state.get(key, 0)
    if now - last >= interval_seconds:
        st.session_state[key] = now
        return True
    return False


def auto_refresh(interval_seconds: int = 3):
    import streamlit.components.v1 as components
    components.html(
        f"""
        <script>
            setTimeout(function() {{
                window.parent.document.querySelectorAll('[data-testid="stApp"]')[0]
                    .__streamlit_connection__.sendBackMsg({{type: "rerun"}});
            }}, {interval_seconds * 1000});
        </script>
        <script>
            setTimeout(function() {{
                window.parent.location.reload();
            }}, {interval_seconds * 1000});
        </script>
        """,
        height=0,
    )
