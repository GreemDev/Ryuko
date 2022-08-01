import logging
import re

import aiohttp
import config
from discord import Colour, Embed
from discord.ext.commands import Cog

logging.basicConfig(
    format="%(asctime)s (%(levelname)s) %(message)s (Line %(lineno)d)",
    level=logging.INFO,
)


class LogFileReader(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot_log_allowed_channels = config.bot_log_allowed_channels
        self.ryujinx_blue = Colour(0x4A90E2)
        self.uploaded_log_info = []

    async def download_file(self, log_url):
        async with aiohttp.ClientSession() as session:
            # Grabs first and last few bytes of log file to prevent abuse from large files
            headers = {"Range": "bytes=0-35000, -6000"}
            async with session.get(log_url, headers=headers) as response:
                return await response.text("UTF-8")

    async def log_file_read(self, message):
        self.embed = {
            "hardware_info": {
                "cpu": "Unknown",
                "gpu": "Unknown",
                "ram": "Unknown",
                "os": "Unknown",
            },
            "emu_info": {
                "ryu_version": "Unknown",
                "ryu_firmware": "Unknown",
                "logs_enabled": None,
            },
            "game_info": {
                "game_name": "Unknown",
                "errors": "No errors found in log",
                "mods": "No mods found",
                "notes": [],
            },
            "settings": {
                "audio_backend": "Unknown",
                "backend_threading": "Unknown",
                "docked": "Unknown",
                "expand_ram": "Unknown",
                "fs_integrity": "Unknown",
                "graphics_backend": "Unknown",
                "ignore_missing_services": "Unknown",
                "memory_manager": "Unknown",
                "pptc": "Unknown",
                "shader_cache": "Unknown",
                "vsync": "Unknown",
                "resolution_scale": "Unknown",
                "anisotropic_filtering": "Unknown",
                "aspect_ratio": "Unknown",
            },
        }
        attached_log = message.attachments[0]
        author_name = f"@{message.author.name}"
        log_file = await self.download_file(attached_log.url)
        # Large files show a header value when not downloaded completely
        # this regex makes sure that the log text to read starts from the first timestamp, ignoring headers
        log_file_header_regex = re.compile(r"\d{2}:\d{2}:\d{2}\.\d{3}.*", re.DOTALL)
        log_file = re.search(log_file_header_regex, log_file).group(0)

        def get_hardware_info(log_file=log_file):
            for setting in self.embed["hardware_info"]:
                try:
                    if setting == "cpu":
                        self.embed["hardware_info"][setting] = (
                            re.search(r"CPU:\s([^;\n\r]*)", log_file, re.MULTILINE)
                            .group(1)
                            .rstrip()
                        )
                    if setting == "ram":
                        self.embed["hardware_info"][setting] = (
                            re.search(
                                r"RAM:(\sTotal)?\s([^;\n\r]*)", log_file, re.MULTILINE
                            )
                            .group(2)
                            .rstrip()
                        )
                    if setting == "os":
                        self.embed["hardware_info"][setting] = (
                            re.search(
                                r"Operating System:\s([^;\n\r]*)",
                                log_file,
                                re.MULTILINE,
                            )
                            .group(1)
                            .rstrip()
                        )
                    if setting == "gpu":
                        self.embed["hardware_info"][setting] = (
                            re.search(
                                r"PrintGpuInformation:\s([^;\n\r]*)",
                                log_file,
                                re.MULTILINE,
                            )
                            .group(1)
                            .rstrip()
                        )
                except AttributeError:
                    continue

        def get_ryujinx_info(log_file=log_file):
            for setting in self.embed["emu_info"]:
                try:
                    if setting == "ryu_version":
                        self.embed["emu_info"][setting] = [
                            line.split()[-1]
                            for line in log_file.splitlines()
                            if "Ryujinx Version:" in line
                        ][0]
                    if setting == "logs_enabled":
                        self.embed["emu_info"][setting] = (
                            re.search(
                                r"Logs Enabled:\s([^;\n\r]*)", log_file, re.MULTILINE
                            )
                            .group(1)
                            .rstrip()
                        )
                    if setting == "ryu_firmware":
                        self.embed["emu_info"]["ryu_firmware"] = [
                            line.split()[-1]
                            for line in log_file.splitlines()
                            if "Firmware Version:" in line
                        ][0]
                except (AttributeError, IndexError):
                    continue

        def format_log_embed():
            cleaned_game_name = re.sub(
                r"\s\[(64|32)-bit\]$", "", self.embed["game_info"]["game_name"]
            )
            self.embed["game_info"]["game_name"] = cleaned_game_name

            hardware_info = " | ".join(
                (
                    f"**CPU:** {self.embed['hardware_info']['cpu']}",
                    f"**GPU:** {self.embed['hardware_info']['gpu']}",
                    f"**RAM:** {self.embed['hardware_info']['ram']}",
                    f"**OS:** {self.embed['hardware_info']['os']}",
                )
            )

            system_settings_info = "\n".join(
                (
                    f"**Audio Backend:** `{self.embed['settings']['audio_backend']}`",
                    f"**Console Mode:** `{self.embed['settings']['docked']}`",
                    f"**PPTC Cache:** `{self.embed['settings']['pptc']}`",
                    f"**Shader Cache:** `{self.embed['settings']['shader_cache']}`",
                    f"**V-Sync:** `{self.embed['settings']['vsync']}`",
                )
            )

            graphics_settings_info = "\n".join(
                (
                    f"**Graphics Backend:** `{self.embed['settings']['graphics_backend']}`",
                    f"**Resolution:** `{self.embed['settings']['resolution_scale']}`",
                    f"**Anisotropic Filtering:** `{self.embed['settings']['anisotropic_filtering']}`",
                    f"**Aspect Ratio:** `{self.embed['settings']['aspect_ratio']}`",
                )
            )

            ryujinx_info = " | ".join(
                (
                    f"**Version:** {self.embed['emu_info']['ryu_version']}",
                    f"**Firmware:** {self.embed['emu_info']['ryu_firmware']}",
                )
            )

            log_embed = Embed(title=f"{cleaned_game_name}", colour=self.ryujinx_blue)
            log_embed.set_footer(text=f"Log uploaded by {author_name}")
            log_embed.add_field(
                name="General Info",
                value=" | ".join((ryujinx_info, hardware_info)),
                inline=False,
            )
            log_embed.add_field(
                name="System Settings",
                value=system_settings_info,
                inline=True,
            )
            log_embed.add_field(
                name="Graphics Settings",
                value=graphics_settings_info,
                inline=True,
            )
            if (
                cleaned_game_name == "Unknown"
                and self.embed["game_info"]["errors"] == "No errors found in log"
            ):
                log_embed.add_field(
                    name="Empty Log",
                    value=f"""The log file appears to be empty. To get a proper log, follow these steps:
1) In Logging settings, ensure `Enable Logging to File` is checked.
2) Ensure the following default logs are enabled: `Info`, `Warning`, `Error`, `Guest` and `Stub`.
3) Start a game up.
4) Play until your issue occurs.
5) Upload the latest log file which is larger than 2KB.""",
                    inline=False,
                )
            if (
                cleaned_game_name == "Unknown"
                and self.embed["game_info"]["errors"] != "No errors found in log"
            ):
                log_embed.add_field(
                    name="Latest Error Snippet",
                    value=self.embed["game_info"]["errors"],
                    inline=False,
                )
                log_embed.add_field(
                    name="No Game Boot Detected",
                    value=f"""No game boot has been detected in log file. To get a proper log, follow these steps:
1) In Logging settings, ensure `Enable Logging to File` is checked.
2) Ensure the following default logs are enabled: `Info`, `Warning`, `Error`, `Guest` and `Stub`.
3) Start a game up.
4) Play until your issue occurs.
5) Upload the latest log file which is larger than 2KB.""",
                    inline=False,
                )
            else:
                log_embed.add_field(
                    name="Latest Error Snippet",
                    value=self.embed["game_info"]["errors"],
                    inline=False,
                )
                log_embed.add_field(
                    name="Mods", value=self.embed["game_info"]["mods"], inline=False
                )

            try:
                notes_value = "\n".join(game_notes)
            except TypeError:
                notes_value = "Nothing to note"
            log_embed.add_field(
                name="Notes",
                value=notes_value,
                inline=False,
            )

            return log_embed

        def analyse_log(log_file=log_file):
            try:
                for setting_name in self.embed["settings"]:
                    # Some log info may be missing for users that use older versions of Ryujinx, so reading the settings is not always possible.
                    # As settings are initialized with "Unknown" values, False should not be an issue for setting.get()
                    def get_setting(name, setting_string, log_file=log_file):
                        setting = self.embed["settings"]
                        setting_value = [
                            line.split()[-1]
                            for line in log_file.splitlines()
                            if re.search(fr"LogValueChange: ({setting_string})\s", line)
                        ][-1]
                        if setting_value and setting.get(name):
                            setting[name] = setting_value
                            if name == "docked":
                                setting[
                                    name
                                ] = f"{'Docked' if setting_value == 'True' else 'Handheld'}"
                            if name == "resolution_scale":
                                resolution_map = {
                                    "-1": "Custom",
                                    "1": "Native (720p/1080p)",
                                    "2": "2x (1440p/2160p)",
                                    "3": "3x (2160p/3240p)",
                                    "4": "4x (2880p/4320p)",
                                }
                                setting[name] = resolution_map[setting_value]
                            if name == "anisotropic_filtering":
                                anisotropic_map = {
                                    "-1": "Auto",
                                    "2": "2x",
                                    "4": "4x",
                                    "8": "8x",
                                    "16": "16x",
                                }
                                setting[name] = anisotropic_map[setting_value]
                            if name == "aspect_ratio":
                                aspect_map = {
                                    "Fixed4x3": "4:3",
                                    "Fixed16x9": "16:9",
                                    "Fixed16x10": "16:10",
                                    "Fixed21x9": "21:9",
                                    "Fixed32x9": "32:9",
                                    "Stretched": "Stretch to Fit Window",
                                }
                                setting[name] = aspect_map[setting_value]
                            if name in [
                                "pptc",
                                "shader_cache",
                                "vsync",
                            ]:
                                setting[
                                    name
                                ] = f"{'Enabled' if setting_value == 'True' else 'Disabled'}"
                        return setting[name]

                    setting_map = {
                        "anisotropic_filtering": "MaxAnisotropy",
                        "aspect_ratio": "AspectRatio",
                        "audio_backend": "AudioBackend",
                        "backend_threading": "BackendThreading",
                        "docked": "EnableDockedMode",
                        "expand_ram": "ExpandRam",
                        "fs_integrity": "EnableFsIntegrityChecks",
                        "graphics_backend": "GraphicsBackend",
                        "ignore_missing_services": "IgnoreMissingServices",
                        "memory_manager": "MemoryManagerMode",
                        "pptc": "EnablePtc",
                        "resolution_scale": "ResScale",
                        "shader_cache": "EnableShaderCache",
                        "vsync": "EnableVsync",
                    }
                    try:
                        self.embed[setting_name] = get_setting(
                            setting_name, setting_map[setting_name], log_file=log_file
                        )
                    except (AttributeError, IndexError) as error:
                        logging.info(
                            f"Settings exception: {setting_name}: {type(error).__name__}"
                        )
                        continue

                def analyse_error_message(log_file=log_file):
                    try:
                        errors = []
                        curr_error_lines = []
                        for line in log_file.splitlines():
                            if line == "":
                                continue
                            if "|E|" in line:
                                curr_error_lines = [line]
                                errors.append(curr_error_lines)
                            elif line[0] == " " or line == "":
                                curr_error_lines.append(line)

                        def error_search(search_terms):
                            for term in search_terms:
                                for error_lines in errors:
                                    line = "\n".join(error_lines)
                                    if term in line:
                                        return True

                            return False

                        shader_cache_collision = error_search(["Cache collision found"])
                        dump_hash_warning = error_search(
                            [
                                "ResultFsInvalidIvfcHash",
                                "ResultFsNonRealDataVerificationFailed",
                            ]
                        )
                        shader_cache_corruption = error_search(
                            [
                                "Ryujinx.Graphics.Gpu.Shader.ShaderCache.Initialize()",
                                "System.IO.InvalidDataException: End of Central Directory record could not be found",
                                "ICSharpCode.SharpZipLib.Zip.ZipException: Cannot find central directory",
                            ]
                        )
                        update_keys_error = error_search(["MissingKeyException"])
                        file_permissions_error = error_search(
                            ["ResultFsPermissionDenied"]
                        )
                        file_not_found_error = error_search(["ResultFsTargetNotFound"])
                        missing_services_error = error_search(
                            ["ServiceNotImplementedException"]
                        )

                        last_errors = "\n".join(
                            errors[-1][:2] if "|E|" in errors[-1][0] else ""
                        )
                    except IndexError:
                        last_errors = None
                    return (
                        last_errors,
                        shader_cache_collision,
                        dump_hash_warning,
                        shader_cache_corruption,
                        update_keys_error,
                        file_permissions_error,
                        file_not_found_error,
                        missing_services_error,
                    )

                # Finds the lastest error denoted by |E| in the log and its first line
                # Also warns of common issues
                (
                    last_error_snippet,
                    shader_cache_warn,
                    dump_hash_warning,
                    shader_cache_corruption_warn,
                    update_keys_error,
                    file_permissions_error,
                    file_not_found_error,
                    missing_services_error,
                ) = analyse_error_message()
                if last_error_snippet:
                    self.embed["game_info"]["errors"] = f"```{last_error_snippet}```"
                else:
                    pass
                # Game name parsed last so that user settings are visible with empty log
                try:
                    self.embed["game_info"]["game_name"] = (
                        re.search(
                            r"Loader LoadNca: Application Loaded:\s([^;\n\r]*)",
                            log_file,
                            re.MULTILINE,
                        )
                        .group(1)
                        .rstrip()
                    )
                except AttributeError:
                    pass

                if shader_cache_warn:
                    shader_cache_warn = f"⚠️ Cache collision detected. Investigate possible shader cache issues"
                    self.embed["game_info"]["notes"].append(shader_cache_warn)

                if shader_cache_corruption_warn:
                    shader_cache_corruption_warn = f"⚠️ Cache corruption detected. Investigate possible shader cache issues"
                    self.embed["game_info"]["notes"].append(
                        shader_cache_corruption_warn
                    )

                if dump_hash_warning:
                    dump_hash_warning = f"⚠️ Dump error detected. Investigate possible bad game/firmware dump issues"
                    self.embed["game_info"]["notes"].append(dump_hash_warning)

                if update_keys_error:
                    update_keys_error = (
                        f"⚠️ Keys or firmware out of date, consider updating them"
                    )
                    self.embed["game_info"]["notes"].append(update_keys_error)

                if file_permissions_error:
                    file_permissions_error = f"⚠️ File permission error. Consider deleting save directory and allowing Ryujinx to make a new one"
                    self.embed["game_info"]["notes"].append(file_permissions_error)

                if file_not_found_error:
                    file_not_found_error = f"⚠️ Save not found error. Consider starting game without a save file or using a new save file"
                    self.embed["game_info"]["notes"].append(file_not_found_error)

                if (
                    missing_services_error
                    and self.embed["settings"]["ignore_missing_services"] == "False"
                ):
                    missing_services_error = f"⚠️ Consider enabling `Ignore Missing Services` in Ryujinx settings"
                    self.embed["game_info"]["notes"].append(missing_services_error)

                timestamp_regex = re.compile(r"\d{2}:\d{2}:\d{2}\.\d{3}")
                latest_timestamp = re.findall(timestamp_regex, log_file)[-1]
                if latest_timestamp:
                    timestamp_message = f"ℹ️ Time elapsed in log: `{latest_timestamp}`"
                    self.embed["game_info"]["notes"].append(timestamp_message)

                def mods_information(log_file=log_file):
                    mods_regex = re.compile(r"Found mod\s\'(.+?)\'\s(\[.+?\])")
                    matches = re.findall(mods_regex, log_file)
                    if matches:
                        mods = [
                            {"mod": match[0], "status": match[1]} for match in matches
                        ]
                        mods_status = [
                            f"ℹ️ {i['mod']} ({'ExeFS' if i['status'] == '[E]' else 'RomFS'})"
                            for i in mods
                        ]
                        return mods_status

                game_mods = mods_information()
                if game_mods:
                    self.embed["game_info"]["mods"] = "\n".join(game_mods)
                else:
                    pass

                controllers_regex = re.compile(r"Hid Configure: ([^\r\n]+)")
                controllers = re.findall(controllers_regex, log_file)
                if controllers:
                    input_status = [f"ℹ {match}" for match in controllers]
                    # Hid Configure lines can appear multiple times, so converting to dict keys removes duplicate entries,
                    # also maintains the list order
                    input_status = list(dict.fromkeys(input_status))
                    input_string = "\n".join(input_status)
                    self.embed["game_info"]["notes"].append(input_string)
                # If emulator crashes on startup without game load, there is no need to show controller notification at all
                if (
                    not controllers
                    and self.embed["game_info"]["game_name"] != "Unknown"
                ):
                    input_string = "⚠️ No controller information found"
                    self.embed["game_info"]["notes"].append(input_string)

                try:
                    ram_available_regex = re.compile(r"Available\s(\d+)(?=\sMB)")
                    ram_available = re.search(ram_available_regex, log_file)[1]
                    if int(ram_available) < 8000:
                        ram_warning = (
                            f"⚠️ Less than 8GB RAM available ({str(ram_available)} MB)"
                        )
                        self.embed["game_info"]["notes"].append(ram_warning)
                except TypeError:
                    pass

                if "Darwin" in self.embed["hardware_info"]["os"]:
                    mac_os_warning = "**❌ macOS is currently unsupported**"
                    self.embed["game_info"]["notes"].append(mac_os_warning)

                if "Intel" in self.embed["hardware_info"]["gpu"]:
                    if (
                        "Darwin" in self.embed["hardware_info"]["os"]
                        or "Windows" in self.embed["hardware_info"]["os"]
                    ):
                        intel_gpu_warning = "**⚠️ Intel iGPUs are known to have driver issues, consider using a discrete GPU**"
                        self.embed["game_info"]["notes"].append(intel_gpu_warning)
                try:
                    default_logs = ["Info", "Warning", "Error", "Guest", "Stub"]
                    user_logs = (
                        self.embed["emu_info"]["logs_enabled"]
                        .rstrip()
                        .replace(" ", "")
                        .split(",")
                    )
                    if "Debug" in user_logs:
                        debug_warning = f"⚠️ **Debug logs enabled will have a negative impact on performance**"
                        self.embed["game_info"]["notes"].append(debug_warning)
                    disabled_logs = set(default_logs).difference(set(user_logs))
                    if disabled_logs:
                        logs_status = [
                            f"⚠️ {log} log is not enabled" for log in disabled_logs
                        ]
                        log_string = "\n".join(logs_status)
                    else:
                        log_string = "✅ Default logs enabled"
                    self.embed["game_info"]["notes"].append(log_string)
                except AttributeError:
                    pass

                if self.embed["emu_info"]["ryu_firmware"] == "Unknown":
                    firmware_warning = f"**❌ Nintendo Switch firmware not found**"
                    self.embed["game_info"]["notes"].append(firmware_warning)

                if self.embed["settings"]["anisotropic_filtering"] not in [
                    "Auto",
                    "Unknown",
                ]:
                    anisotropic_filtering_warning = "⚠️ Anisotropic filtering not set to `Auto` can cause graphical issues"
                    self.embed["game_info"]["notes"].append(
                        anisotropic_filtering_warning
                    )

                if self.embed["settings"]["audio_backend"] == "Dummy":
                    dummy_warning = (
                        f"⚠️ Dummy audio backend, consider changing to SDL2 or OpenAL"
                    )
                    self.embed["game_info"]["notes"].append(dummy_warning)

                if self.embed["settings"]["pptc"] == "Disabled":
                    pptc_warning = f"🔴 **PPTC cache should be enabled**"
                    self.embed["game_info"]["notes"].append(pptc_warning)

                if self.embed["settings"]["shader_cache"] == "Disabled":
                    shader_warning = f"🔴 **Shader cache should be enabled**"
                    self.embed["game_info"]["notes"].append(shader_warning)

                if self.embed["settings"]["expand_ram"] == "True":
                    expand_ram_warning = f"⚠️ `Expand DRAM size to 6GB` should only be enabled for 4K mods"
                    self.embed["game_info"]["notes"].append(expand_ram_warning)

                if self.embed["settings"]["memory_manager"] == "SoftwarePageTable":
                    software_memory_manager_warning = "🔴 **`Software` setting in Memory Manager Mode will give slower performance than the default setting of `Host unchecked`**"
                    self.embed["game_info"]["notes"].append(
                        software_memory_manager_warning
                    )

                if self.embed["settings"]["ignore_missing_services"] == "True":
                    ignore_missing_services_warning = "⚠️ `Ignore Missing Services` being enabled can cause instability"
                    self.embed["game_info"]["notes"].append(
                        ignore_missing_services_warning
                    )

                if self.embed["settings"]["vsync"] == "Disabled":
                    vsync_warning = f"⚠️ V-Sync disabled can cause instability like games running faster than intended or longer load times"
                    self.embed["game_info"]["notes"].append(vsync_warning)

                if self.embed["settings"]["fs_integrity"] == "Disabled":
                    fs_integrity_warning = f"⚠️ Disabling file integrity checks may cause corrupted dumps to not be detected"
                    self.embed["game_info"]["notes"].append(fs_integrity_warning)

                if self.embed["settings"]["backend_threading"] == "Off":
                    backend_threading_warning = (
                        f"🔴 **Graphics Backend Multithreading should be set to `Auto`**"
                    )
                    self.embed["game_info"]["notes"].append(backend_threading_warning)

                mainline_version = re.compile(r"^\d\.\d\.\d+$")
                old_mainline_version = re.compile(r"^\d\.\d\.(\d){4}$")
                pr_version = re.compile(r"^\d\.\d\.\d\+([a-f]|\d){7}$")
                ldn_version = re.compile(r"^\d\.\d\.\d\-ldn\d\.\d$")

                if (
                    message.channel.id == config.bot_log_allowed_channels["support"]
                    or message.channel.id
                    == config.bot_log_allowed_channels["patreon-support"]
                    or message.channel.id
                    == config.bot_log_allowed_channels["linux-master-race"]
                ):
                    if re.match(pr_version, self.embed["emu_info"]["ryu_version"]):
                        pr_version_warning = f"**⚠️ PR build logs should be posted in <#{config.bot_log_allowed_channels['pr-testing']}>**"
                        self.embed["game_info"]["notes"].append(pr_version_warning)

                    if re.match(
                        old_mainline_version, self.embed["emu_info"]["ryu_version"]
                    ):
                        old_mainline_version_warning = f"**🔴 Old Ryujinx version, please re-download from the Ryujinx website as auto-updates will not work on this version**"
                        self.embed["game_info"]["notes"].append(
                            old_mainline_version_warning
                        )

                    if not (
                        re.match(
                            mainline_version, self.embed["emu_info"]["ryu_version"]
                        )
                        or re.match(
                            old_mainline_version, self.embed["emu_info"]["ryu_version"]
                        )
                        or re.match(ldn_version, self.embed["emu_info"]["ryu_version"])
                        or re.match(pr_version, self.embed["emu_info"]["ryu_version"])
                        or re.match("Unknown", self.embed["emu_info"]["ryu_version"])
                    ):
                        custom_build_warning = (
                            "**⚠️ Custom builds are not officially supported**"
                        )
                        self.embed["game_info"]["notes"].append(custom_build_warning)

                def severity(log_note_string):
                    symbols = ["❌", "🔴", "⚠️", "ℹ", "✅"]
                    return next(
                        i
                        for i, symbol in enumerate(symbols)
                        if symbol in log_note_string
                    )

                game_notes = [note for note in self.embed["game_info"]["notes"]]
                # Warnings split on the string after the warning symbol for alphabetical ordering
                # Severity key then orders alphabetically sorted warnings to show most severe first
                ordered_game_notes = sorted(
                    sorted(game_notes, key=lambda x: x.split()[1]), key=severity
                )
                return ordered_game_notes
            except AttributeError:
                pass

        get_hardware_info()
        get_ryujinx_info()
        game_notes = analyse_log()

        return format_log_embed()

    @Cog.listener()
    async def on_message(self, message):
        await self.bot.wait_until_ready()
        if message.author.bot:
            return
        try:
            author_id = message.author.id
            author_mention = message.author.mention
            filename = message.attachments[0].filename
            filesize = message.attachments[0].size
            # Any message over 2000 chars is uploaded as message.txt, so this is accounted for
            ryujinx_log_file_regex = re.compile(r"^Ryujinx_.*\.log|message\.txt$")
            log_file = re.compile(r"^.*\.log|.*\.txt$")
            log_file_link = message.jump_url
            is_ryujinx_log_file = re.match(ryujinx_log_file_regex, filename)
            is_log_file = re.match(log_file, filename)

            if (
                message.channel.id in self.bot_log_allowed_channels.values()
                and is_ryujinx_log_file
            ):
                uploaded_logs_exist = [
                    True for elem in self.uploaded_log_info if filename in elem.values()
                ]
                if not any(uploaded_logs_exist):
                    reply_message = await message.channel.send(
                        "Log detected, parsing..."
                    )
                    try:
                        embed = await self.log_file_read(message)
                        if "Ryujinx_" in filename:
                            self.uploaded_log_info.append(
                                {
                                    "filename": filename,
                                    "file_size": filesize,
                                    "link": log_file_link,
                                    "author": author_id,
                                }
                            )
                            # Avoid duplicate log file analysis, at least temporarily; keep track of the last few filenames of uploaded logs
                            # this should help support channels not be flooded with too many log files
                            # fmt: off
                            self.uploaded_log_info = self.uploaded_log_info[-5:]
                            # fmt: on
                        return await reply_message.edit(content=None, embed=embed)
                    except UnicodeDecodeError:
                        return await message.channel.send(
                            content=author_mention,
                            embed=Embed(
                                description=f"This log file appears to be invalid. Please re-check and re-upload your log file.",
                                colour=self.ryujinx_blue,
                            ),
                        )
                    except Exception as error:
                        await reply_message.edit(
                            content=f"Error: Couldn't parse log; parser threw `{type(error).__name__}` exception."
                        )
                        print(logging.warn(error))
                else:
                    duplicate_log_file = next(
                        (
                            elem
                            for elem in self.uploaded_log_info
                            if elem["filename"] == filename
                            and elem["file_size"] == filesize
                            and elem["author"] == author_id
                        ),
                        None,
                    )
                    await message.channel.send(
                        content=author_mention,
                        embed=Embed(
                            description=f"The log file `{filename}` appears to be a duplicate [already uploaded here]({duplicate_log_file['link']}). Please upload a more recent file.",
                            colour=self.ryujinx_blue,
                        ),
                    )
            elif (
                is_log_file
                and not is_ryujinx_log_file
                and message.channel.id in self.bot_log_allowed_channels.values()
            ):
                return await message.channel.send(
                    content=author_mention,
                    embed=Embed(
                        description=f"Your file does not match the Ryujinx log format. Please check your file.",
                        colour=self.ryujinx_blue,
                    ),
                )
            elif (
                is_log_file
                and not message.channel.id in self.bot_log_allowed_channels.values()
            ):
                return await message.author.send(
                    content=author_mention,
                    embed=Embed(
                        description="\n".join(
                            (
                                f"Please upload Ryujinx log files to the correct location:\n",
                                f'<#{config.bot_log_allowed_channels["support"]}>: General help and troubleshooting',
                                f'<#{config.bot_log_allowed_channels["patreon-support"]}>: Help and troubleshooting for Patreon subscribers',
                                f'<#{config.bot_log_allowed_channels["development"]}>: Ryujinx development discussion',
                                f'<#{config.bot_log_allowed_channels["pr-testing"]}>: Discussion of in-progress pull request builds',
                                f'<#{config.bot_log_allowed_channels["linux-master-race"]}>: Linux support and discussion',
                            )
                        ),
                        colour=self.ryujinx_blue,
                    ),
                )
        except IndexError:
            pass


def setup(bot):
    bot.add_cog(LogFileReader(bot))
