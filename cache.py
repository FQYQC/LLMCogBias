# TODO: cache
# receive request and request id(in case doing 1 exp for multiple times),
# if request and id has been done before, return the result

import os
import os.path as osp
import json


class Cacher:
    def __init__(
        self,
        cache_path: str,
        cache_id: str = "default",
        cache_type: str = "json",
        write_cache: bool = False,
        write_interval: int = 10,
    ):

        self.cache_path = cache_path
        self.cache_id = cache_id
        self.cache_type = cache_type
        self.write_cache = write_cache
        self.write_interval = write_interval
        self.cache = None
        self.call_count = 0
        self.cache_hit = 0
        self.last_ret = None

        self.active_bot_chatId = {}

        if not osp.exists(self.cache_path):
            if write_cache:
                os.makedirs(osp.dirname(self.cache_path), exist_ok=True)
                self.cache = {}
                self.save_cache()
                print(
                    f"Cache file not found. Created new cache file at {self.cache_path}"
                )
            else:
                raise FileNotFoundError(
                    f"Cache file not found at {self.cache_path}. Set write_cache=True to create new cache file"
                )

    def load_cache(self):
        self.cache = json.load(open(self.cache_path, "r"))

    def save_cache(self):
        json.dump(self.cache, open(self.cache_path, "w"), indent=4)

    def _request_2_respond(self, client, bot, message, chatId, *args, **kwargs):

        if chatId is None:
            chatId = self.active_bot_chatId.get(bot, None)

        ret = client.send_message(bot, message, chatId, *args, **kwargs)
        for chunk in ret:
            pass

        self.active_bot_chatId[bot] = chunk["chatId"]

        client.chat_break(bot, chatId)

        self.last_ret = {
            "is_cache": False,
            "text": chunk["text"],
            "msgPrice": chunk["msgPrice"],
            "chatId": chunk["chatId"],
            "chatCode": chunk["chatCode"],
            "bot": chunk["bot"]["displayName"],
        }

        self.active_bot_chatId[chunk["bot"]["displayName"]] = chunk["chatId"]

        return chunk["text"]

    def hitting_cache(self):
        self.cache_hit += 1
        self.last_ret = None

    def send_message(
        self,
        client,
        bot: str,
        message: str,
        chatId: int = None,
        chatCode: str = None,
        msgPrice: int = 20,
        file_path: list = [],
        suggest_replies: bool = False,
        timeout: int = 10,
        use_cache: bool = True,
        add_to_cache: bool = True,
        trial_id: int = 0,
    ):
        if not use_cache:
            return self._request_2_respond(
                client,
                bot,
                message,
                chatId,
                chatCode,
                msgPrice,
                file_path,
                suggest_replies,
                timeout,
            )

        if self.cache is None:
            self.load_cache()

        if bot not in self.cache:
            current_bot_cache = {}
        else:
            current_bot_cache = self.cache[bot]

        if message not in current_bot_cache:
            ret = self._request_2_respond(
                client,
                bot,
                message,
                chatId,
                chatCode,
                msgPrice,
                file_path,
                suggest_replies,
                timeout,
            )

            current_bot_cache[message] = {trial_id: ret}

        else:
            current_msg_cache = current_bot_cache[message]
            if trial_id not in current_msg_cache:
                ret = self._request_2_respond(
                    client,
                    bot,
                    message,
                    chatId,
                    chatCode,
                    msgPrice,
                    file_path,
                    suggest_replies,
                    timeout,
                )

                current_msg_cache[trial_id] = ret
                current_bot_cache[message].update(current_msg_cache)

            else:
                ret = current_msg_cache[trial_id]
                self.hitting_cache()

        if add_to_cache:
            if bot not in self.cache:
                self.cache[bot] = current_bot_cache
            else:
                self.cache[bot].update(current_bot_cache)

        self.call_count += 1

        if self.write_cache and self.call_count % self.write_interval == 0:
            self.save_cache()

        return ret
