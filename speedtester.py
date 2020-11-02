#!/usr/bin/python3
import csv
import json
import logging
import os.path
import subprocess
from logging.handlers import RotatingFileHandler

# Loggers
logger = logging.getLogger('s_logger')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)s : %(message)s')

detailed_logger = logging.getLogger('d_logger')
detailed_logger.setLevel(logging.DEBUG)

# Console Handler
s_h = logging.StreamHandler()
s_h.setLevel(logging.DEBUG)
s_h.setFormatter(formatter)

r_h_a = RotatingFileHandler(
        '/home/pi/scripts/logs/speedtest_simple.log',
        backupCount=5,
        maxBytes=51200)
r_h_a.setLevel(logging.DEBUG)
r_h_a.setFormatter(formatter)

r_h_b = RotatingFileHandler(
        '/home/pi/scripts/logs/speedtest_detailed.log',
        backupCount=5,
        maxBytes=51200)
r_h_b.setLevel(logging.DEBUG)
r_h_b.setFormatter(logging.Formatter('%(message)s'))

# Add handlers
logger.addHandler(s_h)
logger.addHandler(r_h_a)
detailed_logger.addHandler(r_h_b)

# Misc
res_list = []
client = {"country": None, "isp": None, "ip": None, "lon": None, "lat": None}
servers = [22910, 15658, 15658, 34338, 30907, 3945]
""" 22910 - Telenor Denmark (Söborg, Denmark) [36.40 km]
    34024 - Bahnhof AB (Stockholm, Sweden) [484.75 km]      (Deprecated as of Oct 2020)
    12919 - Telenor Norge AS (Oslo, Norway) [448.69 km]     (Deprecated as of Oct 2020)
    6061  - Tele2 (Kista, Sweden) [485.84 km]               (Deprecated as of Oct 2020)
    15658 - Telia Denmark (Copenhagen, Denmark) [42.07 km]
    34338 - Banhof AB (Malmö, Sweden) [55.71 km]
    30907 - Deutsche Telekom (Berlin, Germany) [394.54 km]
    3945  - TYGFRYS (Rumia, Poland) [395.75 km]
"""

def main():
    logger.info("Running Speedtest Script ...")
    for srv in servers:
        logger.info("Querying server %s ...", srv)
        try:
            result = subprocess.Popen(
                    '/home/pi/.local/bin/speedtest-cli --json --server {}'.format(srv),
                    shell=True,
                    stdout=subprocess.PIPE).stdout.read()
            try:
                logger.info("Trying to append data to result list ...")
                res_list.append(json.loads(result))
            except Exception as e:
                logger.error("Cant append data to list because: %s", e)
            else:
                logger.info("Data appended successfully.")
        except Exception as e:
            logger.error("Subprocess failed to run. Exception thrown: %s", e)


    avg_dl = 0
    avg_ul = 0
    avg_pi = 0
    total_entries = 0

    logger.info("Processing res_list into output data...")
    headers = ['Timestamp', 'Latency', 'UploadMbps', 'DownloadMbps']
    for entry in res_list:
        try:
            detailed_logger.info(entry)
            dl_Mbps = round(int(entry['download'] / 1000000), 2)
            ul_Mbps = round(int(entry['upload'] / 1000000), 2)
            ping = round(int(entry['ping']), 2)
            logger.info(
                    "%s --- Server %s - Latency: %s ms - Speed DOWN: %s Mbps - Speed UP: %s Mbps",
                    entry['timestamp'],
                    entry['server'],
                    ping,
                    dl_Mbps,
                    ul_Mbps)

            csv_file = "/home/pi/scripts/logs/st_res_{}".format(entry['server']['sponsor'].replace(" ", "_"))
            csv_exists = os.path.isfile(csv_file)

            with open(csv_file, 'a') as cfile:
                writer = csv.DictWriter(
                        cfile,
                        delimiter=',',
                        lineterminator='\n',
                        fieldnames=headers,
                        quoting=csv.QUOTE_ALL)
                if not csv_exists:
                    writer.writeheader()

                writer.writerow({
                    'Timestamp': entry['timestamp'],
                    'Latency': ping,
                    'UploadMbps': ul_Mbps,
                    'DownloadMbps': dl_Mbps})

                avg_pi += ping
                avg_dl += dl_Mbps
                avg_ul += ul_Mbps
                total_entries += 1

        except Exception as e:
            logger.error("Unable to handle entry: \"%s\" with error: %s", entry, e)

    if not total_entries == 0:
        logger.info(
                "Average Result --- Latency: %s ms - Speed Down: %s Mbps - Speed UP: %s Mbps",
                round(avg_pi / total_entries),
                round(avg_dl / total_entries),
                round(avg_ul / total_entries))

if __name__ == '__main__':
    main()
