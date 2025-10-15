"""
Intent Library - Browse available intents
"""

import streamlit as st
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from frontend.backend_interface import BackendInterface

st.set_page_config(page_title="Intent Library", page_icon="📚", layout="wide")

st.title("📚 Intent Library")
st.markdown("Browse available intent specifications")

# Initialize backend
backend = BackendInterface()

# Load intents
intents = backend.get_available_intents()

if not intents:
    st.warning("No intents found. Add intent specifications to `data/intents/`")
else:
    st.success(f"Found {len(intents)} intent(s)")

    # Search/filter
    search_query = st.text_input("🔍 Search intents", placeholder="Enter keywords...")

    # Filter intents
    if search_query:
        filtered_intents = [
            intent for intent in intents
            if search_query.lower() in intent['name'].lower()
            or search_query.lower() in intent['txt_description'].lower()
        ]
    else:
        filtered_intents = intents

    st.markdown(f"Showing {len(filtered_intents)} intent(s)")

    # Display intents
    for intent in filtered_intents:
        with st.expander(f"📋 {intent['name'].replace('_', ' ').title()}"):
            # Natural language description
            st.markdown("### Description")
            if intent['txt_description']:
                st.markdown(intent['txt_description'])
            else:
                st.info("No natural language description available")

            st.markdown("---")

            # Structured specification
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown("### Structured Specification (TTL)")

                # Read TTL file
                ttl_path = Path(intent['ttl_path'])
                if ttl_path.exists():
                    with open(ttl_path, 'r') as f:
                        ttl_content = f.read()
                    st.code(ttl_content, language="turtle")
                else:
                    st.error("TTL file not found")

            with col2:
                st.markdown("### Metadata")

                # Display structured info
                structured = intent.get('structured', {})

                if structured.get('intents'):
                    st.markdown("**Intents:**")
                    for i in structured['intents']:
                        st.write(f"- {i.get('description', 'No description')}")

                if structured.get('expectations'):
                    st.markdown("**Expectations:**")
                    for exp in structured['expectations']:
                        st.write(f"- {exp.get('description', 'No description')}")

                if structured.get('conditions'):
                    st.markdown("**Conditions:**")
                    for cond in structured['conditions']:
                        st.write(f"- {cond.get('description', 'No description')}")

                # File info
                st.markdown("---")
                st.markdown("**Files:**")
                st.write(f"📄 {Path(intent['ttl_path']).name}")

    # Info section
    st.markdown("---")
    with st.expander("ℹ️ About Intents"):
        st.markdown("""
        ### What are Intents?

        Intents represent administrative goals and expectations for system behavior.
        Each intent includes:

        - **Natural Language Description**: Human-readable explanation
        - **Structured Specification (TTL)**: Machine-readable format following TMForum standards
        - **Expectations**: Specific requirements (e.g., response time < 500ms)
        - **Conditions**: Constraints and rules

        ### Intent Compliance

        When analyzing logs, iExplain can check if system behavior complies with intent expectations:
        - ✅ **COMPLIANT**: All expectations met
        - ⚠️ **DEGRADED**: Some expectations not met
        - ❌ **NON_COMPLIANT**: Critical expectations violated

        ### Adding New Intents

        To add a new intent:
        1. Create a folder in `data/intents/<intent_name>/`
        2. Add `<intent_name>.txt` with natural language description
        3. Add `<intent_name>.ttl` with TMForum specification
        4. Restart the app to reload intents
        """)
