import configparser
import logging
import os
import pathlib
import subprocess
from configparser import NoSectionError


class RcloneWindows:
    def __init__(self):
        self.config = configparser.ConfigParser(allow_no_value=True)
        self.utils_dir = str(pathlib.Path(__file__).parent.absolute())
        self.ini_path = self.utils_dir + r'\cmd_options.ini'

        logging.basicConfig(
            filename='custom-rclone-gui.log',
            format=
            '%(asctime)s %(levelname)s {%(module)s} [%(funcName)s] %(message)s',
            datefmt='%Y/%m/%d %H:%M:%S',
            level=logging.INFO)

    def _exec_block(self, cmd):
        logging.info(cmd)
        try:
            rclone_cmd = subprocess.run(cmd, capture_output=True, shell=True)
            rc = rclone_cmd.returncode
            output = rclone_cmd.stdout.decode('utf-8')
            err = rclone_cmd.stderr.decode('utf-8')
            logging.info(f'({rc})\n{output}\n{err}')
            if output:
                return output
            else:
                return err
        except Exception as err:
            logging.error(err)
            return False

    def _exec_non_block(self, cmd):
        try:
            with subprocess.Popen(cmd,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE) as proc:
                output, err = proc.communicate()

                if err:
                    logging.error(err.decode("utf-8"))
                else:
                    logging.info(output.decode("utf-8"))

        except Exception as err:
            logging.error(err.decode("utf-8"))

        return None

    def create(self, cmd_args=[]):
        """Creates new storage types without any configurations.

        Args:
            cmd_args (list): Separated string values of the storage name and storage type.
        """
        cmd = ['rclone', 'config', 'create']
        cmd.extend(cmd_args)
        return self._exec_block(cmd)

    def copy(self, src=[], dst=[]):
        """Executes the `rclone copy` command.

        Args:
            src (list): Separated string values of the source and path.
            dst (list): Separated string values of the destination and path.
        """
        src = ':'.join(map(str, src))
        dst = ':'.join(map(str, dst))
        exe, cmd, verbose = 'rclone', 'copy', '--verbose'
        return self._exec_block([exe, cmd, verbose, src, dst])

    def sync(self, src=[], dst=[]):
        """Executes the `rclone sync` command.

        Args:
            src (list): Separated string values of the source and path.
            dst (list): Separated string values of the destination and path.
        """
        src = ':'.join(map(str, src))
        dst = ':'.join(map(str, dst))
        exe, cmd, verbose = 'rclone', 'sync', '--verbose'
        return self._exec_block([exe, cmd, verbose, src, dst])

    def gui_edit_auto(self,
                      src_list,
                      dst_list,
                      copy_active='false',
                      sync_active='false',
                      order='false'):
        """Modifies the intermediary config file for the automated `rclone copy-sync` commands.

        Args:
            src_list (list): List of source files/directories (e.g. source:\\path\\to\\file)
            dst_list (list): Simply, a list of destinations (e.g. destination:\\my-remote-folder)
            copy_active (str): Boolean value submitted from a django views in string format
            sync_active (str): Boolean value submitted from a django views in string format
            order (str): String type of the boolean that will start or stop the automation script
        """
        ini_path = self.ini_path
        config = self.config
        bg_proc_file = self.utils_dir + r'\_rclone_auto.pyw'
        err = None

        try:
            config.read(ini_path)
            err = None
        except IOError as file_err:
            err = file_err
        except Exception as generic_err:
            err = generic_err

        # If copy_btn_active and sync_btn_active is True
        # Make sync_btn_active False as the two must not
        # be executed concurrently to avoid data loss.
        if copy_active == sync_active:
            sync_active = 'false'

        try:
            config['status']['run'] = order
            config['copysect']['active'] = copy_active
            config['syncsect']['active'] = sync_active

            if copy_active == 'false':
                config['copysect']['source'] = 'none'
                config['copysect']['destination'] = 'none'
            else:
                config['copysect']['source'] = ",".join(src_list)
                config['copysect']['destination'] = ",".join(dst_list)

            if sync_active == 'false':
                config['syncsect']['source'] = 'none'
                config['syncsect']['destination'] = 'none'
            else:
                config['syncsect']['source'] = ",".join(src_list)
                config['syncsect']['destination'] = ",".join(dst_list)

            with open(ini_path, 'w') as configfile:
                config.write(configfile)

            err = None
        except NoSectionError as config_err:
            err = config_err
        except AttributeError as attrib_err:
            err = attrib_err
        except Exception as generic_err:
            err = generic_err

        if err:
            logging.error(err)
        else:
            os.startfile(bg_proc_file)

    def read_conf(self):
        """Returns the contents of Rclone's default config file. 
        Specifically, the `remote name` and `remote type`

        Returns:
            list: A list containing storage names and storage types.
        """
        conf_content = []

        configparse = configparser.ConfigParser()
        cmd = ['rclone', 'config', 'file']

        rclone_cmd = subprocess.run(cmd, capture_output=True, shell=True)
        path = rclone_cmd.stdout.decode("utf-8").splitlines()[1]

        configparse.read(path)
        config_details = dict(configparse.items())

        for details in config_details:
            if details != 'DEFAULT':
                remote_type = configparse.items(details.strip())
                remote_type = ' '.join(remote_type[0]).replace('type',
                                                               '').strip()
                conf_content.append((details, remote_type))

        return conf_content

    def config_file(self):
        """Acquires the default path of Rclone's config file.

        Returns: 
            str: The default location of Rclone's config file.
        """
        cmd = ['rclone', 'config', 'file']
        rclone_cmd = subprocess.run(cmd, capture_output=True, shell=True)
        return rclone_cmd.stdout.decode("utf-8").splitlines()[1]

    def view_conf_options(self):
        """Parses the .ini config file for Django views.
        
        Returns:
            bool: The boolean value of the intermediary .ini file
        """
        ini_path = self.ini_path
        config = self.config

        try:
            config.read(ini_path)
            err = None
        except IOError as file_err:
            err = file_err
        except Exception as generic_err:
            err = generic_err

        try:
            copy_stat = config.getboolean('copysect', 'active')
            sync_stat = config.getboolean('syncsect', 'active')
            script_stat = config.getboolean('status', 'run')
            err = None
        except NoSectionError as config_err:
            copy_stat, sync_stat, script_stat = None, None, None
            err = config_err
        except AttributeError as attrib_err:
            copy_stat, sync_stat, script_stat = None, None, None
            err = attrib_err
        except Exception as generic_err:
            copy_stat, sync_stat, script_stat = None, None, None
            err = generic_err

        if err:
            logging.error(err)

        return (copy_stat, sync_stat, script_stat)

    def webui_files_path(self, pkg_mdia_path=r'webui\utils'):
        """Acquire path to directory containing the app's uploaded files.
        """
        path = self.utils_dir.replace(pkg_mdia_path, r'media')
        return path.split(':')

    def rclone_dst_default(self):
        return r'\rclone-gui'
