"""Versioned serial protocol shared by physical and simulated devices."""
import math
import time

BAUD_RATE = 115200


def parse_sample(line):
    # CHEM1,sequence,millis,pH,tempC,rawADC,status
    fields = line.strip().split(',')
    if len(fields) != 7 or fields[0] != 'CHEM1':
        raise ValueError('Expected CHEM1 sensor record')
    _, seq, ms, ph, temp, adc, status = fields
    sample = dict(sequence=int(seq), timestamp=int(ms)/1000,
                  ph=float(ph), temperature=float(temp), raw_adc=int(adc),
                  valid=status == 'OK', error='' if status == 'OK' else status)
    if sample['sequence'] < 0 or sample['timestamp'] < 0:
        raise ValueError('Invalid sample clock or sequence')
    if not all(math.isfinite(sample[k]) for k in ('ph','temperature')):
        raise ValueError('Non-finite sensor reading')
    if not 0 <= sample['raw_adc'] <= 1023:
        raise ValueError('Invalid ADC reading')
    if not (0 <= sample['ph'] <= 14 and 5 <= sample['temperature'] <= 60):
        sample.update(valid=False, error='Reading outside supported probe range')
    return sample


def list_available_ports():
    from serial.tools.list_ports import comports
    return [p.device for p in comports()]


class SerialReader:
    def __init__(self, port):
        import serial
        self.connection = serial.Serial(port, BAUD_RATE, timeout=0.25)
        self.buffer = bytearray()
        self.last_sequence = None
        self.last_timestamp = None
        self.last_valid = time.monotonic()

    def read(self):
        chunk = self.connection.read_until(b'\n', size=256)
        self.buffer.extend(chunk)
        if len(self.buffer) > 512:
            self.buffer.clear()
            raise ValueError('Oversized serial record')
        if not self.buffer.endswith(b'\n'):
            if time.monotonic() - self.last_valid > 3:
                raise TimeoutError('No fresh sensor data for 3 seconds')
            return None
        line = self.buffer.decode('ascii').strip()
        self.buffer.clear()
        if line.startswith('#'):
            if time.monotonic() - self.last_valid > 3:
                raise TimeoutError('Device has not provided measurements')
            return None
        sample = parse_sample(line)
        if self.last_sequence is not None and (sample['sequence'] <= self.last_sequence or sample['timestamp'] <= self.last_timestamp):
            raise ValueError('Duplicate/out-of-order sample or device reset; reconnect')
        self.last_sequence = sample['sequence']
        self.last_timestamp = sample['timestamp']
        self.last_valid = time.monotonic()
        return sample

    def close(self):
        self.connection.close()
