# 通信方式
## 登录 
客户端->`{"username": USERNAME, "password": PASSWORD}`  
服务器回复->`{"code": 0, "message": SESSION_ID}`或`{"code": 1, "message": ERROR}`
## 发送信息
客户端->`{"action": "send", "message": [{"type": TYPE, "data": DATA}]}`  
服务端广播->`{"send_message_id": SESSION_ID, "message": 客户端发送的message}`  
> type目前只有text  
> 服务端广播中的`send_message_id`为客户端的session_id，服务器自己加入，`message`为客户端发送的`message`,不处理直接转发  
