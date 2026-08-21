# Databricks notebook source
# DBTITLE 1,Install Required Packages
# %uv pip install torch==2.1.2 transformers==4.36.2 accelerate==0.25.0
# %uv pip install llama-index==0.9.48 llama-index-core==0.9.48 llama-index-llms-huggingface==0.1.4 llama-index-embeddings-huggingface==0.1.4

%uv pip install torch transformers accelerate

%uv pip install llama-index llama-index-core llama-index-llms-huggingface llama-index-embeddings-huggingface

dbutils.library.restartPython()

# COMMAND ----------

# pip install pypdf==3.17.4
!pip install pypdf

# COMMAND ----------

# DBTITLE 1,Install required packages for LLM setup
# MAGIC %pip install bitsandbytes transformers hf_transfer accelerate llama-index llama-index-llms-huggingface llama-index-embeddings-huggingface

# COMMAND ----------

# DBTITLE 1,Install latest bitsandbytes with restart
# Install all required packages for LLM with 4-bit quantization
%uv pip install bitsandbytes transformers accelerate hf_transfer llama-index llama-index-llms-huggingface llama-index-embeddings-huggingface
%restart_python

# COMMAND ----------

# MAGIC %pip install --upgrade langchain-core langchain

# COMMAND ----------

from typing import List, Dict, Any, Literal
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

# Try importing langgraph - if it fails due to version issues, fix it
try:
    from langgraph.graph import StateGraph, START, END
    print("✅ Successfully imported langgraph.graph components")
    print(f"   - StateGraph: {StateGraph}")
    print(f"   - START: {START}")
    print(f"   - END: {END}")
except ModuleNotFoundError as e:
    if "_compat_bridge" in str(e):
        print(f"❌ Version incompatibility detected: {e}")
        print("📦 Installing compatible langchain packages...")
        import sys
        import subprocess
        # Install compatible versions
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--quiet", "--upgrade",
            "langchain-core>=0.3.0", "langgraph>=0.2.0"
        ])
        print("✅ Packages upgraded. Please restart the Python kernel using: dbutils.library.restartPython()")
        print("Then re-run this cell.")
        raise SystemExit("Kernel restart required")
    else:
        raise

# COMMAND ----------

# DBTITLE 1,Restart Python Kernel
# Restart the Python kernel to load the upgraded packages
dbutils.library.restartPython()

# COMMAND ----------

# DBTITLE 1,Cell 3
# MAGIC %run /Users/takashi.canada.toronto@gmail.com/Manage_OneDrive $skip_tests="true"

# COMMAND ----------

# MAGIC %run /Users/takashi.canada.toronto@gmail.com/Manage_LLM $skip_tests="true"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Get OneDrive access token

# COMMAND ----------

# DBTITLE 1,Authenticate OneDrive
PERSONAL_CLIENT_ID = "277a0c97-691d-4f16-a6ac-1df892794f8f" 
token = PersonalOneDriveClient.get_personal_onedrive_token(PERSONAL_CLIENT_ID)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Import LLM from Local Storage

# COMMAND ----------

import requests

# Define paths
onedrive_model_path = "/AI/RAG/mineral/vector_store"
local_model_dir = "/tmp/RAG/vector_store"

try:
    print(f"📥 Downloading model from OneDrive: {onedrive_model_path}\n")
    
    # Download all model files from OneDrive
    downloaded = LLMManager.download_folder_from_onedrive(token,onedrive_model_path, local_model_dir)
    
    print(f"\n✅ Downloaded {downloaded} model files\n")
    
    # Load the model and tokenizer from the local directory
    print(f"🤖 Loading vectore store from local directory: {local_model_dir}")
    print("\n🎉 Model loaded successfully from OneDrive!")
   
except Exception as e:
    print(f"❌ Error: {e}")
    print("\n💡 Tip: If you see an authentication error, run Cell 6 again to refresh the token.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Set up LLM

# COMMAND ----------

# DBTITLE 1,Cell 8
from llama_index.core import StorageContext, load_index_from_storage, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.huggingface import HuggingFaceLLM
from transformers import BitsAndBytesConfig
import torch
import os

# Securely retrieve the Hugging Face token from Databricks Secrets
try:
    hf_token = dbutils.secrets.get(scope="HF", key="HF_TOKEN")
    print("✅ HF_TOKEN retrieved successfully.")
except Exception:
    print("❌ Error: 'HF_TOKEN' secret not found.")
    print("Please ensure the secret is stored using Cell 3 or run: dbutils.secrets.put(scope='HF', key='HF_TOKEN', value='your_token')")
    raise ValueError("Authentication failed: HF_TOKEN is required.")

# Configure 4-bit quantization to fit the model in GPU memory
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
    llm_int8_enable_fp32_cpu_offload=True
)

# Configure TinyLlama (open-access, no gating)
Settings.llm = HuggingFaceLLM(
    # model_name="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    # tokenizer_name="TinyLlama/TinyLlama-1.1B-Chat-v1.0",

    # Longer context model for detailed compliance audits
    model_name="mistralai/Mistral-7B-Instruct-v0.2", 
    tokenizer_name="mistralai/Mistral-7B-Instruct-v0.2", 

    query_wrapper_prompt="<|system|>\nYou are a helpful assistant.</s>\n<|user|>\n{query_str}</s>\n<|assistant|>\n",
    context_window=32768,  # Mistral v0.2 supports up to 32K
    max_new_tokens=4096,  # Allow longer, more detailed audit reports
    generate_kwargs={"temperature": 0.1, "do_sample": True, "top_p": 0.9, "pad_token_id": 2},
    device_map="auto",
    model_kwargs={
        "dtype": torch.float16,
        "quantization_config": quantization_config,
        "token": hf_token
    }
)

# Load embedding model (CPU-compatible)
Settings.embed_model = HuggingFaceEmbedding(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    token=hf_token
)

# Load the vector store index
storage_context_hf = StorageContext.from_defaults(persist_dir=local_model_dir)
index = load_index_from_storage(storage_context_hf)

print("✅ Vector store loaded successfully!")
print(f"📊 Index ready for querying with {Settings.embed_model.model_name}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Pre-cleaning Retriever: negative constraint filter 

# COMMAND ----------

# 1. Extract and inspect all nodes currently sitting in memory
# Hard unnecessary node elimination

docstore = index.docstore
all_nodes = docstore.get_nodes(list(docstore.docs.keys()))

forbidden_frameworks = ["JORC","acceptable foreign code”","USE OF FOREIGN CODE","Foreign Association"]

nodes_to_delete = []

print("🧹 Running Pre-Cleaning scan on loaded Vector DB...")

for node in all_nodes:
    text = node.get_content().upper()
    title = node.metadata.get("document_title", "").upper()
    summary = node.metadata.get("section_summary", "").upper()
    
    full_context = f"{text} {title} {summary}"
    
    # If it contains a negative constraint code, mark its ID for deletion
    if any(code in full_context for code in forbidden_frameworks):
        nodes_to_delete.append(node.node_id)

# 2. Purge non-compliant nodes from the active in-memory index
# Delete from both docstore AND vector store to fully remove nodes
for node_id in nodes_to_delete:
    docstore.delete_document(node_id)
    # Also remove from vector store so they don't appear in retrieval
    index.vector_store.delete(node_id)

print(f"✅ Pre-cleaning complete. Purged {len(nodes_to_delete)} foreign standard nodes from memory.")
# Now your index is completely sanitized for your LangGraph queries!


# COMMAND ----------

import asyncio
from llama_index.core import StorageContext, load_index_from_storage, Settings
# from llama_index.core.program import LLMTextCompletionProgram
# from llama_index.core.query_engine import RetrieverQueryEngine
from pypdf import PdfReader
import datetime
from typing import List
# from pydantic import BaseModel



class MultiTaskState(TypedDict):
    target_pdf_path: str      # Path to the PDF file to analyze
    target_document: str      # Full text content of the target document
    gaps_answer: str          # Answer generated by gaps_node
    omissions_answer: str     # Answer generated by omissions_node
    final_merged_report: str  # Final merged report


# =====================================================================
# STEP 1: Load target pdf
# =====================================================================
async def read_entire_pdf(state: MultiTaskState):

    pdf_path = state.get("target_pdf_path", "No pdf path found.")

    """Extract all text from a PDF with page markers."""
    reader = PdfReader(pdf_path)
    full_text = []
    for i, page in enumerate(reader.pages):
        full_text.append(f"--- START PAGE {i+1} ---\n{page.extract_text()}\n--- END PAGE {i+1} ---")
    # return "\n".join(full_text)
    return {"target_document": str("\n".join(full_text))}

# =====================================================================
# STEP 1: INITIALIZE AND PRE-CLEAN VECTOR DB (OPTION 2)
# =====================================================================
# def get_sanitized_query_engine(local_model_dir: str):
#     """Loads the physical vector store and purges foreign standards from memory."""
#     print("💾 Loading index from storage context...")
#     storage_context_hf = StorageContext.from_defaults(persist_dir=local_model_dir)
#     index = load_index_from_storage(storage_context_hf)
    
#     # Extract structural node keys directly from the loaded document store
#     all_node_ids = list(index.docstore.docs.keys())
    
#     forbidden_frameworks = ["JORC", "PERC", "SAMREC", "JMEG"]
#     nodes_to_purge = []
    
#     print("🧹 Pre-Cleaning Stage: Sweeping loaded Vector DB metadata blocks...")
#     for node_id in all_node_ids:
#         node = index.docstore.get_node(node_id)
        
#         # Access TitleExtractor and SummaryExtractor metadata maps
#         text = node.get_content().upper()
#         title = node.metadata.get("document_title", "").upper()
#         summary = node.metadata.get("section_summary", "").upper()
        
#         full_context = f"{text} {title} {summary}"
        
#         if any(code in full_context for code in forbidden_frameworks):
#             nodes_to_purge.append(node_id)
            
#     # Perform synchronized cascade deletion from text store and vector space
#     for node_id in nodes_to_purge:
#         index.delete_node(node_id)
        
#     print(f"✅ Clean-up finished. Safely evicted {len(nodes_to_purge)} non-compliant standard entries.")
    
#     # Build a standard retriever query engine out of the sanitized memory map
#     retriever = index.as_retriever(similarity_top_k=5)
#     return RetrieverQueryEngine.from_args(retriever=retriever)

# Initialize the global clean query engine
# index = get_sanitized_query_engine("/path/to/local_model_dir")


# =====================================================================
# STEP 2: DEFINE THE GRAPH STATE AND STRUCTURED SCHEMAS
# =====================================================================
# class OmissionElement(BaseModel):
#     missing_technical_item: str = Field(description="Name of item missing from formatting rules")
#     required_disclosures: str = Field(description="Detailed description of what must be appended")
#     risk_level: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
#     funding_consequence: str = Field(description="Specific impact on funding framework eligibility")
#     compliance_remediation_steps: List[str] = Field(description="Step-by-step remediation action plan")

# class GapElement(BaseModel):
#     checked_item: str = Field(description="Specific standard disclosure requirement item")
#     report_location: str = Field(description="Page X, Section Y, or precise text quote source")
#     regulatory_threshold_requirement: str = Field(description="State explicit disclosure expectation standard")
#     report_actual_disclosure: str = Field(description="Exact quote from prospectus showing deficiency")
#     analyst_gap_analysis: str = Field(description="Granular technical breakdown outlining failure")
#     status: Literal["NON-COMPLIANT", "INSUFFICIENT DETAIL", "WARNING"]
#     required_remediation_immediate: str = Field(description="Immediate step action to execute")
#     required_remediation_documentation: str = Field(description="Supporting documentation package needed")
#     required_remediation_timeline: str = Field(description="Target timeline window for correction")

# class AuditState(TypedDict):
#     """The graph state tracking the context data and parallel engine extractions."""
#     prospectus_text: str
#     retrieved_regulations_context: str
#     omissions_list: List[Dict[str, Any]]
#     gaps_list: List[Dict[str, Any]]
#     final_audit_report: str






# =====================================================================
# STEP 3: LANGRAPH NODES UTILIZING YOUR SETTINGS.LLM (MISTRAL 7B)
# =====================================================================

# Note: query_engine is created fresh inside each node function to avoid stale references

# async def retrieve_regulations_node(state: AuditState):
#     """Queries the local JSON vector store using your MiniLM embeddings."""
#     print("🔍 Querying local JSON Vector Store...")
    
#     # This automatically picks up your HuggingFaceEmbedding & Mistral LLM from Settings
#     query_engine = index.as_query_engine(
#         similarity_top_k=100,  
#         response_mode="compact" 
#     )
    
#     query_str = "Mandatory mineral resource classification reporting formatting rules under Form 43-101F1."
#     response = query_engine.query(query_str)
    
#     return {"retrieved_regulations_context": str(response)}


async def extract_omissions_node(state: MultiTaskState):
    """Extracts omissions using your global Mistral model via text structure guidance."""
    print("🤖 Running Section 1.1 Structural Omissions Extraction (Mistral)...")
    
    # Create fresh query engine to avoid stale node references
    # Reduced top_k to 5 to fit within context window
    query_engine = index.as_query_engine(
        similarity_top_k=5,  
        response_mode="compact" 
    )
    
    # Query the vector store - it will retrieve relevant sections
    # Don't include full PDF in query to avoid context overflow
    query_text = """As an expert investment fund technical analyst specializing in mineral project due diligence, 
identify completely missing elements required by Canadian National Instrument 43-101 technical reporting 
formatting rules or Form 43-101F1 items. Provide a detailed analysis of missing elements that would 
prevent institutional funding approval."""
    
    response = query_engine.query(query_text)    
    return {"omissions_answer": str(response)}

async def extract_gaps_node(state: MultiTaskState):
    """Extracts data gaps using your global Mistral model via text structure guidance."""
    print("🤖 Running Section 1.2 Active Project Gaps Analysis (Mistral)...")
    
    # Create fresh query engine to avoid stale node references
    # Reduced top_k to 5 to fit within context window
    query_engine = index.as_query_engine(
        similarity_top_k=5,  
        response_mode="compact" 
    )
    
    # Query the vector store - it will retrieve relevant sections
    # Don't include full PDF in query to avoid context overflow
    query_text = """As an expert investment fund technical analyst specializing in mineral project due diligence, 
identify items present in the document that are non-compliant, vague, or insufficient for an institutional 
funding decision under Canadian National Instrument 43-101 Regulatory Framework. Provide a detailed gap analysis 
of deficiencies that need to be addressed."""

    response = query_engine.query(query_text) 
    return {"gaps_answer": str(response)}

# async def synthesizer_node(state: AuditState):
#     """Compiles findings directly into the explicit target Markdown layout."""
#     print("📊 Compiling Final Executive Audit Report Layout...")
    
#     omissions = state.get('omissions_list', [])
#     gaps = state.get('gaps_list', [])
    
#     has_critical = any(x.get('risk_level') == 'CRITICAL' for x in omissions) or any(y.get('status') == 'NON-COMPLIANT' for y in gaps)
#     consensus_risk = "CRITICAL" if has_critical else "HIGH"
#     status_verdict = "Fail" if has_critical else "Action Required"
    
#     current_date = datetime.date.today().strftime("%Y-%m-%d")
    
#     report = f"""Executive Funding Risks Status: {status_verdict}
# **Evaluation Date:** {current_date}
# **Document Type Evaluated:** Audit Review
# **Consensus Risk Level:** {consensus_risk}

# ### 1.1 Critical Omissions & Mandatory Absences
# """
#     if not omissions:
#         report += "No critical structural omissions identified.\n"
#     for om in omissions:
#         report += f"""- **Missing Technical Item**: {om['missing_technical_item']}
# - **Required Disclosures**: {om['required_disclosures']}
# - **Risk Level**: {om['risk_level']}
# - **Funding Consequence**: {om['funding_consequence']}
# - **Compliance Remediation Steps**: 
# """
#         for step in om.get('compliance_remediation_steps', []):
#             report += f"  {step}\n"

#     report += "\n### 1.2 Active Project Gaps & Deficiencies\n"
#     if not gaps:
#         report += "No project data gaps identified.\n"
#     for gap in gaps:
#         report += f"""- **Checked Item**: {gap['checked_item']}
# - **Report Location**: {gap['report_location']}
# - **Regulatory Threshold Requirement**: {gap['regulatory_threshold_requirement']}
# - **Report Actual Disclosure**: {gap['report_actual_disclosure']}
# - **Analyst Gap Analysis**: {gap['analyst_gap_analysis']}
# - **Status**: {gap['status']}
# - **Required Remediation**: 
#   1. [Immediate action] {gap['required_remediation_immediate']}
#   2. [Supporting documentation] {gap['required_remediation_documentation']}
#   3. [Timeline] {gap['required_remediation_timeline']}
# """
#     return {"final_audit_report": report}

from langchain_core.messages import HumanMessage
from llama_index.core import Settings

async def synthesizer_node(state: MultiTaskState):
    print("\n--- [Node: Synthesizer] Merging Gaps & Omissions into Final Report... ---")
    
    # 1. Pull the individual answers generated by the previous nodes from the state
    gaps_content = state.get("gaps_answer", "No gaps identified.")
    omissions_content = state.get("omissions_answer", "No omissions identified.")
    
    # 2. Build a rigid engineering prompt to ensure Mistral merges them cleanly
    # without dropping critical data codes or hallucinating outside information.
    synthesis_prompt = (
        "SYSTEM INSTRUCTION:\n"
        "You are a senior compliance auditor. Your job is to synthesize two distinct sub-reports "
        "into a single, high-level Executive Summary. Group your findings logically and remain highly objective. "
        "Do NOT lose any specific names, codes, numbers, or facts listed in either sub-report.\n\n"
        f"--- SUB-REPORT A: EXTRACTED GAPS ---\n{gaps_content}\n\n"
        f"--- SUB-REPORT B: EXTRACTED OMISSIONS ---\n{omissions_content}\n\n"
        "FINAL SYNTHESIZED EXECUTIVE SUMMARY:"
    )
    
    # 3. Call your local Mistral model to read the combined string and write the final document
    response = Settings.llm.complete(synthesis_prompt)
    
    # 4. Save the final string output directly into the state
    return {"final_merged_report": response.text}


# =====================================================================
# STEP 4: ASSEMBLE AND COMPILE THE LANGGRAPH
# =====================================================================
builder = StateGraph(MultiTaskState)

# Add processing nodes to the flow configuration map
# builder.add_node("retrieve_regs", retrieve_regulations_node)
builder.add_node("read_entire_pdf", read_entire_pdf)
builder.add_node("extract_omissions", extract_omissions_node)
builder.add_node("extract_gaps", extract_gaps_node)
builder.add_node("synthesize_report", synthesizer_node)

# Map edge connections
# builder.add_edge(START, "retrieve_regs")

# Load target PDF document into state
builder.add_edge(START, "read_entire_pdf")

# Parallel Fan-Out split execution step
builder.add_edge("read_entire_pdf", "extract_omissions")
builder.add_edge("read_entire_pdf", "extract_gaps")

# Parallel Fan-In convergence join step back to synthesizer node
builder.add_edge("extract_omissions", "synthesize_report")
builder.add_edge("extract_gaps", "synthesize_report")

builder.add_edge("synthesize_report", END)

# Compile LangGraph app engine
app = builder.compile()


# COMMAND ----------

# DBTITLE 1,Execute Multi-Agent Workflow
# Execute the LangGraph workflow
import asyncio

print("🚀 Starting Multi-Agent Compliance Audit Workflow...\n")

# Initialize the state with the PDF path
initial_state = {
    "target_pdf_path": "/Workspace/Users/takashi.canada.toronto@gmail.com/thundercloud_43-101_technical_report.pdf",
    "target_document": "",
    "gaps_answer": "",
    "omissions_answer": "",
    "final_merged_report": ""
}

# Run the workflow
final_state = await app.ainvoke(initial_state)

print("\n" + "="*80)
print("📊 FINAL AUDIT REPORT")
print("="*80 + "\n")
print(final_state["final_merged_report"])

print("\n" + "="*80)
print("✅ Workflow Complete!")
print("="*80)

# COMMAND ----------



# COMMAND ----------

# MAGIC %md
# MAGIC                  +--------------------------+
# MAGIC
# MAGIC                   |        Start Node        |
# MAGIC                   +--------------------------+
# MAGIC                                |
# MAGIC                                v
# MAGIC                   +--------------------------+
# MAGIC
# MAGIC                   |   1. Load & Sanitize     | <--- Option 2: Wipes JORC/SAMREC/PERC
# MAGIC                   |      Vector DB Index     |      from memory right out of storage
# MAGIC                   +--------------------------+
# MAGIC                                |
# MAGIC                                v
# MAGIC          +---------------------+---------------------+
# MAGIC
# MAGIC          |                                           |
# MAGIC          v                                           v
# MAGIC +--------------------------+               +--------------------------+
# MAGIC
# MAGIC |   2. Omissions Node      |               |     3. Gap Node          |
# MAGIC |  (Extract Missing Items) |               | (Extract Vague Details)  |
# MAGIC +--------------------------+               +--------------------------+
# MAGIC
# MAGIC          |                                           |
# MAGIC          +---------------------+---------------------+
# MAGIC                                |
# MAGIC                                v
# MAGIC                   +--------------------------+
# MAGIC
# MAGIC                   |   4. Synthesizer Node    | <--- Compiles target layout
# MAGIC                   +--------------------------+
# MAGIC                                |
# MAGIC                                v
# MAGIC                   +--------------------------+
# MAGIC
# MAGIC                   |         End Node         |
# MAGIC                   +--------------------------+
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test Agent

# COMMAND ----------

# DBTITLE 1,Test Vector Store Retrieval
# Test the vector store with a sample query
from llama_index.core import VectorStoreIndex

# Create a retriever (no LLM needed for retrieval)
retriever = index.as_retriever(similarity_top_k=3)

# Test query
test_query = "Does the document states explicitly state that this is formal mandatory regulatory standard? If not,say no "

print(f"🔍 Query: {test_query}\n")
print("=" * 80)

# Retrieve relevant documents
nodes = retriever.retrieve(test_query)

print(f"\n📚 Found {len(nodes)} relevant documents:\n")

for i, node in enumerate(nodes, 1):
    print(f"\n--- Document {i} (Score: {node.score:.4f}) ---")
    print(node.text[:300] + "..." if len(node.text) > 300 else node.text)
    print()

print("\n✅ Vector store retrieval working correctly!")

# COMMAND ----------

# Create a query engine from the loaded Hugging Face index
# This cell depends on 'loaded_index_hf' being defined in the previous cell
try:
    query_engine_hf = index.as_query_engine()

    # Example query using mistralai/Mistral-7B
    print("\nQuerying with Hugging Face model...")
    # response_hf = query_engine_hf.query("What are the main contents of the document regarding disclosure?")

    response_hf = query_engine_hf.query("Is this mandatory regulatory standard?")

    print("\nQuery Response (mistralai/Mistral-7B):")
    print(response_hf)
except NameError:
    print("Error: 'index' is not defined. Please ensure the model loading cell (89d2a302) has executed successfully.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Simple AI Agent Example

# COMMAND ----------

# DBTITLE 1,Compliance Audit Function (RAG)
# import os
from pypdf import PdfReader

def read_entire_pdf(pdf_path):
    """Extract all text from a PDF with page markers."""
    reader = PdfReader(pdf_path)
    full_text = []
    for i, page in enumerate(reader.pages):
        full_text.append(f"--- START PAGE {i+1} ---\n{page.extract_text()}\n--- END PAGE {i+1} ---")
    return "\n".join(full_text)

def evaluate_document_with_rag(pdf_path):
    """
    Audit a mining document using RAG (Retrieval-Augmented Generation).
    The vector store automatically retrieves relevant Canadian regulatory standards.
    """
    # Read the uploaded mining document
    entire_doc_text = read_entire_pdf(pdf_path)
    
    # Create a query engine with custom system prompt
    query_engine = index.as_query_engine(
        similarity_top_k=100,  # Retrieve extensive regulatory context (32K context window)
        response_mode="compact"  # Use all chunks in single prompt with 32K window
    )
   
    # Construct the audit query
    # The query engine will automatically retrieve relevant regulations from the vector store
    audit_query = f"""
      ROLE & OBJECTIVE:
      You are an expert investment fund technical analyst specializing in mineral project due diligence. Validate [UPLOADED MINING INVESTMENT PROSPECTUS].

      [UPLOADED MINING INVESTMENT PROSPECTUS]:
      {entire_doc_text}

      NEGATIVE CONSTRAINT (CRITICAL):
      DO NOT validate or audit foreign standard compliance codes (e.g., JORC, PERC, SAMREC).
      ### 1.1 Critical Omissions & Mandatory Absences
      For EACH completely missing element required by technical reporting formatting rules:
      - **Missing Technical Item**: [Name of item]
      - **Required Disclosures**: [Detailed description of what must be added]
      - **Risk Level**: [CRITICAL / HIGH / MEDIUM / LOW]
      - **Funding Consequence**: [Specific impact on funding eligibility]
      - **Compliance Remediation Steps**: [Step-by-step action plan to fix]
      ### 1.2 Active Project Gaps & Deficiencies
      For EACH item present in the text but non-compliant, vague, or insufficient for an institutional funding decision:
      - **Checked Item**: [Specific disclosure requirement]
      - **Report Location**: [Page X, Section Y, or exact text quote]
      - **Regulatory Threshold Requirement**: [State the disclosure expectation standard]
      - **Report Actual Disclosure**: [Exact quote demonstrating the deficiency]
      - **Analyst Gap Analysis**: [Granular technical breakdown detailing why it fails]
      - **Status**: [NON-COMPLIANT / INSUFFICIENT DETAIL / WARNING]
      - **Required Remediation**: 
      1. [Immediate action] 
      2. [Supporting documentation] 
      3. [Timeline]
      OUTPUT FORMAT REQUIREMENTS:
      Provide an "Executive Funding Risks Status" summary at the top (Pass/Fail/Action Required), followed strictly by these two headers and their exact bullet layouts:
          **Evaluation Date:** [Current Date]
          **Document Type Evaluated:** Audit Review
          **Consensus Risk Level:** [CRITICAL / HIGH / MEDIUM / LOW]
    """

    
    print("🔍 Querying vector store for relevant regulations...\n")
    print("🤖 Running compliance audit with RAG...\n")
    
    # Query the RAG system (automatically retrieves + generates)
    response = query_engine.query(audit_query)
    
    return str(response)


# COMMAND ----------

evaluate_document_with_rag("/Workspace/Users/takashi.canada.toronto@gmail.com/NI_43-101_Technical_Services_RFP_Template.pdf")

# COMMAND ----------

# Read the entire PDF into one comprehensive string
def read_entire_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    full_text = []
    for i, page in enumerate(reader.pages):
        full_text.append(f"--- START PAGE {i+1} ---\n{page.extract_text()}\n--- END PAGE {i+1} ---")
    return "\n".join(full_text)

def evaluate_entire_document(pdf_path, vector_store):
    entire_doc_text = read_entire_pdf(pdf_path)
    
    # 1. Fetch the entire applicable regulatory framework from your vector store
    # (Using a broad metadata search or retrieving a dense overview suite)
    all_relevant_regs = vector_store.similarity_search("General Canadian Mining Compliance Framework Checklist", k=20)
    regulatory_context = "\n\n".join([doc.page_content for doc in all_relevant_regs])
    
    # 2. Evaluate everything in one massive context window
    llm = ChatOpenAI(model="gpt-4o", temperature=0.0) # Or Gemini / Claude
    
    prompt = f"""
    You are an elite Canadian mining auditor. You have access to the ENTIRE draft document and the relevant rules.
    Evaluate the overall document for absolute compliance. You must identify both active errors AND omissions.
    
    [OFFICIAL CANADIAN REGULATORY BACKGROUND]:
    {regulatory_context}
    
    [ENTIRE USER DOCUMENT TO TEST]:
    {entire_doc_text}
    
    Provide a comprehensive audit report. Call out pages and sections explicitly. 
    List any mandatory Canadian regulatory requirements that are completely MISSING from the user's document.
    """
    
    return llm.invoke(prompt).content