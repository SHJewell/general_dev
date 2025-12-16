import sys
import struct
from dataclasses import dataclass


SUBSYSTEM_NUMBER = {0: "Sub-bottom",
                     20: "Lower frequency side-scan",
                     21: "Higher frequency side-scan",
                     100: "Raw serial data",
                     101: "Parsed serial data"}

@dataclass
class jsfMessage:
    msgType: int
    version: int
    sessionID: int
    msgLen: int
    data: bytes

    MESSAGE_TYPES = {80: "Sonar Data",
                     82: "Side-scan Sonar Message",
                     2020: "Pitch Roll Data",
                     2002: "NMEA String",
                     2060: "Pressure Sensor Reading",
                     2080: "Doppler Velocity Log",
                     2090: "Situational Message",
                     426: "File Timestamp Message",
                     428: "File Padding Message",
                     182: "System Event Message",
                     2100: "Cable Counter Data Message",
                     2111: "Container Timestamp Message",
                     9001: "Discover-2 General Prefix Message",
                     9002: "Discover-2 Situation Data",
                     9003: "Discover-2 Acoustic Prefix Message"}

    def __init__(self, packet, verbose=False):
        header = struct.unpack('<HBBHBBBBHL', packet[:16])

        self.msgType = header[3]
        self.version = header[1]
        self.sessionID = header[2]
        self.msgLen = header[9]
        self.data = packet[16:16 + self.msgLen]

        if verbose:
            # Print header info
            print(f"Message Type: {self.MESSAGE_TYPES.get(self.msgType, f'Unknown: {header[3]}')}")
            print(f"Version: {self.version}")
            print(f"Session ID: {self.sessionID}")
            print(f"Data Length: {self.msgLen} bytes")
            print(f"Data (first 20 bytes): {self.data[16:36]}")
            print("-" * 40)

        return

@dataclass
class decodeSonarData(jsfMessage):
    """
    Message Type 80: Sonar Data Message
    """

    ping_t: int
    start_depth: int
    ping_num: int
    MSBs: int
    ID: int
    valid_flag: int
    data_format: int
    dist_to_antenna_aft: int
    dist_to_antenna_starboard: int

    # navigation data
    km_of_pipe: float
    X_in_mm: int
    Y_in_mm: int
    coord_units: int

    # pulse info
    annotation_str: str
    num_data_samples: int
    sampling_interval: int
    gain: int
    transmit_level: int # decaHz
    starting_freq: int  # decaHz
    ending_freq: int    # decaHz
    sweep_length: int   # ms
    pressure: int       # mPSI
    depth: int          # mm
    fs: int             # Hz, mod 65536
    pulse_ID: int

    # cpu time
    cpu_year: int
    cpu_day: int
    cpu_hour: int
    cpu_min: int
    cpu_sec: int
    time_basis: int

    # weighting factors
    weighting_factor: int
    N_pulses: int

    # orientation
    heading: int        # cdeg
    pitch: int          # cdeg
    roll: int           # cdeg
    temperature: int    # 0.1 deg C

    # misc1
    trigger_source: int
    mark_num: int

    # NMEA data
    NMEA_hour: int
    NMEA_min: int
    NMEA_sec: int
    NMEA_course: int
    NMEA_speed: int
    NMEA_day: int
    NMEA_year: int

    # misc2
    ms_since_midnight: int
    max_ADC_samples: int
    sonar_sw_version: int
    spherical_corr: int
    packet_num: int
    ADC_decimation: int         # x100
    decimation_after_fft: int
    water_temp: int             # 0.1 deg C
    layback: float              # m
    cable_out: int              # m


    def __init__(self, packet):
        super().__init__(packet)
        header = struct.unpack('<lLLhhHhhhhhhHHhhhhh', packet[:44])

        self.ping_t = header[0]
        self.start_depth = header[1]
        self.ping_num = header[2]
        self.MSBs = header[4]
        self.ID = header[6]
        self.valid_flag = header[7]
        self.data_format = header[9]
        self.dist_to_antenna_aft = header[10]
        self.dist_to_antenna_starboard = header[11]

        nav_data = struct.unpack('<fhhhhhhhhhhhhhhhhhhlh', packet[44:90])

        self.km_of_pipe = nav_data[0]
        self.X_in_mm = nav_data[1]
        self.Y_in_mm = nav_data[2]
        self.coord_units = nav_data[3]

        pulse_info = struct.unpack('<ccccccccccccccccccccccccHLHhhHHHhhHHLlll', packet[90:156])

        self.annotation_str = pulse_info[0:20]
        self.num_data_samples = pulse_info[21]
        self.sampling_interval = pulse_info[22]
        self.gain = pulse_info[23]
        self.transmit_level = pulse_info[24]     # decaHz
        self.starting_freq = pulse_info[26]      # decaHz
        self.ending_freq = pulse_info[27]        # decaHz
        self.sweep_length = pulse_info[28]       # ms
        self.pressure = pulse_info[29]           # mPSI
        self.depth = pulse_info[30]              # mm
        self.fs = pulse_info[31]                 # Hz, mod 65536
        self.pulse_ID = pulse_info[32]

        cpu_time = struct.unpack('<hhhhhh', packet[156:168])

        self.cpu_year = cpu_time[0]
        self.cpu_day = cpu_time[0]
        self.cpu_hour = cpu_time[0]
        self.cpu_min = cpu_time[0]
        self.cpu_sec = cpu_time[0]
        self.time_basis = cpu_time[0]

        weighting_factors = struct.unpack('<hh', packet[168:172])

        self.weighting_factor = weighting_factors[0]
        self.N_pulses = weighting_factors[1]

        orientation = struct.unpack('<Hhhh', packet[172:180])

        self.heading = orientation[0]        # cdeg
        self.pitch = orientation[1]          # cdeg
        self.roll = orientation[2]           # cdeg
        self.temperature = orientation[3]    # 0.1 deg C

        misc = struct.unpack('<hhH', packet[180:186])

        self.trigger_source = misc[0]
        self.mark_num = misc[1]

        NMEA_data = struct.unpack('<hhhhhhh', packet[186:200])

        self.NMEA_hour = NMEA_data[0]
        self.NMEA_min = NMEA_data[1]
        self.NMEA_sec = NMEA_data[2]
        self.NMEA_course = NMEA_data[3]
        self.NMEA_speed = NMEA_data[4]
        self.NMEA_day = NMEA_data[5]
        self.NMEA_year = NMEA_data[6]

        other_misc = struct.unpack('<LHhhcccccclHhhhflHH', packet[200:240])

        self.ms_since_midnight = other_misc[0]
        self.max_ADC_samples = other_misc[1]
        self.sonar_sw_version = other_misc[4]
        self.spherical_corr = other_misc[5]
        self.packet_num = other_misc[6]
        self.ADC_decimation = other_misc[7]  # x100
        self.decimation_after_fft = other_misc[8]
        self.water_temp = other_misc[9]  # 0.1 deg C
        self.layback = other_misc[10] # m
        self.cable_out = other_misc[12]  # m

@dataclass
class decodeSidecanSonarMsg(jsfMessage):

    subsystem: int
    channel_num: int
    ping_num: int
    packet_num: int
    trigger_source: int
    samples_in_packet: int
    sample_interval: int    # ns
    starting_depth: int     # window offset, in samples
    weighting_factor: int   # 2^-N Volts
    ADC_gain_factor: int
    max_ADC_value: int
    range_settign: int      # 10 * m
    pulse_ID: int
    mark_num: int
    data_format: int
    num_pulses: int

    # cpu time
    cpu_ms_today: int
    cpu_year: int
    cpu_day: int
    cpu_hour: int
    cpu_min: int
    cpu_sec: int

    # auxillary sensor info
    compass_heading: int    # deg * 60
    pitch_scale: int        # 180 / 32768 to get degrees, + = bow up
    roll_scale: int         # 180 / 32768 to get degrees, + = port up
    heave: int              # cm
    yaw: int                # degree minutes
    pressure: int           # 0.001 PSI
    temperature: int        # 0.1 deg C
    water_temp: int         # 0.1 deg C
    altitude: int           # mm

    trace_data: bytes

    def __init__(self, packet):
        super().__init__(packet)
        header = struct.unpack('<HHLHHLLLhhhhhhhBB', packet[:40])

        self.subsystem = header[0]
        self.channel_num = header[1]
        self.ping_num = header[2]
        self.packet_num = header[3]
        self.trigger_source = header[4]
        self.samples_in_packet = header[5]
        self.sample_interval = header[6]    # ns
        self.starting_depth = header[7]     # window offset, in samples
        self.weighting_factor = header[8]
        self.ADC_gain_factor = header[9]
        self.max_ADC_value = header[10]
        self.range_settign = header[11]      # 10 * m
        self.pulse_ID = header[12]
        self.mark_num = header[13]
        self.data_format = header[14]
        self.num_pulses = header[15]

        cpu_time = struct.unpack('<LhHHHH', packet[40:54])

        self.cpu_ms_today = cpu_time[0]
        self.cpu_year = cpu_time[1]
        self.cpu_day = cpu_time[2]
        self.cpu_hour = cpu_time[3]
        self.cpu_min = cpu_time[4]
        self.cpu_sec = cpu_time[5]

        aux_sensor = struct.unpack('<HhhhhhLhhl', packet[54:76])

        self.compass_heading = aux_sensor[0]    # deg * 60
        self.pitch_scale = aux_sensor[1]        # 180 / 32768 to get degrees, + = bow up
        self.roll_scale = aux_sensor[2]         # 180 / 32768 to get degrees, + = port up
        self.heave = aux_sensor[3]              # cm
        self.yaw = aux_sensor[4]                # degree minutes
        self.pressure = aux_sensor[5]           # 0.001 PSI
        self.temperature = aux_sensor[6]        # 0.1 deg C
        self.water_temp = aux_sensor[7]         # 0.1 deg C
        self.altitude = aux_sensor[8]           # mm

        self.trace_data = packet[80:]

@dataclass
class decodePitchRollData(jsfMessage):

    time: int   # seconds since 1 Jan 1970
    ms_in_record: int
    acceleration_x: int   # Multiply by (20 * 1.5) / (32768) to get gs
    acceleration_y: int   # Multiply by (20 * 1.5) / (32768) to get gs
    acceleration_z: int   # Multiply by (20 * 1.5) / (32768) to get gs
    gyro_rate_x: int    # Multiply by (500 * 1.5) / (32768) to get Degrees/Sec
    gyro_rate_y: int    # Multiply by (500 * 1.5) / (32768) to get Degrees/Sec
    gyro_rate_z: int    # Multiply by (500 * 1.5) / (32768) to get Degrees/Sec
    pitch_multiplier: int   # (180.0 / 32768.0) to get Degrees Bow up is positive
    roll_multiplier: int    # (180.0 / 32768.0) to get Degrees Port up is positive
    temperature: int       # 0.1 deg C
    divice_info: int
    heave_est: int    # mm
    heading: int      # cdeg
    data_valid_flags: int

    def __init__(self, packet):
        super().__init__(packet)
        """
        TODO:
            Use data_valid_flags to determine which fields are available
        """

        pitch_roll = struct.unpack('<lLLhhhhhhhhhHhHll', packet[:44])

        self.time = pitch_roll[0]   # seconds since 1 Jan 1970
        self.ms_in_record = pitch_roll[1]
        self.acceleration_x = pitch_roll[2]   # Multiply by (20 * 1.5) / (32768) to get gs
        self.acceleration_y = pitch_roll[3]   # Multiply by (20 * 1.5) / (32768) to get gs
        self.acceleration_z = pitch_roll[4]   # Multiply by (20 * 1.5) / (32768) to get gs
        self.gyro_rate_x = pitch_roll[5]    # Multiply by (500 * 1.5) / (32768) to get Degrees/Sec
        self.gyro_rate_y = pitch_roll[6]    # Multiply by (500 * 1.5) / (32768) to get Degrees/Sec
        self.gyro_rate_z = pitch_roll[7]    # Multiply by (500 * 1.5) / (32768) to get Degrees/Sec
        self.pitch_multiplier = pitch_roll[8]   # (180.0 / 32768.0) to get Degrees Bow up is positive
        self.roll_multiplier = pitch_roll[9]    # (180.0 / 32768.0) to get Degrees Port up is positive
        self.temperature = pitch_roll[10]       # 0.1 deg C
        self.divice_info = pitch_roll[11]
        self.heave_est = pitch_roll[12]    # mm
        self.heading = pitch_roll[13]      # cdeg
        self.data_valid_flags = pitch_roll[14]

@dataclass
class decodeNMEAString(jsfMessage):
    time: int           # unix time
    ms_in_record: int
    source: int
    NMEAstring: str

    def __init__(self, packet):
        super().__init__(packet)
        NMEAheader = struct.unpack("<llcccc", packet[:12])

        self.time = NMEAheader[0]           # unix time
        self.ms_in_record = NMEAheader[1]
        self.source = NMEAheader[2]

        self.NMEAstring = packet[12:].decode('utf-8', errors='ignore').strip("\n\x00")

@dataclass
class decodePressureSensorReading(jsfMessage):
    """UNTESTED"""

    time: int   # unix time
    ms_in_record: int
    pressure: int   # 0.001 PSI
    temperature: int    # 0.1 deg C
    salinity: int       # ppm
    data_valid_flags: int
    conductivity: int  # microSiemens/cm
    sound_velocity: int   # 0.1 m/s

    def __init__(self, packet):
        super().__init__(packet)
        """
        TODO:
            Use data_valid_flags to determine which fields are available
        """
        pressure_data = struct.unpack('<llllllll', packet[:32])

        self.time = pressure_data[0]   # unix time
        self.ms_in_record = pressure_data[1]
        self.pressure = pressure_data[2]
        self.temperature = pressure_data[3]
        self.salinity = pressure_data[4]
        self.data_valid_flags = pressure_data[5]
        self.conductivity = pressure_data[6]
        self.sound_velocity = pressure_data[7]

@dataclass
class decodeDopperVeloctyLog(jsfMessage):
    """UNTESTED"""

    time: int   # in seconds since "start of time", see Edgetech_jsf_rev1.13.pdf
    ms_in_record: int
    data_valid_flags: int
    dist_to_bottom: int   # cm, 4 beams
    x_velocity_to_bottom: int   # mm/s
    y_velocity_forward: int   # mm/s
    z_velocity_up: int   # mm/s
    x_velocity_wrp_water: int   # mm/s
    y_velocity: int   # mm/s
    z_vertical_velocity: int   # mm/s
    depth_from_depth_sensor: int   # mm
    pitch: int   # -180 to +180 degree (units = 0.01 of a degree) + Bow up
    roll: int    # -180 to +180 degree (units = 0.01 of a degree) + Port up
    heading: int  # 0 to 360 degree (units = 0.01 of a degree)
    salinity: int   # part per thousand
    temperature: int    # 0.01 deg C
    sound_velocity: int   # m/s

    def __init__(self, packet):
        super().__init__(packet)
        dvl_data = struct.unpack('<llllllllhhhhhhhhHhhHHhh', packet[:58])

        self.time = dvl_data[0]
        self.ms_in_record = dvl_data[1]
        self.data_valid_flags = dvl_data[3]
        self.dist_to_bottom = dvl_data[4]   # cm, 4 beams
        self.x_velocity_to_bottom = dvl_data[5]   # mm/s
        self.y_velocity_forward = dvl_data[6]   # mm/s
        self.z_velocity_up = dvl_data[7]   # mm/s
        self.x_velocity_wrp_water = dvl_data[8]   # mm/s
        self.y_velocity = dvl_data[9]   # mm/s
        self.z_vertical_velocity = dvl_data[10]   # mm/s
        self.depth_from_depth_sensor = dvl_data[11]   # mm
        self.pitch = dvl_data[12]   # -180 to +180 degree (units = 0.01 of a degree) + Bow up
        self.roll = dvl_data[13]    # -180 to +180 degree (units = 0.01 of a degree) + Port up
        self.heading = dvl_data[14]  # 0 to 360 degree (units = 0.01 of a degree)
        self.salinity = dvl_data[15]   # part per thousand
        self.temperature = dvl_data[16]    # 0.01 deg C
        self.sound_velocity = dvl_data[17]   # m/s

@dataclass
class decodeSitMsg(jsfMessage):
    """UNTESTED"""

    time: int   # seconds since 1 Jan 1970
    ms_in_record: int
    data_valid_flags: int
    timestamp: int      # microseconds
    lat: float      # degrees, + is North
    lon: float      # degrees, + is East
    depth: float    # meters
    heading: float  # degrees
    pitch: float    # degrees
    roll: float     # degrees
    x_foward: float   # forward, relative position in meters, surge
    y_starboard: float  # starboard, relative position in meters, sway
    z_down: float   # down, relative position in meters, heave
    x_velocity: float  # m/s
    y_velocity: float  # m/s
    z_velocity: float  # m/s
    north_velocity: float  # m/s
    east_velocity: float   # m/s
    down_velocity: float  # m/s
    x_angular_rate: float  # deg/s, port up is positive
    y_angular_rate: float  # deg/s, bow up is positive
    z_angular_rate: float  # deg/s, starboard is positive
    x_acceleration: float  # m/s^2
    y_acceleration: float  # m/s^2
    z_acceleration: float  # m/s^2
    lat_std_dev: float  # meters
    lon_std_dev: float  # meters
    depth_std_dev: float  # meters
    heading_std_dev: float  # degrees
    pitch_std_dev: float  # degrees
    roll_std_dev: float  # degrees

    def __init__(self, packet):
        super().__init__(packet)
        sit_msg = struct.unpack('<lllLcQddddddddddddddddddddddddddd', packet[:244])

        self.time = sit_msg[0]  # seconds since 1 Jan 1970
        self.ms_in_record = sit_msg[1]
        self.data_valid_flags = sit_msg[3]
        self.timestamp = sit_msg[5]  # microseconds
        self.lat = sit_msg[6]  # degrees, + is North
        self.lon = sit_msg[7]  # degrees, + is East
        self.depth = sit_msg[8]  # meters
        self.heading = sit_msg[9]  # degrees
        self.pitch = sit_msg[10] # degrees
        self.roll = sit_msg[11]  # degrees
        self.x_foward = sit_msg[12]  # forward, relative position in meters, surge
        self.y_starboard = sit_msg[13]  # starboard, relative position in meters, sway
        self.z_down = sit_msg[14]  # down, relative position in meters, heave
        self.x_velocity = sit_msg[15]  # m/s
        self.y_velocity = sit_msg[16]  # m/s
        self.z_velocity = sit_msg[17]  # m/s
        self.north_velocity = sit_msg[18]  # m/s
        self.east_velocity = sit_msg[19]  # m/s
        self.down_velocity = sit_msg[20]  # m/s
        self.x_angular_rate = sit_msg[21]  # deg/s, port up is positive
        self.y_angular_rate = sit_msg[22]  # deg/s, bow up is positive
        self.z_angular_rate = sit_msg[23]  # deg/s, starboard is positive
        self.x_acceleration = sit_msg[24]  # m/s^2
        self.y_acceleration = sit_msg[25]  # m/s^2
        self.z_acceleration = sit_msg[26]  # m/s^2
        self.lat_std_dev = sit_msg[27]  # meters
        self.lon_std_dev = sit_msg[28]  # meters
        self.depth_std_dev = sit_msg[29]  # meters
        self.heading_std_dev = sit_msg[30]  # degrees
        self.pitch_std_dev = sit_msg[31]  # degrees
        self.roll_std_dev = sit_msg[32]  # degrees

@dataclass
class decodeFileTimestamp(jsfMessage):
    """UNTESTED"""

    time: int
    ms: int     # in current second

    def __init__(self, packet):
        super().__init__(packet)
        timestamp = struct.unpack('<ll', packet[:8])

        self.time = timestamp[0]
        self.ms = timestamp[1]     # in current second

@dataclass
class decodeSysInfoMsg(jsfMessage):

    sys_type: str
    sys_sw_version: int
    serial_num: int

    def __init__(self, packet):
        super().__init__(packet)
        sys_info = struct.unpack('<lll', packet[:12])

        SYSTEM_TYPE = {1: "2xxx Series, Combined Sub-Bottom / Side Scan with SIB Electronics",
                       2: "2xxx Series, Combined Sub-Bottom / Side Scan with FSIC Electronics",
                       4: "4300-MPX (Multi-Ping) JSF FILE FORMAT Rev 1.13 Doc: 990-0000048-1000 21",
                       5: "3200-XS, Sub-Bottom Profiler with AIC Electronics",
                       6: "4400-SAS, 12-Channel Side Scan",
                       7: "3200-XS, Sub Bottom Profiler with SIB Electronics",
                       11: "4200 Limited Multipulse Dual Frequency Side Scan",
                       14: "3100-P, Sub Bottom Profiler",
                       16: "2xxx Series, Dual Side Scan with SIB Electronics",
                       17: "4200 Multipulse Dual Frequency Side Scan",
                       18: "4700 Dynamic Focus",
                       19: "4200 Dual Frequency Side Scan",
                       20: "4200 Dual Frequency non Simultaneous Side Scan",
                       21: "2200-MP Combined Sub-Bottom / Dual Frequency Multipulse Side Scan",
                       23: "4600 Multipulse Bathymetric System",
                       24: "4200 Single Frequency Dynamically Focused Side Scan",
                       25: "4125 Dual Frequency Side Scan",
                       27: "4600 Monopulse Bathymetric System",
                       128: "4100, 272 /560A Side Scan"}

        self.sys_type = SYSTEM_TYPE.get(sys_info[0], f"Unknown: {sys_info[0]}")
        self.sys_sw_version = sys_info[1]
        self.serial_num = sys_info[2]

@dataclass
class decodeCableCounterDataMsg(jsfMessage):
    """UNTESTED"""

    time: int   # seconds since 1 Jan 1970
    ms_in_record: int
    length: float   # meters
    speed: float    # meters / minute
    length_flag: bool
    speed_flag: bool
    counter_error: bool
    tension_flag: bool

    def __init__(self, packet):
        super().__init__(packet)
        cable_counter_data = struct.unpack('<lllffhhhhf', packet[:28])

        self.time = cable_counter_data[0]   # seconds since 1 Jan 1970
        self.ms_in_record = cable_counter_data[1]
        self.length = cable_counter_data[3]   # meters
        self.speed = cable_counter_data[4]    # meters / minute
        self.length_flag = cable_counter_data[5] != 0
        self.speed_flag = cable_counter_data[6] != 0
        self.counter_error = cable_counter_data[7] != 0
        self.tension_flag = cable_counter_data[8] != 0

@dataclass
class decodeContainerTimestampMsg(jsfMessage):
    """UNTESTED"""
    
    time: int   # seconds since 1 Jan 1970
    ms_in_record: int

    def __init__(self, packet):
        super().__init__(packet)
        container_timestamp = struct.unpack('<ll', packet[:8])
        
        self.time = container_timestamp[0]   # seconds since 1 Jan 1970
        self.ms_in_record = container_timestamp[1]

@dataclass
class decodeDisc2GeneralPrefixMsg(jsfMessage):
    """UNTESTED"""

    timestamp: int
    data_source_serial_num: int
    message_version: int
    device: int

    def __init__(self, packet):
        super().__init__(packet)

        disc2_prefix = struct.unpack('<qlhL', packet[:16])

        self.timestamp = disc2_prefix[0]
        self.data_source_serial_num = disc2_prefix[1]
        self.message_version = disc2_prefix[2]
        self.device = disc2_prefix[3]

@dataclass
class decodeDisc2SitDataMsg(jsfMessage):
    """UNTESTED"""

    GUID: bytes
    sit_general_prefix: decodeDisc2GeneralPrefixMsg
    sensor_platform: int
    platform_enum: int
    IDs_in_list: int
    sit_data_obj: bytes


    def __init__(self, packet):
        super().__init__(packet)

        self.sit_general_prefix = decodeDisc2GeneralPrefixMsg(packet[:16])

        self.GUID = packet[16:32]
        sit_ID_header = struct.unpack("<HHL", packet[16:24])

        self.sensor_platform = sit_ID_header[0]
        self.platform_enum = sit_ID_header[1]
        self.IDs_in_list = sit_ID_header[2]

        self.sit_data_obj = packet[24:]

@dataclass
class decodeDisc2AcousticPrefixMsg(jsfMessage):
    """UNTESTED"""

    general_prefix: decodeDisc2GeneralPrefixMsg
    ping_num: int
    mixer_freq: float # kHz
    mixer_phase: float #  Range is 0.0 to 1.0 where 0.0 indicates a phase of 0 and 0.5 indicates a phase of 180 degrees.
    fs: float        # kHz
    sample_offset: int
    pulse_index: int
    data_source: int
    MPX_pulse_num: int
    packet_num: int
    disc2_data_obj: bytes

    def __init__(self, packet):
        super().__init__(packet)

        disc2_acoustic_prefix = decodeDisc2GeneralPrefixMsg(packet[:16])
        acoustic_data = struct.unpack('<LfffLHHccccL', packet[16:48])

        self.ping_num = acoustic_data[0]
        self.mixer_freq = acoustic_data[1]
        self.mixer_phase = acoustic_data[2]
        self.fs = acoustic_data[3]
        self.sample_offset = acoustic_data[4]
        self.pulse_index = acoustic_data[6]
        self.data_source = acoustic_data[8]
        self.MPX_pulse_num = acoustic_data[9]
        self.packet_num = acoustic_data[10]

        self.disc2_data_obj = decodeDisc2SitDataMsg(packet[48:])

def unknownMsg(packet):
    print(f"Unknown message type: {packet[:16]}")
    pass

@dataclass
class jsfFile:
    file_path: str
    message = []

    header: jsfMessage

    DECODE_SWITCH = {80: decodeSonarData,
                     82: decodeSidecanSonarMsg,
                     426: decodeFileTimestamp,
                     182: decodeSysInfoMsg,
                     2020: decodePitchRollData,
                     2002: decodeNMEAString,
                     2060: decodePressureSensorReading,
                     2080: decodeDopperVeloctyLog,
                     2090: decodeSitMsg,
                     2100: decodeCableCounterDataMsg,
                     2111: decodeContainerTimestampMsg,
                     9001: decodeDisc2GeneralPrefixMsg,
                     9002: decodeDisc2SitDataMsg
                     }

    def __init__(self, file_path, verbose=False):
        self.file_path = file_path

        with open(self.file_path, 'rb') as f:
            while True:
                # Read the 16-byte header
                header_bytes = f.read(16)
                if len(header_bytes) < 16:
                    break  # End of file

                # Unpack the header
                try:
                    self.header = jsfMessage(header_bytes, verbose=verbose)
                except struct.error:
                    print("Error unpacking header.")
                    break

                data = f.read(self.header.msgLen)
                decoded_msg = self.DECODE_SWITCH.get(self.header.msgType,unknownMsg)(header_bytes + data)
                if decoded_msg:
                    self.message.append(decoded_msg)

    def getMsgByType(self, msg_type):
        return [msg for msg in self.message if msg.msgType == msg_type]

# def read_jsf_file(file_path):
#     """
#     Reads and decodes a JSF file.
#
#     Args:
#         file_path (str): Path to the .jsf file.
#     """
#     with open(file_path, 'rb') as f:
#         while True:
#             # Read the 16-byte header
#             header = f.read(16)
#             if len(header) < 16:
#                 break  # End of file
#
#             # Unpack the header
#             try:
#                 marker, version, session_id, msg_type, cmd_typ, sub_num, channel, seq, reserved, data_len = struct.unpack(
#                     '<HBBHBBBBHL', header)
#             except struct.error:
#                 print("Error unpacking header.")
#                 break
#
#             # Validate start marker
#             if marker != 0x1601:
#                 print(f"Invalid start marker: {marker}")
#                 break
#
#             # Read the message data
#             data = f.read(data_len)
#             if len(data) != data_len:
#                 print("Error reading message data.")
#                 break
#
#             # Print header info
#             print(f"Message Type: {MESSAGE_TYPES.get(msg_type, f'Unknown: {msg_type}')}")
#             print(f"Subsystem: {SUBSYSTEM_NUMBER.get(sub_num, f'Unknown: {sub_num}')}")
#             print(f"Version: {version}")
#             print(f"Session ID: {session_id}")
#             print(f"Data Length: {data_len} bytes")
#             print(f"Data (first 20 bytes): {data[:20]}")
#             print("-" * 40)
#
#             decode_switch.get(msg_type, lambda x: None)(data)

if __name__ == "__main__":

    jsf_file_path = r"E:\JGS\Willowstick\Processing\ElectroBras Seismic\20250907104924.001.jsf"
    # read_jsf_file(jsf_file_path)
    jsf1 = jsfFile(jsf_file_path, verbose=True)

    jsf1