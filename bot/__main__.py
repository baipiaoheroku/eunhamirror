from signal import signal, SIGINT
from os import path as ospath, remove as osremove, execl as osexecl
from subprocess import run as srun, check_output
from psutil import disk_usage, cpu_percent, swap_memory, cpu_count, virtual_memory, net_io_counters, boot_time
from time import time
from sys import executable
from telegram.ext import CommandHandler
from bot import bot, dispatcher, updater, botStartTime, IGNORE_PENDING_REQUESTS, LOGGER, Interval, INCOMPLETE_TASK_NOTIFIER, DB_URI, alive, app, main_loop
from .helper.ext_utils.fs_utils import start_cleanup, clean_all, exit_clean_up
from .helper.ext_utils.bot_utils import get_readable_file_size, get_readable_time
from .helper.ext_utils.db_handler import DbManger
from .helper.telegram_helper.bot_commands import BotCommands
from .helper.telegram_helper.message_utils import sendMessage, sendMarkup, editMessage, sendLogFile
from .helper.telegram_helper.filters import CustomFilters
from .helper.telegram_helper.button_build import ButtonMaker

def stats(update, context):
    if ospath.exists('.git'):
        last_commit = check_output(["git log -1 --date=short --pretty=format:'%cd <b>From</b> %cr'"], shell=True).decode()
    else:
        last_commit = 'No UPSTREAM_REPO'
    currentTime = get_readable_time(time() - botStartTime)
    osUptime = get_readable_time(time() - boot_time())
    total, used, free, disk= disk_usage('/')
    total = get_readable_file_size(total)
    used = get_readable_file_size(used)
    free = get_readable_file_size(free)
    sent = get_readable_file_size(net_io_counters().bytes_sent)
    recv = get_readable_file_size(net_io_counters().bytes_recv)
    cpuUsage = cpu_percent(interval=0.5)
    p_core = cpu_count(logical=False)
    t_core = cpu_count(logical=True)
    swap = swap_memory()
    swap_p = swap.percent
    swap_t = get_readable_file_size(swap.total)
    memory = virtual_memory()
    mem_p = memory.percent
    mem_t = get_readable_file_size(memory.total)
    mem_a = get_readable_file_size(memory.available)
    mem_u = get_readable_file_size(memory.used)
    stats = f'<b>Commit Date:</b> {last_commit}\n\n'\
            f'<b>Bot Uptime:</b> {currentTime}\n'\
            f'<b>OS Uptime:</b> {osUptime}\n\n'\
            f'<b>Total Disk Space:</b> {total}\n'\
            f'<b>Used:</b> {used} | <b>Free:</b> {free}\n\n'\
            f'<b>Upload:</b> {sent}\n'\
            f'<b>Download:</b> {recv}\n\n'\
            f'<b>CPU:</b> {cpuUsage}%\n'\
            f'<b>RAM:</b> {mem_p}%\n'\
            f'<b>DISK:</b> {disk}%\n\n'\
            f'<b>Physical Cores:</b> {p_core}\n'\
            f'<b>Total Cores:</b> {t_core}\n\n'\
            f'<b>SWAP:</b> {swap_t} | <b>Used:</b> {swap_p}%\n'\
            f'<b>Memory Total:</b> {mem_t}\n'\
            f'<b>Memory Free:</b> {mem_a}\n'\
            f'<b>Memory Used:</b> {mem_u}\n'
    sendMessage(stats, context.bot, update.message)


def start(update, context):
    buttons = ButtonMaker()
    buttons.buildbutton("Channel", "https://t.me/EunhaMirror")
    buttons.buildbutton("Group", "https://t.me/EunhaMirror")
    reply_markup = buttons.build_menu(2)
    if CustomFilters.authorized_user(update) or CustomFilters.authorized_chat(update):
        start_string = f'''
This bot can mirror all your links to Google Drive or to telegram!
Type /{BotCommands.HelpCommand} to get a list of available commands
'''
        sendMarkup(start_string, context.bot, update.message, reply_markup)
    else:
        sendMarkup('Not an Authorized user, deploy your own mirror-leech bot', context.bot, update.message, reply_markup)

def restart(update, context):
    restart_message = sendMessage("Restarting...", context.bot, update.message)
    if Interval:
        Interval[0].cancel()
        Interval.clear()
    alive.kill()
    clean_all()
    srun(["pkill", "-9", "-f", "gunicorn|chrome|firefox|megasdkrest"])
    srun(["python3", "update.py"])
    with open(".restartmsg", "w") as f:
        f.truncate(0)
        f.write(f"{restart_message.chat.id}\n{restart_message.message_id}\n")
    osexecl(executable, executable, "-m", "bot")


def ping(update, context):
    start_time = int(round(time() * 1000))
    reply = sendMessage("Starting Ping", context.bot, update.message)
    end_time = int(round(time() * 1000))
    editMessage(f'{end_time - start_time} ms', reply)


def log(update, context):
    sendLogFile(context.bot, update.message)

help_string = f'''
CATATAN: Coba setiap perintah tanpa perfiks apa pun untuk melihat lebih detail.
/{BotCommands.MirrorCommand[0]} atau /{BotCommands.MirrorCommand[1]}: Mulai mirroring ke Google Drive.
/{BotCommands.ZipMirrorCommand[0]} atau /{BotCommands.ZipMirrorCommand[1]}: Mulai mirroring dan unggah file/folder yang dikompresi dengan ekstensi zip.
/{BotCommands.UnzipMirrorCommand[0]} atau /{BotCommands.UnzipMirrorCommand[1]}: Mulai mirroring dan unggah file/folder yang diekstrak dari ekstensi arsip apa pun.
/{BotCommands.QbMirrorCommand[0]} atau /{BotCommands.QbMirrorCommand[1]}: Mulai Mencerminkan ke Google Drive menggunakan qBittorrent.
/{BotCommands.QbZipMirrorCommand[0]} atau /{BotCommands.QbZipMirrorCommand[1]}: Mulai mirroring menggunakan qBittorrent dan unggah file/folder yang dikompresi dengan ekstensi zip.
/{BotCommands.QbUnzipMirrorCommand[0]} atau /{BotCommands.QbUnzipMirrorCommand[1]}: Mulai mirroring menggunakan qBittorrent dan unggah file/folder yang diekstrak dari ekstensi arsip apa pun.
/{BotCommands.YtdlCommand[0]} atau /{BotCommands.YtdlCommand[1]}: Mencerminkan tautan yang didukung yt-dlp.
/{BotCommands.YtdlZipCommand[0]} atau /{BotCommands.YtdlZipCommand[1]}: Mencerminkan tautan yang didukung yt-dlp sebagai zip.
/{BotCommands.LeechCommand[0]} atau /{BotCommands.LeechCommand[1]}: Mulai leeching ke Telegram.
/{BotCommands.ZipLeechCommand[0]} atau /{BotCommands.ZipLeechCommand[1]}: Mulai leeching dan unggah file/folder yang dikompres dengan ekstensi zip.
/{BotCommands.UnzipLeechCommand[0]} atau /{BotCommands.UnzipLeechCommand[1]}: Mulai leeching dan unggah file/folder yang diekstrak dari ekstensi arsip apa pun.
/{BotCommands.QbLeechCommand[0]} atau /{BotCommands.QbLeechCommand[1]}: Mulai lintah menggunakan qBittorrent.
/{BotCommands.QbZipLeechCommand[0]} atau /{BotCommands.QbZipLeechCommand[1]}: Mulai leeching menggunakan qBittorrent dan unggah file/folder yang dikompresi dengan ekstensi zip.
/{BotCommands.QbUnzipLeechCommand[0]} atau /{BotCommands.QbUnzipLeechCommand[1]}: Mulai leeching menggunakan qBittorrent dan unggah file/folder yang diekstrak dari ekstensi arsip apa pun.
/{BotCommands.YtdlLeechCommand[0]} atau /{BotCommands.YtdlLeechCommand[1]}: Tautan yang didukung Leech yt-dlp.
/{BotCommands.YtdlZipLeechCommand[0]} atau /{BotCommands.YtdlZipLeechCommand[1]}: Lintah yt-dlp mendukung tautan sebagai zip.
/{BotCommands.CloneCommand} [drive_url]: Salin file/folder ke Google Drive.
/{BotCommands.CountCommand} [drive_url]: Menghitung file/folder Google Drive.
/{BotCommands.DeleteCommand} [drive_url]: Menghapus file/folder dari Google Drive (Hanya Pemilik & Sudo).
/{BotCommands.LeechSetCommand} [permintaan]: Setelan lintah.
/{BotCommands.SetThumbCommand}: Balas foto untuk mengaturnya sebagai Thumbnail.
/{BotCommands.BtSelectCommand}: Pilih file dari torrent dengan gid atau balas.
/{BotCommands.RssListCommand[0]} atau /{BotCommands.RssListCommand[1]}: Mencantumkan semua info rss feed yang dilanggan (Hanya Pemilik & Sudo).
/{BotCommands.RssGetCommand[0]} atau /{BotCommands.RssGetCommand[1]}: Ambil paksa N tautan terakhir (Hanya Pemilik & Sudo).
/{BotCommands.RssSubCommand[0]} atau /{BotCommands.RssSubCommand[1]}: Berlangganan rss feed baru (Hanya Pemilik & Sudo).
/{BotCommands.RssUnSubCommand[0]} atau /{BotCommands.RssUnSubCommand[1]}: Berhenti berlangganan umpan rss berdasarkan judul (Hanya Pemilik & Sudo).
/{BotCommands.RssSettingsCommand[0]} atau /{BotCommands.RssSettingsCommand[1]} [query]: Pengaturan Rss (Hanya Pemilik & Sudo).
/{BotCommands.CancelMirror}: Membatalkan tugas dengan gid atau membalas.
/{BotCommands.CancelAllCommand} [query]: Membatalkan semua tugas [status].
/{BotCommands.ListCommand} [query]: Telusuri di Google Drive.
/{BotCommands.SearchCommand} [query]: Mencari torrent dengan API.
/{BotCommands.StatusCommand}: Menampilkan status semua unduhan.
/{BotCommands.StatsCommand}: Menampilkan statistik mesin tempat bot dihosting.
/{BotCommands.PingCommand}: Periksa berapa lama waktu yang dibutuhkan untuk melakukan Ping pada Bot (Hanya Pemilik & Sudo).
/{BotCommands.AuthorizeCommand}: Mengotorisasi obrolan atau pengguna untuk menggunakan bot (Hanya Pemilik & Sudo).
/{BotCommands.UnAuthorizeCommand}: Membatalkan otorisasi obrolan atau pengguna untuk menggunakan bot (Hanya Pemilik & Sudo).
/{BotCommands.AuthorizedUsersCommand}: Menampilkan pengguna yang diotorisasi (Hanya Pemilik & Sudo).
/{BotCommands.AddSudoCommand}: Tambahkan pengguna sudo (Hanya Pemilik).
/{BotCommands.RmSudoCommand}: Menghapus pengguna sudo (Hanya Pemilik).
/{BotCommands.RestartCommand}: Mulai ulang dan perbarui bot (Hanya Pemilik & Sudo).
/{BotCommands.LogCommand}: Dapatkan file log bot. Berguna untuk mendapatkan laporan kerusakan (Hanya Pemilik & Sudo).
/{BotCommands.ShellCommand}: Jalankan perintah shell (Hanya Pemilik).
/{BotCommands.EvalCommand}: Jalankan Baris Kode Python | Garis (Hanya Pemilik).
/{BotCommands.ExecCommand}: Jalankan Perintah Di Exec (Hanya Pemilik).
/{BotCommands.ClearLocalsCommand}: Hapus penduduk lokal {BotCommands.EvalCommand} atau {BotCommands.ExecCommand} (Hanya Pemilik).
'''

def bot_help(update, context):
    sendMessage(help_string, context.bot, update.message)

botcmds = [

        (f'{BotCommands.MirrorCommand[0]}', 'Mirror'),
        (f'{BotCommands.ZipMirrorCommand[0]}','Mirror lalu arsip ke zip'),
        (f'{BotCommands.UnzipMirrorCommand[0]}','Mirror dan ekstrak file'),
        (f'{BotCommands.QbMirrorCommand[0]}','Mirror torrent menggunakan qBittorrent'),
        (f'{BotCommands.QbZipMirrorCommand[0]}','Mirror torrent menggunakan qBittorrent dan arsip ke zip'),
        (f'{BotCommands.QbUnzipMirrorCommand[0]}','Mirror torrent menggunakan qBittorrent dan ekstrak file'),
        (f'{BotCommands.YtdlCommand[0]}','Mirror YouTube link'),
        (f'{BotCommands.YtdlZipCommand[0]}','Mirror YouTube link lalu arsip ke zip'),
        (f'{BotCommands.LeechCommand[0]}','Upload file ke telegram'),
        (f'{BotCommands.ZipLeechCommand[0]}','Arsip file ke zip lalu Upload ke telegram'),
        (f'{BotCommands.UnzipLeechCommand[0]}','Ekstrak file lalu Upload file ke telegram'),
        (f'{BotCommands.QbLeechCommand[0]}','Upload torrent ke telegram menggunakan qBittorrent'),
        (f'{BotCommands.QbZipLeechCommand[0]}','Arsip torrent ke zip lalu Upload ke telegram menggunakan qBittorrent'),
        (f'{BotCommands.QbUnzipLeechCommand[0]}','Ekstrak torrent lalu Upload ke telegram menggunakan qBittorrent'),
        (f'{BotCommands.YtdlLeechCommand[0]}','Upload YouTube video ke telegram'),
        (f'{BotCommands.YtdlZipLeechCommand[0]}','Arsip ke zip YouTube video lalu upload ke telegram'),
        (f'{BotCommands.CloneCommand}','Copy file/folder to Drive'),
        (f'{BotCommands.CountCommand}','Menghitung file/folder dari Drive'),
        (f'{BotCommands.DeleteCommand}','Menghapus file/folder dari Drive'),
        (f'{BotCommands.CancelMirror}','Cancel sebuah task'),
        (f'{BotCommands.CancelAllCommand}','Cancel semua downloading tasks'),
        (f'{BotCommands.LeechSetCommand}','Leech settings'),
        (f'{BotCommands.SetThumbCommand}','Set Leech thumbnail'),
        (f'{BotCommands.ListCommand}', 'Mencari file yang sudah ada di Drive'),
        (f'{BotCommands.StatusCommand}','Menampilkan status mirror'),
        (f'{BotCommands.StatsCommand}','Statistik penggunaan bot'),
        (f'{BotCommands.PingCommand}','Ping bot'),
        (f'{BotCommands.HelpCommand}','Mendapatkan detail perintah bot')
    ]

def main():
    bot.set_my_commands(botcmds)
    start_cleanup()
    notifier_dict = False
    if INCOMPLETE_TASK_NOTIFIER and DB_URI is not None:
        if notifier_dict := DbManger().get_incomplete_tasks():
            for cid, data in notifier_dict.items():
                if ospath.isfile(".restartmsg"):
                    with open(".restartmsg") as f:
                        chat_id, msg_id = map(int, f)
                    msg = '♻️ <b>Restarted successfully!</b>'
                else:
                    msg = '♻️ <b>Bot Restarted!</b>'
                for tag, links in data.items():
                    msg += f"\n\n⚠️ {tag} <b>{len(links)} Proses mirror kamu dibatalkan</b>"
                    for index, link in enumerate(links, start=1):
                        msg += f"\n📍 <a href='{link}'><u>Proses ke {index}</u></a>"
                        if len(msg.encode()) > 4000:
                            if '♻️ <b>Restarted successfully!</b>' in msg and cid == chat_id:
                                bot.editMessageText(msg, chat_id, msg_id, parse_mode='HTMl', disable_web_page_preview=True)
                                osremove(".restartmsg")
                            else:
                                try:
                                    bot.sendMessage(cid, msg, 'HTML', disable_web_page_preview=True)
                                except Exception as e:
                                    LOGGER.error(e)
                            msg = ''
                if '♻️ <b>Restarted successfully!</b>' in msg and cid == chat_id:
                    bot.editMessageText(msg, chat_id, msg_id, parse_mode='HTMl', disable_web_page_preview=True)
                    osremove(".restartmsg")
                else:
                    try:
                        bot.sendMessage(cid, msg, 'HTML', disable_web_page_preview=True)
                    except Exception as e:
                        LOGGER.error(e)

    if ospath.isfile(".restartmsg"):
        with open(".restartmsg") as f:
            chat_id, msg_id = map(int, f)
        bot.editMessageText("♻️ <b>Restarted successfully!</b>", chat_id, msg_id, parse_mode='HTMl', disable_web_page_preview=True)
        osremove(".restartmsg")

    start_handler = CommandHandler(BotCommands.StartCommand, start, run_async=True)
    ping_handler = CommandHandler(BotCommands.PingCommand, ping,
                                  filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
    restart_handler = CommandHandler(BotCommands.RestartCommand, restart,
                                     filters=CustomFilters.owner_filter | CustomFilters.sudo_user, run_async=True)
    help_handler = CommandHandler(BotCommands.HelpCommand,
                                  bot_help, filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
    stats_handler = CommandHandler(BotCommands.StatsCommand,
                                   stats, filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
    log_handler = CommandHandler(BotCommands.LogCommand, log, filters=CustomFilters.owner_filter | CustomFilters.sudo_user, run_async=True)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(ping_handler)
    dispatcher.add_handler(restart_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(stats_handler)
    dispatcher.add_handler(log_handler)
    updater.start_polling(drop_pending_updates=IGNORE_PENDING_REQUESTS)
    LOGGER.info("Bot Started!")
    signal(SIGINT, exit_clean_up)

app.start()
main()

main_loop.run_forever()
