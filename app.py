import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from src.pipeline import NL2SQLPipeline
from langchain_openai import ChatOpenAI
import logging
import os

# Configure logging for the application
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')

# --- Page Configuration ---
st.set_page_config(
    page_title="NL2SQL Intelligent Pipeline",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Load Custom CSS ---
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

try:
    load_css("assets/style.css")
except FileNotFoundError:
    pass

# --- Initialize Session State ---
if 'pipeline' not in st.session_state:
    st.session_state.pipeline = None

def init_pipeline(api_key: str, db_uri: str, model_name: str = "gpt-4"):
    try:
        os.environ["OPENAI_API_KEY"] = api_key
        engine = create_engine(db_uri)
        llm = ChatOpenAI(temperature=0, model=model_name)
        st.session_state.pipeline = NL2SQLPipeline(engine=engine, llm=llm, max_retries=2)
        return True, "Pipeline initialized successfully!"
    except Exception as e:
        return False, str(e)

# --- Sidebar: Configuration ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/8313/8313098.png", width=100) # Placeholder robot icon
    st.title("⚙️ Configuration")
    st.markdown("Enter your credentials to connect the NLP engine to your database.")
    
    api_key_input = st.text_input("OpenAI API Key", type="password", help="Ensure your key has access to the chosen model.")
    
    db_uri_input = st.text_input("Database Connection URI", value="sqlite:///:memory:", help="Example: postgresql://user:password@localhost:5432/db")
    
    model_choice = st.selectbox("OpenAI Model", ["gpt-4", "gpt-3.5-turbo"])
    
    if st.button("Connect & Initialize"):
        if not api_key_input:
            st.error("Please provide an OpenAI API Key.")
        elif not db_uri_input:
            st.error("Please provide a Database Connection URI.")
        else:
            with st.spinner("Connecting to database..."):
                success, msg = init_pipeline(api_key_input, db_uri_input, model_choice)
                if success:
                    st.success(msg)
                else:
                    st.error(f"Initialization failed: {msg}")
                    
    st.markdown("---")
    st.markdown("<small>Designed for secure, read-only analytics.</small>", unsafe_allow_html=True)

# --- Main App Header ---
st.title("🤖 Intelligent NL2SQL Pipeline")
st.markdown("""
Welcome to the Natural Language to SQL analytics dashboard. 
Transform your everyday language into complex SQL queries effortlessly. 
Get started by connecting your database in the sidebar!
""")

# --- Main Interaction Area ---
st.markdown("### 📝 Ask your database a question")

question = st.text_area(
    "Type your question here (e.g., 'Show me the top 5 customers by revenue strictly descending'):",
    height=100
)

col1, col2, col3 = st.columns([1, 1, 4])
with col1:
    generate_btn = st.button("Generate & Run")

if generate_btn:
    if not st.session_state.pipeline:
        st.warning("⚠️ Please initialize the pipeline in the sidebar first.")
    elif not question.strip():
        st.warning("⚠️ Please enter a question.")
    else:
        with st.spinner("Thinking... generating SQL and analyzing results..."):
            try:
                final_sql, resulting_df = st.session_state.pipeline.run(question)
                
                if resulting_df is not None:
                    st.success("Query executed successfully!")
                    
                    # Layout for results: tabs for easy switching
                    tab1, tab2 = st.tabs(["📊 Data Results", "💻 Generated SQL"])
                    
                    with tab1:
                        st.markdown("#### Excerpt of Results")
                        st.dataframe(resulting_df, use_container_width=True)
                        st.caption(f"Showing up to {len(resulting_df)} rows.")
                        
                    with tab2:
                        st.markdown("#### Executed Query")
                        st.code(final_sql, language="sql")
                else:
                    st.error("Pipeline failed to generate a valid result or ran into an error.")
                    
            except Exception as e:
                st.error(f"An error occurred during execution: {e}")

# --- Footer ---
st.markdown("---")
st.markdown("<div style='text-align: center; color: #94a3b8;'><small>Powered by LangChain & Streamlit</small></div>", unsafe_allow_html=True)
