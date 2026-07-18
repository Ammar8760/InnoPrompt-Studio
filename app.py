import streamlit as st
import json
from google import genai
from google.genai.errors import APIError

# 1. Page Configuration (Must be first)
st.set_page_config(
    page_title="InnoPrompt Studio", 
    page_icon="", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Inject Custom Premium CSS Styling
st.markdown("""
<style>
    /* Global Styles & Background Adjustments */
    .stApp {
        background-color: #0d1117;
    }
    
    /* Global Typography refinements */
    h1, h2, h3, h4, p, span, label {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    }
    
    /* Clean, elevated Section Cards */
    div[data-testid="stVerticalBlock"] > div {
        border-radius: 8px;
    }
    
    /* Distinct styling for input boxes */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        color: #c9d1d9 !important;
        border-radius: 6px !important;
        transition: border-color 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
    }
    
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #58a6ff !important;
        box-shadow: 0 0 0 3px rgba(88, 166, 255, 0.15) !important;
    }
    
    /* Clean, modern style for headers */
    h2 {
        font-weight: 700 !important;
        letter-spacing: -0.5px !important;
        color: #f0f6fc !important;
        margin-bottom: 0.5rem !important;
    }
    
    h3 {
        font-weight: 600 !important;
        color: #e6edf3 !important;
        margin-bottom: 0.4rem !important;
    }

    /* Target the primary "Generate AI Response" button for a clean gradient glow */
    button[kind="primary"] {
        background: linear-gradient(135deg, #ff5e62, #ff9966) !important;
        border: none !important;
        color: white !important;
        font-weight: 600 !important;
        border-radius: 6px !important;
        padding: 0.6rem 1.2rem !important;
        transition: transform 0.1s ease, filter 0.2s ease !important;
    }
    button[kind="primary"]:hover {
        filter: brightness(1.1) !important;
        transform: translateY(-1px);
    }
    button[kind="primary"]:active {
        transform: translateY(1px);
    }
</style>
""", unsafe_allow_html=True)

# --- APP HEADER ---
st.title("Inno-Prompt Studio")

st.markdown("---")

# Initialize Local Session State for Prompt Library & AI Output
if "prompt_library" not in st.session_state:
    st.session_state.prompt_library = {}
if "ai_response" not in st.session_state:
    st.session_state.ai_response = ""

# --- LAYOUT: Two Main Columns for Blueprinting ---
col_inputs, col_preview = st.columns([6, 5], gap="large")

# --- LEFT COLUMN: Input Fields & Templates ---
with col_inputs:
    st.subheader(" Prompt Blueprint")
    
    # --- SHOWCASE TEMPLATES DATABASE ---
    templates = {
        "None": {
            "role": "", "tone": "", "task": "", "context": "",
            "constraints": "", "negative_instructions": "", "examples": "",
            "output_format": "", "success_criteria": ""
        },
        " Cybersecurity: SOC Incident Responder": {
            "role": "Lead Incident Responder & Security Operations Center (SOC) Analyst",
            "tone": "Clinical, highly technical, analytical, and objective",
            "task": "Analyze raw server auth and firewall logs to determine if an active intrusion, brute-force attack, or lateral movement is taking place.",
            "context": "A localized security incident on an enterprise subnet. The system logs might contain a mix of benign administrative actions and targeted attacks.",
            "constraints": "Focus purely on indicators of compromise (IoCs). Explain the technical mechanism behind any malicious log sequences.",
            "negative_instructions": "Do not make assumptions without log-based evidence. Do not suggest specific commercial antivirus or EDR/XDR brands.",
            "examples": 'Input: "2026-07-15 03:14:22 Failed SSH password for admin from 10.0.0.12 port 4912"\nOutput: "Failed Authentication: Potential internal reconnaissance/brute-force from unauthorized local IP 10.0.0.12. Recommendation: Temporary IP block."',
            "output_format": "Markdown table containing: Timestamp, Target Vector, Severity (High/Medium/Low), and Actionable Remediation Step.",
            "success_criteria": "Zero false positives on benign system cron-job logs, with immediate critical alerts on network enumeration logs."
        },
        " Computer Science: Parallel Code Optimizer": {
            "role": "Senior Performance & Systems Engineer",
            "tone": "Academic, highly technical, and optimization-focused",
            "task": "Identify execution bottlenecks in sequential Python code and redesign it using parallel or distributed processing architectures.",
            "context": "Code is designed to process 10 million transactions but is currently running sequentially on a single thread of an 8-core CPU.",
            "constraints": "Code must remain fully thread-safe. Use Amdahl's Law to mathematically calculate the theoretical speedup limit based on the parallelizable fraction (p) of the program.",
            "negative_instructions": "Do not use heavy external frameworks like Apache Spark if standard library multiprocessing or concurrent.futures can handle the load.",
            "examples": 'Input: "for x in range(1000000): process(x)"\nOutput: "Redesign sequential iterations using multi-core multiprocessing pool maps."',
            "output_format": "Modern structural breakdown: 'Original Bottleneck Analysis', 'Optimized Code Block', and 'Theoretical Speedup Equation & Curve'.",
            "success_criteria": "The resulting parallelized logic prevents thread race conditions and achieves a measurable reduction in execution time."
        },
        " Electronics: Circuit Protection Designer": {
            "role": "Senior Analog Hardware Architect",
            "tone": "Practical, precise, engineering-focused",
            "task": "Design a dual-diode clipper and clamper circuit to modify a raw ±12V AC input signal for a specific micro-controller ADC input pin (0V to 3.3V).",
            "context": "Designing protection circuitry for a delicate, low-voltage embedded system input.",
            "constraints": "Must use standard silicon diode voltage drops (0.7V) or Schottky diodes (0.3V) in the structural circuit logic.",
            "negative_instructions": "Do not use active operational-amplifier layouts if simple passive components (resistors, diodes, capacitors) can safely achieve the clipping limits.",
            "examples": 'Input: AC signal exceeds peak of 5V\nOutput: Signal is actively clipped at 3.3V + 0.3V (diode drop threshold) protecting the micro-controller.',
            "output_format": "Bulleted component list followed by a step-by-step schematic logic walk-through.",
            "success_criteria": "The final circuit design mathematically prevents the voltage from exceeding 3.3V or dropping below 0V under any input spike scenario."
        }
    }
    
    # Template Selection UI
    selected_template = st.selectbox(" Quick-Load Showcase Blueprint:", list(templates.keys()))
    t_data = templates[selected_template]
    
    st.markdown("---")
    
    r_col1, r_col2 = st.columns(2)
    with r_col1:
        role = st.text_input("Role / Persona", value=t_data["role"], placeholder="e.g., Senior React Developer")
    with r_col2:
        tone = st.text_input("Tone", value=t_data["tone"], placeholder="e.g., Professional, direct, casual")
        
    task = st.text_area("The Task", value=t_data["task"], placeholder="What exactly should the AI generate or do?", height=68)
    context = st.text_area("Context & Background", value=t_data["context"], placeholder="Provide relevant history, domain information, or audience details", height=68)
    
    c_col1, c_col2 = st.columns(2)
    with c_col1:
        constraints = st.text_area("Constraints & Rules", value=t_data["constraints"], placeholder="Length, specific vocabulary, processing rules", height=100)
    with c_col2:
        negative_instructions = st.text_area("Negative Instructions (What to avoid)", value=t_data["negative_instructions"], placeholder="What should the AI absolutely NOT do?", height=100)
        
    examples = st.text_area("Few-Shot Examples (Optional)", value=t_data["examples"], placeholder="Input: ... \nOutput: ...", height=68)
    
    f_col1, f_col2 = st.columns(2)
    with f_col1:
        output_format = st.text_input("Output Format", value=t_data["output_format"], placeholder="e.g., Markdown table, raw JSON")
    with f_col2:
        success_criteria = st.text_input("Success Criteria", value=t_data["success_criteria"], placeholder="What standards make this output perfect?")

# --- COMPILE PROMPT STRING ---
compiled_prompt = f"""# ROLE
{role if role else '[Define the persona/role...]'}

# CONTEXT & TASK
Task: {task if task else '[What needs to be done?]'}
Context: {context if context else '[Background info]'}

# CONSTRAINTS & NEGATIVE INSTRUCTIONS
- {constraints if constraints else '[Any rules to follow?]'}
- Do NOT: {negative_instructions if negative_instructions else '[What should the AI avoid?]'}

# FEW-SHOT EXAMPLES
{examples if examples else '[Provide examples of ideal output if any...]'}

# OUTPUT FORMAT & TONE
- Format: {output_format if output_format else '[Markdown, JSON, Bullet points...]'}
- Tone: {tone if tone else '[Professional, casual, technical...]'}

# SUCCESS CRITERIA
- {success_criteria if success_criteria else '[What makes this output perfect?]'}\n"""

# --- RIGHT COLUMN: Live Preview ---
with col_preview:
    st.subheader("Live Preview & Compiled Output")
    st.code(compiled_prompt, language="markdown")
    
    st.download_button(
        label=" Download Prompt as .txt",
        data=compiled_prompt,
        file_name="structured_prompt.txt",
        mime="text/plain",
        use_container_width=True
    )

st.markdown("---")

# --- MIDDLE SECTION: Side-by-Side Actions ---
col_save, col_lib = st.columns(2, gap="large")

with col_save:
    st.markdown("### Save to Library")
    save_name = st.text_input("Name this prompt setup to save it:")
    if st.button("Save Prompt", type="primary", use_container_width=True):
        if save_name.strip():
            st.session_state.prompt_library[save_name] = {
                "role": role, "tone": tone, "task": task, "context": context,
                "constraints": constraints, "negative_instructions": negative_instructions,
                "examples": examples, "output_format": output_format, "success_criteria": success_criteria
            }
            st.success(f"Successfully saved '{save_name}' to Library!")
        else:
            st.warning("Please provide a name to save the prompt configuration.")

with col_lib:
    st.markdown("###  Prompt Library")
    if not st.session_state.prompt_library:
        st.info("Your saved prompt library is empty. Build and save a prompt configuration on the left!")
    else:
        selected_saved = st.selectbox("Select a saved prompt to load/view:", list(st.session_state.prompt_library.keys()))
        if selected_saved:
            loaded_data = st.session_state.prompt_library[selected_saved]
            st.write(f"**Loaded Configuration:** {selected_saved}")
            if st.button("❌ Delete Selected Prompt", use_container_width=True):
                del st.session_state.prompt_library[selected_saved]
                st.rerun()

st.markdown("---")

# --- BOTTOM SECTION: Full-Page Width Gemini Playground ---
st.subheader("Run Prompt with Gemini")

# Handle API Key
api_key = ""
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    api_key = st.text_input("Enter your Gemini API Key:", type="password", help="Get a free key from Google AI Studio")

# Perfect, bottom-aligned columns using native layout engine
g_col1, g_col2 = st.columns([4, 1], vertical_alignment="bottom")
with g_col1:
    model_choice = st.selectbox("Select Gemini Model", ["gemini-2.5-flash", "gemini-2.5-pro"])
with g_col2:
    run_btn = st.button("✨ Generate AI Response", use_container_width=True, type="primary")

if run_btn:
    if not api_key:
        st.error("API Key is missing! Please set it up in secrets or enter it above.")
    else:
        with st.spinner("Gemini is processing your prompt structure..."):
            try:
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model=model_choice,
                    contents=compiled_prompt
                )
                st.session_state.ai_response = response.text
                st.toast("Success! Response generated.")
            except APIError as e:
                st.error(f"API Error: {e.message}")
            except Exception as e:
                st.error(f"Error calling API: {str(e)}")

# Display the output using the full width of the screen, just like an official LLM!
if st.session_state.ai_response:
    st.markdown("---")
    st.subheader("AI Output")
    st.info("The output below was generated using your structured system prompt rules above.")
    st.markdown(st.session_state.ai_response)