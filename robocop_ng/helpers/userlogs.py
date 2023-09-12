import json
import os
import time

from robocop_ng.helpers.notifications import report_critical_error

userlog_event_types = {
    "warns": "Warn",
    "bans": "Ban",
    "kicks": "Kick",
    "mutes": "Mute",
    "notes": "Note",
}


def get_userlog_path(bot):
    return os.path.join(bot.state_dir, "data/userlog.json")


def get_userlog(bot):
    if os.path.isfile(get_userlog_path(bot)):
        with open(get_userlog_path(bot), "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError as e:
                content = f.read()
                report_critical_error(
                    bot,
                    e,
                    additional_info={
                        "file": {"length": len(content), "content": content}
                    },
                )
    return {}


def set_userlog(bot, contents):
    with open(get_userlog_path(bot), "w") as f:
        f.write(contents)


def fill_userlog(bot, userid, uname):
    userlogs = get_userlog(bot)
    uid = str(userid)
    if uid not in userlogs:
        userlogs[uid] = {
            "warns": [],
            "mutes": [],
            "kicks": [],
            "bans": [],
            "notes": [],
            "watch": False,
            "name": "n/a",
        }
    if uname:
        userlogs[uid]["name"] = uname

    return userlogs, uid


def userlog(bot, uid, issuer, reason, event_type, uname: str = ""):
    userlogs, uid = fill_userlog(bot, uid, uname)

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    log_data = {
        "issuer_id": issuer.id,
        "issuer_name": f"{issuer}",
        "reason": reason,
        "timestamp": timestamp,
    }
    if event_type not in userlogs[uid]:
        userlogs[uid][event_type] = []
    userlogs[uid][event_type].append(log_data)
    set_userlog(bot, json.dumps(userlogs))
    return len(userlogs[uid][event_type])


def setwatch(bot, uid, issuer, watch_state, uname: str = ""):
    userlogs, uid = fill_userlog(bot, uid, uname)

    userlogs[uid]["watch"] = watch_state
    set_userlog(bot, json.dumps(userlogs))
    return
