"""
Main application entry point for Chemical-to-Audio Intelligent Monitoring System.

This is the primary entry point that launches the Streamlit dashboard.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import streamlit as st
from src.io.sensor_manager import SensorManager
from src.io.simulator import ChemicalSimulator, PresetScenario
from src.io.serial_reader import SerialReader, auto_detect_port
from src.core.signal_tools import SignalProcessor
from src.core.feature_extraction import FeatureExtractor, FeatureBuffer
from src.core.classifier import StateClassifier, ReactionState
from src.core.mapping import ParameterMapper, AudioMapping
from src.audio.tone_engine import ToneEngine
from src.audio.voice_engine import VoiceEngine
from src.ui.charts import ChartGenerator
from src.ui.state_panels import StatePanelGenerator
from src.config.settings import settings


def main():
    """Main dashboard application."""
    # Configure page
    st.set_page_config(
        page_title="Chemical-to-Audio Intelligent Monitoring System",
        page_icon="🧪",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Apply custom CSS
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #0d1117;
        }
        .stTextInput > div > div > input,
        .stSelectbox > div > div > select {
            background-color: #1e1e1e;
            color: white;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    # Initialize components
    sensor_manager = SensorManager()
    signal_processor = SignalProcessor()
    feature_extractor = FeatureExtractor()
    classifier = StateClassifier()
    mapper = ParameterMapper()
    tone_engine = ToneEngine()
    voice_engine = VoiceEngine()
    chart_generator = ChartGenerator()
    state_panel_generator = StatePanelGenerator()
    
    feature_buffer = FeatureBuffer(max_length=300)
    event_log = []
    
    running = False
    audio_enabled = True
    voice_enabled = True
    
    # Sidebar
    st.sidebar.title("⚙️ Settings")
    
    mode = st.sidebar.radio("System Mode", ["Simulation", "Hardware"], index=0)
    
    if mode == "Simulation":
        st.sidebar.info("Simulation Mode Active")
        scenario = st.sidebar.selectbox(
            "Scenario",
            ["Stable Reaction", "Acid-Base Titration", "Exothermic Reaction", "Unstable Oscillation"]
        )
        if st.sidebar.button("Apply Scenario"):
            simulator = get_scenario_simulator(scenario)
            sensor_manager.set_simulation_mode(simulator)
            event_log.append(f"Scenario changed: {scenario}")
    else:
        st.sidebar.info("Hardware Mode Active")
        port = st.sidebar.text_input("Serial Port", value="/dev/ttyUSB0")
        if st.sidebar.button("Connect"):
            serial_reader = SerialReader(port=port)
            if sensor_manager.set_hardware_mode(serial_reader):
                event_log.append(f"Connected to {port}")
                st.sidebar.success("Connected!")
            else:
                event_log.append(f"Failed to connect to {port}")
                st.sidebar.error("Connection failed")
        if st.sidebar.button("Auto-Detect"):
            detected_port = auto_detect_port()
            if detected_port:
                st.sidebar.text(f"Detected: {detected_port}")
            else:
                st.sidebar.warning("No Arduino detected")
    
    audio_enabled = st.sidebar.checkbox("Enable Audio", value=True)
    voice_enabled = st.sidebar.checkbox("Enable Voice", value=True)
    refresh_rate = st.sidebar.slider("Refresh Rate (ms)", 50, 500, 100, 50)
    
    # Main area
    st.title("🧪 Chemical-to-Audio Intelligent Monitoring System")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        current_mode = sensor_manager.get_mode()
        mode_str = current_mode.value if current_mode else "Not configured"
        st.caption(f"Mode: {mode_str}")
    with col2:
        connected = sensor_manager.is_connected()
        status = "🟢 Connected" if connected else "🔴 Disconnected"
        st.caption(status)
    with col3:
        if st.button("Start/Stop"):
            running = not running
            if running:
                if not sensor_manager.is_connected():
                    st.error("No sensor source connected!")
                    running = False
                else:
                    if audio_enabled:
                        tone_engine.start()
                    if voice_enabled:
                        if voice_engine.initialize():
                            voice_engine.start()
                    event_log.append("System started")
            else:
                tone_engine.stop()
                voice_engine.stop()
                event_log.append("System stopped")
    
    # Initialize with simulation
    if not sensor_manager.is_connected():
        simulator = PresetScenario.stable_reaction()
        sensor_manager.set_simulation_mode(simulator)
        event_log.append("Initialized in simulation mode")
    
    # Update loop
    if running:
        reading = sensor_manager.read()
        if reading:
            ph_filtered = signal_processor.process(reading.ph)
            temp_filtered = signal_processor.process(reading.temperature)
            
            features = feature_extractor.extract(
                ph_filtered, temp_filtered, reading.timestamp,
                reading.color_r, reading.color_g, reading.color_b
            )
            
            classification = classifier.classify(features)
            audio_mapping = mapper.map(features, classification.state)
            
            if audio_enabled:
                tone_engine.update_mapping(audio_mapping)
            
            if voice_enabled:
                voice_engine.announce_state(classification.state, classification.severity)
            
            feature_buffer.add_features(features, classification.state.value)
            
            if classification.triggers:
                for trigger in classification.triggers:
                    event_log.append(f"Trigger: {trigger}")
            
            # Render
            state_panel_generator.render_main_status(classification.state, classification.confidence)
            state_panel_generator.render_sensor_cards(features.ph, features.temperature, features.instability_score)
            
            ph_history = feature_buffer.get_ph_history()
            temp_history = feature_buffer.get_temp_history()
            timestamps = list(range(len(ph_history)))
            
            if len(ph_history) > 1:
                col1, col2 = st.columns(2)
                with col1:
                    fig = chart_generator.create_combined_chart(timestamps, ph_history, temp_history)
                    st.plotly_chart(fig, use_container_width=True)
                with col2:
                    volatility_history = feature_buffer.get_instability_history()
                    fig = chart_generator.create_volatility_chart(timestamps, volatility_history)
                    st.plotly_chart(fig, use_container_width=True)
            
            state_history = feature_buffer.get_state_history()
            if len(state_history) > 1:
                fig = chart_generator.create_state_timeline(timestamps, state_history)
                st.plotly_chart(fig, use_container_width=True)
            
            col1, col2 = st.columns(2)
            with col1:
                state_panel_generator.render_triggers_panel(classification.triggers)
            with col2:
                state_panel_generator.render_severity_meter(classification.severity)
            
            if audio_enabled:
                state_panel_generator.render_audio_status(
                    audio_mapping.pitch_center,
                    audio_mapping.rhythm_density,
                    audio_mapping.harmonic_consistency
                )
            
            state_panel_generator.render_event_log(event_log[-10:])
        else:
            st.warning("No sensor data available")
    else:
        st.info("System stopped. Click 'Start/Stop' to begin monitoring.")


def get_scenario_simulator(scenario: str) -> ChemicalSimulator:
    """Get simulator for selected scenario."""
    if scenario == "Stable Reaction":
        return PresetScenario.stable_reaction()
    elif scenario == "Acid-Base Titration":
        return PresetScenario.acid_base_titration()
    elif scenario == "Exothermic Reaction":
        return PresetScenario.exothermic_reaction()
    elif scenario == "Unstable Oscillation":
        return PresetScenario.unstable_oscillation()
    else:
        return PresetScenario.stable_reaction()


if __name__ == "__main__":
    main()
