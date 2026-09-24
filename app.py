"""Run with: .venv/bin/streamlit run app.py"""
import streamlit as st
from src.core.runtime import Monitor
from src.core.classifier import DetectionProfile
from src.io.simulator import SCENARIOS
from src.io.serial_reader import list_available_ports

@st.cache_resource
def monitor():
    return Monitor()

def main():
    st.set_page_config(page_title='Chemical-to-Audio Monitor',page_icon='🧪',layout='wide')
    service = monitor()
    st.title('Chemical-to-Audio Monitor')
    st.caption('Continuous pH + temperature monitoring. Audio plays on the computer running this app.')
    with st.sidebar:
        st.header('Monitoring')
        mode = st.selectbox('Source',['simulation','hardware'],disabled=service.running)
        scenario, port, calibration_id = 'Full demo', '', ''
        if mode == 'simulation':
            scenario = st.selectbox('Simulated readings',SCENARIOS,disabled=service.running)
            st.info('SIMULATED data — full demo repeats every 60 seconds.')
        else:
            try: ports = list_available_ports()
            except Exception: ports = []
            st.caption('Detected ports: '+(', '.join(ports) or 'none'))
            port = st.text_input('Serial port',value=ports[0] if ports else '',disabled=service.running)
            calibration_id = st.text_input('Completed calibration record ID',disabled=service.running,
                                          help='Use the dated record from your two-point calibration and reference checks.')
        audio = st.checkbox('Enable sound',value=False,disabled=service.running)
        st.caption('Stop before changing settings. Controls are shared by browser sessions.')
        with st.expander('Demo detection limits'):
            st.warning('Demo values only. Set limits for your actual experiment before use.')
            low = st.number_input('Minimum pH',0.,14.,4.,disabled=service.running)
            high = st.number_input('Maximum pH',0.,14.,10.,disabled=service.running)
            hot = st.number_input('Maximum temperature °C',5.,60.,40.,disabled=service.running)
        if st.button('Start',disabled=service.running):
            try:
                service.start(mode,port,scenario,audio,DetectionProfile(low,high,hot),calibration_id)
                st.rerun()
            except Exception as exc: st.error(str(exc))
        if st.button('Stop',disabled=not service.running):
            service.stop()
            st.rerun()
    render_status(service)

@st.fragment(run_every=0.5)
def render_status(service):
    current, history = service.snapshot()
    st.subheader(current['state'].upper())
    st.write(current['reason'])
    st.caption('Source: '+current.get('mode','not running'))
    if current['state'] == 'fault': st.error('Measurement fault. Check wiring/port; use Stop then Start to reconnect.')
    if service.audio.error: st.error('Audio output: '+service.audio.error)
    sample = current.get('sample',{})
    valid = sample.get('valid',False)
    a,b = st.columns(2)
    a.metric('pH',f"{sample['ph']:.2f}" if valid else '—')
    b.metric('Temperature',f"{sample['temperature']:.2f} °C" if valid else '—')
    rows = [dict(seconds=r['sample']['timestamp'],pH=r['sample']['ph'],temperature=r['sample']['temperature'])
            for r in history if r.get('sample',{}).get('valid')]
    if rows:
        a,b = st.columns(2)
        a.line_chart(rows,x='seconds',y='pH')
        b.line_chart(rows,x='seconds',y='temperature')
    if history:
        st.dataframe([dict(time=r['received_at'],state=r['state'],reason=r['reason']) for r in history[-10:]],hide_index=True)
    if service.log_path:
        st.caption('Recording: '+str(service.log_path))
        if not service.running and service.log_path.exists():
            st.download_button('Download recording',service.log_path.read_bytes(),file_name=service.log_path.name)

if __name__ == '__main__': main()
