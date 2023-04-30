import logging
from gzip import open as gzopen
from os import listdir, makedirs, path
from time import localtime


def setupLogging():
    def compress(filename: str):
        makedirs('logs', exist_ok=True)
        out_path = 'logs/'
        files = listdir('logs')
        if filename in listdir():
            modtime = path.getmtime(filename)
            time_data = localtime(modtime)
            i = 1
            while True:
                new_file = '{year:04d}-{month:02d}-{day:02d}-{i}.log.gz'.format(
                    year=time_data.tm_year, month=time_data.tm_mon, day=time_data.tm_mday, i=i)
                if new_file in files:
                    i += 1
                    continue
                else:
                    with open(filename, 'rb') as src, gzopen(out_path + new_file, 'wb') as dst:
                        for chunk in iter(lambda: src.read(4096), b""):
                            dst.write(chunk)
                    break

    filename = 'latest.log'

    compress(filename)

    logging_format = '[%(asctime)s] [%(name)s/%(levelname)s]: %(message)s'
    logging_timeFormat = '%H:%M:%S'
    loggingFormater = logging.Formatter(
        logging_format, datefmt=logging_timeFormat)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    cHandler = logging.StreamHandler()
    cHandler.setFormatter(loggingFormater)

    fHandler = logging.FileHandler(filename, mode='w', encoding="utf-8")
    fHandler.setFormatter(loggingFormater)

    logger.addHandler(cHandler)
    logger.addHandler(fHandler)

    logging.addLevelName(logging.WARN, 'WARN')
    logging.addLevelName(logging.FATAL, 'FATAL')
