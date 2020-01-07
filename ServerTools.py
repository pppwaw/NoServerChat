import json
import logging
import random
import asyncio
import time


class BaseTools:
    def __init__(self, logger: logging.Logger = logging.getLogger(__name__)):
        self.super = ["pppwaw"]
        self.func = []
        self.logger = logger

    async def serve(self, message: dict, name: str) -> (bool, str):
        message["name"] = name
        kwargs = {}
        if "action" in message:
            if message["action"] not in self.func and name not in self.super:
                return False, "Permission denied"
            if not hasattr(self, (message["action"])):
                return False, "Error action"
            else:
                call = getattr(self, message["action"])
            del message["action"]
            for i in message.keys():
                kwargs[i] = message[i]
            try:
                r = await call(**kwargs)
            except Exception as e:
                return False, repr(e)
            else:
                return r[0], r[1:]

        else:
            return False, "No action"


class ClientTools(BaseTools):
    def __init__(self, user_table: str, logger: logging.Logger = logging.getLogger("Client")):
        """
        初始化tools，从user.json加载用户表，需要一个logger来打印信息

        :param logger:
        :param user_table:用户表的名称
        """
        super().__init__(logger)
        self.stools = None
        self.user_table = user_table
        with open(user_table) as f:
            try:
                d = json.loads(f.read())
            except Exception:
                self.user_table_broken = True
                self.logger.warning("Cannot load users.Please check the user table.Will not save the user table")
                d = {}
            else:
                self.user_table_broken = False
            finally:
                self.user = d
                logger.debug(self.user)
        self.func.append("send")
        self.session = {}
        self.session_id = {}
        self.queues = {}

    def set_stools(self, stools):
        self.stools = stools

    async def login(self, username, password) -> (bool, str):
        """
        登录，返回成功与否，若成功会返回session_id，若失败会返回原因

        :param username: 用户名
        :param password: 密码
        :return: session_id或原因
        """
        if username in self.user:
            user = self.user[username]
            if user["password"] == password:
                session_id = await self._generate_session_id()
                self.session_id[session_id] = username
                if username not in self.session:
                    self.session[username] = []
                self.session[username].append(session_id)
                if username not in self.queues:
                    self.queues[username] = asyncio.Queue()
                return True, session_id
            return False, "Invalid password"
        return False, "Invalid username"

    async def logout(self, session_id: str, name: str = None) -> (bool, str):
        """
        登出，返回成功与否，若成功会返回特定字符串break，若失败会返回原因（目前只有无session）

        :param session_id:
        :return: 原因或break
        """
        if session_id in self.session:
            self.session[self.session_id[session_id]].remove(session_id)
            return True, "break"
        return False, "No session"

    async def add_user(self, username: str, password: str, name: str = None) -> (bool, str):
        """
        在用户表中新增用户

        :param name:
        :param username: 用户名
        :param password: 密码
        :return: 成功与否，若成功会返回用户信息(json)，失败会返回原因
        """
        if username not in self.user:
            a = {"password": password}
            self.user[username] = a
            await self.save()
            return True, json.dumps(a)
        return False, "User already exist"

    async def save(self, name: str = None) -> (bool, str):
        """
        保存用户表（目前到user.json）

        :return: 是否保存成功，若没保存成功会有原因（若用户表加载失败为保险起见则不可保存）
        """
        try:
            if not self.user_table_broken:
                with open(self.user_table, "w") as f:
                    f.write(json.dumps(self.user))
                    return True, ""
            return False, "User table is broken"
        except Exception as e:
            return False, e

    async def _generate_session_id(self, name: str = None) -> str:
        """
        不要在外部调用！

        :return: 生成的session_id
        """
        while True:
            r = str(random.randint(0000000000, 9999999999)).zfill(10)
            if r not in self.session_id:
                return r

    async def send(self, message: list, name: str) -> (bool, str):
        """
        把消息发送给（暂时为所有人）
        格式为[{"action":"text","data":"message"},...]

        :param message: 发送的消息
        :return:  发送的人数
        """
        if not isinstance(message, list):
            return False, "message not list"

        m = {"name": name, "message": message}
        x = 0
        for i, j in self.queues.items():
            if i == name:
                continue
            try:
                await j.put(m)

            except Exception as e:
                self.logger.error(repr(e))
            else:
                x += 1
        return True, str(x)


def makertn(sync_id, message, **kwargs):
    mb = {'action': 'rtn', 'sync_id': sync_id, "message": message}
    return mb


class ServerTools(BaseTools):
    def __init__(self, name: str, ctools: ClientTools, logger: logging.Logger = logging.getLogger("Server")):
        super().__init__(logger)
        self.server = {}
        self.func.append("find_user")
        self.ctools = ctools
        self.name = name
        self.sync = {}

    async def join(self, name) -> (bool, str):
        if name not in self.server:
            self.server[name] = asyncio.Queue()
            return True, ""
        return False, "server exist"

    async def send(self, message: dict, servers: list = None, name: str = None) -> (bool, str):
        if name is None:
            name = self.name
        if servers is None:
            servers = self.server.keys()
        if not isinstance(message, dict):
            return False, "message not dict"
        x = 0
        for i in servers:
            try:
                await self.server[i].put(message)
            except Exception as e:
                self.logger.error(repr(e))
            else:
                x += 1
        return True, str(x)

    async def rtn(self, sync_id, message, **kwargs):
        if sync_id in self.sync:
            try:
                self.sync[sync_id].put(message)
            except:
                return False, "NoJSON"
            else:
                return True, ""
        else:
            return False, "Error sync id"

    async def _generate_sync_id(self):
        x = 0
        while True:
            if x in self.sync:
                continue
            self.sync[x] = asyncio.Queue()
            return x, self.sync[x]

    async def find_user(self, username, sync_id, name, **kwargs):
        if username in self.ctools.user:
            r = makertn(sync_id, self.ctools.user[username])

            await self.send(r, [name])
            return True, ""
        else:
            id, queue = await self._generate_sync_id()
            server = list(self.server.keys()).remove(name)
            _, i = await self.send({"action": "find_user", "username": username, "sync_id": id, **kwargs}, server
                                   )
            i = int(i)
            t = time.time()
            while i:
                try:
                    r = await queue.get_nowait()
                except:
                    pass
                else:
                    if r:
                        i -= 1
                        continue
                    else:
                        await self.ctools.add_user(username, r["password"])
                        await self.send(r, [name])
                        return True, ""
                finally:
                    if time.time() - t >= 30:
                        await self.send(makertn(sync_id, None), [name])
                        return False, "time out"
