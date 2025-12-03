import streamlit as st
import os
import time
from workflows.ml_coach import autonomous_loop

st.set_page_config(page_title="Autonomous ML Coach", layout="wide")

st.title("🤖 Autonomous ML Coach")
st.markdown(
    "This app uses a multi-agent system to research a topic, write Python code, "
    "generate tests, and iteratively debug itself. Enter a prompt and watch it work!"
)

# --- Sidebar for Configuration ---
with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("Enter your Google API Key", type="password")
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key

    st.info(
        "Your API key is used for this session only and is not stored.", icon="🔒"
    )

    max_iters = st.slider(
        "Max Debugging Iterations",
        min_value=1,
        max_value=10,
        value=3,
        help="The maximum number of times the debugger will try to fix the code.",
    )
    run_timeout = st.slider(
        "Code Execution Timeout (s)",
        min_value=5,
        max_value=30,
        value=8,
        help="Timeout for running the generated code and tests.",
    )
    auto_patch = st.toggle(
        "Auto-Apply Patches",
        value=True,
        help="If enabled, the workflow will automatically apply patches suggested by the debugger without asking.",
    )


# --- Main App Body ---
user_prompt = st.text_area(
    "Enter your coding prompt below:",
    height=150,
    placeholder="e.g., Explain how bubble sort works and write a Python function for it.",
)

run_button = st.button("🚀 Run Workflow")

if run_button:
    if not api_key:
        st.error("Please enter your Google API Key in the sidebar to begin.")
        st.stop()

    if not user_prompt:
        st.warning("Please enter a prompt.")
        st.stop()

    # Create placeholders for live output
    st.subheader("Workflow Progress")
    status_placeholder = st.empty()
    latest_code = ""

    # Use columns to display results side-by-side
    col1, col2 = st.columns(2)
    with col1:
        code_placeholder = st.empty()
    with col2:
        test_placeholder = st.empty()
    debugger_placeholder = st.empty()

    # The autonomous_loop is now a generator yielding status updates
    for status in autonomous_loop(
        user_prompt,
        max_iters=max_iters,
        run_timeout=run_timeout,
        auto_patch_enabled=auto_patch,
    ):
        status_placeholder.info(status["message"])

        if "code_text" in status:
            latest_code = status["code_text"]
            with col1:
                st.code(latest_code, language="python", line_numbers=True)

        if "test_text" in status:
            with col2:
                st.code(status["test_text"], language="python", line_numbers=True)

        if "debugger_output" in status:
            with debugger_placeholder.container():
                st.subheader("Debugger Analysis")
                st.markdown(status["debugger_output"])

        time.sleep(0.5) # Small delay for better UX

    st.success("✅ Workflow finished!")
    st.balloons()
