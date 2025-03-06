import asyncio
import os
from pywebio import start_server
from pywebio.input import *
from pywebio.output import *
from pywebio.session import defer_call, info as session_info, run_async, run_js
from utils import validate_image
from pywebio import config
chat_msgs = []
online_users = set()

a = True

MAX_MESSAGES_COUNT = 100


@config(theme='dark')


async def main():
    

    global chat_msgs
    
    put_markdown("## Добро пожаловать в онлайн чат!\nОбщайтесь и делитесь изображениями!")

    msg_box = output()
 
    
    put_scrollable(msg_box, height=500, keep_bottom=True)

    nickname = await input("Войти в чат", required=True, placeholder="Ваше имя", 
                       validate=lambda n: "Такой ник уже используется!" if n in online_users or n == '📢' else None)
    online_users.add(nickname)

    chat_msgs.append(('📢', f'`{nickname}` присоединился к чату!'))
    msg_box.append(put_markdown(f'📢 `{nickname}` присоединился к чату'))

    refresh_task = run_async(refresh_msg(nickname, msg_box))

    while True:
        data = await input_group("💭 Новое сообщение", [
            
            input(placeholder="Текст сообщения ...", name="msg"),
            file_upload("Изображение (опционально)", accept="image/*", name="img"),
            actions(name="cmd", buttons=["Отправить", {'label': "Выйти из чата", 'type': 'cancel'}])
        ], validate = lambda m: ('msg', "Введите текст сообщения или загрузите изображение!") 
                             if m["cmd"] == "Отправить" and not m['msg'] and not m['img'] else None)
        
        if data is None:
            break
        
        content = []
        if data['msg']:
            content.append(('text', data['msg']))


        if data['img']:
            img_data = data['img']['content']
            img_base64, error = validate_image(img_data)
            if error:
                toast(error)
                continue
            content.append(('image', img_base64))


        msg_box.append(put_markdown(f"`{nickname}`:"))
        for content_type, content_data in content:
            if content_type == 'text':
                msg_box.append(put_markdown(content_data))
            else:  # image
                msg_box.append(put_image(content_data, width='300px'))


        chat_msgs.append((nickname, content))

    refresh_task.close()

    online_users.remove(nickname)
    toast("Вы вышли из чата!")
    msg_box.append(put_markdown(f'📢 Пользователь `{nickname}` покинул чат!'))
    chat_msgs.append(('📢', f'Пользователь `{nickname}` покинул чат!'))

    put_buttons(['Перезайти'], onclick=lambda btn:run_js('window.location.reload()'))

async def refresh_msg(nickname, msg_box):
    global chat_msgs
    last_idx = len(chat_msgs)

    while True:
        await asyncio.sleep(1)

        for m in chat_msgs[last_idx:]:
            if m[0] != nickname:  # if not a message from current user
                if isinstance(m[1], str):  # System message
                    msg_box.append(put_markdown(f"`{m[0]}`: {m[1]}"))
                else:  # User message with possible image
                    msg_box.append(put_markdown(f"`{m[0]}`:"))
                    for content_type, content_data in m[1]:
                        if content_type == 'text':
                            msg_box.append(put_markdown(content_data))

                        else:  # image
                            msg_box.append(put_image(content_data, width='300px'))

        # remove expired
        if len(chat_msgs) > MAX_MESSAGES_COUNT:
            chat_msgs = chat_msgs[len(chat_msgs) // 2:]

        last_idx = len(chat_msgs)
if __name__ == "__main__":
    start_server(main, debug=True, port=8080, cdn=False)