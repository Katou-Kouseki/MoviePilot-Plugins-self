import json
from typing import Optional, Union, List, Tuple, Any, Dict

from app.core.context import MediaInfo, Context
from app.core.config import settings
from app.log import logger
from app.modules import _ModuleBase, checkMessage
from app.plugins.qqmsg.qq.qq import QQ
from app.schemas import MessageChannel, CommingMessage, Notification


class QQModule(_ModuleBase):
    qq: QQ = None

    def init_module(self, url, num) -> None:
        self.qq = QQ(url=url,num=num)

    def stop(self):
        self.qq.stop()

    def init_setting(self) -> Tuple[str, Union[str, bool]]:
        return "MESSAGER", "telegram"

    def message_parser(self, body: Any, form: Any,
                       args: Any) -> Optional[CommingMessage]:
        """
        解析消息内容，返回字典，注意以下约定值：
        : 用户ID
        username: 用户名
        text: 内容
        :param body: 请求体
        :param form: 表单
        :param args: 参数
        :return: 渠道、消息体
        """
        """
            {
                'is_qq': ,
                'message': {
                    'message_id': ,
                    'user_id': ,
                    'group_id': ,        
                    'user_name': ,  
                    'date': ,
                    'text': ''
                }
            }
        """
        # 校验token
        token = args.get("token")
        if not token or token != settings.API_TOKEN:
            return None
        try:
            message: dict = json.loads(body).get('message')
            is_qq: dict = json.loads(body).get('is_qq')
            logger.info(message)
        except Exception as err:
            logger.debug(f"解析QQ消息失败：{str(err)}")
            return None
        if not is_qq:
            return None
        
        if message:
            text = message.get("text")
            user_id = message.get("user_id")
            group_id = message.get("group_id")
            # 获取用户名
            user_name = message.get("username")
            if text:
                logger.info(f"收到QQ消息：userid={user_id}, groupid={group_id}, username={user_name}, text={text}")
                return CommingMessage(channel=MessageChannel.Telegram,
                                      userid=user_id, groupid=group_id, username=user_name, text=text)
        return None

    @checkMessage(MessageChannel.Telegram)
    def post_message(self, message: Notification) -> None:
        """
        发送消息
        :param message: 消息体
        :return: 成功或失败
        """
        self.qq.send_msg(title=message.title, text=message.text,
                               image=message.image, userid=message.userid, groupid=message.groupid)

    @checkMessage(MessageChannel.Telegram)
    def post_medias_message(self, message: Notification, medias: List[MediaInfo]) -> Optional[bool]:
        """
        发送媒体信息选择列表
        :param message: 消息体
        :param medias: 媒体列表
        :return: 成功或失败
        """
        return self.qq.send_meidas_msg(title=message.title, medias=medias,
                                             userid=message.userid, groupid=message.groupid)

    @checkMessage(MessageChannel.Telegram)
    def post_torrents_message(self, message: Notification, torrents: List[Context]) -> Optional[bool]:
        """
        发送种子信息选择列表
        :param message: 消息体
        :param torrents: 种子列表
        :return: 成功或失败
        """
        return self.qq.send_torrents_msg(title=message.title, torrents=torrents, userid=message.userid, groupid=message.groupid)

    def register_commands(self, commands: Dict[str, dict]):
        """
        注册命令，实现这个函数接收系统可用的命令菜单
        :param commands: 命令字典
        """
        # self.qq.register_commands(commands)
        pass
