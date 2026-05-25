"""
charts.py

Plotly chart builders for the Streamlit dashboard.

Provides:
  - FFT spectrum display (frequency domain)
  - Spectrogram (time-frequency waterfall)
  - Radar chart (multi-dimensional feature visualization)
  - Time-series charts for pH, temperature, state
"""

import plotly.graph_objects as go
import numpy as np


def plot_fft(audio_chunk: np.ndarray, sample_rate: int = 44100):
    """Compute and plot FFT magnitude spectrum."""
    fft = np.abs(np.fft.rfft(audio_chunk))
    freqs = np.fft.rfftfreq(len(audio_chunk), 1/sample_rate)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=freqs[:500],  # Show first 500 Hz
        y=fft[:500],
        mode='lines',
        line=dict(color='#00ff88', width=1),
        fill='tozeroy',
        fillcolor='rgba(0, 255, 136, 0.2)'
    ))
    fig.update_layout(
        title="FFT Spectrum",
        xaxis_title="Frequency (Hz)",
        yaxis_title="Magnitude",
        template="plotly_dark",
        height=200,
        margin=dict(l=0, r=0, t=30, b=0),
        showlegend=False
    )
    return fig


def plot_spectrogram(spec_buffer: np.ndarray):
    """Plot spectrogram from pre-computed buffer."""
    fig = go.Figure(data=go.Heatmap(
        z=spec_buffer,
        colorscale='Viridis',
        zmin=0, zmax=1,
        showscale=False
    ))
    fig.update_layout(
        title="Real-time Spectrogram",
        xaxis_title="Time (frames)",
        yaxis_title="Frequency bins",
        template="plotly_dark",
        height=200,
        margin=dict(l=0, r=0, t=30, b=0)
    )
    return fig


def plot_radar(features: dict):
    """Radar chart showing normalized feature dimensions."""
    categories = ['pH', 'Temp', 'Luminance', 'Volatility', 'Trend']
    values = [
        features.get('ph_norm', 0.5),
        features.get('temp_norm', 0.5),
        features.get('luminance', 0.5),
        features.get('volatility', 0.5),
        (features.get('trend', 0) + 1) / 2  # normalize -1..1 to 0..1
    ]
    values += values[:1]  # close the loop

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories + [categories[0]],
        fill='toself',
        line=dict(color='#ffd93d', width=2)
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        showlegend=False,
        template="plotly_dark",
        height=250,
        margin=dict(l=0, r=0, t=30, b=0)
    )
    return fig


def plot_time_series(ph_history, temp_history, state_history):
    """Combined time-series with dual y-axes."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=ph_history,
        mode='lines',
        name='pH',
        line=dict(color='#00ff88', width=2),
        yaxis='y'
    ))
    fig.add_trace(go.Scatter(
        y=temp_history,
        mode='lines',
        name='Temperature',
        line=dict(color='#ff6b6b', width=2),
        yaxis='y2'
    ))
    fig.update_layout(
        title="Sensor History",
        yaxis=dict(title="pH", color='#00ff88'),
        yaxis2=dict(title="Temperature (°C)", color='#ff6b6b', overlaying='y', side='right'),
        template="plotly_dark",
        height=250,
        margin=dict(l=0, r=0, t=30, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig


def plot_waveform(waveform: np.ndarray):
    """Simple waveform display."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=waveform,
        mode='lines',
        line=dict(color='cyan', width=1)
    ))
    fig.update_layout(
        title="Audio Waveform",
        template="plotly_dark",
        height=150,
        margin=dict(l=0, r=0, t=30, b=0),
        showlegend=False,
        yaxis_range=[-1, 1]
    )
    return fig
