import streamlit as st

# Page configuration
st.set_page_config(
    page_title="EF Gap Year Assistant",
    page_icon="🌎",
    layout="centered"
)

# Header
st.title("EF Gap Year Assistant")
st.write("Welcome to the EF Gap Year Assistant! This is a minimal version to test deployment.")

# Simple interaction
if st.button("Click me"):
    st.success("Button clicked successfully!")

# Display basic information
st.markdown("""
### This is a diagnostic version
This ultra-minimal app is designed to test Streamlit Cloud deployment.
No complex functionality is included.

Once this deploys successfully, we can gradually add the full functionality back.
""")
