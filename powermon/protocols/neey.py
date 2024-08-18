""" protocols / neey.py """
import logging

import construct as cs

from powermon.commands.command import CommandType
from powermon.commands.command_definition import CommandDefinition
from powermon.commands.reading_definition import ReadingType, ResponseType
from powermon.commands.result import ResultType
from powermon.libs.errors import InvalidCRC, InvalidResponse, CommandDefinitionIncorrect
from powermon.ports.porttype import PortType
from powermon.protocols.abstractprotocol import AbstractProtocol

log = logging.getLogger("neey")

device_info_construct = cs.Struct(
    "start_flag" / cs.Bytes(2),
    "module_address" / cs.Bytes(1),
    "function" / cs.Bytes(1),
    "command" / cs.Int16ul,
    "length" / cs.Int16ul,
    "model" / cs.Bytes(16),
    "hw_version" / cs.Bytes(8),
    "sw_version" / cs.Bytes(8),
    "protocol_version" / cs.Bytes(8),
    "production_date" / cs.Bytes(8),
    "power_on_count" / cs.Int32ul,
    "total_runtime" / cs.Int32ul,
    "unused" / cs.Bytes(34),
    "crc" / cs.Bytes(1),
    "end_flag" / cs.Bytes(1),
)

operation_status = cs.Enum(cs.Int8sb, wrong_cell_count=1,
                                    AcqLine_Res_test=2,
                                    AcqLine_Res_exceed=3,
                                    Systest_Completed=4,
                                    Balancing=5,
                                    Balancing_finished=6,
                                    Low_voltage=7,
                                    System_Overtemp=8,
                                    Host_fails=9,
                                    Low_battery_voltage_balancing_stopped=10,
                                    Temperature_too_high_balancing_stopped=11,
                                    Self_test_completed=12,
)

cell_info_construct = cs.Struct(
    "start_flag" / cs.Bytes(2),
    "module_address" / cs.Bytes(1),
    "function" / cs.Bytes(1),
    "command" / cs.Int16ul,
    "length" / cs.Int16ul,
    "frame_counter" / cs.Byte,
    "cell_voltage_array" / cs.Array(24, cs.Float32l),
    "cell_resistance_array" / cs.Array(24, cs.Float32l),
    "total_voltage" / cs.Float32l,
    "average_cell_voltage" / cs.Float32l,
    "delta_cell_voltage" / cs.Float32l,
    "max_voltage_cell" / cs.Byte,
    "min_voltage_cell" / cs.Byte,
    "unknown" / cs.Bytes(1),
    "operation_status" / operation_status,
    "balancing_current" / cs.Float32l,
    "temperature_1" / cs.Float32l,
    "temperature_2" / cs.Float32l,
    "cell_detection_failed" / cs.Bytes(3),      # bitmask
    "cell_overvoltage_failed" / cs.Bytes(3),    # bitmask
    "cell_undervoltage_failed" / cs.Bytes(3),   # bitmask
    "cell_polarity_error" / cs.Bytes(3),        # bitmask
    "excessive_line_resistance" / cs.Bytes(3),  # bitmask
    "overheating" / cs.Bytes(1),  # bit 0 - sensor 1 warning, bit 1 - sensor 2
    "charging_fault" / cs.Bytes(1),  # 00: off, 01:on
    "discharge_fault" / cs.Bytes(1),  # 00: off, 01:on
    "read_write_error" / cs.Bytes(1),  # bit 0: read failed, bit 1 write failedd
    "unused" / cs.Bytes(6),
    "uptime" / cs.Float32l,
    "unused" / cs.Bytes(40),
    "crc" / cs.Bytes(1),
    "end_flag" / cs.Bytes(1),
)



COMMANDS = {
    "device_info": {
        "name": "device_info",
        "description": "balancer device information",
        "help": " -- display the balancer info",
        # "type": "DALY",
        "command_type": CommandType.SERIAL_READ_UNTIL_DONE,
        "command_code": "01",
        "result_type": ResultType.CONSTRUCT,
        "construct": device_info_construct,
        "construct_min_response": 100,
        "reading_definitions": [
            {"index": "start_flag", "description": "start flag", "reading_type": ReadingType.IGNORE, "response_type": ResponseType.HEX_CHARS},
            {"index": "module_address", "description": "module address", "reading_type": ReadingType.IGNORE, "response_type": ResponseType.HEX_CHAR},
            {"index": "function", "description": "function", "reading_type": ReadingType.IGNORE, "response_type": ResponseType.HEX_CHAR},
            {"index": "command", "description": "command", "reading_type": ReadingType.IGNORE},
            {"index": "length", "description": "length", "reading_type": ReadingType.IGNORE},
            {"index": "crc", "description": "crc", "reading_type": ReadingType.IGNORE, "response_type": ResponseType.HEX_CHAR},
            {"index": "end_flag", "description": "end flag", "reading_type": ReadingType.IGNORE, "response_type": ResponseType.HEX_CHAR},

            {"index": "model", "description": "model", "reading_type": ReadingType.MESSAGE, "response_type": ResponseType.BYTES_STRIP_NULLS},
            {"index": "hw_version", "description": "hw_version", "reading_type": ReadingType.MESSAGE, "response_type": ResponseType.BYTES_STRIP_NULLS},
            {"index": "sw_version", "description": "sw_version", "reading_type": ReadingType.MESSAGE, "response_type": ResponseType.BYTES_STRIP_NULLS},
            {"index": "protocol_version", "description": "protocol_version", "reading_type": ReadingType.MESSAGE, "response_type": ResponseType.BYTES_STRIP_NULLS},
            {"index": "production_date", "description": "production_date", "reading_type": ReadingType.MESSAGE, "response_type": ResponseType.BYTES_STRIP_NULLS},
            {"index": "power_on_count", "description": "power_on_count", "reading_type": ReadingType.MESSAGE},
            {"index": "total_runtime", "description": "total_runtime", "reading_type": ReadingType.TIME_SECONDS},

        ],
        "test_responses": [
            b'U\xaa\x11\x01\x01\x00d\x00GW-24S4EB\x00\x00\x00\x00\x00\x00\x00HW-2.8.0ZH-1.2.3V1.0.0\x00\x0020220916\x04\x00\x00\x00n\x85?\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00G\xff'
        ],
    },
    "cell_info": {
        "name": "cell_info",
        "description": "information about the cells",
        "help": " -- display the cell info",
        # "type": "DALY",
        "command_type": CommandType.SERIAL_READ_UNTIL_DONE,
        "command_code": "02",
        "result_type": ResultType.CONSTRUCT,
        "construct": cell_info_construct,
        "construct_min_response": 300,
        "reading_definitions": [
            {"index": "start_flag", "description": "start flag", "reading_type": ReadingType.IGNORE, "response_type": ResponseType.HEX_CHARS},
            {"index": "module_address", "description": "module address", "reading_type": ReadingType.IGNORE, "response_type": ResponseType.HEX_CHAR},
            {"index": "function", "description": "function", "reading_type": ReadingType.IGNORE, "response_type": ResponseType.HEX_CHAR},
            {"index": "command", "description": "command", "reading_type": ReadingType.IGNORE},
            {"index": "length", "description": "length", "reading_type": ReadingType.IGNORE},
            {"index": "frame_counter", "description": "frame_counter", "reading_type": ReadingType.IGNORE},
            {"index": "crc", "description": "crc", "reading_type": ReadingType.IGNORE, "response_type": ResponseType.HEX_CHAR},
            {"index": "end_flag", "description": "end flag", "reading_type": ReadingType.IGNORE, "response_type": ResponseType.HEX_CHAR},

            {"index": "operation_status", "description": "operation_status", "reading_type": ReadingType.MESSAGE, "response_type": ResponseType.STRING},
            {"index": "balancing_current", "description": "balancing_current", "reading_type": ReadingType.CURRENT, "response_type": ResponseType.FLOAT},
            {"index": "total_voltage", "description": "total_voltage", "reading_type": ReadingType.VOLTS, "response_type": ResponseType.FLOAT},
            {"index": "average_cell_voltage", "description": "average_cell_voltage", "reading_type": ReadingType.VOLTS, "response_type": ResponseType.FLOAT},
            {"index": "delta_cell_voltage", "description": "delta_cell_voltage", "reading_type": ReadingType.VOLTS, "response_type": ResponseType.FLOAT},
            {"index": "max_voltage_cell", "description": "max_voltage_cell", "reading_type": ReadingType.MESSAGE, "response_type": ResponseType.TEMPLATE_INT, "format_template": "r+1"},
            {"index": "min_voltage_cell", "description": "min_voltage_cell", "reading_type": ReadingType.MESSAGE, "response_type": ResponseType.TEMPLATE_INT, "format_template": "r+1"},
            {"index": "cell_01_voltage", "description": "cell_01_voltage", "reading_type": ReadingType.VOLTS, "response_type": ResponseType.FLOAT},
            {"index": "cell_02_voltage", "description": "cell_02_voltage", "reading_type": ReadingType.VOLTS, "response_type": ResponseType.FLOAT},
            {"index": "cell_03_voltage", "description": "cell_03_voltage", "reading_type": ReadingType.VOLTS, "response_type": ResponseType.FLOAT},
            {"index": "cell_04_voltage", "description": "cell_04_voltage", "reading_type": ReadingType.VOLTS, "response_type": ResponseType.FLOAT},
            {"index": "cell_05_voltage", "description": "cell_05_voltage", "reading_type": ReadingType.VOLTS, "response_type": ResponseType.FLOAT},
            {"index": "cell_06_voltage", "description": "cell_06_voltage", "reading_type": ReadingType.VOLTS, "response_type": ResponseType.FLOAT},
            {"index": "cell_07_voltage", "description": "cell_07_voltage", "reading_type": ReadingType.VOLTS, "response_type": ResponseType.FLOAT},
            {"index": "cell_08_voltage", "description": "cell_08_voltage", "reading_type": ReadingType.VOLTS, "response_type": ResponseType.FLOAT},
            {"index": "cell_09_voltage", "description": "cell_09_voltage", "reading_type": ReadingType.VOLTS, "response_type": ResponseType.FLOAT},
            {"index": "cell_10_voltage", "description": "cell_10_voltage", "reading_type": ReadingType.VOLTS, "response_type": ResponseType.FLOAT},
            {"index": "cell_11_voltage", "description": "cell_11_voltage", "reading_type": ReadingType.VOLTS, "response_type": ResponseType.FLOAT},
            {"index": "cell_12_voltage", "description": "cell_12_voltage", "reading_type": ReadingType.VOLTS, "response_type": ResponseType.FLOAT},
            {"index": "cell_13_voltage", "description": "cell_13_voltage", "reading_type": ReadingType.VOLTS, "response_type": ResponseType.FLOAT},
            {"index": "cell_14_voltage", "description": "cell_14_voltage", "reading_type": ReadingType.VOLTS, "response_type": ResponseType.FLOAT},
            {"index": "cell_15_voltage", "description": "cell_15_voltage", "reading_type": ReadingType.VOLTS, "response_type": ResponseType.FLOAT},
            {"index": "cell_16_voltage", "description": "cell_16_voltage", "reading_type": ReadingType.VOLTS, "response_type": ResponseType.FLOAT},
            {"index": "cell_17_voltage", "description": "cell_17_voltage", "reading_type": ReadingType.VOLTS, "response_type": ResponseType.FLOAT},
            {"index": "cell_18_voltage", "description": "cell_18_voltage", "reading_type": ReadingType.VOLTS, "response_type": ResponseType.FLOAT},
            {"index": "cell_19_voltage", "description": "cell_19_voltage", "reading_type": ReadingType.VOLTS, "response_type": ResponseType.FLOAT},
            {"index": "cell_20_voltage", "description": "cell_20_voltage", "reading_type": ReadingType.VOLTS, "response_type": ResponseType.FLOAT},
            {"index": "cell_21_voltage", "description": "cell_21_voltage", "reading_type": ReadingType.VOLTS, "response_type": ResponseType.FLOAT},
            {"index": "cell_22_voltage", "description": "cell_22_voltage", "reading_type": ReadingType.VOLTS, "response_type": ResponseType.FLOAT},
            {"index": "cell_23_voltage", "description": "cell_23_voltage", "reading_type": ReadingType.VOLTS, "response_type": ResponseType.FLOAT},
            {"index": "cell_24_voltage", "description": "cell_24_voltage", "reading_type": ReadingType.VOLTS, "response_type": ResponseType.FLOAT},
            {"index": "cell_01_resistance", "description": "cell_01_resistance", "reading_type": ReadingType.RESISTANCE, "response_type": ResponseType.FLOAT},
            {"index": "cell_02_resistance", "description": "cell_01_resistance", "reading_type": ReadingType.RESISTANCE, "response_type": ResponseType.FLOAT},
            {"index": "cell_03_resistance", "description": "cell_01_resistance", "reading_type": ReadingType.RESISTANCE, "response_type": ResponseType.FLOAT},
            {"index": "cell_04_resistance", "description": "cell_01_resistance", "reading_type": ReadingType.RESISTANCE, "response_type": ResponseType.FLOAT},
            {"index": "cell_05_resistance", "description": "cell_01_resistance", "reading_type": ReadingType.RESISTANCE, "response_type": ResponseType.FLOAT},
            {"index": "cell_06_resistance", "description": "cell_01_resistance", "reading_type": ReadingType.RESISTANCE, "response_type": ResponseType.FLOAT},
            {"index": "cell_07_resistance", "description": "cell_01_resistance", "reading_type": ReadingType.RESISTANCE, "response_type": ResponseType.FLOAT},
            {"index": "cell_08_resistance", "description": "cell_01_resistance", "reading_type": ReadingType.RESISTANCE, "response_type": ResponseType.FLOAT},
            {"index": "cell_09_resistance", "description": "cell_01_resistance", "reading_type": ReadingType.RESISTANCE, "response_type": ResponseType.FLOAT},
            {"index": "cell_10_resistance", "description": "cell_01_resistance", "reading_type": ReadingType.RESISTANCE, "response_type": ResponseType.FLOAT},
            {"index": "cell_11_resistance", "description": "cell_01_resistance", "reading_type": ReadingType.RESISTANCE, "response_type": ResponseType.FLOAT},
            {"index": "cell_12_resistance", "description": "cell_01_resistance", "reading_type": ReadingType.RESISTANCE, "response_type": ResponseType.FLOAT},
            {"index": "cell_13_resistance", "description": "cell_01_resistance", "reading_type": ReadingType.RESISTANCE, "response_type": ResponseType.FLOAT},
            {"index": "cell_14_resistance", "description": "cell_01_resistance", "reading_type": ReadingType.RESISTANCE, "response_type": ResponseType.FLOAT},
            {"index": "cell_15_resistance", "description": "cell_01_resistance", "reading_type": ReadingType.RESISTANCE, "response_type": ResponseType.FLOAT},
            {"index": "cell_16_resistance", "description": "cell_01_resistance", "reading_type": ReadingType.RESISTANCE, "response_type": ResponseType.FLOAT},
            {"index": "cell_17_resistance", "description": "cell_01_resistance", "reading_type": ReadingType.RESISTANCE, "response_type": ResponseType.FLOAT},
            {"index": "cell_18_resistance", "description": "cell_01_resistance", "reading_type": ReadingType.RESISTANCE, "response_type": ResponseType.FLOAT},
            {"index": "cell_19_resistance", "description": "cell_01_resistance", "reading_type": ReadingType.RESISTANCE, "response_type": ResponseType.FLOAT},
            {"index": "cell_20_resistance", "description": "cell_01_resistance", "reading_type": ReadingType.RESISTANCE, "response_type": ResponseType.FLOAT},
            {"index": "cell_21_resistance", "description": "cell_01_resistance", "reading_type": ReadingType.RESISTANCE, "response_type": ResponseType.FLOAT},
            {"index": "cell_22_resistance", "description": "cell_01_resistance", "reading_type": ReadingType.RESISTANCE, "response_type": ResponseType.FLOAT},
            {"index": "cell_23_resistance", "description": "cell_01_resistance", "reading_type": ReadingType.RESISTANCE, "response_type": ResponseType.FLOAT},
            {"index": "cell_24_resistance", "description": "cell_01_resistance", "reading_type": ReadingType.RESISTANCE, "response_type": ResponseType.FLOAT},
            {"index": "temperature_1", "description": "temperature_1", "reading_type": ReadingType.TEMPERATURE, "response_type": ResponseType.FLOAT},
            {"index": "temperature_2", "description": "temperature_2", "reading_type": ReadingType.TEMPERATURE, "response_type": ResponseType.FLOAT},
            {"index": "cell_detection_failed", "description": "cell_detection_failed", "reading_type": ReadingType.HEX_CHARS, "response_type": ResponseType.HEX_CHARS},
            {"index": "cell_overvoltage_failed", "description": "cell_overvoltage_failed", "reading_type": ReadingType.HEX_CHARS, "response_type": ResponseType.HEX_CHARS},
            {"index": "cell_undervoltage_failed", "description": "cell_undervoltage_failed", "reading_type": ReadingType.HEX_CHARS, "response_type": ResponseType.HEX_CHARS},
            {"index": "cell_polarity_error", "description": "cell_polarity_error", "reading_type": ReadingType.HEX_CHARS, "response_type": ResponseType.HEX_CHARS},
            {"index": "excessive_line_resistance", "description": "excessive_line_resistance", "reading_type": ReadingType.HEX_CHARS, "response_type": ResponseType.HEX_CHARS},
            {"index": "overheating", "description": "overheating", "reading_type": ReadingType.HEX_STR, "response_type": ResponseType.HEX_CHAR},
            {"index": "charging_fault", "description": "charging_fault", "reading_type": ReadingType.HEX_STR, "response_type": ResponseType.HEX_CHAR},
            {"index": "discharge_fault", "description": "discharge_fault", "reading_type": ReadingType.HEX_STR, "response_type": ResponseType.HEX_CHAR},
            {"index": "read_write_error", "description": "read_write_error", "reading_type": ReadingType.HEX_STR, "response_type": ResponseType.HEX_CHAR},
        ],
        "test_responses": [
            b'U\xaa\x11\x01\x02\x00,\x01\xed\xb2\x15S@4zT@\xe5}T@JuT@o{T@\xd0\x82T@ \x7fT@o{T@\xaflT@\x9aqT@\xf9xT@4zT@ \x7fT@_pT@[\x80T@\xb3\\T@\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xee\x971>b9;>m\x852>\xb5\xf00>\x14R0>\xd1s3>\x86d5>\xdb\xaf7>f\xf7:>,\xa8@>\xb3)@>\x86\xcd=>\xf2W8>\xd3~3>\x19c1>^\xfe.>\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x9faTB\x9faT@\x00\x8f\xb6<\x05\x00\x0f\x05\xc4?\x81\xc0\xaeG\xf5A\xaeG\xf5A\x00\x00\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x8a\x8a\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xbe\xff'
        ],
    },
}

# static const uint8_t FUNCTION_WRITE = 0x00;
# static const uint8_t FUNCTION_READ = 0x01;

# static const uint8_t COMMAND_NONE = 0x00;

# static const uint8_t COMMAND_FACTORY_DEFAULTS = 0x03;
# static const uint8_t COMMAND_SETTINGS = 0x04;
# static const uint8_t COMMAND_WRITE_REGISTER = 0x05;

#   // Request factory settings:
#   // 0xAA 0x55 0x11 0x01 0x03 0x00 0x14 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0xF8 0xFF
#   //
#   // Request settings:
#   // 0xAA 0x55 0x11 0x01 0x04 0x00 0x14 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0xFF 0xFF
#   //
#   // Enable balancer:
#   // 0xAA 0x55 0x11 0x00 0x05 0x0D 0x14 0x00 0x01 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0xF3 0xFF
#   //
#   // Disable balancer:
#   // 0xAA 0x55 0x11 0x00 0x05 0x0D 0x14 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0xF2 0xFF

# single_num     Cell count [1,24]: Set 1                              aa55110005 01 1400 01000000 000000000000ffff
# triger_mpa     Balancing Trigger Delta [0.001d, 1.0d]: Set 1.0f      aa55110005 02 1400 0000803f 00000000000042ff
# max_cur        Max balancing current [1.0f, 4.0f]: Set 1.0f          aa55110005 03 1400 0000803f 00000000000043ff
# auto_close     Balancing stop voltage [1.0f, 4.5f]: Set 1.0f         aa55110005 04 1400 0000803f 00000000000044ff
# auto_open      Balancing start voltage [1.0f, 4.5f]: Set 1.0f        aa55110005 17 1400 0000803f 00000000000057ff
# volume         Capacity [1.0f, 2000.0f]: Set 1                       aa55110005 16 1400 01000000 000000000000e8ff
# alarm_mode     Buzzer mode {1, 2, 3, 4}: Set 1                       aa55110005 14 1400 01000000 000000000000eaff
# bat_mode       Battery type {1, 2, 3}: Set 2                         aa55110005 15 1400 02000000 000000000000e8ff
#                Change device name: Set "test"                        aa55110005 13 1400 74657374000000000000 faff
#
# Factory defaults
#
# standardVol2   ReferenceVoltage [0.001f, 5.0f]: Set 1.0f             aa55110005 05 1400 0000803f 00000000000045ff
# battery_vol    BatteryVoltage [0.001f, 5.0f]: Set 1.0f               aa55110005 06 1400 0000803f 00000000000046ff
# standardCur2   Balancing Current Default? [0.001f, 5.0f]: Set 1.0f   aa55110005 07 1400 0000803f 00000000000047ff
# superBat2      Mean SuperCap Voltage [0.001f, 5.0f]: Set 1.0f        aa55110005 0e 1400 0000803f 0000000000004eff
# triger_mpa     StartVol(V) [0.001f, 5.0f]: Set 1.0f                  aa55110005 08 1400 0000803f 00000000000048ff
# open_num       Boot count []: Set 1.0f                               aa55110005 09 1400 0000803f 00000000000049ff
# batStatu       RefBat Vol [0.001f, 5.0f]: Set 1.0f                   aa55110005 0f 1400 0000803f 0000000000004fff
# battery_max    BatMax [0.001f, 5.0f]: Set 1.0f                       aa55110005 0b 1400 0000803f 0000000000004bff
# battery_min    BatMin [0.001f, 5.0f]: Set 1.0f                       aa55110005 0c 1400 0000803f 0000000000004cff
# ntc_max        NtcMax [-19.9f, 120.0f]: Set 1.0f                     aa55110005 11 1400 0000803f 00000000000051ff
# ntc_min        NtcMin [-19.9f, 120.0f]: Set 1.0f                     aa55110005 12 1400 0000803f 00000000000052ff
# total_time     Working time []: Set 1                                aa55110005 0a 1400 01000000 000000000000f4ff
# cycle          Production date: Set 20220802                         aa55110005 10 1400 3230323230383032 0000e7ff


class Neey(AbstractProtocol):
    """
    Neey Active Balancer rotocol handler
    """

    def __str__(self):
        return "NEEY protocol handler for NEEY balanceer"

    def __init__(self) -> None:
        super().__init__()
        self.protocol_id = b"NEEY"
        self.add_command_definitions(COMMANDS)
        self.add_supported_ports([PortType.BLE])
        self.notifier_handle = 9
        self.intializing_handle = 0
        self.command_handle = 15
        self.check_definitions_count(expected=None)

        # bytes.fromhex('aa5511 010100140000000000000000000000faff')

    def get_full_command(self, command: bytes|str) -> bytes:
        # test_command = bytes.fromhex('aa5511010100140000000000000000000000faff')
        # test_command = bytes.fromhex('aa5511010200001400000000000000000000f9ff')
        log.info("Using protocol %s with %i commands", self.protocol_id, len(self.command_definitions))

        command_definition : CommandDefinition = self.get_command_definition(command)
        if command_definition is None:
            return None

        # fix a 'bug' that seems to be implemented on the device?
        if command_definition.code == "device_info":
            data_length = cs.Int16ul.build(20)
        else:
            data_length = cs.Int16ub.build(20)
        command_bytes = cs.Int16ul.build(int(command_definition.command_code))

        full_command = bytearray(20)
        full_command[0] = 0xaa  # start flag
        full_command[1] = 0x55  # start flag
        full_command[2] = 0x11  # module address
        full_command[3] = 0x01  # function
        full_command[4] = command_bytes[0]  # command code
        full_command[5] = command_bytes[1]  # command code
        full_command[6] = data_length[0]  # length
        full_command[7] = data_length[1]  # length
        checksum = self.checksum(full_command)
        full_command[-2] = checksum
        full_command[-1] = 0xff
        # print(test_command)
        # print(bytes(full_command))
        # print(test_command == bytes(full_command))
        return bytes(full_command)

    def check_valid(self, response: str, command_definition: CommandDefinition = None) -> bool:
        """check if the response is valid

        Args:
            response (str): the response to check
            command_definition (CommandDefinition, optional): not used in the check for this protocol. Defaults to None.

        Raises:
            InvalidResponse: exception raised if the response is invalid for any reason

        Returns:
            bool: True if response doesnt meet any 'invalid' tests
        """
        log.debug("check valid for %s, definition: %s", response, command_definition)
        if response is None:
            raise InvalidResponse("Response is None")
        if len(response) <= 6:
            raise InvalidResponse("Response is too short")
        if response[0] != 0x55:
            raise InvalidResponse("Response has incorrect start byte")
        if int(response[-1]) != 0xff:
            raise InvalidResponse("Response has incorrect end byte")
        return True

    def checksum(self, response):
        calc_crc = 0 
        for i in response:
            calc_crc = calc_crc ^ i
        return calc_crc

    def crc(self, response):
        return sum(response) & 0xFF

    def check_crc(self, response: str, command_definition: CommandDefinition = None) -> bool:
        """ crc check, needs override in protocol """
        log.debug("checking crc for %s", response)
        if response.count(b'\xa5') > 1:
            # multiframe response - crch calc incorrect
            return True
        calc_crc = self.crc(response[:-2])
        response_crc = response[-2]

        if response_crc != calc_crc:
            raise InvalidCRC(f"response has invalid CRC - got '\\x{response_crc:02x}', calculated '\\x{calc_crc:02x}")
        # log.debug("Checksum matches in response '%s' response_crc:'%s'", response, calc_crc)
        return True

    def trim_response(self, response: str, command_definition: CommandDefinition = None) -> str:
        """ Remove extra characters from response """
        log.debug("response: %s", response)
        return response

    def split_response(self, response: str, command_definition: CommandDefinition = None) -> list:
        """ split response into individual items, return as ordered list or list of tuples """
        result_type = getattr(command_definition, "result_type", None)
        log.debug("daly splitting %s, result_type %s", response, result_type)
        # build a list of (index, value) tuples, after parsing with a construct
        responses = []
        # check for construct
        if command_definition.construct is None:
            raise CommandDefinitionIncorrect("No construct found in command_definition")
        if not command_definition.construct_min_response:
            raise CommandDefinitionIncorrect("No construct_min_response found in command_definition")
        if len(response) < command_definition.construct_min_response:
            raise InvalidResponse(f"response:{response}, len:{len(response)} too short for parsing (expecting {command_definition.construct_min_response:})")
        # parse with construct
        result = command_definition.construct.parse(response)
        # print(result)
        if result is None:
            log.debug("construct parsing returned None")
            return responses

        for x in result:
            # print(x)
            if x == "_io":
                continue
            elif x == 'cell_voltage_array':
                # print("cell_voltages")
                for i, value in enumerate(result[x]):
                    # print(i+1,cell)
                    if value:  # explicit exclusion of 0 value results
                        key = f"cell_{i+1:02d}_voltage"
                        responses.append((key,value))
            elif x == 'cell_resistance_array':
                for i, value in enumerate(result[x]):
                    # print(i+1,cell)
                    if value:  # explicit exclusion of 0 value results
                        key = f"cell_{i+1:02d}_resistance"
                        responses.append((key,value))
            else:
                key = x
                value = result[x]
                responses.append((key, value))
        log.debug("responses: '%s'", responses)
        return responses
