# Step 2: Import Libraries
import os
import sqlite3
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_openai import ChatOpenAI
import streamlit as st

# Step 3: Load Environment Variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not found. Please add it to your .env file.")
os.environ["OPENAI_API_KEY"] = api_key

# Step 4: Initialize the SQLite Database
db_path = "fraud.db"  # Path to your SQLite database
engine = create_engine(f"sqlite:///{db_path}")
db = SQLDatabase(engine=engine)

# Step 5: Set Up the LLM Agent
llm = ChatOpenAI(model="gpt-4o", temperature=0)
agent_executor = create_sql_agent(llm, db=db, agent_type="openai-tools", verbose=True)

# Step 6: Create a Data Dictionary for Context
data_dictionary = """
### Database Structure and Relationships
The database contains the following tables:

1. **alert_audit**:
    - ENTITY_ID: Unique identifier for the entity.
    - ALERT_ID: Unique identifier for the alert (links to ALERT_ID in alert_table).
    - ALERT_DT: Date of the alert.
    - RULE_ID: Rule applied to trigger the alert.
    - ALERT_REASON: Reason for the alert.
    - AGENT_ID: Agent associated with the alert (links to AGENT_ID in alert_table).
    - ALERT_CLASS: Classification of the alert (e.g., confirmed fraud).

2. **transaction_summary**:
    - TRANS_DT: Date of the transaction.
    - TRANS_TYPE: Type of the transaction (e.g., log-in, lost card).
    - MULTI_ORG: Organization involved in the transaction (links to MULTI_ORG in alert_table).
    - TRANS_COUNT: Number of transactions.

3. **alert_table**:
    - ALERT_ID: Unique identifier for the alert (links to ALERT_ID in alert_audit).
    - ALERT_TYPE: Type of the alert.
    - STRATEGY_NAME: Represents the name of the strategy applied for monitoring or analyzing suspicious activities. This typically identifies a predefined rule, workflow, or model used for processing alerts.
    - QUEUE_NAME: Specifies the queue to which a particular alert or case is assigned. Queues help in organizing and routing alerts to appropriate teams or individuals for investigation based on priority or type.
    - ALERT_STATUS: status of alert
    - ALERT_DISP: Represents the disposition of the alert after review or investigation. This could include categories such as "False Positive," "Confirmed Fraud," or "Requires Further Investigation," helping to document the outcome of the analysis.
    - RULE_DSC: description of the rule
    - AGENT_ID: ID of the agent handling the alert
    - ALERT_CLASS: Classification of the alert.
    - MULTI_ORG: Organization involved (links to MULTI_ORG in transaction_summary).
    - ALERT_DTTM: Date and time of the alert.
    - FP_RATIO: False positive ratio for the alert.
    - ALERT_INVS: time taken to close an alert in hours (total time of investigating the alert)


Relationships:
- alert_audit.ALERT_ID links to alert_table.ALERT_ID.
- alert_table.MULTI_ORG links to transaction_summary.MULTI_ORG.
"""

# Step 7: Build the Streamlit UI
st.title("SFM Digital Assistant")
st.write("Ask me anything about fraud data!")

# Initialize conversation history
if "conversation" not in st.session_state:
    st.session_state.conversation = []

# Input field for user query
user_input = st.text_input("You:", key="user_input")

if user_input:
    # Combine data dictionary with user query for better context
    query = f"{data_dictionary}\n\n{user_input}"

    try:
        # Use the LLM agent to handle the query
        result = agent_executor.invoke({"input": query})["output"]
        st.session_state.conversation.append(("User", user_input))
        st.session_state.conversation.append(("Zainab", result))
    except Exception as e:
        st.session_state.conversation.append(("Zainab", f"Error: {str(e)}"))

    # Clear input field after submission
    user_input = ""

# Display conversation history
for speaker, message in st.session_state.conversation:
    if speaker == "User":
        st.markdown(f"**You:** {message}")
    else:
        st.markdown(f"**Zainab:** {message}")