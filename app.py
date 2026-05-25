"""
app.py

Streamlit dashboard for Chemical-to-Audio Intelligent Monitoring System.

Architecture:
  - Main thread: Streamlit UI (refreshes at DASHBOARD_REFRESH_MS)
  - Background thread: Sensor → Feature → Classify → Map → Audio loop (20 Hz)
  - SharedState: Thread-safe ring buffer for data exchange
"""

import sys
import os
import time
import threading
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import streamlit as st
import numpy as np

from src.io.sensor_manager import SensorManager
from src.core.feature_extraction import FeatureExtractor
from src.core.classifier import StateClassifier
from src.core.mapping import compute_audio_params
from src.audio.tone_engine import ToneEngine
from src.audio.voice_engine import VoiceEngine
from src.ui.charts import plot_fft, plot_spectrogram, plot_radar, plot_time_series, plot_waveform
from shared_state.ringbuffer import SharedState
from src.config.settings import DASHBOARD_REFRESH_MS, SAMPLE_RATE


def processing_loop(shared_state, sensor_manager, feature_extractor,
                     classifier, tone_engine, voice_engine):
    """Background thread: continuous sensor → audio pipeline."""
    prev_state = "stable"
    while True:
        sensor_data = sensor_manager.read()
        features = feature_extractor.update(sensor_data)
        classification = classifier.classify(features)
        audio_params = compute_audio_params(features, classification["state"])

        # Update tone engine
        tone_engine.update_params(audio_params)

        # Voice announcements on state change
        if classification["changed"]:
            voice_engine.announce_transition(prev_state, classification["state"], features)
            prev_state = classification["state"]

        # Update shared state
        shared_state.update(sensor_data, features, classification["state"])

        # Update spectrogram from audio engine waveform
        waveform = tone_engine.get_waveform()
        shared_state.update_waveform(waveform)
        shared_state.update_spectrogram(waveform)

        time.sleep(1.0 / 20.0)  # 20 Hz processing rate


def main():
    st.set_page_config(page_title="Chemical-to-Audio Monitoring", page_icon="🧪", layout="wide")

    # Initialize components (once)
    if "initialized" not in st.session_state:
        st.session_state.shared_state = SharedState()
        st.session_state.sensor_manager = SensorManager()
        st.session_state.feature_extractor = FeatureExtractor()
        st.session_state.classifier = StateClassifier()
        st.session_state.tone_engine = ToneEngine()
        st.session_state.voice_engine = VoiceEngine()
        st.session_state.initialized = True

        # Start background processing thread
        proc_thread = threading.Thread(
            target=processing_loop,
            args=(
                st.session_state.shared_state,
                st.session_state.sensor_manager,
                st.session_state.feature_extractor,
                st.session_state.classifier,
                st.session_state.tone_engine,
                st.session_state.voice_engine
            ),
            daemon=True
        )
        proc_thread.start()

        # Start audio
        st.session_state.tone_engine.start()
        st.session_state.voice_engine.start()

    shared_state = st.session_state.shared_state
    sensor_manager = st.session_state.sensor_manager
    tone_engine = st.session_state.tone_engine

    # Sidebar controls
    st.sidebar.title("Controls")
    if st.sidebar.button("Inject Disturbance"):
        sensor_manager.inject_disturbance()

    if st.sidebar.button("Reset Simulator"):
        sensor_manager.reset()

    # Main dashboard
    st.title("🧪 Chemical-to-Audio Intelligent Monitoring System")

    # Current status
    current = shared_state.get_current()
    state = current["state"]
    features = current["features"]

    col1, col2, col3 = st.columns(3)
    col1.metric("State", state.upper())
    col2.metric("pH", f"{features.get('ph_value', 0):.2f}")
    col3.metric("Temperature", f"{features.get('temp_value', 0):.1f}°C")

    # Charts row 1: Time series + Radar
    history = shared_state.get_history()
    col1, col2 = st.columns([2, 1])
    with col1:
        st.plotly_chart(plot_time_series(history["ph"], history["temp"], history["state"]), use_container_width=True)
    with col2:
        st.plotly_chart(plot_radar(features), use_container_width=True)

    # Charts row 2: FFT + Spectrogram + Waveform
    waveform = shared_state.get_waveform()
    spectrogram = shared_state.get_spectrogram()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.plotly_chart(plot_fft(waveform, SAMPLE_RATE), use_container_width=True)
    with col2:
        st.plotly_chart(plot_spectrogram(spectrogram), use_container_width=True)
    with col3:
        st.plotly_chart(plot_waveform(waveform), use_container_width=True)

    # Auto-refresh
    time.sleep(DASHBOARD_REFRESH_MS / 1000.0)
    st.rerun()


if __name__ == "__main__":
    main()
