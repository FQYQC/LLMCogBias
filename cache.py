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

    def load_cache(self):
        self.cache = json.load(open(self.cache_path, "r"))

    def save_cache(self):
        json.dump(self.cache, open(self.cache_path, "w"))

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
            return client.send_message(
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
            ret = client.send_message(
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
                ret = client.send_message(
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

        if add_to_cache:
            self.cache[bot].update(current_bot_cache)

        self.call_count += 1

        if self.write_cache and self.call_count % self.write_interval == 0:
            self.save_cache()

        return ret
