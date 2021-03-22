"""Automation script that runs as a background process.

This will execute an infinite sequence of `rclone copy-sync --options 
source:path destination:path` once called via os.startfile() from a 
another module or script, and it will continue to run headless for an 
indefinite amount of time.

The script's actions are dictated by <cmd_options.ini>
For example, the process will end once the word `quit` 
is set and located inside the aforementioned config file.
"""
import concurrent.futures
import configparser
import logging
import pathlib
import subprocess
import time
from configparser import NoSectionError

logging.basicConfig(
    filename="bg-rclone-proc.log",
    format='%(asctime)s %(levelname)s {%(module)s} [%(funcName)s] %(message)s',
    datefmt='%Y/%m/%d %H:%M:%S',
    level=logging.INFO)

config = configparser.ConfigParser(allow_no_value=True)
ini_path = str(pathlib.Path(__file__).parent.absolute()) + r'\cmd_options.ini'
alive = True
copy_status = False
sync_status = False
copy_src_dst = {}
sync_src_dst = {}


def _get_stats():
    """Determine the script's next actions according to the .ini file.
    """
    global alive, config, copy_status, sync_status, copy_src_dst, sync_src_dst
    timeout = 2

    while alive:
        try:
            config.read(ini_path)
        except IOError as file_err:
            logging.error(f'[Configparser Error] {file_err}')
            break
        except Exception as err:
            logging.error(f'[Error] {err}')
            break

        status = config['status']['run']
        sections = config.sections()

        if status == 'false':
            logging.info(f'[Status] {status}')
            break

        if sections:
            try:
                copy_status = config.getboolean('copysect', 'active')
                sync_status = config.getboolean('syncsect', 'active')
            except NoSectionError as no_section:
                logging.error(f'[Configparser Error] {no_section}')
            except Exception as err:
                logging.error(f'[Error] {err}')
        else:
            logging.warning(f'Sections: {sections}')
            break

        # Set source and destination for copy and sync if `active` is True
        # Get `auto-copy` .ini values (i.e. src and dst)
        if copy_status:
            copy_src = config.get('copysect', 'source')
            copy_dst = config.get('copysect', 'destination')
        else:
            copy_src, copy_dst = None, None

        # Get `auto-sync` .ini values (i.e. src and dst)
        if sync_status:
            sync_src = config.get('syncsect', 'source')
            sync_dst = config.get('syncsect', 'destination')
        else:
            sync_src, sync_dst = None, None

        copy_src_dst.clear()
        sync_src_dst.clear()

        if copy_status or sync_status:
            copy_src_dst['src'] = copy_src
            copy_src_dst['dst'] = copy_dst
            sync_src_dst['src'] = sync_src
            sync_src_dst['dst'] = sync_dst
            time.sleep(timeout)
        else:
            logging.info('[Copy||Sync] keys (active) are set to false')
            logging.info({
                copy_status: copy_src_dst,
                sync_status: sync_src_dst
            })
            break

    # Set script status to False as failsafe and exit status
    config['status']['run'] = 'false'
    with open(ini_path, 'w') as configfile:
        config.write(configfile)

    logging.info(f'[Finished] status: run is set to false.')
    alive = False


def _exec_commands():
    """Executes commands passed from the .ini file.
    """
    timeout = 2.5
    cooldown = 3600
    exe = 'rclone'
    opt = '--verbose'
    copy = 'copy'
    sync = 'sync'

    time.sleep(timeout)  # Wait for get_stats()'s initial checks

    while alive:
        copy_num = 0
        sync_num = 0
        if copy_status and copy_src_dst:
            srcs = copy_src_dst.get('src').split(',')
            dsts = copy_src_dst.get('dst').split(',')
            copy_num = 1
        elif sync_status and sync_src_dst:
            srcs = sync_src_dst.get('src').split(',')
            dsts = sync_src_dst.get('dst').split(',')
            sync_num = 1
        else:
            srcs, dsts = None, None

        if srcs and dsts:
            for src in srcs:
                for dst in dsts:
                    if src == dst:
                        continue
                    else:
                        if copy_num > sync_num:
                            main_cmd = [exe, copy, opt]
                        else:
                            main_cmd = [exe, sync, opt]

                        main_cmd.append(src)
                        main_cmd.append(dst)

                        copy_sync_proc = subprocess.run(main_cmd,
                                                        capture_output=True,
                                                        shell=True)
                        copy_sync_out = copy_sync_proc.stdout.decode('utf-8')
                        copy_sync_err = copy_sync_proc.stderr.decode('utf-8')
                        if len(copy_sync_err) == 0:
                            logging.info(copy_sync_err)
                        else:
                            logging.error(copy_sync_out)

        time.sleep(
            cooldown
        )  # Interval between the most recent subprocess and the next in seconds


if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.submit(_get_stats)
        executor.submit(_exec_commands)
        executor.shutdown()
