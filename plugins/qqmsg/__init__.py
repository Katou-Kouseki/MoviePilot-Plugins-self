from urllib.parse import urlencode

from app.plugins import _PluginBase
from app.core.event import eventmanager, Event
from app.schemas.types import EventType, NotificationType
from app.utils.http import RequestUtils
from typing import Any, List, Dict, Tuple
from app.log import logger

import json

class QqMsg(_PluginBase):
    # 插件名称
    plugin_name = "QQ消息通知"
    # 插件描述
    plugin_desc = "支持使用QQ发送消息通知。"
    # 插件图标
    plugin_icon = "https://qzonestyle.gtimg.cn/qzone/qzact/act/external/tiqq/logo.png"
    # 主题色
    plugin_color = "#00ffff"
    # 插件版本
    plugin_version = "0.1"
    # 插件作者
    plugin_author = "anjoyli"
    # 作者主页
    author_url = "https://github.com/anjoyli"
    # 插件配置项ID前缀
    plugin_config_prefix = "qqmsg_"
    # 加载顺序
    plugin_order = 28
    # 可使用的用户级别
    auth_level = 1

    # 私有属性
    _enabled = False
    _token = None
    _msgtypes = []
    ## qq对应的api
    _send_msg_url = "http://192.168.6.189:13579/LittlePaimon/api/message2admin"

    def init_plugin(self, config: dict = None):
        if config:
            self._enabled = config.get("enabled")
            self._token = config.get("token")
            self._msgtypes = config.get("msgtypes") or []

    def get_state(self) -> bool:
        return self._enabled and (True if self._token else False)

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        pass

    def get_api(self) -> List[Dict[str, Any]]:
        pass

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """
        拼装插件配置页面，需要返回两块数据：1、页面配置；2、数据结构
        """
        # 编历 NotificationType 枚举，生成消息类型选项
        MsgTypeOptions = []
        for item in NotificationType:
            MsgTypeOptions.append({
                "title": item.value,
                "value": item.name
            })
        return [
            {
                'component': 'VForm',
                'content': [
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 6
                                },
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'enabled',
                                            'label': '启用插件',
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'token',
                                            'label': 'QQ令牌',
                                            'placeholder': 'QQxxx',
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12
                                },
                                'content': [
                                    {
                                        'component': 'VSelect',
                                        'props': {
                                            'multiple': True,
                                            'chips': True,
                                            'model': 'msgtypes',
                                            'label': '消息类型',
                                            'items': MsgTypeOptions
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                ]
            }
        ], {
            "enabled": False,
            'token': '',
            'msgtypes': []
        }

    def get_page(self) -> List[dict]:
        pass

    @eventmanager.register(EventType.NoticeMessage)
    def send(self, event: Event):
        """
        消息发送事件
        """
        if not self.get_state():
            return

        if not event.event_data:
            return

        msg_body = event.event_data
        # 渠道
        # channel = msg_body.get("channel")
        # if channel:
        #     return
        # 类型
        msg_type: NotificationType = msg_body.get("type")
        # 标题
        title = msg_body.get("title")
        # 文本
        text = msg_body.get("text")
        # 图片
        image = msg_body.get("image")

        if not title and not text:
            logger.warn("标题和内容不能同时为空")
            return

        if (msg_type and self._msgtypes
                and msg_type.name not in self._msgtypes):
            logger.info(f"消息类型 {msg_type.value} 未开启消息发送")
            return

        try:
            state, res = self.send_msg_to_qq(title=title,
                                        text=text,
                                        image=""if image == None else image,
                                        user_id="Anjoy")
        except Exception as msg_e:
            logger.error(f"QQ消息发送失败，{str(msg_e)}")

    
    def send_msg_to_qq(self, title, text="", image="", user_id=""):
        message_url = self._send_msg_url
        if text:
            conent = "%s\n%s" % (title, text.replace("\n\n", "\n"))
        else:
            conent = title
        if not user_id:
            user_id = "@Anjoy"
        req_json = {
            "user_id": user_id,
            "title": title,
            "image": image,
            "text": conent
        }
        return self.__post_request(message_url, req_json)

    def __post_request(self, message_url, req_json):
        """
        向qq发送请求
        """
        headers = {'content-type': 'application/json'}
        try:
            res = RequestUtils(headers=headers).post(message_url,
                                                     data=json.dumps(req_json, ensure_ascii=False).encode('utf-8'))
            if res and res.status_code == 200:
                ret_json = res.json()
                if ret_json.get('status') == 0:
                    return True, ret_json.get('msg')
                else:
                    return False, ret_json.get('msg')
            elif res is not None:
                return False, f"错误码：{res.status_code}，错误原因：{res.reason}"
            else:
                return False, "未获取到返回信息"
        except Exception as err:
            return False, str(err)
    

    def stop_service(self):
        """
        退出插件
        """
        pass
