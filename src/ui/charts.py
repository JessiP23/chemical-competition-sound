"""
Real-time chart visualization module.

Provides live plotting of sensor data, volatility, and audio features
using Plotly for interactive visualizations.
"""

import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from typing import List, Optional
from dataclasses import dataclass

from src.config.settings import DashboardConfig


@dataclass
class ChartData:
    """Container for chart data."""
    timestamps: List[float]
    ph_values: List[float]
    temp_values: List[float]
    volatility_values: List[float]
    state_history: List[str]


class ChartGenerator:
    """
    Generates real-time charts for the dashboard.
    
    Creates interactive Plotly charts for sensor data visualization
    with dark theme styling.
    """
    
    def __init__(self, config: Optional[DashboardConfig] = None):
        """
        Initialize chart generator.
        
        Args:
            config: Dashboard configuration
        """
        self.config = config or DashboardConfig()
        self.max_length = self.config.HISTORY_LENGTH
    
    def create_ph_chart(
        self,
        timestamps: List[float],
        ph_values: List[float]
    ) -> go.Figure:
        """
        Create pH time-series chart.
        
        Args:
            timestamps: List of timestamps
            ph_values: List of pH values
        
        Returns:
            Plotly figure
        """
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=ph_values,
            mode='lines',
            name='pH',
            line=dict(color=self.config.COLOR_PH, width=2),
            fill='tozeroy',
            fillcolor=f'rgba(0, 255, 136, 0.1)'
        ))
        
        # Add neutral pH reference line
        if timestamps:
            fig.add_hline(
                y=7.0,
                line_dash="dash",
                line_color="gray",
                annotation_text="Neutral pH"
            )
        
        fig.update_layout(
            title="pH Level",
            xaxis_title="Time",
            yaxis_title="pH",
            template="plotly_dark",
            height=300,
            margin=dict(l=0, r=0, t=30, b=0),
            showlegend=False
        )
        
        return fig
    
    def create_temperature_chart(
        self,
        timestamps: List[float],
        temp_values: List[float]
    ) -> go.Figure:
        """
        Create temperature time-series chart.
        
        Args:
            timestamps: List of timestamps
            temp_values: List of temperature values
        
        Returns:
            Plotly figure
        """
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=temp_values,
            mode='lines',
            name='Temperature',
            line=dict(color=self.config.COLOR_TEMP, width=2),
            fill='tozeroy',
            fillcolor=f'rgba(255, 107, 107, 0.1)'
        ))
        
        fig.update_layout(
            title="Temperature (°C)",
            xaxis_title="Time",
            yaxis_title="Temperature",
            template="plotly_dark",
            height=300,
            margin=dict(l=0, r=0, t=30, b=0),
            showlegend=False
        )
        
        return fig
    
    def create_volatility_chart(
        self,
        timestamps: List[float],
        volatility_values: List[float]
    ) -> go.Figure:
        """
        Create volatility chart.
        
        Args:
            timestamps: List of timestamps
            volatility_values: List of volatility values
        
        Returns:
            Plotly figure
        """
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=volatility_values,
            mode='lines',
            name='Volatility',
            line=dict(color=self.config.COLOR_VOLATILITY, width=2),
            fill='tozeroy',
            fillcolor=f'rgba(255, 217, 61, 0.1)'
        ))
        
        # Add threshold lines
        fig.add_hline(
            y=0.3,
            line_dash="dash",
            line_color="red",
            annotation_text="Critical"
        )
        
        fig.update_layout(
            title="Instability Score",
            xaxis_title="Time",
            yaxis_title="Volatility",
            template="plotly_dark",
            height=300,
            margin=dict(l=0, r=0, t=30, b=0),
            showlegend=False,
            yaxis_range=[0, 1]
        )
        
        return fig
    
    def create_combined_chart(
        self,
        timestamps: List[float],
        ph_values: List[float],
        temp_values: List[float]
    ) -> go.Figure:
        """
        Create combined pH and temperature chart.
        
        Args:
            timestamps: List of timestamps
            ph_values: List of pH values
            temp_values: List of temperature values
        
        Returns:
            Plotly figure with dual y-axes
        """
        fig = go.Figure()
        
        # pH on left y-axis
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=ph_values,
            mode='lines',
            name='pH',
            line=dict(color=self.config.COLOR_PH, width=2),
            yaxis='y'
        ))
        
        # Temperature on right y-axis
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=temp_values,
            mode='lines',
            name='Temperature',
            line=dict(color=self.config.COLOR_TEMP, width=2),
            yaxis='y2'
        ))
        
        fig.update_layout(
            title="Sensor Data",
            xaxis_title="Time",
            yaxis=dict(
                title="pH",
                titlefont=dict(color=self.config.COLOR_PH),
                tickfont=dict(color=self.config.COLOR_PH)
            ),
            yaxis2=dict(
                title="Temperature (°C)",
                titlefont=dict(color=self.config.COLOR_TEMP),
                tickfont=dict(color=self.config.COLOR_TEMP),
                anchor="x",
                overlaying="y",
                side="right"
            ),
            template="plotly_dark",
            height=350,
            margin=dict(l=0, r=0, t=30, b=0),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
    
    def create_state_timeline(
        self,
        timestamps: List[float],
        state_history: List[str]
    ) -> go.Figure:
        """
        Create state timeline visualization.
        
        Args:
            timestamps: List of timestamps
            state_history: List of state names
        
        Returns:
            Plotly figure
        """
        # Map states to numeric values for plotting
        state_values = []
        state_colors = []
        
        for state in state_history:
            if state == "stable":
                state_values.append(0)
                state_colors.append(self.config.COLOR_STABLE)
            elif state == "transitional":
                state_values.append(1)
                state_colors.append(self.config.COLOR_TRANSITIONAL)
            elif state == "critical":
                state_values.append(2)
                state_colors.append(self.config.COLOR_CRITICAL)
            elif state == "chaotic":
                state_values.append(3)
                state_colors.append(self.config.COLOR_CHAOTIC)
            else:
                state_values.append(0)
                state_colors.append("gray")
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=state_values,
            mode='lines+markers',
            name='State',
            line=dict(color='white', width=1),
            marker=dict(
                color=state_colors,
                size=8
            ),
            text=state_history,
            hovertemplate='%{text}<extra></extra>'
        ))
        
        fig.update_layout(
            title="Reaction State Timeline",
            xaxis_title="Time",
            yaxis=dict(
                tickvals=[0, 1, 2, 3],
                ticktext=['Stable', 'Transitional', 'Critical', 'Chaotic']
            ),
            template="plotly_dark",
            height=250,
            margin=dict(l=0, r=0, t=30, b=0),
            showlegend=False
        )
        
        return fig
    
    def create_audio_visualizer(
        self,
        audio_data: Optional[np.ndarray] = None
    ) -> go.Figure:
        """
        Create audio waveform visualizer.
        
        Args:
            audio_data: Audio samples (optional)
        
        Returns:
            Plotly figure
        """
        fig = go.Figure()
        
        if audio_data is not None and len(audio_data) > 0:
            # Downsample for visualization
            downsample = max(1, len(audio_data) // 1000)
            audio_downsampled = audio_data[::downsample]
            time_axis = np.arange(len(audio_downsampled))
            
            fig.add_trace(go.Scatter(
                x=time_axis,
                y=audio_downsampled,
                mode='lines',
                name='Waveform',
                line=dict(color='cyan', width=1)
            ))
        else:
            # Placeholder
            fig.add_trace(go.Scatter(
                x=[0, 100],
                y=[0, 0],
                mode='lines',
                name='Waveform',
                line=dict(color='cyan', width=1)
            ))
        
        fig.update_layout(
            title="Audio Waveform",
            xaxis_title="Sample",
            yaxis_title="Amplitude",
            template="plotly_dark",
            height=200,
            margin=dict(l=0, r=0, t=30, b=0),
            showlegend=False,
            yaxis_range=[-1, 1]
        )
        
        return fig
    
    def create_gauge_chart(
        self,
        value: float,
        title: str,
        min_val: float = 0.0,
        max_val: float = 1.0,
        color: str = "#00ff88"
    ) -> go.Figure:
        """
        Create gauge chart for single value display.
        
        Args:
            value: Current value
            title: Chart title
            min_val: Minimum value
            max_val: Maximum value
            color: Gauge color
        
        Returns:
            Plotly figure
        """
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=value,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': title},
            gauge={
                'axis': {'range': [min_val, max_val]},
                'bar': {'color': color},
                'steps': [
                    {'range': [min_val, max_val], 'color': "lightgray"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': max_val * 0.9
                }
            }
        ))
        
        fig.update_layout(
            template="plotly_dark",
            height=200,
            margin=dict(l=0, r=0, t=30, b=0)
        )
        
        return fig
