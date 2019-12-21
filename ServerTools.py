import json
import logging
import random


class Tools:
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        with open("user.json") as f:
            try:
                d = json.loads(f.read())
            except:
                self.user_table_broken = True
                self.logger.warning("Cannot load users.Please check the user table.Will not save the user table")
                d = {}
            else:
                self.user_table_broken = False
            finally:
                self.user = d
                logger.debug(self.user)
        self.superfunc = ["adduser"]
        self.super = ["pppwaw"]
        self.session = {}
        self.session_id = []

    async def serve(self, message: dict, session_id: str):
        kwargs = {}
        if "action" in message:
            try:
                mod = eval("self." + message["action"])
            except:
                return False, "Error arg action"
            else:
                if message["action"] in self.superfunc and self.session[session_id] not in self.super:
                    return False, "Permission denied"
                del message["action"]
                for i in message:
                    kwargs[i] = message[i]
                try:
                    return True, str(await mod(**kwargs))
                except Exception as e:
                    return False, repr(e)

        else:
            return False, "No action"

    async def login(self, username, password) -> (bool, str):
        if username in self.user:
            if self.user[username]["password"] == password:
                session_id = await self._generate_session_id()
                self.session[session_id] = username
                return True, session_id
            return False, "Invalid password"
        return False, "Invalid username"

    async def logout(self, session_id: str) -> (bool, str):
        if session_id in self.session:
            del self.session[session_id]
            return True, "break"
        return False, "No session"

    async def adduser(self, username: str, password: str):
        a = {"password": password}
        self.user[username] = a

    async def save(self) -> bool:
        if not self.user_table_broken:
            with open("user.json", "w") as f:
                f.write(json.dumps(self.user))
                return True
        return False

    async def _generate_session_id(self) -> str:
        while True:
            r = str(random.randint(0000000000, 9999999999)).zfill(10)
            if r not in self.session_id:
                return r
