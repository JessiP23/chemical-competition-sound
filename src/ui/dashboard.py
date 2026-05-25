"""
Main Streamlit dashboard.

Provides the primary user interface for the Chemical-to-Audio
Intelligent Monitoring System with real-time visualizations.
"""

import streamlit as st
import time
import threading
from typing import Optional
from collections import deque

from src.io.sensor_manager import SensorManager, SensorReading
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
from src.config.settings import (
    settings,
    SystemMode,
    DashboardConfig
)


class ChemicalDashboard:
    """
    Main dashboard application.
    
    Orchestrates all system components and provides the
    Streamlit user interface.
    """
    
    def __init__(self):
        """Initialize dashboard."""
        self.sensor_manager = SensorManager()
        self.signal_processor = SignalProcessor()
        self.feature_extractor = FeatureExtractor()
        self.classifier = StateClassifier()
        self.mapper = ParameterMapper()
        self.tone_engine = ToneEngine()
        self.voice_engine = VoiceEngine()
        self.chart_generator = ChartGenerator()
        self.state_panel_generator = StatePanelGenerator()
        
        # Data buffers
        self.feature_buffer = FeatureBuffer(max_length=300)
        self.event_log: deque = deque(maxlen=50)
        
        # Control flags
        self.running = False
        self.audio_enabled = True
        self.voice_enabled = True
    
    def configure_page(self) -> None:
        """Configure Streamlit page settings."""
        st.set_page_config(
            page_title=settings.dashboard.PAGE_TITLE,
            page_icon=settings.dashboard.PAGE_ICON,
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    def apply_custom_css(self) -> None:
        """Apply custom CSS for dark theme."""
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
    
    def render_sidebar(self) -> None:
        """Render sidebar controls."""
        st.sidebar.title("⚙️ Settings")
        
        # Mode selection
        st.sidebar.subheader("System Mode")
        mode = st.sidebar.radio(
            "Select Mode",
            ["Simulation", "Hardware"],
            index=0
        )
        
        if mode == "Simulation":
            self._configure_simulation_mode()
        else:
            self._configure_hardware_mode()
        
        # Audio controls
        st.sidebar.subheader("Audio")
        self.audio_enabled = st.sidebar.checkbox("Enable Audio", value=True)
        self.voice_enabled = st.sidebar.checkbox("Enable Voice", value=True)
        
        # Display settings
        st.sidebar.subheader("Display")
        refresh_rate = st.sidebar.slider(
            "Refresh Rate (ms)",
            min_value=50,
            max_value=500,
            value=100,
            step=50
        )
        
        return refresh_rate
    
    def _configure_simulation_mode(self) -> None:
        """Configure simulation mode settings."""
        st.sidebar.info("Simulation Mode Active")
        
        scenario = st.sidebar.selectbox(
            "Scenario",
            ["Stable Reaction", "Acid-Base Titration", "Exothermic Reaction", "Unstable Oscillation"]
        )
        
        if st.sidebar.button("Apply Scenario"):
            simulator = self._get_scenario_simulator(scenario)
            self.sensor_manager.set_simulation_mode(simulator)
            self._log_event(f"Scenario changed: {scenario}")
    
    def _configure_hardware_mode(self) -> None:
        """Configure hardware mode settings."""
        st.sidebar.info("Hardware Mode Active")
        
        port = st.sidebar.text_input("Serial Port", value="/dev/ttyUSB0")
        
        if st.sidebar.button("Connect"):
            serial_reader = SerialReader(port=port)
            if self.sensor_manager.set_hardware_mode(serial_reader):
                self._log_event(f"Connected to {port}")
                st.sidebar.success("Connected!")
            else:
                self._log_event(f"Failed to connect to {port}")
                st.sidebar.error("Connection failed")
        
        if st.sidebar.button("Auto-Detect"):
            detected_port = auto_detect_port()
            if detected_port:
                st.sidebar.text(f"Detected: {detected_port}")
            else:
                st.sidebar.warning("No Arduino detected")
    
    def _get_scenario_simulator(self, scenario: str) -> ChemicalSimulator:
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
    
    def render_main_area(self) -> None:
        """Render main dashboard area."""
        # Title
        st.title("🧪 Chemical-to-Audio Intelligent Monitoring System")
        
        # Status bar
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            mode = self.sensor_manager.get_mode()
            mode_str = mode.value if mode else "Not configured"
            st.caption(f"Mode: {mode_str}")
        
        with col2:
            connected = self.sensor_manager.is_connected()
            status = "🟢 Connected" if connected else "🔴 Disconnected"
            st.caption(status)
        
        with col3:
            if st.button("Start/Stop"):
                self._toggle_system()
    
    def _toggle_system(self) -> None:
        """Toggle system running state."""
        if self.running:
            self.stop_system()
        else:
            self.start_system()
    
    def start_system(self) -> None:
        """Start the monitoring system."""
        if not self.sensor_manager.is_connected():
            st.error("No sensor source connected!")
            return
        
        self.running = True
        
        # Initialize audio
        if self.audio_enabled:
            if self.tone_engine.start():
                self._log_event("Audio engine started")
            else:
                self._log_event("Failed to start audio engine")
        
        # Initialize voice
        if self.voice_enabled:
            if self.voice_engine.initialize():
                self.voice_engine.start()
                self._log_event("Voice engine started")
        
        self._log_event("System started")
    
    def stop_system(self) -> None:
        """Stop the monitoring system."""
        self.running = False
        
        # Stop audio
        self.tone_engine.stop()
        self._log_event("Audio engine stopped")
        
        # Stop voice
        self.voice_engine.stop()
        self._log_event("Voice engine stopped")
        
        self._log_event("System stopped")
    
    def update_loop(self, refresh_rate: int) -> None:
        """
        Main update loop.
        
        Args:
            refresh_rate: Refresh rate in milliseconds
        """
        if not self.running:
            st.info("System stopped. Click 'Start/Stop' to begin monitoring.")
            return
        
        # Read sensor data
        reading = self.sensor_manager.read()
        
        if reading is None:
            st.warning("No sensor data available")
            return
        
        # Process signal
        ph_filtered = self.signal_processor.process(reading.ph)
        temp_filtered = self.signal_processor.process(reading.temperature)
        
        # Extract features
        features = self.feature_extractor.extract(
            ph_filtered,
            temp_filtered,
            reading.timestamp,
            reading.color_r,
            reading.color_g,
            reading.color_b
        )
        
        # Classify state
        classification = self.classifier.classify(features)
        
        # Map to audio parameters
        audio_mapping = self.mapper.map(features, classification.state)
        
        # Update audio
        if self.audio_enabled:
            self.tone_engine.update_mapping(audio_mapping)
        
        # Update voice
        if self.voice_enabled:
            self.voice_engine.announce_state(classification.state, classification.severity)
        
        # Update buffers
        self.feature_buffer.add_features(features, classification.state.value)
        
        # Log events
        if classification.triggers:
            for trigger in classification.triggers:
                self._log_event(f"Trigger: {trigger}")
        
        # Render visualizations
        self._render_dashboard(features, classification, audio_mapping)
        
        # Sleep for refresh rate
        time.sleep(refresh_rate / 1000.0)
    
    def _render_dashboard(
        self,
        features,
        classification,
        audio_mapping
    ) -> None:
        """Render dashboard visualizations."""
        # Main status
        self.state_panel_generator.render_main_status(
            classification.state,
            classification.confidence
        )
        
        # Sensor cards
        self.state_panel_generator.render_sensor_cards(
            features.ph,
            features.temperature,
            features.instability_score
        )
        
        # Charts row
        col1, col2 = st.columns(2)
        
        with col1:
            ph_history = self.feature_buffer.get_ph_history()
            temp_history = self.feature_buffer.get_temp_history()
            timestamps = list(range(len(ph_history)))
            
            if len(ph_history) > 1:
                fig = self.chart_generator.create_combined_chart(
                    timestamps,
                    ph_history,
                    temp_history
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            volatility_history = self.feature_buffer.get_instability_history()
            timestamps = list(range(len(volatility_history)))
            
            if len(volatility_history) > 1:
                fig = self.chart_generator.create_volatility_chart(
                    timestamps,
                    volatility_history
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # State timeline
        state_history = self.feature_buffer.get_state_history()
        timestamps = list(range(len(state_history)))
        
        if len(state_history) > 1:
            fig = self.chart_generator.create_state_timeline(
                timestamps,
                state_history
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Additional panels
        col1, col2 = st.columns(2)
        
        with col1:
            self.state_panel_generator.render_triggers_panel(classification.triggers)
        
        with col2:
            self.state_panel_generator.render_severity_meter(classification.severity)
        
        # Audio status
        if self.audio_enabled:
            self.state_panel_generator.render_audio_status(
                audio_mapping.pitch_center,
                audio_mapping.rhythm_density,
                audio_mapping.harmonic_consistency
            )
        
        # Event log
        self.state_panel_generator.render_event_log(list(self.event_log))
    
    def _log_event(self, message: str) -> None:
        """Log event to event log."""
        timestamp = time.strftime("%H:%M:%S")
        self.event_log.append(f"[{timestamp}] {message}")
    
    def run(self) -> None:
        """Run the dashboard application."""
        self.configure_page()
        self.apply_custom_css()
        
        refresh_rate = self.render_sidebar()
        self.render_main_area()
        
        # Initialize with simulation mode by default
        simulator = PresetScenario.stable_reaction()
        self.sensor_manager.set_simulation_mode(simulator)
        self._log_event("Initialized in simulation mode")
        
        # Main loop
        while True:
            try:
                self.update_loop(refresh_rate)
            except Exception as e:
                st.error(f"Error in update loop: {e}")
                self.stop_system()
                break


def main():
    """Main entry point."""
    dashboard = ChemicalDashboard()
    dashboard.run()


if __name__ == "__main__":
    main()
