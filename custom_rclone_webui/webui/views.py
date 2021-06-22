import pathlib
import platform

from django.contrib import messages
from django.shortcuts import redirect, render

from .forms import NewRemoteForm, RemoteDriveOptions, UploadForm
from .models import Upload
from .utils.rclone import RcloneWindows

RCLONE_WINDOWS = RcloneWindows()
HOME_PATH = str(pathlib.Path.home())[0]
OS_ROOT = ['C', 'c' '/']
OS_TYPE = platform.system()

# VALID_REMOTE represents the short string values
# of the storage providers Rclone supports. For more info,
# run the rclone config command or visit https://rclone.org/overview/
VALID_REMOTE = [
    'fichier', 'alias', 'amazon cloud drive', 's3', 'b2', 'box', 'cache',
    'sharefile', 'dropbox', 'crypt', 'ftp', 'google cloud storage', 'drive',
    'google photos', 'hubic', 'memory', 'jottacloud', 'koofr', 'local',
    'mailru', 'mega', 'azureblob', 'onedrive', 'opendrive', 'swift', 'pcloud',
    'putio', 'qingstor', 'sftp', 'sugarsync', 'tardigrade', 'chunker', 'union',
    'webdav', 'yandex', 'http', 'premiumizeme', 'seafile'
]


def dashboard(request):
    global storage_name, storage_type
    uploads = Upload.objects.all()
    if OS_TYPE == 'Windows':
        remotes_conf = RCLONE_WINDOWS.read_conf()
        remotes_conf_path = RCLONE_WINDOWS.config_file()
        copy_stat, sync_stat, script_stat = RCLONE_WINDOWS.view_conf_options()
    else:
        remotes_conf = [('storage', 'storage')]
        remotes_conf_path = 'path/to/rclone/config/file'
        copy_stat, sync_stat, script_stat = False, False, False

    src_list = []
    dst_list = []
    remotes_conf_list = [list(remote) for remote in remotes_conf]
    for remote in remotes_conf_list:
        for pair in remote:
            if pair in VALID_REMOTE:
                continue
            else:
                src_list.append(pair)
                dst_list.append(pair)

    drive_form = RemoteDriveOptions()
    storage_name = None
    storage_type = None
    success_sub = False

    for remote in remotes_conf_list:
        for pair in remote:
            if pair in VALID_REMOTE:
                continue
            else:
                src_list.append(pair)
                dst_list.append(pair)

    if request.method == 'POST':
        upload_form = UploadForm(request.POST, request.FILES)
        new_remote_form = NewRemoteForm(request.POST)

        files = request.FILES.getlist('upload')

        if upload_form.is_valid():
            for f in files:
                newfile = Upload(file=f)
                newfile.owner = request.user
                newfile.save()

        elif new_remote_form.is_valid():
            storage_type = new_remote_form['storage_type'].value()
            success_sub = True

        elif 'copyDestinationFolder' in request.POST or 'syncDestinationFolder' in request.POST:
            copy_sync = copy_sync_cmd(request)
            if 'Failed' in copy_sync:
                messages.error(request, copy_sync)
            elif not copy_sync:
                messages.error(request, '500: Internal Server Error')
            else:
                messages.success(request, copy_sync)

        elif 'iniFile' in request.POST:
            rclone_webui_auto(request, src_list, dst_list)
            return redirect('dashboard')

        elif 'clearList' in request.POST:
            Upload.objects.all().delete()
            return redirect('dashboard')

        elif 'refreshPage' in request.POST:
            return redirect('dashboard')

        else:
            pass

    else:
        upload_form = UploadForm()
        new_remote_form = NewRemoteForm()

    context = {
        'home_path': HOME_PATH,
        'uploads': uploads,
        'remotes_conf': remotes_conf,
        'remotes_conf_path': remotes_conf_path,
        'valid_remote': VALID_REMOTE,
        'new_remote': new_remote_form,
        'copy_stat': copy_stat,
        'sync_stat': sync_stat,
        'script_stat': script_stat,
        'drive_form': drive_form,
        'successful_submit': success_sub,
        'modal_name': storage_type
    }
    return render(request, 'webui/dashboard.html', context)


def create_remote_drive(request):
    if OS_TYPE != 'Windows':
        return
    global storage_name, storage_type
    default_scope = {'drive': 'drive'}
    drive_options = {
        'client_id': '--drive-client-id=',
        'client_secret': '--drive-client-secret=',
        'drive_scope': '--drive-scope='
    }

    if request.method == 'POST':
        drive_form = RemoteDriveOptions(request)
        if drive_form.is_valid():
            client_id = drive_options['client_id'] + drive_form[
                'client_id'].value()
            client_secret = drive_options['client_secret'] + drive_form[
                'client_secret'].value()
            drive_scope = drive_options['drive_scope'] + default_scope['drive']

            if storage_name and storage_type:
                cmd_args = [
                    storage_name, storage_type, client_id, client_secret,
                    drive_scope
                ]
                RCLONE_WINDOWS.create(cmd_args)

    return redirect('dashboard')


def copy_sync_cmd(request):
    if OS_TYPE != 'Windows':
        return
    webui_src_path = RCLONE_WINDOWS.webui_files_path()
    default_src_path = default_dst_path = RCLONE_WINDOWS.rclone_dst_default()
    src_input = request.POST.get('src')
    dst_input = request.POST.get('dst')
    copy_src_input = request.POST.get('copySourceFolder')
    copy_dst_input = request.POST.get('copyDestinationFolder')
    sync_src_input = request.POST.get('syncSourceFolder')
    sync_dst_input = request.POST.get('syncDestinationFolder')
    out = None

    if src_input and dst_input:
        if copy_src_input or copy_dst_input:
            src_path_input, dst_path_input = copy_src_input, copy_dst_input
        elif sync_src_input or sync_dst_input:
            src_path_input, dst_path_input = sync_src_input, sync_dst_input
        else:
            src_path_input, dst_path_input = None, None

        if src_input != dst_input:
            if src_path_input:
                src = [src_input, src_path_input]
            elif src_input in OS_ROOT:
                src = [webui_src_path[0], webui_src_path[1]]
            else:
                src = [src_input, default_src_path]

            if dst_path_input:
                dst = [dst_input, dst_path_input]
            else:
                dst = [dst_input, default_dst_path]

            out = RCLONE_WINDOWS.copy(src, dst)
    else:
        out = None

    return out


def copy_files(request):
    if OS_TYPE != 'Windows':
        return
    webui_src_path = RCLONE_WINDOWS.webui_files_path()
    default_src_path = default_dst_path = RCLONE_WINDOWS.rclone_dst_default()
    src_input = request.POST.get('src')
    dst_input = request.POST.get('dst')
    src_path_input = request.POST.get('copySourceFolder')
    dst_path_input = request.POST.get('copyDestinationFolder')

    if src_input and dst_input:
        if src_input != dst_input:
            if src_path_input:
                src = [src_input, src_path_input]
            elif src_input in OS_ROOT:
                src = [webui_src_path[0], webui_src_path[1]]
            else:
                src = [src_input, default_src_path]

            if dst_path_input:
                dst = [dst_input, dst_path_input]
            else:
                dst = [dst_input, default_dst_path]

            out = RCLONE_WINDOWS.copy(src, dst)
            return out


def sync_files(request):
    if OS_TYPE != 'Windows':
        return
    webui_src_path = RCLONE_WINDOWS.webui_files_path()
    src_input = request.POST.get('src')
    dst_input = request.POST.get('dst')
    src_path_input = request.POST.get('syncSourceFolder')
    dst_path_input = request.POST.get('syncDestinationFolder')
    default_src_path = default_dst_path = RCLONE_WINDOWS.rclone_dst_default()

    if src_input and dst_input:
        if src_input != dst_input:
            if src_path_input:
                src = [src_input, src_path_input]
            elif src_input in OS_ROOT:
                src = [webui_src_path[0], webui_src_path[1]]
            else:
                src = [src_input, default_src_path]

            if dst_path_input:
                dst = [dst_input, dst_path_input]
            else:
                dst = [dst_input, default_dst_path]

            out = RCLONE_WINDOWS.sync(src, dst)
            return out


def rclone_webui_auto(request, src_list, dst_list):
    if OS_TYPE != 'Windows':
        return
    script_btn_active = request.POST.get('scriptActive')
    copy_btn_active = request.POST.get('copyActive')
    sync_btn_active = request.POST.get('syncActive')
    copy_active = 'false'
    sync_active = 'false'
    order = 'quit'

    if script_btn_active == 'on':
        order = 'true'

    if copy_btn_active:
        copy_active = 'true'

    if sync_btn_active:
        sync_btn_active = 'true'

    RCLONE_WINDOWS.gui_edit_auto(src_list=src_list,
                                 dst_list=dst_list,
                                 copy_active=copy_active,
                                 sync_active=sync_active,
                                 order=order)
