from google.adk.agents import LlmAgent, SequentialAgent
import google.auth
from google.adk.tools.bigquery import BigQueryCredentialsConfig
from google.adk.tools.bigquery import BigQueryToolset
from google.adk.tools.bigquery.config import BigQueryToolConfig
from google.adk.tools.bigquery.config import WriteMode
from google.genai import types

CLOUD_PROJECT_ID = "cr-ai-nov-2025"
DEFAULT_DATASET_ID = "retail_db"
read_tool_config = BigQueryToolConfig(
    write_mode=WriteMode.BLOCKED,

)
write_tool_config = BigQueryToolConfig(
    write_mode=WriteMode.ALLOWED,
)

application_default_credentials, _ = google.auth.default()
credentials_config = BigQueryCredentialsConfig(
    credentials=application_default_credentials
)

bigquery_read_toolset = BigQueryToolset(
    credentials_config=credentials_config, bigquery_tool_config=read_tool_config
)
bigquery_write_toolset = BigQueryToolset(
    credentials_config=credentials_config, bigquery_tool_config=write_tool_config
)

# --- 2. Individual Specialized Agents (LlmAgent) ---
# ... (DataFinder, CMOAgent, CFOAgent, OpsAgent, CEOAgent remain the same) ...

data_finder = LlmAgent(
    name="DataFinder",
    model="gemini-2.5-flash",
    description=f"Finds instances where competitors are undercutting our products by checking the market_signals and products tables in retail_db dataset in the project {CLOUD_PROJECT_ID}.",
    instruction=f"""\
        You are a data analyst. Use the BigQuery tool to identify products where a competitor's price is lower than our product's cost price.
        Specifically: 
        1. Join the 'products' table (columns: product_id, name, cost_price) and 'market_signals' table (columns: product_id, competitor_name, detected_price).
        2. Filter for recent signals where 'detected_price' in 'market_signals' is LESS THAN 'cost_price' in 'products'.
        3. Present the output as a clean, simple JSON list containing the following details for each matching product: 
           our **product_id**, our **name**, our **cost_price**, the **competitor_name**, and the **detected_price**.
        4. If no such products are found, output an empty JSON list: [].
        SAVE THE JSON OUTPUT TO THE STATE KEY: 'undercut_signals'
    """,
    tools=[bigquery_read_toolset],
    output_key="undercut_signals" # Saves the JSON list of undercutting events
)

cmo_agent = LlmAgent(
    name="CMOAgent",
    model="gemini-2.5-flash",
    description="The Chief Marketing Officer agent provides a promotional strategy in response to competitor undercutting.",
    instruction="""\
        The following competitor undercutting signals were detected: {undercut_signals}.
        Based on this, propose a high-level **Marketing Decision (cmo_proposal)** to counter the pricing threat. 
        Your decision must be a concise strategy (e.g., 'Launch a defensive pricing match campaign').
        SAVE THE MARKETING DECISION TEXT TO THE STATE KEY: 'cmo_proposal'
    """,
    output_key="cmo_proposal" 
)

cfo_agent = LlmAgent(
    name="CFOAgent",
    model="gemini-2.5-flash",
    description="The Chief Financial Officer agent analyzes the financial impact of undercutting and proposes a price-related countermeasure.",
    instruction="""\
        The competitor undercutting signals are: {undercut_signals}. 
        The CMO's proposal is: {cmo_proposal}. 
        Based on this, propose a **Financial Decision (cfo_rebuttal)**, focusing on profitability and budget allocation (e.g., 'Approve a temporary 10% margin reduction budget' or 'Source cheaper supplier').
        SAVE THE FINANCIAL DECISION AND ANALYSIS TO THE STATE KEY: 'cfo_rebuttal'
    """,
    output_key="cfo_rebuttal" 
)

ops_agent = LlmAgent(
    name="OpsAgent",
    model="gemini-2.5-flash",
    description="The Operations Agent provides input on logistics and inventory related to the pricing threat and proposed decisions.",
    instruction="""\
        The competitor undercutting signals are: {undercut_signals}. 
        The CMO proposes: {cmo_proposal}. The CFO proposes: {cfo_rebuttal}.
        Provide a concise **Operational Input (ops_input)** on feasibility, stock readiness (current_stock from the products table in retail_db dataset in the project "cr-ai-nov-2025" is available for context), and potential delays. 
        SAVE THE OPERATIONAL INPUT TEXT TO THE STATE KEY: 'ops_input'
    """,
    output_key="ops_input" 
)

ceo_agent = LlmAgent(
    name="CEOAgent",
    model="gemini-2.5-flash",
    description="The Chief Executive Officer agent reviews all inputs and delivers the final, validated verdict.",
    instruction="""\
        Review the following inputs:
        1. Undercut Products/Signals: {undercut_signals}
        2. CMO Proposal: {cmo_proposal}
        3. CFO Rebuttal: {cfo_rebuttal}
        4. Ops Input: {ops_input}

        Synthesize these into a single, cohesive **Final Verdict (ceo_verdict)** and set a **status** (e.g., 'APPROVED', 'DEFERRED', 'REJECTED').
        The output must be a clean JSON object with two keys: "verdict" and "status".
        SAVE THE JSON OBJECT TO THE STATE KEY: 'ceo_decision_json'
    """,
    output_key="ceo_decision_json" 
)

log_agent = LlmAgent(
    name="CouncilDebatesLogger",
    model="gemini-2.5-flash",
    description=f"Agent responsible for logging the final, multi-agent executive decision into the 'council_debates' BigQuery table in retail_db dataset in the project {CLOUD_PROJECT_ID}.",
    instruction=f"""\
        The multi-agent inputs are:
        - Product Signals: {{undercut_signals}}
        - CMO Proposal: {{cmo_proposal}}
        - CFO Rebuttal: {{cfo_rebuttal}}
        - Ops Input: {{ops_input}}
        - CEO Final Decision (JSON): {{ceo_decision_json}}

        **PERFORM THE INSERT OPERATION ONLY.** This step is for logging and should not generate text output for the user.
        
        ... (BigQuery INSERT logic as before) ...
    """,
    tools=[bigquery_write_toolset],
    # The log agent is primarily for side effects (writing data), not direct output
    # We will let the next agent handle the final user-facing output.
)

## 2.6. Final Reporting Agent (NEW STEP)
final_reporter = LlmAgent(
    name="FinalReporter",
    model="gemini-2.5-flash",
    description="Summarizes the entire executive workflow output for the user.",
    instruction="""\
        Generate a final report based on the workflow's state keys. Start with the list of undercut products, followed by the executive proposals.
        
        **Undercut Products (undercut_signals):** {undercut_signals}
        **CMO Proposal (cmo_proposal):** {cmo_proposal}
        **CFO Rebuttal (cfo_rebuttal):** {cfo_rebuttal}
        **Ops Input (ops_input):** {ops_input}
        **CEO Final Decision (ceo_decision_json):** {ceo_decision_json}

        Format the entire response as a single, clean, markdown-formatted report.
    """,
    # This agent's output is what the SequentialAgent will ultimately return
    # if it's the last agent in the list. No explicit output_key needed if 
    # the LlmAgent is the last one and its response is the final response.
)


# --- 3. Root Coordinator (SequentialAgent) ---
# Added the FinalReporter agent to the end
root_agent = SequentialAgent(
    name="ExecutiveDecisionWorkflow_V2",
    description="Orchestrates data finding, executive decision-making (CMO, CFO, Ops, CEO), and final logging based on competitor signals.",
    sub_agents=[
        data_finder, 
        cmo_agent, 
        cfo_agent, 
        ops_agent, 
        ceo_agent, 
        log_agent, 
        final_reporter 
    ]
)
