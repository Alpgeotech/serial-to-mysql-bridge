import sys
import os
import logging
import logging.handlers

from classes import mysql

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        sys.exit

from classes import serial_receiver

with open("config.toml", "rb") as f:
    config = tomllib.load(f)

general_settings_dict = config['general']
mysql_settings_dict = config['mysql']
serial_settings_dict = dict(config['serial'])

def str2bool(value : str) -> bool:
    return value.lower() in ['true', '1', 't', 'y', 'yes', 'yeah', 'yup', 'ja', 'jawoll', 'definitiv']


log_location = general_settings_dict.get("log_location", "./log")
if not os.path.exists(log_location):
    os.mkdir(log_location)

logger = logging.getLogger()
logger.setLevel(general_settings_dict.get("log_level", "INFO").upper())

formatter = logging.Formatter(
    "[%(levelname)-7s] [%(asctime)s] %(name)10s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

file_handler = logging.handlers.RotatingFileHandler(
    f"{log_location}/udp_to_serial.log", maxBytes=(1048576*5), backupCount=7, encoding='utf-8'
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Stream handler (stdout -> captured by systemd)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

file_handler.doRollover()

# Catch unhandled exceptions in main thread
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        # Let KeyboardInterrupt go through without logging
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception

logger.warning("=========== NEW START OF serial-to-mysql-converter ===========")

database_caller = mysql.MySql(mysql_settings_dict)
receiver = serial_receiver.SerialReceiver(serial_settings_dict)

try: 
    while 1:

        database_state, database_state_change = database_caller.ensureDatabaseConnection()

        if database_state_change:
            logger.debug(f"database_state_change: {database_state_change}")
            logger.debug(f"database_active: {database_state}")
            continue

        line = receiver.read()
        
        # hdf;1760563031.63;1760563041.63;2025;9;8988;17871
        
        values = (
            line[0],
            float(line[1]),
            float(line[2]),
            int(line[3]),
            int(line[4]),
            int(line[5]),
        )

        database_caller.insertDataset(values)
        

finally:
    receiver.close()
    # transmitter.close()
    

