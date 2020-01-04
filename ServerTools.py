import json
import logging
import random
import asyncio


class ClientTools:
    def __init__(self, logger: logging.Logger, user_table: str):
        """
        初始化tools，从user.json加载用户表，需要一个logger来打印信息

        :param logger:
        :param user_table:用户表的名称
        """
        self.logger = logger
        self.user_table = user_table
        with open(user_table) as f:
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
        self.func = ["send"]
        self.super = ["pppwaw"]
        self.session = {}
        self.session_id = []
        self.queues = {}

    async def serve(self, message: dict) -> (bool, str):
        """
        对用户发来的信息进行处理，返回失败与否，若成功会返回结果，若失败会反悔原因

        :param message:
        :return: 失败与否，若成功会返回结果，若失败会返回原因
        """
        global call
        kwargs = {}
        if "action" in message:
            if message["action"] not in self.func and self.session[message["session_id"]] not in self.super:
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
                return True, r

        else:
            return False, "No action"

    async def login(self, username, password) -> (bool, str):
        """
        登录，返回成功与否，若成功会返回session_id，若失败会返回原因

        :param username: 用户名
        :param password: 密码
        :return: session_id或原因
        """
        if username in self.user:
            if self.user[username]["password"] == password:
                session_id = await self._generate_session_id()
                self.session_id.append(session_id)
                self.session[session_id] = username
                self.queues[session_id] = asyncio.Queue()
                return True, session_id
            return False, "Invalid password"
        return False, "Invalid username"

    async def logout(self, session_id: str) -> (bool, str):
        """
        登出，返回成功与否，若成功会返回特定字符串break，若失败会返回原因（目前只有无session）

        :param session_id:
        :return: 原因或break
        """
        if session_id in self.session:
            del self.session[session_id]
            self.session_id.remove(session_id)
            del self.queues[session_id]
            return True, "break"
        return False, "No session"

    async def adduser(self, username: str, password: str, session_id: str = None) -> (bool, str):
        """
        在用户表中新增用户

        :param username: 用户名
        :param password: 密码
        :return: 成功与否，若成功会返回用户信息(json)，失败会返回原因
        """
        if username not in self.user:
            a = {"password": password}
            self.user[username] = a
            return True, json.dumps(a)
        return False, "User already exist"

    async def save(self, session_id: str = None) -> (bool, str):
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

    async def _generate_session_id(self) -> str:
        """

        不要在外部调用！
        :return: 生成的session_id
        """
        while True:
            r = str(random.randint(0000000000, 9999999999)).zfill(10)
            if r not in self.session_id:
                return r

    async def send(self, message: list, session_id: str) -> (bool, str):
        """
        把消息发送给（暂时为所有人）
        格式为[{"action":"text","data":"message"},...]

        :param message: 发送的消息
        :return:  发送的人数
        """
        if not isinstance(message, list):
            return False, "message not list"
        try:
            m = {"send_message_id": session_id, "message": message}
            for i, j in self.queues.items():
                await j.put(m)
            return True, str(len(self.queues))
        except Exception as e:
            return False, str(e)


class ServerTools:
    def __init__(self, logger: logging.Logger):
        self.server = {}
        self.logger = logger

    async def join(self, name) -> (bool, str):
        if name not in self.server:
            self.server[name] = asyncio.Queue()
            return True, ""
        return False, "server exist"

    async def send(self, message: dict, servers: list = None) -> (bool, str):

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
