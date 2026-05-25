"""
State panel visualization module.

Provides animated status indicators and state-specific
visual feedback for the dashboard.
"""

import streamlit as st
from typing import Optional
from dataclasses import dataclass

from src.core.classifier import ReactionState, get_state_color, get_state_description
from src.config.settings import DashboardConfig


@dataclass
class StateDisplay:
    """Container for state display data."""
    state: ReactionState
    confidence: float
    severity: float
    triggers: list[str]
    ph: float
    temperature: float
    instability: float


class StatePanelGenerator:
    """
    Generates state panels and status indicators.
    
    Creates visually appealing, animated status displays
    for the current reaction state.
    """
    
    def __init__(self, config: Optional[DashboardConfig] = None):
        """
        Initialize state panel generator.
        
        Args:
            config: Dashboard configuration
        """
        self.config = config or DashboardConfig()
    
    def render_main_status(self, state: ReactionState, confidence: float) -> None:
        """
        Render main status indicator.
        
        Args:
            state: Current reaction state
            confidence: Classification confidence
        """
        color = get_state_color(state)
        description = get_state_description(state)
        
        # Create status container
        st.markdown(
            f"""
            <div style="
                background-color: {color}20;
                border-left: 5px solid {color};
                padding: 20px;
                border-radius: 5px;
                margin-bottom: 20px;
            ">
                <h2 style="color: {color}; margin: 0;">
                    {state.value.upper()}
                </h2>
                <p style="color: white; margin: 5px 0 0 0;">
                    {description}
                </p>
                <p style="color: gray; margin: 5px 0 0 0; font-size: 0.9em;">
                    Confidence: {confidence:.1%}
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    def render_sensor_cards(
        self,
        ph: float,
        temperature: float,
        instability: float
    ) -> None:
        """
        Render sensor value cards.
        
        Args:
            ph: Current pH value
            temperature: Current temperature
            instability: Current instability score
        """
        col1, col2, col3 = st.columns(3)
        
        with col1:
            self._render_value_card(
                "pH Level",
                f"{ph:.2f}",
                self.config.COLOR_PH,
                "0.0 - 14.0"
            )
        
        with col2:
            self._render_value_card(
                "Temperature",
                f"{temperature:.1f}°C",
                self.config.COLOR_TEMP,
                "0.0 - 100.0°C"
            )
        
        with col3:
            self._render_value_card(
                "Instability",
                f"{instability:.2f}",
                self.config.COLOR_VOLATILITY,
                "0.0 - 1.0"
            )
    
    def _render_value_card(
        self,
        title: str,
        value: str,
        color: str,
        range_str: str
    ) -> None:
        """
        Render individual value card.
        
        Args:
            title: Card title
            value: Display value
            color: Accent color
            range_str: Value range string
        """
        st.markdown(
            f"""
            <div style="
                background-color: #1e1e1e;
                border: 1px solid {color};
                padding: 15px;
                border-radius: 10px;
                text-align: center;
            ">
                <h3 style="color: gray; margin: 0; font-size: 0.9em;">
                    {title}
                </h3>
                <p style="color: {color}; margin: 10px 0; font-size: 2em; font-weight: bold;">
                    {value}
                </p>
                <p style="color: gray; margin: 0; font-size: 0.8em;">
                    {range_str}
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    def render_triggers_panel(self, triggers: list[str]) -> None:
        """
        Render state trigger information.
        
        Args:
            triggers: List of trigger descriptions
        """
        if not triggers:
            st.info("No active triggers")
            return
        
        st.markdown("### Active Triggers")
        for trigger in triggers:
            st.markdown(
                f"""
                <div style="
                    background-color: #2d2d2d;
                    padding: 10px;
                    border-radius: 5px;
                    margin-bottom: 5px;
                    border-left: 3px solid #ffd93d;
                ">
                    <span style="color: white;">{trigger}</span>
                </div>
                """,
                unsafe_allow_html=True
            )
    
    def render_severity_meter(self, severity: float) -> None:
        """
        Render severity meter.
        
        Args:
            severity: Severity value (0-1)
        """
        # Determine color based on severity
        if severity < 0.33:
            color = self.config.COLOR_STABLE
        elif severity < 0.67:
            color = self.config.COLOR_TRANSITIONAL
        elif severity < 0.9:
            color = self.config.COLOR_CRITICAL
        else:
            color = self.config.COLOR_CHAOTIC
        
        st.markdown("### Severity Level")
        st.markdown(
            f"""
            <div style="
                background-color: #1e1e1e;
                border-radius: 10px;
                padding: 15px;
            ">
                <div style="
                    background-color: #2d2d2d;
                    border-radius: 5px;
                    height: 20px;
                    overflow: hidden;
                ">
                    <div style="
                        background-color: {color};
                        height: 100%;
                        width: {severity * 100}%;
                        transition: width 0.3s ease;
                    "></div>
                </div>
                <p style="color: white; text-align: center; margin-top: 10px;">
                    {severity:.1%}
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    def render_audio_status(
        self,
        pitch_center: float,
        rhythm_density: float,
        harmonic_consistency: float
    ) -> None:
        """
        Render audio parameter status.
        
        Args:
            pitch_center: Current pitch center (Hz)
            rhythm_density: Current rhythm density
            harmonic_consistency: Current harmonic consistency
        """
        st.markdown("### Audio Parameters")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Pitch", f"{pitch_center:.1f} Hz")
        
        with col2:
            st.metric("Rhythm", f"{rhythm_density:.1f} Hz")
        
        with col3:
            st.metric("Harmony", f"{harmonic_consistency:.2f}")
    
    def render_event_log(self, events: list[str]) -> None:
        """
        Render event log.
        
        Args:
            events: List of event messages
        """
        st.markdown("### Event Log")
        
        if not events:
            st.info("No events recorded")
            return
        
        # Show last 10 events
        recent_events = events[-10:]
        
        for event in recent_events:
            st.markdown(
                f"""
                <div style="
                    background-color: #1e1e1e;
                    padding: 8px;
                    border-radius: 3px;
                    margin-bottom: 3px;
                    font-size: 0.9em;
                    color: #ccc;
                ">
                    {event}
                </div>
                """,
                unsafe_allow_html=True
            )
    
    def render_system_info(
        self,
        mode: str,
        connected: bool,
        sample_rate: int
    ) -> None:
        """
        Render system information panel.
        
        Args:
            mode: Current system mode
            connected: Connection status
            sample_rate: Audio sample rate
        """
        st.markdown("### System Info")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_color = "#00ff88" if connected else "#ff6b6b"
            st.markdown(
                f"""
                <div style="text-align: center;">
                    <p style="color: gray; margin: 0;">Mode</p>
                    <p style="color: white; margin: 0; font-weight: bold;">{mode}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        with col2:
            st.markdown(
                f"""
                <div style="text-align: center;">
                    <p style="color: gray; margin: 0;">Status</p>
                    <p style="color: {status_color}; margin: 0; font-weight: bold;">
                        {'Connected' if connected else 'Disconnected'}
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        with col3:
            st.markdown(
                f"""
                <div style="text-align: center;">
                    <p style="color: gray; margin: 0;">Sample Rate</p>
                    <p style="color: white; margin: 0; font-weight: bold;">{sample_rate} Hz</p>
                </div>
                """,
                unsafe_allow_html=True
            )
