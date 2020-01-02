# 获取所有服务器
GET或POST`/dns`  
返回
```
[
  {
    "name": NAME,
    "ipv6": [
      IPV6s
    ],
    "ipv4": [
      IPV4s
    ]
  }
  ......
]
```
# 添加服务器
POST`/dns/add`
```
{
  "name": NAME,
  "ipv6": [
    IPV6s
  ],
  "ipv4": [
    IPV4s
  ]
}```