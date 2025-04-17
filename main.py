import asyncio
import os
from pywebio import config
from pywebio import start_server
from pywebio.input import *
from pywebio.output import *
from pywebio.session import defer_call, info as session_info, run_async, run_js
from utils import validate_image

chat_msgs = {}  # Dict to store messages for each room
online_users = set()
rooms = {}  # Dict to store room information
host_ip = None  # Store host IP

MAX_MESSAGES_COUNT = 100


async def main():
    global chat_msgs, host_ip

    put_markdown("## Добро пожаловать в онлайн чат!")

    current_ip = session_info.user_ip
    
    if host_ip is None:
        is_host = await actions("Вы хост?", ["Да", "Нет"]) == "Да"
        if is_host:
            host_ip = current_ip
    
    nickname = await input("Войти в чат", required=True, placeholder="Ваше имя", 
                       validate=lambda n: "Такой ник уже используется!" if n in online_users or n == '📢' else None)
    online_users.add(nickname)
    
    is_host = current_ip == host_ip

    if is_host:
        room_action = await select("Выберите действие", ['Создать комнату', 'Присоединиться к существующей комнате'])
        if room_action == 'Создать комнату':
            room_name = await input("Введите название комнаты", required=True,
                                validate=lambda n: "Такая комната уже существует!" if n in rooms else None)
            rooms[room_name] = set([nickname])
            chat_msgs[room_name] = []
        else:
            if not rooms:
                put_error("Нет доступных комнат")
                return
            room_name = await select("Выберите комнату", list(rooms.keys()))
            rooms[room_name].add(nickname)
    else:
        if not rooms:
            put_error("Нет доступных комнат. Дождитесь, пока хост создаст комнату.")
            return
        room_name = await select("Выберите комнату для присоединения", list(rooms.keys()))
        rooms[room_name].add(nickname)
        
    put_info(f"{'Вы хост' if is_host else 'Вы участник'} | Ваш IP: {current_ip}")
    
    msg_box = output()
    def switch_room():
        run_js('window.location.reload()')
        online_users.remove(nickname)

    put_markdown(f"## Комната: {room_name}")
    put_button("Сменить комнату", onclick=lambda: run_async(switch_room()))
    put_scrollable(msg_box, height=500, keep_bottom=True)

    chat_msgs[room_name].append(('📢', f'`{nickname}` присоединился к комнате!'))
    msg_box.append(put_markdown(f'📢 `{nickname}` присоединился к комнате'))

    refresh_task = run_async(refresh_msg(nickname, msg_box, room_name))

    while True:
        data = await input_group("💭 Новое сообщение", [
            input(placeholder="Текст сообщения ...", name="msg"),
            file_upload("Изображение (опционально)", accept="image/*", name="img"),
            actions(name="cmd", buttons=["Отправить"])
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
            else:
                msg_box.append(put_image(content_data, width='300px'))

        chat_msgs[room_name].append((nickname, content))

    refresh_task.close()

    # Cleanup
    online_users.remove(nickname)
    rooms[room_name].remove(nickname)
    if not rooms[room_name]:  # If room is empty
        del rooms[room_name]
        del chat_msgs[room_name]
    else:
        chat_msgs[room_name].append(('📢', f'`{nickname}` покинул комнату!'))
        msg_box.append(put_markdown(f'📢 `{nickname}` покинул комнату!'))


async def refresh_msg(nickname, msg_box, room_name):
    last_idx = len(chat_msgs[room_name])

    while True:
        await asyncio.sleep(1)

        for m in chat_msgs[room_name][last_idx:]:
            if m[0] != nickname:
                if isinstance(m[1], str):
                    msg_box.append(put_markdown(f"`{m[0]}`: {m[1]}"))
                else:
                    msg_box.append(put_markdown(f"`{m[0]}`:"))
                    for content_type, content_data in m[1]:
                        if content_type == 'text':
                            msg_box.append(put_markdown(content_data))
                        else:
                            msg_box.append(put_image(content_data, width='300px'))

        if len(chat_msgs[room_name]) > MAX_MESSAGES_COUNT:
            chat_msgs[room_name] = chat_msgs[room_name][len(chat_msgs[room_name]) // 2:]

        last_idx = len(chat_msgs[room_name])

if __name__ == "__main__":
    start_server(main, debug=True, port=8080, cdn=False)
