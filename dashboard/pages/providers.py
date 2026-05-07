"""
Providers Page
==============
Paid provider management with intuitive API key input.
"""
import streamlit as st

from dashboard.data.keys import key_present, set_env_key, remove_env_key
from dashboard.data.profiles import get_paid_profiles
from dashboard.ui.components import section_header, action_result, provider_card_header
from dashboard.utils import file_preview, run_ps


def render():
    """Render providers page."""
    section_header(
        "Providers",
        "Manage paid API keys for turbo mode",
        [("Paid Optional", "warn"), ("Local Default", "ready")]
    )

    # Quick actions
    cols = st.columns(2)
    with cols[0]:
        if st.button("Refresh Status", use_container_width=True):
            for key in list(st.session_state.keys()):
                if key.startswith("key_present_"):
                    del st.session_state[key]
            st.rerun()

    with cols[1]:
        if st.button("Compare Models", use_container_width=True):
            code, out = run_ps("compare-models.ps1", timeout=240)
            action_result("Compare", code, out)

    st.warning("Paid providers are for manual turbo mode only. Scheduled workers always use local models.")

    # Provider cards
    st.markdown("### API Keys")
    st.info("Enter your API keys below. They are stored in Windows environment variables and never saved to files.")

    profiles = get_paid_profiles()
    if not profiles:
        st.info("No paid provider profiles are configured.")
        return

    for profile_name, profile in profiles.items():
        env_var = profile.get("apiKeyEnvVar")
        provider = profile.get("provider", "unknown").title()
        model = profile.get("model", "unknown")
        role = profile.get("role", "")

        has_key = key_present(env_var)

        # Card container
        with st.container():
            st.markdown('<div class="key-input-group">', unsafe_allow_html=True)

            # Header with status
            provider_card_header(provider, model, role, has_key)

            # Key management
            if not has_key:
                with st.form(key=f"key_form_{profile_name}"):
                    st.markdown(f"Enter the **{provider}** API key:")
                    key_input = st.text_input(
                        "API Key",
                        type="password",
                        key=f"input_{profile_name}",
                        placeholder="sk-...",
                        label_visibility="collapsed"
                    )

                    cols = st.columns([1, 3])
                    with cols[0]:
                        submitted = st.form_submit_button("Save API Key", type="primary")

                    if submitted and key_input:
                        if set_env_key(env_var, key_input):
                            st.success(f"{provider} API key saved.")
                            st.rerun()
                        else:
                            st.error("Failed to save key. Try again or verify the target environment variable.")
                    elif submitted:
                        st.error("API key cannot be blank.")
            else:
                # Show actions for configured key
                cols = st.columns([1, 1, 2])

                with cols[0]:
                    if st.button("Remove", key=f"remove_{profile_name}"):
                        if remove_env_key(env_var):
                            st.success(f"{provider} key removed.")
                            st.rerun()

                with cols[1]:
                    if st.button("Test", key=f"test_{profile_name}"):
                        code, out = run_ps(
                            "test-provider-model.ps1",
                            "-ProviderName", profile.get("provider"),
                            "-BaseUrl", profile.get("baseUrl"),
                            "-Model", profile.get("model"),
                            "-ApiKeyEnvVar", env_var,
                            timeout=180
                        )
                        action_result(f"Test {provider}", code, out)

            st.markdown('</div>', unsafe_allow_html=True)

    # Reference
    with st.expander("Provider Configuration"):
        from dashboard.config import PROFILES_FILE
        st.code(file_preview(PROFILES_FILE, 12000))
